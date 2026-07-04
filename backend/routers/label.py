# -*- coding: utf-8 -*-
"""
标签管理路由
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import LabelEnums
from database import get_db, DatasetImage, DatasetLabel, SysUser, OperationLog
from routers.auth import get_current_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 数据模型 ====================
class LabelUpdate(BaseModel):
    """标签更新请求"""
    image_id: int
    season: Optional[str] = None
    time_period: Optional[str] = None
    day_type: Optional[str] = None
    weather: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[str] = None
    shoot_angle: Optional[str] = None
    scene_scale: Optional[str] = None
    clarity: Optional[str] = None
    exposure: Optional[str] = None
    scene_type: Optional[str] = None
    device_type: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None


class LabelResponse(BaseModel):
    """标签响应"""
    id: int
    image_id: int
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    hour: Optional[int]
    season: Optional[str]
    time_period: Optional[str]
    day_type: Optional[str]
    weather: Optional[str]
    temperature: Optional[float]
    humidity: Optional[float]
    light: Optional[str]
    shoot_angle: Optional[str]
    scene_scale: Optional[str]
    clarity: Optional[str]
    exposure: Optional[str]
    scene_type: Optional[str]
    device_type: Optional[str]
    device_brand: Optional[str]
    device_model: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    province: Optional[str]
    city: Optional[str]
    district: Optional[str]
    address: Optional[str]
    ai_scene_labels: Optional[dict]
    ai_objects: Optional[dict]
    ai_quality_score: Optional[float]
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchLabelUpdate(BaseModel):
    """批量标签更新"""
    image_ids: List[int]
    labels: LabelUpdate


# ==================== 路由 ====================
@router.get("/enums")
async def get_label_enums():
    """获取所有标签枚举值"""
    return {
        "seasons": LabelEnums.SEASONS,
        "time_periods": LabelEnums.TIME_PERIODS,
        "day_types": LabelEnums.DAY_TYPES,
        "weather_types": LabelEnums.WEATHER_TYPES,
        "light_conditions": LabelEnums.LIGHT_CONDITIONS,
        "shoot_angles": LabelEnums.SHOOT_ANGLES,
        "scene_scales": LabelEnums.SCENE_SCALES,
        "clarity_levels": LabelEnums.CLARITY_LEVELS,
        "exposure_levels": LabelEnums.EXPOSURE_LEVELS,
        "scene_types": LabelEnums.SCENE_TYPES,
        "device_types": LabelEnums.DEVICE_TYPES,
    }


@router.get("/{image_id}", response_model=LabelResponse)
async def get_label(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取图片标签"""
    result = await db.execute(
        select(DatasetLabel).where(DatasetLabel.image_id == image_id)
    )
    label = result.scalar_one_or_none()

    if not label:
        raise HTTPException(status_code=404, detail="标签不存在")

    return label


@router.put("/update", response_model=LabelResponse)
async def update_label(
    label_data: LabelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新图片标签（人工修正）"""
    # 获取标签
    result = await db.execute(
        select(DatasetLabel).where(DatasetLabel.image_id == label_data.image_id)
    )
    label = result.scalar_one_or_none()

    if not label:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 验证枚举值
    if label_data.season and label_data.season not in LabelEnums.SEASONS:
        raise HTTPException(status_code=400, detail=f"无效的季节值: {label_data.season}")

    if label_data.weather and label_data.weather not in LabelEnums.WEATHER_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的天气值: {label_data.weather}")

    if label_data.scene_type and label_data.scene_type not in LabelEnums.SCENE_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的场景值: {label_data.scene_type}")

    # 更新字段
    update_fields = label_data.dict(exclude_unset=True)
    for key, value in update_fields.items():
        if key != "image_id" and hasattr(label, key):
            setattr(label, key, value)

    # 标记为人工修改
    label.source = "mixed" if label.source == "auto" else "manual"
    label.creator_id = current_user.id
    label.updated_at = datetime.now()

    await db.commit()
    await db.refresh(label)

    # 记录操作日志
    log = OperationLog(
        user_id=current_user.id,
        action="update_label",
        target_type="image",
        target_id=label_data.image_id,
        detail=update_fields,
    )
    db.add(log)
    await db.commit()

    logger.info(f"标签更新成功: image_id={label_data.image_id}")

    return label


@router.post("/batch-update")
async def batch_update_labels(
    batch_data: BatchLabelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """批量更新标签"""
    success_count = 0
    failed_count = 0
    errors = []

    for image_id in batch_data.image_ids:
        try:
            result = await db.execute(
                select(DatasetLabel).where(DatasetLabel.image_id == image_id)
            )
            label = result.scalar_one_or_none()

            if not label:
                errors.append(f"图片 {image_id} 标签不存在")
                failed_count += 1
                continue

            # 更新字段
            update_fields = batch_data.labels.dict(exclude_unset=True)
            for key, value in update_fields.items():
                if key != "image_id" and hasattr(label, key):
                    setattr(label, key, value)

            label.source = "mixed"
            label.creator_id = current_user.id
            label.updated_at = datetime.now()

            success_count += 1

        except Exception as e:
            errors.append(f"图片 {image_id} 更新失败: {str(e)}")
            failed_count += 1

    await db.commit()

    return {
        "total": len(batch_data.image_ids),
        "success": success_count,
        "failed": failed_count,
        "errors": errors
    }
