import re
from io import BytesIO
from PIL import Image


class OCRService:
    """铭牌OCR识别服务"""

    def recognize_nameplate(self, image_bytes: bytes, filename: str = "") -> dict:
        """
        识别叉车铭牌图片，提取结构化信息。
        返回: {
            "raw_text": "原始OCR文本",
            "fields": {
                "brand": "品牌",
                "model": "型号",
                "serial_number": "序列号",
                ...
            },
            "matched_model_id": None,
            "confidence": 0.0,
        }
        """
        try:
            image = Image.open(BytesIO(image_bytes))
        except Exception:
            return {"error": "无法解析图片"}

        # 尝试使用PaddleOCR
        raw_text = self._run_ocr(image)
        fields = self._extract_fields(raw_text)

        return {
            "raw_text": raw_text,
            "fields": fields,
            "matched_model_id": None,
            "confidence": 0.8 if fields.get("model") else 0.0,
        }

    def _run_ocr(self, image: Image.Image) -> str:
        try:
            from paddleocr import PaddleOCR

            ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            import numpy as np

            img_array = np.array(image)
            result = ocr.ocr(img_array, cls=True)

            lines = []
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    lines.append(text)
            return "\n".join(lines)
        except ImportError:
            return "PaddleOCR未安装，请运行: pip install paddleocr"
        except Exception as e:
            return f"OCR识别失败: {str(e)}"

    def _extract_fields(self, raw_text: str) -> dict:
        """从OCR文本中提取结构化字段"""
        fields = {
            "brand": "",
            "model": "",
            "serial_number": "",
            "product_number": "",
            "load_capacity": "",
            "lift_height": "",
            "weight": "",
            "manufacture_year": "",
            "engine_model": "",
        }

        lines = raw_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 品牌识别
            brand_keywords = [
                "丰田", "TOYOTA", "合力", "HELI", "杭叉", "HANGCHA",
                "林德", "LINDE", "小松", "KOMATSU", "三菱", "MITSUBISHI",
                "日产", "NISSAN", "柳工", "LiuGong", "龙工", "LONKING",
                "TCM", "永恒力", "JUNGHEINRICH",
            ]
            for brand in brand_keywords:
                if brand.lower() in line.lower():
                    fields["brand"] = brand
                    break

            # 型号识别 - 匹配常见叉车型号格式
            model_match = re.search(
                r'([A-Z]{1,3}\d{2,4}[A-Z]?\d{0,3})', line
            )
            if model_match and not fields["model"]:
                fields["model"] = model_match.group(1)

            # 序列号
            sn_match = re.search(r'(?:SN|序列号|Serial)[：:\s]*(\S+)', line, re.IGNORECASE)
            if sn_match:
                fields["serial_number"] = sn_match.group(1)

            # 载荷
            load_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|KG|公斤|吨)', line)
            if load_match:
                fields["load_capacity"] = load_match.group(0)

            # 起升高度
            height_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:mm|MM|毫米)', line)
            if height_match and "高度" in line:
                fields["lift_height"] = height_match.group(0)

            # 年份
            year_match = re.search(r'(20\d{2})', line)
            if year_match:
                fields["manufacture_year"] = year_match.group(1)

            # 发动机型号
            engine_match = re.search(
                r'(?:发动机|Engine)[：:\s]*(\S+)', line, re.IGNORECASE
            )
            if engine_match:
                fields["engine_model"] = engine_match.group(1)

        return fields

    def match_forklift_model(self, fields: dict, db) -> int | None:
        """根据识别字段匹配数据库中的车型"""
        if not fields.get("brand") or not fields.get("model"):
            return None

        from app.models.forklift import ForkliftBrand, ForkliftSeries, ForkliftModel

        brand = db.query(ForkliftBrand).filter(
            ForkliftBrand.name.ilike(f"%{fields['brand']}%")
        ).first()

        if not brand:
            return None

        model_pattern = f"%{fields['model']}%"
        model = (
            db.query(ForkliftModel)
            .join(ForkliftSeries)
            .filter(
                ForkliftSeries.brand_id == brand.id,
                ForkliftModel.name.ilike(model_pattern),
            )
            .first()
        )

        return model.id if model else None
