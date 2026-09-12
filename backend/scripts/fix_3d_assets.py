"""3D/AR 数据断点修复脚本（幂等）。

修复三个已确认的断点：
1. `model_3d` 已有记录但 `uploads/` 为空 → 模型二进制缺失，`file_url` 全部 404；
2. `model_3d_parts` 0 行 → 前端零件列表必然为空；
3. `ar_model_config` 0 行 → AR 1:1 真实尺寸对所有车型都取不到。

**根因确认（重要）：** `backend/uploads/` 被清空过，但数据库记录本身是对的。
`Glb/001.glb` 的 SHA256 前缀正好是 `623408c9631c90ba`，与 `model_3d` v1 的
`storage_key` 完全一致；`Glb/002.glb` 同理匹配 v2。所以正确做法是**把文件放回原位**，
而不是新建 v3 —— 否则会多出两个内容与旧版重复的模型记录。

设计要点：
- 存储逻辑复用 `app/core/storage.py`，与上传端点同一套口径；
- 零件数据由 `tools/generate_model_metadata.py` 解析**真实 GLB** 得到，
  不写对不上的部件名（旧版 `generate_model_metadata.py` 吐硬编码模板，
  声称有 `Mast_Inner`/`Fork_Left` 等节点，而实际资产里根本没有）；
- 真实尺寸取自 `forklift_models` 已录入的车辆参数，缺的字段保持 NULL，不编造；
- 资产来源为 AI 生成（tripo3d.ai），`license_type` 按 `internal_only`、禁止商用，
  避免权利未确认的资产随付费套餐下发。

用法：
    python3 scripts/fix_3d_assets.py --from-dir ../../Glb --dry-run
    python3 scripts/fix_3d_assets.py --from-dir ../../Glb
    python3 scripts/fix_3d_assets.py --from-dir ../../Glb --upload-new   # 顺带把未入库的资产上传为新版本
"""

import argparse
import hashlib
import json
import shutil
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.storage import get_storage_client  # noqa: E402
from app.models.model3d import Model3D, Model3DPart, ArModelConfig  # noqa: E402
from app.models.forklift import ForkliftModel  # noqa: E402

MIME_GLB = "model/gltf-binary"
LICENSE_INTERNAL_ONLY = "internal_only"  # 仅内部使用：权利未确认，不可随付费套餐商用下发
GLB_MAGIC = b"glTF"


def glb_info(data: bytes) -> dict:
    """解析 GLB JSON chunk，返回节点名/动画数/网格数，用于生成诚实的零件数据。"""
    magic, version, _declared = struct.unpack('<4sII', data[:12])
    if magic != GLB_MAGIC:
        raise ValueError(f'文件内容不是 GLB（magic={magic!r}）')
    if version != 2:
        raise ValueError(f'glTF 版本 {version}，仅支持 2.0')
    chunk_len, chunk_type = struct.unpack('<I4s', data[12:20])
    if chunk_type != b'JSON':
        raise ValueError(f'首个 chunk 类型 {chunk_type!r}，应为 JSON')
    doc = json.loads(data[20:20 + chunk_len].decode('utf-8'))
    nodes = doc.get('nodes', [])
    return {
        'generator': (doc.get('asset') or {}).get('generator', 'unknown'),
        'node_count': len(nodes),
        'mesh_count': len(doc.get('meshes', [])),
        'animation_count': len(doc.get('animations', [])),
        'nodes_with_mesh': [
            {'index': i, 'name': n.get('name') or f'node_{i}', 'mesh': n['mesh']}
            for i, n in enumerate(nodes) if 'mesh' in n
        ],
    }


def capability_note(info: dict) -> list:
    """把资产真实能力写出来，避免下游误以为有零件层级/动画。"""
    n = len(info['nodes_with_mesh'])
    lines = [f'资产来源：{info["generator"]}',
             f'几何：{info["mesh_count"]} 个网格 / {info["node_count"]} 个节点 / '
             f'{n} 个可识别零件 / {info["animation_count"]} 段动画']
    if n <= 1:
        lines.append('能力限制：单网格模型，不支持多零件高亮与爆炸图。')
    if info['animation_count'] == 0:
        lines.append('无动画剪辑：门架升降/倾斜/货叉开合等机械动作暂不可用。')
    lines.append('AR 1:1 放置与整体浏览可用。')
    return lines


def next_version(db, forklift_model_id: int) -> int:
    """与上传端点的 `.order_by(version.desc()).first()` 一致。

    不能用 `scalar_one_or_none()`：同一车型会有多个历史版本，会抛
    `MultipleResultsFound`。
    """
    row = db.execute(
        select(Model3D.version)
        .filter(Model3D.forklift_model_id == forklift_model_id)
        .order_by(Model3D.version.desc())
        .limit(1)
    ).scalar_one_or_none()
    return 1 if row is None else row + 1


def ensure_parts(db, model_id: int, info: dict, dry_run: bool) -> int:
    """按真实节点补零件记录；已有记录的模型不动（幂等）。"""
    count = db.execute(select(Model3DPart).where(Model3DPart.model_3d_id == model_id)).scalars().all()
    if count:
        return 0
    nodes = info['nodes_with_mesh'] or [{'name': 'model_root', 'mesh': 0}]
    if dry_run:
        return len(nodes)
    for entry in nodes:
        db.add(Model3DPart(
            model_3d_id=model_id,
            name=entry['name'],
            mesh_name=entry['name'],
            material='unknown',
            color='#888888',
            is_interactive=1,
            group='body',
        ))
    return len(nodes)


def ensure_ar_config(db, forklift_model_id: int, model: Model3D, dry_run: bool) -> str:
    """真实尺寸取自车辆参数表；缺失字段保持 NULL，不编造。"""
    fl = db.execute(select(ForkliftModel).filter(ForkliftModel.id == forklift_model_id)).scalar_one()
    cfg = db.execute(
        select(ArModelConfig).filter(ArModelConfig.forklift_model_id == forklift_model_id)
    ).scalar_one_or_none()
    existed = cfg is not None
    if not dry_run:
        cfg = cfg or ArModelConfig(forklift_model_id=forklift_model_id)
        cfg.model_3d_id = model.id
        cfg.forklift_model_id = forklift_model_id
        cfg.real_length_mm = fl.length_mm
        cfg.real_width_mm = fl.width_mm
        cfg.real_height_mm = fl.height_mm
        cfg.real_mast_height_mm = fl.lift_height_mm
        cfg.real_wheelbase_mm = fl.wheelbase_mm            # 8FG30 未录入，保持 NULL
        cfg.real_turning_radius_mm = fl.turning_radius_mm   # 8FG30 未录入，保持 NULL
        cfg.scale_factor = 1.0
        cfg.anchor_type = 'horizontal_plane'
        if not existed:
            db.add(cfg)
    return (f'{"更新" if existed else "新建"} ar_model_config：'
            f'{fl.length_mm}×{fl.width_mm}×{fl.height_mm} mm（scale_factor=1.0）'
            + (f'，wheelbase={fl.wheelbase_mm} / turning_radius={fl.turning_radius_mm} 未录入，保持 NULL'
               if fl.wheelbase_mm is None or fl.turning_radius_mm is None else ''))


def index_candidates(from_dir: Path) -> dict:
    """按 SHA256 索引候选目录里的 GLB，用于匹配数据库里已有的 storage_key。"""
    out = {}
    for p in sorted(from_dir.glob('*.glb')):
        try:
            out[hashlib.sha256(p.read_bytes()).hexdigest()] = p
        except Exception as e:
            print(f'  跳过无法读取的 {p.name}：{e}')
    return out


def main():
    p = argparse.ArgumentParser(description='修复 3D/AR 数据断点（幂等）')
    p.add_argument('--from-dir', default='../../Glb', help='候选 GLB 资产目录')
    p.add_argument('--forklift-model-id', type=int, default=1)
    p.add_argument('--upload-new', action='store_true',
                   help='把候选目录中尚未入库的 GLB 作为新版本上传')
    p.add_argument('--dry-run', action='store_true', help='只打印将执行的动作')
    args = p.parse_args()

    from_dir = Path(args.from_dir).expanduser().resolve()
    if not from_dir.is_dir():
        print(f'错误：候选目录不存在 {from_dir}', file=sys.stderr)
        return 2

    storage = get_storage_client()
    candidates = index_candidates(from_dir)
    print(f'候选资产：{len(candidates)} 个 GLB（{from_dir}）')
    if not candidates:
        return 1

    db = SessionLocal()
    log = []
    try:
        fl = db.execute(
            select(ForkliftModel).filter(ForkliftModel.id == args.forklift_model_id)
        ).scalar_one_or_none()
        if fl is None:
            print(f'错误：找不到车型 ID={args.forklift_model_id}', file=sys.stderr)
            return 1
        print(f'车型：{fl.name}（{fl.load_capacity_ton}t，{fl.length_mm}×{fl.width_mm}×{fl.height_mm} mm）')
        print(f'存储后端：{storage.provider} → {storage.upload_dir}')
        print()

        models = db.execute(
            select(Model3D)
            .filter(Model3D.forklift_model_id == args.forklift_model_id)
            .order_by(Model3D.version)
        ).scalars().all()

        # ── 1. 补齐缺失的模型二进制：按 SHA256 从候选目录找回 ──
        print('── 1/3 模型二进制 ──')
        restored, missing = [], []
        for m in models:
            key = (m.storage_key or '').lstrip('/')
            if not key or m.content_hash is None:
                log.append(f'model_3d id={m.id} v{m.version}：无 storage_key/content_hash，需人工处理')
                continue
            target = Path(storage.upload_dir).resolve() / key
            if target.exists():
                log.append(f'v{m.version} 文件已存在，跳过（{target.name}）')
                continue
            cand = candidates.get(m.content_hash)
            if cand is None:
                missing.append(m)
                log.append(f'v{m.version} 文件缺失，候选目录无同哈希文件 → 需人工上传')
                continue
            if args.dry_run:
                log.append(f'[DRY-RUN] v{m.version} 恢复 {target} ← {cand.name} '
                           f'({cand.stat().st_size/1048576:.1f} MB)')
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cand, target)
                log.append(f'v{m.version} 已恢复 {target} ← {cand.name}')
            restored.append(cand)

        # ── 2. 可选：把未入库的候选资产作为新版本上传 ──
        if args.upload_new:
            new_ones = [h for h in candidates if h not in {m.content_hash for m in models}]
            if not new_ones:
                log.append('无尚未入库的候选资产')
            for h in new_ones:
                cand = candidates[h]
                data = cand.read_bytes()
                version = next_version(db, args.forklift_model_id)
                key = f'models/{args.forklift_model_id}/{h[:16]}.glb'
                if args.dry_run:
                    log.append(f'[DRY-RUN] 上传 {cand.name} 为 v{version} → /uploads/{key}')
                else:
                    file_url = storage.put_object(key, data, content_type=MIME_GLB)
                    info = glb_info(data)
                    db.add(Model3D(
                        forklift_model_id=args.forklift_model_id,
                        name=f'{fl.name} 3D',
                        description='\n'.join(capability_note(info)),
                        file_url=file_url,
                        file_size_mb=round(len(data) / (1024 * 1024), 3),
                        format='glb', version=version, content_hash=h,
                        storage_provider=storage.provider, storage_key=key,
                        mime_type=MIME_GLB,
                        uploaded_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc), status='ready',
                        source=f'{cand.as_posix()}（{info["generator"]} 生成）',
                        license_type=LICENSE_INTERNAL_ONLY, commercial_use=0,
                    ))
                    log.append(f'已上传 {cand.name} 为 v{version}')
            db.flush()
            models = db.execute(
                select(Model3D).filter(Model3D.forklift_model_id == args.forklift_model_id)
                .order_by(Model3D.version)
            ).scalars().all()

        # ── 3. 补齐零件 + AR 配置 ──
        print('── 2/3 零件数据 ──')
        total_parts = 0
        root = Path(storage.upload_dir).resolve()
        for m in models:
            local = root / (m.storage_key or '')
            if not local.exists():
                log.append(f'v{m.version}：文件不在本地，跳过零件生成')
                continue
            info = glb_info(local.read_bytes())
            n = ensure_parts(db, m.id, info, args.dry_run)
            detail = f'新增 {n} 条零件（真实节点名）' if n else '已有零件记录，跳过'
            log.append(f'v{m.version}：{detail}')
            total_parts += n
        print('── 3/3 AR 配置 ──')
        latest = models[-1] if models else None
        if latest is not None:
            log.append(ensure_ar_config(db, args.forklift_model_id, latest, args.dry_run))
        else:
            log.append('无 model_3d 记录，跳过 AR 配置')

        if not args.dry_run:
            db.commit()
    finally:
        db.close()

    print()
    print('--- 结果 ---')
    for line in log:
        print(f'  · {line}')
    print()
    print(f'汇总：恢复文件 {len(restored)} 个，仍缺 {len(missing)} 个，新增零件 {total_parts} 条')
    if missing:
        print('⚠ 以下版本缺少二进制且候选目录无匹配哈希，3D 功能对这些版本仍不可用：')
        for m in missing:
            print(f'   v{m.version} {m.name}（storage_key={m.storage_key}）')
    print()
    print('提示：脚本幂等，可重复执行。对同一资产重复执行 --upload-new 会生成新版本记录。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
