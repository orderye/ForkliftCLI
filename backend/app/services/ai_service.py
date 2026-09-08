import httpx
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.forklift import ForkliftModel
from app.models.ai import KnowledgeDocument, KnowledgeChunk, FaultTree
from app.services.embedding_service import get_text_embedding
from app.core.vector_store import search_similar, ensure_collection

settings = get_settings()


def _retrieve_context(query: str, forklift_model_id: int | None = None, top_k: int = 5) -> str:
    """用 WeMM 向量化查询，从 Qdrant 召回相关资料片段。"""
    try:
        ensure_collection()
        vec = get_text_embedding(query)
        hits = search_similar(vec, top_k=top_k, forklift_model_id=forklift_model_id)
        if not hits:
            return ""
        lines = []
        for h in hits:
            p = h.get("payload", {})
            title = p.get("title", "")
            text = p.get("text", "")
            url = p.get("url", "")
            lines.append(f"- {title}: {text[:300]}{' (' + url + ')' if url else ''}")
        return "\n".join(lines)
    except Exception:
        return ""


class AIService:
    def __init__(self, db: Session):
        self.db = db

    def _build_system_prompt(
        self,
        query: str,
        forklift_model_id: int | None = None,
        engine_model_id: int | None = None,
    ) -> str:
        prompt = (
            "你是「ForkliftCLI」AI维修助手，专门负责叉车维修技术支持。\n"
            "请用专业但易懂的方式回答维修相关问题。\n"
            "涉及安全操作时，必须给出安全提示。\n"
            "不要编造不确定的维修参数，如果知识库中没有相关信息，请诚实告知。\n"
        )

        if forklift_model_id:
            model = self.db.query(ForkliftModel).filter(
                ForkliftModel.id == forklift_model_id
            ).first()
            if model:
                prompt += f"\n当前叉车车型: {model.series.brand.name} {model.name}"
                if model.load_capacity_kg:
                    prompt += f"，额定载荷: {model.load_capacity_kg}kg"
                if model.fuel_type:
                    prompt += f"，燃料类型: {model.fuel_type}"

        # 检索相关知识库文档
        if forklift_model_id:
            chunks = (
                self.db.query(KnowledgeChunk)
                .join(KnowledgeDocument)
                .filter(KnowledgeDocument.forklift_model_id == forklift_model_id)
                .limit(5)
                .all()
            )
            if chunks:
                prompt += "\n\n相关维修资料:\n"
                for chunk in chunks:
                    prompt += f"- {chunk.chunk_text[:500]}\n"

        # 检索故障树
        if forklift_model_id:
            trees = (
                self.db.query(FaultTree)
                .filter(FaultTree.forklift_model_id == forklift_model_id)
                .limit(3)
                .all()
            )
            if trees:
                prompt += "\n\n已知故障信息:\n"
                for tree in trees:
                    prompt += f"- 症状: {tree.symptom}\n"

        # 向量召回：WeMM + Qdrant
        ctx = _retrieve_context(query, forklift_model_id)
        if ctx:
            prompt += "\n\n检索到的相关资料:\n" + ctx

        return prompt

    def chat(
        self,
        message: str,
        forklift_model_id: int | None = None,
        engine_model_id: int | None = None,
        history: list = None,
    ) -> dict:
        system_prompt = self._build_system_prompt(message, forklift_model_id, engine_model_id)

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history:
                messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": message})

        try:
            reply = self._call_llm(messages)
        except Exception as e:
            reply = f"AI服务暂时不可用，请稍后重试。错误信息: {str(e)}"

        return {
            "reply": reply,
            "sources": [],
            "suggestions": [
                "查看相关结构图",
                "查看常见故障",
                "查看配件信息",
            ],
        }

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

        # 检索故障树
        if forklift_model_id:
            trees = (
                self.db.query(FaultTree)
                .filter(FaultTree.forklift_model_id == forklift_model_id)
                .all()
            )
            for tree in trees:
                system_prompt += f"\n已知故障: {tree.symptom}"
                if tree.causes_json:
                    system_prompt += f"\n原因: {tree.causes_json}"
                if tree.solutions_json:
                    system_prompt += f"\n解决方案: {tree.solutions_json}"

        ctx = _retrieve_context(symptom, forklift_model_id)
        if ctx:
            system_prompt += "\n\n检索到的相关资料:\n" + ctx

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"故障症状: {symptom}"},
        ]

        try:
            reply = self._call_llm(messages)
        except Exception as e:
            reply = f"诊断服务暂时不可用: {str(e)}"

        return {
            "possible_causes": [
                {"cause": "请参考AI回复获取详细诊断结果", "probability": "参见回复"}
            ],
            "check_order": ["请参考AI回复获取检查步骤"],
            "safety_warnings": [
                "维修前请先停车、熄火",
                "释放液压压力",
                "固定门架",
                "请由具备相应资质的维修人员操作",
            ],
            "references": [reply],
        }

    def _call_llm(self, messages: list) -> str:
        if not settings.AI_API_KEY:
            return "AI服务未配置，请在 .env 文件中设置 AI_API_KEY"

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
