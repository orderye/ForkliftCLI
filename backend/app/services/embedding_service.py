"""WeMM-Embedding 多模态向量服务。

调用方式严格对齐 Tencent 官方 examples/transformers_inference.py：
  - processor = AutoProcessor.from_pretrained(..., trust_remote_code=True)
  - model     = AutoModel.from_pretrained(..., trust_remote_code=True, torch_dtype=bfloat16)
  - prompt    = processor.apply_chat_template(messages, ...)
  - inputs    = processor(text=prompt, images=images, ...)
  - vector    = model.embedding(**inputs).float()

重依赖 (torch/transformers) 全部延迟到首次调用时导入，
模块级只读 config，不碰 GPU/模型。
"""
import logging
import threading

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── 常量（从 config 读取，运行时固定，不依赖 torch） ─────────────
SUPPORTED_DIMS_2B = (64, 128, 256, 512, 1024, 2048)


def _model_name() -> str:
    return getattr(settings, "WEMM_MODEL_NAME", "tencent/WeMM-Embedding-2B")


def _embed_dim() -> int:
    return int(getattr(settings, "WEMM_EMBED_DIM", 1024))


EMBED_DIM: int = _embed_dim()
if EMBED_DIM not in SUPPORTED_DIMS_2B:
    raise ValueError(
        f"WEMM_EMBED_DIM={EMBED_DIM} 不受支持，可选值: {list(SUPPORTED_DIMS_2B)}"
    )

# ── 模型缓存（首次调用时加载） ──────────────────────────────────
_model_cache: tuple | None = None
_model_lock = threading.Lock()


def _load_model():
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    import torch
    from transformers import AutoProcessor, AutoModel

    name = _model_name()
    cache_dir = (getattr(settings, "WEMM_CACHE_DIR", "") or "").strip() or None
    device = torch.device((getattr(settings, "WEMM_DEVICE", "") or "cpu").strip())
    try:
        with _model_lock:
            if _model_cache is not None:
                return _model_cache
            logger.info("loading WeMM model: %s (device=%s)", name, device)
            processor = AutoProcessor.from_pretrained(
                name, trust_remote_code=True, cache_dir=cache_dir
            )
            model = AutoModel.from_pretrained(
                name,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
                cache_dir=cache_dir,
            ).to(device)
            model.eval()
            _model_cache = (processor, model, device)
            logger.info("WeMM model loaded, embed_dim=%d", EMBED_DIM)
            return _model_cache
    except Exception as e:
        logger.error("failed to load WeMM model: %s", e)
        raise RuntimeError(f"WeMM model load failed: {e}") from e


# ── 工具函数 ────────────────────────────────────────────────────
def _truncate_and_normalize(vec, dim: int) -> list[float]:
    """截断到目标维度 + L2 归一化（Matryoshka）。"""
    import torch.nn.functional as F

    if vec.shape[-1] < dim:
        raise RuntimeError(
            f"WeMM 输出维度 {vec.shape[-1]} 小于配置的 WEMM_EMBED_DIM={dim}"
        )
    vec = F.normalize(vec[..., :dim], dim=-1)
    return vec[0].cpu().float().numpy().tolist()


def _fake_enabled() -> bool:
    """测试/开发模式：WEMM_FAKE_EMBEDDING=true 时不加载模型。"""
    return bool(getattr(settings, "WEMM_FAKE_EMBEDDING", False))


def _fake_vector(seed: str) -> list[float]:
    """由 seed 确定性生成的 L2 归一化伪向量，仅供测试/开发。"""
    import hashlib
    import math

    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < EMBED_DIM:
        block = hashlib.sha256(digest + counter.to_bytes(4, "big")).digest()
        for i in range(0, len(block) - 1, 2):
            if len(values) >= EMBED_DIM:
                break
            values.append(int.from_bytes(block[i : i + 2], "big") / 32767.5 - 1.0)
        counter += 1
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


# ── 文本 embedding ─────────────────────────────────────────────
def get_text_embedding(text: str) -> list[float]:
    if _fake_enabled():
        return _fake_vector(f"text:{text}")

    import torch

    processor, model, device = _load_model()
    messages = [{"role": "user", "content": text}]
    prompt = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )
    inputs = processor(text=prompt, return_tensors="pt").to(device)
    with torch.inference_mode():
        vec = model.embedding(**inputs).float()
    return _truncate_and_normalize(vec, EMBED_DIM)


# ── 图片 embedding ─────────────────────────────────────────────
def get_image_embedding(image) -> list[float]:
    """接受 PIL.Image.Image 对象。"""
    if _fake_enabled():
        return _fake_vector(f"image:{image.size}:{image.mode}")

    import torch
    from PIL import Image as _PILImage

    if not isinstance(image, _PILImage.Image):
        raise TypeError(f"expected PIL.Image.Image, got {type(image)}")

    processor, model, device = _load_model()

    # 构造带图片的 chat message
    messages = [
        {
            "role": "user",
            "content": [{"type": "image", "image": image}],
        }
    ]
    prompt = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )

    # 从 messages 提取视觉输入（trust_remote_code 提供）
    try:
        from qwen_vl_utils import process_vision_info

        images, videos, video_kwargs = process_vision_info(
            messages, return_video_kwargs=True
        )
    except ImportError:
        # 降级：直接把 PIL image 当 list 传给 processor
        images = [image]
        videos = None
        video_kwargs = {}

    inputs = processor(
        text=prompt,
        images=images,
        videos=videos,
        return_tensors="pt",
        **video_kwargs,
    ).to(device)
    with torch.inference_mode():
        vec = model.embedding(**inputs).float()
    return _truncate_and_normalize(vec, EMBED_DIM)
