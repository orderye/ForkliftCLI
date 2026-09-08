"""数据库种子数据填充脚本"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal, engine, Base
from app.models.forklift import ForkliftBrand, ForkliftSeries, ForkliftModel
from app.models.engine import EngineBrand, EngineModel
from app.data.seed_brands import BRANDS, MODELS_DATA, ENGINE_BRANDS, ENGINE_MODELS


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 插入叉车品牌
        brand_map = {}
        for b in BRANDS:
            existing = db.query(ForkliftBrand).filter(ForkliftBrand.name == b["name"]).first()
            if existing:
                brand_map[b["name"]] = existing
                continue
            brand = ForkliftBrand(**b)
            db.add(brand)
            db.flush()
            brand_map[b["name"]] = brand
        db.commit()
        print(f"✅ 品牌: {len(brand_map)} 个")

        # 插入车型
        model_count = 0
        for brand_name, data in MODELS_DATA.items():
            brand = brand_map.get(brand_name)
            if not brand:
                continue
            for s in data["series"]:
                series = db.query(ForkliftSeries).filter(
                    ForkliftSeries.brand_id == brand.id,
                    ForkliftSeries.name == s["name"],
                ).first()
                if not series:
                    series = ForkliftSeries(brand_id=brand.id, name=s["name"])
                    db.add(series)
                    db.flush()
                for m in s["models"]:
                    existing = db.query(ForkliftModel).filter(
                        ForkliftModel.series_id == series.id,
                        ForkliftModel.name == m["name"],
                    ).first()
                    if existing:
                        continue
                    db.add(ForkliftModel(series_id=series.id, **m))
                    model_count += 1
        db.commit()
        print(f"✅ 车型: {model_count} 个")

        # 插入发动机品牌
        engine_brand_map = {}
        for eb in ENGINE_BRANDS:
            existing = db.query(EngineBrand).filter(EngineBrand.name == eb["name"]).first()
            if existing:
                engine_brand_map[eb["name"]] = existing
                continue
            brand = EngineBrand(**eb)
            db.add(brand)
            db.flush()
            engine_brand_map[eb["name"]] = brand
        db.commit()
        print(f"✅ 发动机品牌: {len(engine_brand_map)} 个")

        # 插入发动机型号
        engine_count = 0
        for em in ENGINE_MODELS:
            brand = engine_brand_map.get(em["brand"])
            if not brand:
                continue
            existing = db.query(EngineModel).filter(
                EngineModel.brand_id == brand.id,
                EngineModel.model_name == em["model_name"],
            ).first()
            if existing:
                continue
            db.add(EngineModel(
                brand_id=brand.id,
                model_name=em["model_name"],
                displacement=em["displacement"],
                power_kw=em["power_kw"],
                power_hp=em["power_hp"],
                cylinders=em["cylinders"],
                fuel_type=em["fuel_type"],
            ))
            engine_count += 1
        db.commit()
        print(f"✅ 发动机型号: {engine_count} 个")

        print("\n🎉 种子数据导入完成！")

    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
