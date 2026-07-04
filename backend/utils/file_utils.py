# -*- coding: utf-8 -*-
"""
文件处理工具
"""

import hashlib
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple

from config import settings

import logging

logger = logging.getLogger(__name__)


class FileUtils:
    """文件处理工具类"""

    ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS
    MAX_FILE_SIZE = settings.MAX_FILE_SIZE

    @staticmethod
    def generate_uuid() -> str:
        """生成UUID"""
        return str(uuid.uuid4())

    @staticmethod
    def calculate_md5(file_path: str) -> str:
        """
        计算文件MD5

        Args:
            file_path: 文件路径

        Returns:
            MD5哈希值
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    @staticmethod
    def calculate_md5_from_bytes(data: bytes) -> str:
        """
        计算字节数据的MD5

        Args:
            data: 字节数据

        Returns:
            MD5哈希值
        """
        return hashlib.md5(data).hexdigest()

    @classmethod
    def validate_file(cls, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        验证文件

        Args:
            filename: 文件名
            file_size: 文件大小

        Returns:
            (是否有效, 错误信息)
        """
        # 检查文件扩展名
        ext = Path(filename).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"不支持的文件格式: {ext}，支持: {', '.join(cls.ALLOWED_EXTENSIONS)}"

        # 检查文件大小
        if file_size > cls.MAX_FILE_SIZE:
            max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"文件大小超过限制: {max_mb}MB"

        return True, ""

    @staticmethod
    def get_stored_filename(original_filename: str, uuid_str: str) -> str:
        """
        生成存储文件名

        Args:
            original_filename: 原始文件名
            uuid_str: UUID

        Returns:
            存储文件名
        """
        ext = Path(original_filename).suffix.lower()
        return f"{uuid_str}{ext}"

    @staticmethod
    async def save_upload_file(file_content: bytes, save_path: str) -> bool:
        """
        保存上传文件

        Args:
            file_content: 文件内容
            save_path: 保存路径

        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'wb') as f:
                f.write(file_content)

            return True
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return False

    @staticmethod
    def move_file(src: str, dst: str) -> bool:
        """
        移动文件

        Args:
            src: 源路径
            dst: 目标路径

        Returns:
            是否成功
        """
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return True
        except Exception as e:
            logger.error(f"移动文件失败: {e}")
            return False

    @staticmethod
    def copy_file(src: str, dst: str) -> bool:
        """
        复制文件

        Args:
            src: 源路径
            dst: 目标路径

        Returns:
            是否成功
        """
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
            return False

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    @staticmethod
    def ensure_dir(dir_path: str) -> str:
        """
        确保目录存在

        Args:
            dir_path: 目录路径

        Returns:
            目录路径
        """
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """获取文件扩展名"""
        return Path(filename).suffix.lower()

    @staticmethod
    def get_temp_path(filename: str) -> str:
        """获取临时文件路径"""
        return str(settings.TEMP_DIR / filename)

    @staticmethod
    def get_dataset_path(relative_path: str, filename: str) -> str:
        """获取数据集文件路径"""
        return str(settings.DATASET_DIR / relative_path / filename)

    @staticmethod
    def get_discard_path(filename: str) -> str:
        """获取废弃文件路径"""
        return str(settings.DISCARD_DIR / filename)


class ImageValidator:
    """图片验证器"""

    @staticmethod
    def is_valid_image(file_path: str) -> Tuple[bool, str]:
        """
        验证是否为有效图片

        Args:
            file_path: 文件路径

        Returns:
            (是否有效, 错误信息)
        """
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                img.verify()
            return True, ""
        except Exception as e:
            return False, f"无效的图片文件: {e}"

    @staticmethod
    def get_image_dimensions(file_path: str) -> Optional[Tuple[int, int]]:
        """
        获取图片尺寸

        Args:
            file_path: 文件路径

        Returns:
            (宽度, 高度) 或 None
        """
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return img.size
        except Exception:
            return None
