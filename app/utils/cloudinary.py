"""Cloudinary 图片处理。

全部是同步函数（PIL 解码为 CPU 密集、Cloudinary SDK 为同步 HTTP），
调用方必须用 ``asyncio.to_thread`` / ``run_in_threadpool`` 包裹。

安全限制：单图 base64 解码后 ≤ 5MB、像素 ≤ 50MP；失败返回 None。
"""

import base64
import io
import logging
from typing import Optional

import cloudinary
import cloudinary.uploader
from PIL import Image

from config.security import (
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
    CLOUDINARY_CLOUD_NAME,
)

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 50_000_000

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)


def is_hosted_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def convert_image_to_webp(
    image: str,
    quality: int = 75,
    size: tuple[int, int] = (800, 800),
) -> Optional[str]:
    if not image:
        return None
    try:
        data = image.split(",", 1)[1] if "," in image else image
        image_data = base64.b64decode(data, validate=False)
        if len(image_data) > MAX_IMAGE_BYTES:
            logger.warning("图片超过大小上限 %d 字节，已拒绝", MAX_IMAGE_BYTES)
            return None

        img = Image.open(io.BytesIO(image_data))
        width, height = img.size
        if width * height > MAX_IMAGE_PIXELS:
            logger.warning("图片像素过大 %dx%d，已拒绝", width, height)
            return None

        if img.mode in ("RGBA", "L", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        img.thumbnail(size, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        img.save(output, format="WEBP", quality=quality)
        output.seek(0)
        return base64.b64encode(output.read()).decode("utf-8")
    except Exception as exc:  # noqa: BLE001 - 用户上传的任意文件都可能触发
        logger.warning("图片转换失败：%s", exc)
        return None


def upload_image_to_cloudinary(
    image: str,
    folder: str = "fishmo_upload",
    size: tuple[int, int] = (800, 800),
) -> Optional[dict]:
    """转换并上传单张图片，返回 ``{status,url,public_id}`` 或 None/错误 dict。"""
    if is_hosted_url(image):
        return {"status": True, "url": image, "public_id": None}

    webp_b64 = convert_image_to_webp(image=image, size=size)
    if not webp_b64:
        return None

    try:
        result = cloudinary.uploader.upload(
            f"data:image/webp;base64,{webp_b64}",
            folder=folder,
        )
        return {
            "status": True,
            "url": result["secure_url"],
            "public_id": result["public_id"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Cloudinary 上传失败：%s", exc)
        return {"status": False, "error": "图片上传服务暂不可用"}


def upload_images_to_cloudinary(
    images: list[str],
    folder: str = "fishmo_upload",
    size: tuple[int, int] = (1600, 1600),
) -> list[dict]:
    """逐张上传，返回全部结果（调用方按 status 判断成功或失败）。"""
    results: list[dict] = []
    for image in images or []:
        result = upload_image_to_cloudinary(image, folder=folder, size=size)
        results.append(result or {"status": False, "error": "图片格式不支持或超过大小限制"})
    return results