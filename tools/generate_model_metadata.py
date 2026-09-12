#!/usr/bin/env python3
"""3D 模型元数据生成器 —— 解析真实 GLB，产出与实际几何一致的元数据。

历史问题：本脚本原先只吐一份硬编码模板（8 个叉车部件 + 3 段动画），从不读取模型。
结果元数据声称有 `Mast_Inner`/`Fork_Left` 等节点，而实际资产（如 tripo3d 生成的单网格
模型）里根本没有这些节点名，前端零件列表必然点不亮任何零件。

现在改为：解析 glTF 2.0 GLB 的 JSON chunk，按真实节点/网格/动画产出元数据，
并在资产不满足叉车部件约定时明确告警，而不是静默生成对不上的数据。
"""

import argparse
import json
import struct
import sys
from datetime import datetime
from pathlib import Path

# 叉车部件命名约定（与 mobile/lib/viewer/ 与 unity PartMapping 对齐）
EXPECTED_PART_GROUPS = {
    "Body_Chassis": "body", "Mast_Outer": "mast", "Mast_Inner": "mast",
    "Carriage_Fork": "fork", "Fork_Left": "fork", "Fork_Right": "fork",
    "Counterweight": "body", "Cabin": "body",
}


def read_glb(path: Path) -> dict:
    """读取 GLB 的 JSON chunk，返回 glTF 文档。"""
    data = path.read_bytes()
    magic, version, declared = struct.unpack('<4sII', data[:12])
    if magic != b'glTF':
        raise ValueError(f'{path}: 不是 GLB（magic={magic!r}）')
    if version != 2:
        raise ValueError(f'{path}: glTF 版本 {version}，仅支持 2.0')
    if declared != len(data):
        raise ValueError(f'{path}: 头部声明长度 {declared} 与实际 {len(data)} 不符（文件被截断或拼接损坏）')

    chunk_len, chunk_type = struct.unpack('<I4s', data[12:20])
    if chunk_type != b'JSON':
        raise ValueError(f'{path}: 第一个 chunk 类型 {chunk_type!r}，应为 JSON')
    doc = json.loads(data[20:20 + chunk_len].decode('utf-8'))
    doc.setdefault('_glb', {'file_bytes': len(data), 'json_bytes': chunk_len})
    return doc


def _bbox(doc: dict):
    """从带 min/max 的 3D accessor 汇总整体包围盒。"""
    boxes = []
    for acc in doc.get('accessors', []):
        mn, mx = acc.get('min'), acc.get('max')
        if mn and mx and len(mn) == 3 and len(mx) == 3:
            boxes.append((mn, mx))
    if not boxes:
        return None
    mn = [min(b[0][k] for b in boxes) for k in range(3)]
    mx = [max(b[1][k] for b in boxes) for k in range(3)]
    return {'min': mn, 'max': mx, 'size': [mx[i] - mn[i] for i in range(3)]}


def extract_parts(doc: dict) -> list:
    """按真实节点产出零件列表：只有挂了 mesh 的节点才算零件。"""
    parts = []
    for idx, node in enumerate(doc.get('nodes', [])):
        if 'mesh' not in node:
            continue
        name = node.get('name') or f'node_{idx}'
        mesh = doc['meshes'][node['mesh']]
        prim_count = len(mesh.get('primitives', []))
        extras = node.get('extras', {}) or {}
        part_id = extras.get('partId', extras.get('part_id'))
        group = extras.get('partGroup', EXPECTED_PART_GROUPS.get(name, 'body'))
        parts.append({
            'part_id': int(part_id) if part_id is not None else idx + 1,
            'mesh_name': name,
            'display_name': extras.get('partName', name),
            'node_index': idx,
            'mesh_index': node['mesh'],
            'primitives': prim_count,
            'group': group,
            'has_user_data': bool(extras),
            'translation': node.get('translation', [0, 0, 0]),
            'scale': node.get('scale', [1, 1, 1]),
        })
    return parts


def extract_animations(doc: dict) -> list:
    """按真实动画剪辑产出动画列表。"""
    out = []
    for i, anim in enumerate(doc.get('animations', [])):
        out.append({
            'name': anim.get('name') or f'animation_{i}',
            'display_name': anim.get('name', ''),
            'channels': len(anim.get('channels', [])),
            'samplers': len(anim.get('samplers', [])),
            'duration_ms': None,  # 需按 sampler.input 的 accessor min/max 计算，glTF 不直接给
            'loop': False,
        })
    return out


def build(doc: dict, glb_path: Path) -> dict:
    parts = extract_parts(doc)
    animations = extract_animations(doc)
    bbox = _bbox(doc)

    problems = []
    if not parts:
        problems.append('没有任何带 mesh 的节点，模型无法被识别为可交互零件')
    if len(parts) == 1:
        problems.append('只有一个零件：爆炸图与多零件高亮无意义')
    if not animations:
        problems.append('无动画剪辑：门架升降/倾斜/货叉开合等机械动作全部不可用')
    if not any(p['has_user_data'] for p in parts):
        problems.append('节点未写 extras.partId：Web/Unity 侧按 partId 定位零件会失败')

    mesh_names = {p['mesh_name'] for p in parts}
    convention_hit = sorted(mesh_names & set(EXPECTED_PART_GROUPS))

    meta = {
        'source_file': glb_path.name,
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'generator': (doc.get('asset') or {}).get('generator', 'unknown'),
        'gltf_version': (doc.get('asset') or {}).get('version'),
        'format': 'glb',
        'file_bytes': glb_path.stat().st_size,
        'file_size_mb': round(glb_path.stat().st_size / (1024 * 1024), 3),
        'mesh_count': len(doc.get('meshes', [])),
        'node_count': len(doc.get('nodes', [])),
        'primitive_count': sum(len(m.get('primitives', [])) for m in doc.get('meshes', [])),
        'material_count': len(doc.get('materials', [])),
        'image_count': len(doc.get('images', [])),
        'bounding_box': bbox,
        'parts': parts,
        'animations': animations,
        'capability_check': {
            'part_highlight_usable': bool(convention_hit) or any(p['has_user_data'] for p in parts),
            'part_convention_hit': convention_hit,
            'explode_usable': len(parts) > 1,
            'animation_usable': len(animations) > 0,
            'ar_1_to_1_usable': True,  # 取决于 ar_model_config 是否有真实尺寸，与几何无关
        },
        'problems': problems,
        'recommendation': None,
    }
    if problems:
        meta['recommendation'] = (
            '该资产不具备叉车部件层级。要做零件高亮/爆炸图/机械动作，'
            '需从 STEP 源文件按部件名重新导出（见 docs/SOLIDWORKS_EXPORT_GUIDE.md）；'
            '当前资产只适合整体浏览与 AR 1:1 放置。'
        )
    return meta


def main():
    p = argparse.ArgumentParser(description='解析 GLB 生成真实元数据')
    p.add_argument('--glb', required=True, help='输入 .glb 文件路径')
    p.add_argument('--output', default='.', help='输出目录')
    p.add_argument('--name', default=None, help='输出文件名，默认 <模型名>_metadata.json')
    p.add_argument('--json', action='store_true', help='直接打印 JSON 到 stdout')
    args = p.parse_args()

    glb_path = Path(args.glb).resolve()
    if not glb_path.exists():
        print(f'错误：找不到 {glb_path}', file=sys.stderr)
        return 2

    try:
        doc = read_glb(glb_path)
        meta = build(doc, glb_path)
    except Exception as e:
        print(f'解析失败：{e}', file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return 0

    outdir = Path(args.output).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / (args.name or f'{glb_path.stem}_metadata.json')
    outfile.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'已生成：{outfile}')
    print(f'  生成方：{meta["generator"]}  网格 {meta["mesh_count"]}  节点 {meta["node_count"]}  '
          f'零件 {len(meta["parts"])}  动画 {len(meta["animations"])}')
    if meta['problems']:
        print(f'  ⚠ 发现 {len(meta["problems"])} 个问题：')
        for i, msg in enumerate(meta['problems'], 1):
            print(f'    {i}. {msg}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
