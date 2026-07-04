# -*- coding: utf-8 -*-
"""
Redis缓存服务
提供通用的缓存读写功能，支持优雅降级
"""

import json
import logging
from typing import Optional, Any

import redis.asyncio as redis

from config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis缓存服务"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """连接Redis"""
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
            )
            await self.redis.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}，将降级为无缓存模式")
            self.redis = None

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值（反序列化后的对象），未命中返回None
        """
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.debug(f"缓存读取失败: {e}")
            return None

    async def set(self, key: str, value: Any, expire: int = 300):
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值（可JSON序列化的对象）
            expire: 过期时间（秒），默认300秒（5分钟）
        """
        if not self.redis:
            return
        try:
            await self.redis.setex(key, expire, json.dumps(value, ensure_ascii=False))
        except Exception as e:
            logger.debug(f"缓存写入失败: {e}")

    async def delete(self, key: str):
        """
        删除缓存

        Args:
            key: 缓存键
        """
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.debug(f"缓存删除失败: {e}")

    async def close(self):
        """关闭连接"""
        if self.redis:
            try:
                await self.redis.close()
                logger.info("Redis连接已关闭")
            except Exception as e:
                logger.debug(f"Redis关闭异常: {e}")
            finally:
                self.redis = None


# 全局缓存实例
cache_service = CacheService()
