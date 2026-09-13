import re
import logging

import httpx
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.forklift import ForkliftModel
from app.models.ai import KnowledgeDocument, KnowledgeChunk, FaultTree
from app.models.copyright_mixin import license_active_condition, naive_utc_now
from app.services.embedding_service import get_text_embedding
from app.core.vector_store import search_similar, ensure_collection

logger = logging.getLogger(__name__)
settings = get_settings()


def _source_label(payload: dict) -> str:
    title = (payload.get("title") or "").strip()
    url = (payload.get("url") or "").strip()
    if title and url:
        return f"{title}（{url}）"
    return title or url


def _retrieve_context(
    query: str,
    forklift_model_id: int | None = None,
    engine_model_id: int | None = None,
    top_k: int = 5,
    db: Session | None = None,
) -> tuple[str, list[str]]:
    """双路召回并返回可注入提示词的上下文及去重来源。"""
    sections: list[str] = []
    sources: list[str] = []

    def add_source(payload: dict) -> None:
        source = _source_label(payload)
        if source and source not in sources:
            sources.append(source)

    try:
        ensure_collection()
        vec = get_text_embedding(query)
        hits = search_similar(
            vec,
            top_k=top_k,
            forklift_model_id=forklift_model_id,
            engine_model_id=engine_model_id,
        )
        if db is not None and hits:
            doc_ids = {h.get("payload", {}).get("doc_id") for h in hits}
            doc_ids.discard(None)
            if doc_ids:
                expired_ids = {
                    row.id
                    for row in db.query(KnowledgeDocument.id)
                    .filter(
                        KnowledgeDocument.id.in_(doc_ids),
                        KnowledgeDocument.license_expire.isnot(None),
                        KnowledgeDocument.license_expire < naive_utc_now(),
                    )
                    .all()
                }
                hits = [h for h in hits if h.get("payload", {}).get("doc_id") not in expired_ids]
        if hits:
            lines = []
            for h in hits:
                p = h.get("payload", {})
                add_source(p)
                title = p.get("title", "")
                text = p.get("text", "")
                url = p.get("url", "")
                cite = f" [来源: {url}]" if url else ""
                lines.append(f"- {title}: {text[:300]}{cite}")
            sections.append("(WeMM 召回)\n" + "\n".join(lines))
    except Exception:
        logger.exception("WeMM vector retrieval failed (query=%s)", query[:80])

    if db is not None:
        try:
            from app.core.hybrid_retriever import retrieve as hybrid_retrieve, format_for_prompt
            zh_hits = hybrid_retrieve(
                query,
                db,
                top_n=top_k,
                forklift_model_id=forklift_model_id,
                engine_model_id=engine_model_id,
            )
            for hit in zh_hits:
                add_source(hit.get("payload", {}))
            zh_text = format_for_prompt(zh_hits, max_chars=300)
            if zh_text:
                sections.append("(BM25+MiniLM 混合召回)\n" + zh_text)
        except Exception:
            logger.exception("hybrid retrieval failed (query=%s)", query[:80])

    return "\n\n".join(s for s in sections if s), sources


# ── diagnose 结果解析 ──────────────────────────────────────────
_RE_CAUSES = re.compile(r"可能原因[:：]\s*\n?(.*?)(?=\n检查顺序|\n安全提示|$)", re.S)
_RE_CHECKS = re.compile(r"检查顺序[:：]\s*\n?(.*?)(?=\n安全提示|$)", re.S)
_RE_SAFETY = re.compile(r"安全提示[:：]\s*\n?(.*?)$", re.S)


def _parse_diagnosis(llm_text: str) -> dict:
    """尝试从 LLM 输出中提取结构化诊断字段，失败则返回原文。"""
    causes_raw = _RE_CAUSES.search(llm_text)
    checks_raw = _RE_CHECKS.search(llm_text)
    safety_raw = _RE_SAFETY.search(llm_text)

    def _split_list(text: str | None) -> list[str]:
        if not text:
            return []
        return [line.lstrip("0123456789.-·、 ").strip() for line in text.strip().splitlines() if line.strip()]

    causes = _split_list(causes_raw.group(1) if causes_raw else None)
    checks = _split_list(checks_raw.group(1) if checks_raw else None)
    safety = _split_list(safety_raw.group(1) if safety_raw else None)

    return {
        "possible_causes": [{"cause": c, "probability": ""} for c in causes] or [{"cause": llm_text, "probability": ""}],
        "check_order": checks or ["请参考AI回复"],
        "safety_warnings": safety or [
            "维修前请先停车、熄火",
            "释放液压压力",
            "固定门架",
            "请由具备相应资质的维修人员操作",
        ],
        "references": [llm_text],
    }


class AIService:
    def __init__(self, db: Session):
        self.db = db

    # ── 车型信息检索 ──────────────────────────────────────────
    def _get_model_info(self, forklift_model_id: int | None) -> str:
        if not forklift_model_id:
            return ""
        model = self.db.query(ForkliftModel).filter(
            ForkliftModel.id == forklift_model_id
        ).first()
        if not model:
            return ""
        info = f"\n当前叉车车型: {model.series.brand.name} {model.name}"
        if model.load_capacity_kg:
            info += f"，额定载荷: {model.load_capacity_kg}kg"
        if model.fuel_type:
            info += f"，燃料类型: {model.fuel_type}"
        return info

    # ── 知识库分片检索 ────────────────────────────────────────
    def _get_knowledge_chunks(
        self,
        forklift_model_id: int | None = None,
        engine_model_id: int | None = None,
        limit: int = 5,
    ) -> str:
        q = (
            self.db.query(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .filter(license_active_condition(KnowledgeDocument.license_expire))  # 授权过期文档不参与召回
        )
        if forklift_model_id:
            q = q.filter(KnowledgeDocument.forklift_model_id == forklift_model_id)
        if engine_model_id:
            q = q.filter(KnowledgeDocument.engine_model_id == engine_model_id)
        rows = q.limit(limit).all()
        if not rows:
            return ""
        parts = []
        for chunk, doc in rows:
            cite = doc.title or ""
            if doc.source:
                cite += f"（来源: {doc.source}）"
            parts.append(f"- {cite}: {chunk.chunk_text[:500]}\n")
        return "\n\n相关维修资料:\n" + "".join(parts)

    # ── 故障树检索 ────────────────────────────────────────────
    def _get_fault_trees(
        self,
        forklift_model_id: int | None = None,
        engine_model_id: int | None = None,
        limit: int = 5,
    ) -> str:
        q = self.db.query(FaultTree)
        if forklift_model_id:
            q = q.filter(FaultTree.forklift_model_id == forklift_model_id)
        if engine_model_id:
            q = q.filter(FaultTree.engine_model_id == engine_model_id)
        trees = q.limit(limit).all()
        if not trees:
            return ""
        lines = ["\n\n已知故障信息:"]
        for t in trees:
            lines.append(f"- 症状: {t.symptom}")
            if t.causes_json:
                lines.append(f"  原因: {t.causes_json}")
            if t.solutions_json:
                lines.append(f"  解决方案: {t.solutions_json}")
        return "\n".join(lines)

    # ── system prompt 构建 ────────────────────────────────────
    def _build_system_prompt(
        self,
        query: str,
        forklift_model_id: int | None = None,
        engine_model_id: int | None = None,
        retrieved_context: str = "",
    ) -> str:
        prompt = (
            "你是「ForkliftCLI」AI维修助手，专门负责叉车维修技术支持。\n"
            "请用专业但易懂的方式回答维修相关问题。\n"
            "涉及安全操作时，必须给出安全提示。\n"
            "不要编造不确定的维修参数，如果知识库中没有相关信息，请诚实告知。\n"
        )
        prompt += self._get_model_info(forklift_model_id)
        prompt += self._get_knowledge_chunks(forklift_model_id, engine_model_id)
        prompt += self._get_fault_trees(forklift_model_id, engine_model_id)

        if retrieved_context:
            prompt += "\n\n检索到的相关资料:\n" + retrieved_context

        return prompt

    # ── 对话 ──────────────────────────────────────────────────
    def chat(
        self,
        message: str,
        forklift_model_id: int | None = None,
        engine_model_id: int | None = None,
        history: list = None,
    ) -> dict:
        ctx, sources = _retrieve_context(
            message,
            forklift_model_id,
            engine_model_id,
            db=self.db,
        )
        system_prompt = self._build_system_prompt(message, forklift_model_id, engine_model_id, ctx)

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history:
                if isinstance(h, dict):
                    messages.append({"role": h["role"], "content": h["content"]})
                else:
                    messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": message})

        try:
            reply = self._call_llm(messages)
        except Exception:
            logger.exception("AI chat LLM call failed")
            reply = "AI服务暂时不可用，请稍后重试。"

        return {
            "reply": reply,
            "sources": sources,
            "suggestions": [
                "查看相关结构图",
                "查看常见故障",
                "查看配件信息",
            ],
        }

    # ── 故障诊断 ──────────────────────────────────────────────
    def diagnose(
        self,
        symptom: str,
        forklift_model_id: int | None = None,
        engine_model_id: int | None = None,
    ) -> dict:
        system_prompt = (
            "你是叉车故障诊断专家。根据用户描述的症状，给出可能的故障原因、检查顺序和安全提示。\n"
            "请严格按照以下格式输出:\n"
            "可能原因: [列出可能原因，按概率从高到低排序，每个标注概率(高/中/低)]\n"
            "检查顺序: [列出建议的检查步骤]\n"
            "安全提示: [维修前必须注意的安全事项]\n"
        )

        system_prompt += self._get_knowledge_chunks(forklift_model_id, engine_model_id)
        system_prompt += self._get_fault_trees(forklift_model_id, engine_model_id)

        ctx, _ = _retrieve_context(
            symptom,
            forklift_model_id,
            engine_model_id,
            db=self.db,
        )
        if ctx:
            system_prompt += "\n\n检索到的相关资料:\n" + ctx

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"故障症状: {symptom}"},
        ]

        try:
            reply = self._call_llm(messages)
        except Exception:
            logger.exception("AI diagnose LLM call failed")
            reply = "诊断服务暂时不可用，请稍后重试。"

        return _parse_diagnosis(reply)

    # ── LLM 调用 ──────────────────────────────────────────────
    def _call_llm(self, messages: list) -> str:
        if not settings.AI_API_KEY:
            return "AI服务未配置，请在 .env 文件中设置 AI_API_KEY"
        if not settings.AI_BASE_URL:
            return "AI服务未配置，请在 .env 文件中设置 AI_BASE_URL"

        with httpx.Client(timeout=60) as client:
            response = client.post(
                f"{settings.AI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                json={
                    "model": settings.AI_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
