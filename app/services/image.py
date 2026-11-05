"""图片上传编排：把同步的 PIL/Cloudinary 操作放到线程池。"""

import asyncio
from typing import Optional

from utils.cloudinary import (
    is_hosted_url,
    upload_image_to_cloudinary,
    upload_images_to_cloudinary,
)
from utils.responsed import Unprocessable

COVER_SIZE = (800, 800)
SCREENSHOT_SIZE = (1600, 1600)
AVATAR_SIZE = (400, 400)


class ImageService:
    @staticmethod
    async def UploadOne(
        image: str,
        folder: str,
        size: tuple[int, int] = COVER_SIZE,
        label: str = "图片",
    ) -> str:
        result = await asyncio.to_thread(
            upload_image_to_cloudinary, image, folder, size
        )
        if not result or not result.get("status"):
            error = (result or {}).get("error", "图片格式不支持或超过大小限制")
            raise Unprocessable(f"{label}上传失败：{error}")
        return result["url"]

    @staticmethod
    async def UploadMany(
        images: list[str],
        folder: str,
        size: tuple[int, int] = SCREENSHOT_SIZE,
        label: str = "图片",
    ) -> list[str]:
        if not images:
            return []
        results = await asyncio.to_thread(
            upload_images_to_cloudinary, images, folder, size
        )
        urls: list[str] = []
        for result in results:
            if not result.get("status"):
                error = result.get("error", "图片格式不支持或超过大小限制")
                raise Unprocessable(f"{label}上传失败：{error}")
            urls.append(result["url"])
        return urls

    @staticmethod
    async def ResolveOne(
        image: str,
        folder: str,
        size: tuple[int, int] = COVER_SIZE,
        label: str = "图片",
    ) -> str:
        """已托管 URL 直接复用，base64 才上传。"""
        if is_hosted_url(image):
            return image
        return await ImageService.UploadOne(image, folder, size, label)

    @staticmethod
    async def ResolveMany(
        images: list[str],
        folder: str,
        size: tuple[int, int] = SCREENSHOT_SIZE,
        label: str = "图片",
    ) -> list[str]:
        urls: list[str] = []
        for image in images:
            urls.append(await ImageService.ResolveOne(image, folder, size, label))
        return urls

    @staticmethod
    async def ResolveOptional(
        image: Optional[str],
        folder: str,
        size: tuple[int, int] = COVER_SIZE,
        label: str = "图片",
    ) -> Optional[str]:
        if not image:
            return None
        return await ImageService.ResolveOne(image, folder, size, label)