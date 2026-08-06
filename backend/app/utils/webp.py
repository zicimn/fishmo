import base64
import io
import logging
from typing import Optional

from PIL import Image

import cloudinary
import cloudinary.uploader

from config.security import (
    CLOUNDDINARY_API_KEY,
    CLOUNDDINARY_API_SECRET,
    CLOUDINARY_CLOUD_NAME,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 说明：
# - 本模块将 base64 图片统一转换为 WebP 并等比缩放，再上传到 Cloudinary。
# - 这些是同步函数（PIL 解码为 CPU 密集、cloudinary.uploader.upload 为同步 HTTP），
#   从 async 端点调用时请用 fastapi.concurrency.run_in_threadpool 或 asyncio.to_thread 包裹。
# - 返回 None 表示失败（已记录日志），调用方需判空，不要把 None 当成功结果使用。
# ---------------------------------------------------------------------------

# 反压缩炸弹防护：单张 base64 解码后的字节数上限（默认 5MB），防止超大请求拖垮服务
MAX_IMAGE_BYTES = 5 * 1024 * 1024
# 反压缩炸弹防护：像素总量上限（约 50MP），PIL 解码超大图会占满内存
MAX_IMAGE_PIXELS = 50_000_000

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUNDDINARY_API_KEY,
    api_secret=CLOUNDDINARY_API_SECRET,
)


def convert_image_to_webp(image: str, quality: int = 75, size: tuple = (800, 800)) -> Optional[str]:
    """将一张 base64 图片转换为 webp base64 字符串，失败返回 None。"""
    if not image:
        return None

    try:
        # 处理 data:image/xxx;base64, 前缀
        data = image.split(',', 1)[1] if ',' in image else image

        image_data = base64.b64decode(data)
        # 反压缩炸弹防护：拒绝超大输入
        if len(image_data) > MAX_IMAGE_BYTES:
            logger.warning("图片超过大小上限 %d 字节，已拒绝", MAX_IMAGE_BYTES)
            return None

        img = Image.open(io.BytesIO(image_data))
        # 反压缩炸弹防护：解码后先检查像素总量，再做缩放
        width, height = img.size
        if width * height > MAX_IMAGE_PIXELS:
            logger.warning("图片像素过大 %dx%d，已拒绝", width, height)
            return None

        # 颜色模式转换（RGBA/L/P 转 RGBA 保留透明度，其余转 RGB）
        if img.mode in ("RGBA", "L", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        # 等比缩放（保持宽高比，不超过 size）
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # 保存为 WebP
        output = io.BytesIO()
        img.save(output, format="WEBP", quality=quality)
        output.seek(0)

        return base64.b64encode(output.read()).decode("utf-8")

    except Exception as e:
        logger.warning("图片转换失败: %s", e)
        return None


def convert_images_to_webp(images: list[str], quality: int = 75, size: tuple = (800, 800)) -> list[str]:
    """批量转换，返回成功转换的 webp 列表（跳过转换失败的项）。"""
    if not images:
        return []

    results = []
    for image in images:
        converted = convert_image_to_webp(image, quality=quality, size=size)
        if converted:
            results.append(converted)
        else:
            logger.warning("跳过一张转换失败的图片")
    return results


def _upload_webp(webp_b64: str, folder: str) -> Optional[dict]:
    """上传一张已是 webp base64 的图片，成功返回 dict，失败返回 None。"""
    try:
        result = cloudinary.uploader.upload(
            image=f"data:image/webp;base64,{webp_b64}",
            folder=folder,
        )
        return {
            "status": True,
            "url": result["secure_url"],
            "public_id": result["public_id"],
        }
    except Exception as e:
        logger.error("Cloudinary 上传失败: %s", e)
        return {
            "status": False,
            "error": str(e),
        }


def upload_image_to_cloudinary(image: str, folder: str = "fishmo_upload", size: tuple = (800, 800)) -> Optional[dict]:
    webp_b64 = convert_image_to_webp(image=image, size=size)
    if not webp_b64:
        return None
    return _upload_webp(webp_b64, folder)


def upload_images_to_cloudinary(images: list[str], folder: str = "fishmo_upload", size: tuple = (800, 800)) -> Optional[list[str]]:
    converted = convert_images_to_webp(images=images, size=size)
    if not converted:
        return None

    result = []
    for webp_b64 in converted:
        res = _upload_webp(webp_b64, folder)
        if res and res.get("status"):
            result.append(res["url"])
        else:
            logger.warning("跳过一张上传失败的图片")

    return result if result else None
