# 型号识别测试集

目标：型号识别准确率 ≥95% (20个型号)

数据说明：
- 来源：backend/app/data/seed_brands.py
- 每条记录包含叉车型号 + 发动机型号组合
- 用于验证 OCR 识别后车型/发动机匹配逻辑

测试用例格式 (JSON)：

```json
{
  "test_cases": [
    {
      "id": 1,
      "ocr_output": "CPCD30",
      "expected_forklift_model": "CPCD30",
      "expected_engine_model": "CF75A-K13",
      "expected_match": true
    },
    ...
  ]
}
```

验收标准：
1. OCR 识别结果能正确匹配到叉车型号
2. 型号识别准确率 ≥95%
3. 无匹配时返回空/null（不编造参数）