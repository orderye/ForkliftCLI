"""验收测试脚本 — 验证 5 项验收指标

1. 铭牌识别成功率 ≥90% (10张铭牌)
2. 型号识别准确率 ≥95% (20个型号)
3. 车型匹配成功率 ≥95% (手动输入)
4. AI 引用资料 — 能引用知识库
5. AI 不编造参数 — 不存在的问题诚实告知

运行: python scripts/acceptance_test.py
"""
import sys
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("USE_MEMORY_STORE", "true")

from app.core.database import SessionLocal
from app.models.forklift import ForkliftModel, ForkliftSeries, ForkliftBrand
from app.models.engine import EngineModel
from app.models.ai import KnowledgeDocument, KnowledgeChunk, FaultTree, FaultCode
from app.services.ocr_service import OCRService
from app.services.ai_service import AIService

# ─── 测试用例数据 ───────────────────────────────────────────────

# 10 张铭牌模拟 OCR 文本（模拟 PaddleOCR 输出）
NAMEPLATE_TEST_CASES = [
    {
        "id": 1,
        "simulated_ocr_text": "TOYOTA\n8FG30\nSerial: 8FG30-12345\n3000kg\n2023\nEngine: 4Y",
        "expected_brand": "TOYOTA",
        "expected_model": "8FG30",
        "expected_engine": "4Y",
    },
    {
        "id": 2,
        "simulated_ocr_text": "TOYOTA\n8FG25\nSN: 8FG25-67890\n2500kg\n2022\nEngine: 1DZ",
        "expected_brand": "TOYOTA",
        "expected_model": "8FG25",
        "expected_engine": "1DZ",
    },
    {
        "id": 3,
        "simulated_ocr_text": "HELI 合力\nH30\n序列号: H30-001\n3000kg\n2023",
        "expected_brand": "HELI",
        "expected_model": "H30",
        "expected_engine": "",
    },
    {
        "id": 4,
        "simulated_ocr_text": "HELI 合力\nCPD30\nSN: CPD30-002\n3000kg\n2024",
        "expected_brand": "HELI",
        "expected_model": "CPD30",
        "expected_engine": "",
    },
    {
        "id": 5,
        "simulated_ocr_text": "HANGCHA 杭叉\nCPCD30\nSerial: CPCD30-003\n3000kg\n2023\nEngine: 4JG2",
        "expected_brand": "HANGCHA",
        "expected_model": "CPCD30",
        "expected_engine": "4JG2",
    },
    {
        "id": 6,
        "simulated_ocr_text": "HANGCHA 杭叉\nA25\n序列号: A25-004\n2500kg\n2022",
        "expected_brand": "HANGCHA",
        "expected_model": "A25",
        "expected_engine": "",
    },
    {
        "id": 7,
        "simulated_ocr_text": "LINDE 林德\nH30\nSN: H30-L01\n3000kg\n2023",
        "expected_brand": "LINDE",
        "expected_model": "H30",
        "expected_engine": "",
    },
    {
        "id": 8,
        "simulated_ocr_text": "LINDE 林德\nE20\nSerial: E20-L02\n2000kg\n2024",
        "expected_brand": "LINDE",
        "expected_model": "E20",
        "expected_engine": "",
    },
    {
        "id": 9,
        "simulated_ocr_text": "TOYOTA 丰田\n8FBE15\nSN: 8FBE15-005\n1500kg\n2023",
        "expected_brand": "TOYOTA",
        "expected_model": "8FBE15",
        "expected_engine": "",
    },
    {
        "id": 10,
        "simulated_ocr_text": "HELI 合力\nH25\n序列号: H25-006\n2500kg\n2022\nEngine: 4JG2",
        "expected_brand": "HELI",
        "expected_model": "H25",
        "expected_engine": "4JG2",
    },
]

# 20 个型号匹配测试用例
MODEL_MATCH_CASES = [
    {"input_brand": "TOYOTA", "input_model": "8FG30", "expected_id": 1},
    {"input_brand": "TOYOTA", "input_model": "8FG25", "expected_id": 2},
    {"input_brand": "TOYOTA", "input_model": "8FG35", "expected_id": 3},
    {"input_brand": "TOYOTA", "input_model": "8FBN25", "expected_id": 4},
    {"input_brand": "TOYOTA", "input_model": "8FBE15", "expected_id": 5},
    {"input_brand": "HELI", "input_model": "H30", "expected_id": 6},
    {"input_brand": "HELI", "input_model": "H25", "expected_id": 7},
    {"input_brand": "HELI", "input_model": "H20", "expected_id": 8},
    {"input_brand": "HELI", "input_model": "CPD30", "expected_id": 9},
    {"input_brand": "HELI", "input_model": "CPD25", "expected_id": 10},
    {"input_brand": "HANGCHA", "input_model": "A30", "expected_id": 11},
    {"input_brand": "HANGCHA", "input_model": "A25", "expected_id": 12},
    {"input_brand": "HANGCHA", "input_model": "A20", "expected_id": 13},
    {"input_brand": "HANGCHA", "input_model": "CPCD30", "expected_id": 14},
    {"input_brand": "HANGCHA", "input_model": "CPCD25", "expected_id": 15},
    {"input_brand": "LINDE", "input_model": "H30", "expected_id": 16},
    {"input_brand": "LINDE", "input_model": "H25", "expected_id": 17},
    {"input_brand": "LINDE", "input_model": "E20", "expected_id": 18},
    {"input_brand": "LINDE", "input_model": "E16", "expected_id": 19},
    {"input_brand": "LINDE", "input_model": "R20", "expected_id": 20},
]

# AI 知识库问题测试用例
AI_RAG_QUESTIONS = [
    "发动机无法启动，仪表盘无任何指示灯亮起，是什么原因？",
    "液压系统压力低，举升缓慢怎么解决？",
    "制动系统磨损了怎么处理？",
]

# AI 幻觉测试用例（不存在的参数/问题）
AI_HALLUCINATION_QUESTIONS = [
    "叉车 XYZ-9999 的最大起升速度是多少？",
    "请问 8FG30 的核反应堆功率是多少千瓦？",
    "8FG30 的量子推进器规格是什么？",
]


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─── 测试 1: 铭牌识别 ───────────────────────────────────────────
def test_nameplate_ocr(db) -> dict:
    """测试铭牌 OCR 字段提取（模拟 OCR 文本输入）"""
    separator("测试 1: 铭牌识别成功率 (目标 ≥90%)")
    ocr = OCRService()
    passed = 0
    total = len(NAMEPLATE_TEST_CASES)
    details = []

    for tc in NAMEPLATE_TEST_CASES:
        # 直接调用 _extract_fields 模拟 OCR 后的字段提取
        fields = ocr._extract_fields(tc["simulated_ocr_text"])

        # 品牌匹配：接受中英文（因为 OCR 可能识别到中文或英文）
        actual_brand = fields.get("brand", "").upper()
        expected_brand = tc["expected_brand"].upper()
        # 如果预期是英文品牌，也接受对应的中文
        brand_aliases = {
            "TOYOTA": ["TOYOTA", "丰田"],
            "HELI": ["HELI", "合力"],
            "HANGCHA": ["HANGCHA", "杭叉"],
            "LINDE": ["LINDE", "林德"],
        }
        acceptable_brands = brand_aliases.get(expected_brand, [expected_brand])
        brand_ok = actual_brand in [b.upper() for b in acceptable_brands]
        model_ok = fields.get("model", "").upper() == tc["expected_model"].upper()
        engine_ok = True  # 发动机型号可能为空，不强制要求
        if tc["expected_engine"]:
            engine_ok = fields.get("engine_model", "").upper() == tc["expected_engine"].upper()

        case_pass = brand_ok and model_ok and engine_ok
        if case_pass:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        detail = {
            "id": tc["id"],
            "status": status,
            "expected_brand": tc["expected_brand"],
            "actual_brand": fields.get("brand", ""),
            "expected_model": tc["expected_model"],
            "actual_model": fields.get("model", ""),
            "expected_engine": tc["expected_engine"],
            "actual_engine": fields.get("engine_model", ""),
        }
        details.append(detail)
        print(f"  [{status}] 铭牌 #{tc['id']}: brand={fields.get('brand','')}/{tc['expected_brand']}, "
              f"model={fields.get('model','')}/{tc['expected_model']}, "
              f"engine={fields.get('engine_model','')}/{tc['expected_engine']}")

    rate = passed / total * 100
    target_met = rate >= 90
    print(f"\n  结果: {passed}/{total} = {rate:.0f}% {'✅ 达标' if target_met else '❌ 未达标'}")

    return {"passed": passed, "total": total, "rate": rate, "target_met": target_met, "details": details}


# ─── 测试 2: 型号识别准确率 ─────────────────────────────────────
def test_model_matching(db) -> dict:
    """测试型号匹配到数据库中的车型"""
    separator("测试 2: 型号识别准确率 (目标 ≥95%)")
    ocr = OCRService()
    passed = 0
    total = len(MODEL_MATCH_CASES)
    details = []

    for tc in MODEL_MATCH_CASES:
        fields = {"brand": tc["input_brand"], "model": tc["input_model"]}
        matched_id = ocr.match_forklift_model(fields, db)

        if matched_id == tc["expected_id"]:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        detail = {
            "id": tc["input_model"],
            "status": status,
            "input_brand": tc["input_brand"],
            "input_model": tc["input_model"],
            "expected_id": tc["expected_id"],
            "actual_id": matched_id,
        }
        details.append(detail)
        print(f"  [{status}] {tc['input_brand']} {tc['input_model']}: "
              f"matched={matched_id}, expected={tc['expected_id']}")

    rate = passed / total * 100
    target_met = rate >= 95
    print(f"\n  结果: {passed}/{total} = {rate:.0f}% {'✅ 达标' if target_met else '❌ 未达标'}")

    return {"passed": passed, "total": total, "rate": rate, "target_met": target_met, "details": details}


# ─── 测试 3: 车型匹配成功率（手动输入）────────────────────────
def test_manual_match(db) -> dict:
    """测试手动输入品牌+型号的匹配"""
    separator("测试 3: 车型匹配成功率 (目标 ≥95%)")
    ocr = OCRService()
    passed = 0
    total = len(MODEL_MATCH_CASES)
    details = []

    for tc in MODEL_MATCH_CASES:
        fields = {"brand": tc["input_brand"], "model": tc["input_model"]}
        matched_id = ocr.match_forklift_model(fields, db)
        if matched_id is not None:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        details.append({"input": f"{tc['input_brand']} {tc['input_model']}", "matched": matched_id, "status": status})
        print(f"  [{status}] {tc['input_brand']} {tc['input_model']}: matched_id={matched_id}")

    rate = passed / total * 100
    target_met = rate >= 95
    print(f"\n  结果: {passed}/{total} = {rate:.0f}% {'✅ 达标' if target_met else '❌ 未达标'}")

    return {"passed": passed, "total": total, "rate": rate, "target_met": target_met, "details": details}


# ─── 测试 4: AI 引用资料 ───────────────────────────────────────
def test_ai_rag(db) -> dict:
    """测试 AI 能引用知识库资料"""
    separator("测试 4: AI 引用资料 (目标: 能引用)")
    ai = AIService(db)
    passed = 0
    total = len(AI_RAG_QUESTIONS)
    details = []

    for q in AI_RAG_QUESTIONS:
        try:
            result = ai.chat(message=q, forklift_model_id=1, engine_model_id=1)
            reply = result.get("reply", "")
            # 检查回复是否非空且包含实质性内容
            has_content = len(reply) > 50
            # 检查是否引用了知识库内容（来源标记或知识库关键词）
            has_reference = any(kw in reply for kw in ["来源", "维修", "检查", "故障", "原因", "安全", "液压", "发动机", "制动"])

            if has_content and has_reference:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"

            details.append({
                "question": q,
                "status": status,
                "reply_length": len(reply),
                "has_reference": has_reference,
                "reply_preview": reply[:120],
            })
            print(f"  [{status}] Q: {q[:30]}...")
            print(f"         A: {reply[:80]}...")
        except Exception as e:
            details.append({"question": q, "status": "ERROR", "error": str(e)})
            print(f"  [ERROR] Q: {q[:30]}... -> {e}")

    rate = passed / total * 100
    target_met = passed == total
    print(f"\n  结果: {passed}/{total} = {rate:.0f}% {'✅ 达标' if target_met else '❌ 未达标'}")

    return {"passed": passed, "total": total, "rate": rate, "target_met": target_met, "details": details}


# ─── 测试 5: AI 不编造参数 ─────────────────────────────────────
def test_ai_no_hallucination(db) -> dict:
    """测试 AI 对不存在的问题诚实告知"""
    separator("测试 5: AI 不编造参数 (目标: 诚实告知)")
    ai = AIService(db)
    passed = 0
    total = len(AI_HALLUCINATION_QUESTIONS)
    details = []

    for q in AI_HALLUCINATION_QUESTIONS:
        try:
            result = ai.chat(message=q, forklift_model_id=1, engine_model_id=1)
            reply = result.get("reply", "")
            # 检查 AI 是否承认不知道 / 拒绝编造
            honesty_keywords = [
                "没有", "无法", "不确定", "不存在", "不知道", "未找到",
                "没有相关", "无法提供", "不提供", "无相关", "查不到",
                "not", "没有这个", "不存在的", "不属于", "无此",
            ]
            is_honest = any(kw in reply for kw in honesty_keywords) or len(reply) < 200

            if is_honest:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"

            details.append({
                "question": q,
                "status": status,
                "is_honest": is_honest,
                "reply_preview": reply[:150],
            })
            print(f"  [{status}] Q: {q[:40]}...")
            print(f"         A: {reply[:100]}...")
        except Exception as e:
            details.append({"question": q, "status": "ERROR", "error": str(e)})
            print(f"  [ERROR] Q: {q[:40]}... -> {e}")

    rate = passed / total * 100
    target_met = passed == total
    print(f"\n  结果: {passed}/{total} = {rate:.0f}% {'✅ 达标' if target_met else '❌ 未达标'}")

    return {"passed": passed, "total": total, "rate": rate, "target_met": target_met, "details": details}


# ─── 主函数 ─────────────────────────────────────────────────────
def main():
    separator("ForkliftCLI 验收测试")
    db = SessionLocal()
    results = {}

    # 数据库概览
    print(f"\n数据库状态:")
    print(f"  品牌: {db.query(ForkliftBrand).count()}")
    print(f"  车型: {db.query(ForkliftModel).count()}")
    print(f"  发动机: {db.query(EngineModel).count()}")
    print(f"  知识文档: {db.query(KnowledgeDocument).count()}")
    print(f"  知识分块: {db.query(KnowledgeChunk).count()}")
    print(f"  故障代码: {db.query(FaultCode).count()}")
    print(f"  故障树: {db.query(FaultTree).count()}")

    try:
        # 测试 1: 铭牌识别
        results["nameplate_ocr"] = test_nameplate_ocr(db)

        # 测试 2: 型号识别
        results["model_match"] = test_model_matching(db)

        # 测试 3: 车型匹配（手动输入）
        results["manual_match"] = test_manual_match(db)

        # 测试 4: AI 引用资料
        results["ai_rag"] = test_ai_rag(db)

        # 测试 5: AI 不编造参数
        results["ai_no_hallucination"] = test_ai_no_hallucination(db)
    finally:
        db.close()

    # ─── 汇总报告 ───────────────────────────────────────────
    separator("验收测试汇总报告")
    tests = [
        ("铭牌识别成功率", results.get("nameplate_ocr", {}), "≥90%"),
        ("型号识别准确率", results.get("model_match", {}), "≥95%"),
        ("车型匹配成功率", results.get("manual_match", {}), "≥95%"),
        ("AI引用资料", results.get("ai_rag", {}), "能引用"),
        ("AI不编造参数", results.get("ai_no_hallucination", {}), "诚实告知"),
    ]

    all_pass = True
    for name, r, target in tests:
        passed = r.get("passed", 0)
        total = r.get("total", 0)
        rate = r.get("rate", 0)
        met = r.get("target_met", False)
        mark = "✅" if met else "❌"
        print(f"  {mark} {name}: {passed}/{total} = {rate:.0f}% (目标: {target})")
        if not met:
            all_pass = False

    print(f"\n{'='*60}")
    if all_pass:
        print("  🎉 全部验收指标达标！")
    else:
        print("  ⚠️ 部分指标未达标，请查看上方详细日志。")
    print(f"{'='*60}")

    # 保存 JSON 报告
    report_path = ROOT / "test_data" / "acceptance_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    main()
