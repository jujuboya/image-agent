# -*- coding: utf-8 -*-
"""
图片服务 - 提供图片列表和详情功能
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from database import DatasetImage

import logging

logger = logging.getLogger(__name__)


class ImageService:
    """图片服务"""

    async def get_image_list(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        check_status: Optional[str] = None,
        scene_type: Optional[str] = None,
        weather: Optional[str] = None,
        season: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict:
        """
        获取图片列表（支持多条件筛选）

        Args:
            db: 数据库会话
            page: 页码（从1开始）
            page_size: 每页数量
            status: 图片状态筛选
            check_status: 审核状态筛选
            scene_type: 场景类型筛选
            weather: 天气筛选
            season: 季节筛选
            keyword: 关键词搜索（文件名或UUID）

        Returns:
            包含 total, page, page_size, items 的字典
        """
        query = select(DatasetImage)
        count_query = select(func.count(DatasetImage.id))

        # 构建筛选条件
        conditions = []

        if status:
            conditions.append(DatasetImage.status == status)

        if check_status:
            conditions.append(DatasetImage.check_status == check_status)

        if scene_type:
            from database import DatasetLabel
            query = query.join(DatasetImage.labels)
            count_query = count_query.select_from(
                count_query.froms[0].join(DatasetImage.labels)
            ) if count_query.froms else count_query
            conditions.append(DatasetLabel.scene_type == scene_type)

        if weather:
            from database import DatasetLabel
            if not scene_type:  # 避免重复join
                query = query.join(DatasetImage.labels)
            conditions.append(DatasetLabel.weather == weather)

        if season:
            from database import DatasetLabel
            if not scene_type and not weather:
                query = query.join(DatasetImage.labels)
            conditions.append(DatasetLabel.season == season)

        if keyword:
            conditions.append(
                or_(
                    DatasetImage.original_filename.contains(keyword),
                    DatasetImage.image_uuid.contains(keyword),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页查询
        query = query.order_by(DatasetImage.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        images = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": images,
        }

    async def get_image_detail(
        self,
        db: AsyncSession,
        image_id: int,
    ) -> Optional[DatasetImage]:
        """
        获取图片详情（含标签信息）

        Args:
            db: 数据库会话
            image_id: 图片ID

        Returns:
            DatasetImage 对象或 None
        """
        result = await db.execute(
            select(DatasetImage)
            .options(selectinload(DatasetImage.labels))
            .where(DatasetImage.id == image_id)
        )
        return result.scalar_one_or_none()


# 全局图片服务实例
image_service = ImageService()
