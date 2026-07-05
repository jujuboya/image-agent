# -*- coding: utf-8 -*-
"""
图片管理路由
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db, DatasetImage, SysUser, OperationLog
from routers.auth import get_current_user
from services.cache_service import cache_service
from services.image_service import image_service

import logging
import os
import shutil

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 数据模型 ====================
class ImageResponse(BaseModel):
    """图片响应"""
    id: int
    image_uuid: str
    original_filename: str
    stored_filename: Optional[str] = None
    file_path: str
    file_size: int
    file_format: str
    width: Optional[int]
    height: Optional[int]
    status: str
    check_status: str
    dataset_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    parsed_at: Optional[datetime]
    checked_at: Optional[datetime]

    class Config:
        from_attributes = True


class ImageDetailResponse(ImageResponse):
    """图片详情响应"""
    metadata_json: Optional[dict]
    uploader_id: Optional[int]
    checker_id: Optional[int]
    labels: Optional[dict]


class ImageListResponse(BaseModel):
    """图片列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ImageResponse]


class CheckRequest(BaseModel):
    """审核请求"""
    image_id: int
    status: str  # checked / discard
    comment: Optional[str] = None


class BatchCheckRequest(BaseModel):
    """批量审核请求"""
    image_ids: List[int]
    status: str
    comment: Optional[str] = None


# ==================== 路由 ====================
@router.get("/list", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    check_status: Optional[str] = None,
    scene_type: Optional[str] = None,
    weather: Optional[str] = None,
    season: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取图片列表（支持多条件筛选）"""
    return await image_service.get_image_list(
        db,
        page=page,
        page_size=page_size,
        status=status,
        check_status=check_status,
        scene_type=scene_type,
        weather=weather,
        season=season,
        keyword=keyword,
    )


@router.get("/{image_id}", response_model=ImageDetailResponse)
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取图片详情"""
    image = await image_service.get_image_detail(db, image_id)

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 构建响应
    response = ImageDetailResponse(
        id=image.id,
        image_uuid=image.image_uuid,
        original_filename=image.original_filename,
        stored_filename=image.stored_filename,
        file_path=image.file_path,
        file_size=image.file_size,
        file_format=image.file_format,
        width=image.width,
        height=image.height,
        status=image.status,
        check_status=image.check_status,
        dataset_path=image.dataset_path,
        created_at=image.created_at,
        updated_at=image.updated_at,
        parsed_at=image.parsed_at,
        checked_at=image.checked_at,
        metadata_json=image.metadata_json,
        uploader_id=image.uploader_id,
        checker_id=image.checker_id,
        labels=None
    )

    # 添加标签信息
    if image.labels:
        response.labels = {
            'year': image.labels.year,
            'month': image.labels.month,
            'day': image.labels.day,
            'hour': image.labels.hour,
            'season': image.labels.season,
            'time_period': image.labels.time_period,
            'day_type': image.labels.day_type,
            'weather': image.labels.weather,
            'temperature': image.labels.temperature,
            'humidity': image.labels.humidity,
            'light': image.labels.light,
            'shoot_angle': image.labels.shoot_angle,
            'scene_scale': image.labels.scene_scale,
            'clarity': image.labels.clarity,
            'exposure': image.labels.exposure,
            'scene_type': image.labels.scene_type,
            'device_type': image.labels.device_type,
            'province': image.labels.province,
            'city': image.labels.city,
            'district': image.labels.district,
            'address': image.labels.address,
            'ai_scene_labels': image.labels.ai_scene_labels,
            'ai_objects': image.labels.ai_objects,
            'ai_quality_score': image.labels.ai_quality_score,
        }

    return response


@router.post("/check")
async def check_image(
    check_data: CheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """审核图片"""
    if check_data.status not in ["checked", "discard"]:
        raise HTTPException(status_code=400, detail="无效的审核状态")

    # 获取图片
    result = await db.execute(
        select(DatasetImage).where(DatasetImage.id == check_data.image_id)
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    if image.check_status != "pending":
        raise HTTPException(status_code=400, detail="该图片已审核")

    # 更新状态
    image.check_status = check_data.status
    image.checker_id = current_user.id
    image.checked_at = datetime.now()

    if check_data.status == "checked":
        image.status = "checked"
        # 移动到正式数据集目录
        if image.dataset_path:
            final_path = str(settings.DATASET_DIR / image.dataset_path / image.stored_filename)
            if os.path.exists(image.file_path) and not os.path.exists(final_path):
                os.makedirs(os.path.dirname(final_path), exist_ok=True)
                shutil.move(image.file_path, final_path)
                image.file_path = final_path
    else:
        image.status = "discarded"
        # 移动到废弃目录
        discard_path = str(settings.DISCARD_DIR / image.stored_filename)
        if os.path.exists(image.file_path):
            shutil.move(image.file_path, discard_path)
            image.file_path = discard_path

    await db.commit()

    # 记录日志
    log = OperationLog(
        user_id=current_user.id,
        action="check_image",
        target_type="image",
        target_id=image.id,
        detail={"status": check_data.status, "comment": check_data.comment},
    )
    db.add(log)
    await db.commit()

    logger.info(f"图片审核完成: {image.id} -> {check_data.status}")

    return {"message": "审核成功", "status": check_data.status}


@router.post("/batch-check")
async def batch_check_images(
    batch_data: BatchCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """批量审核图片"""
    if batch_data.status not in ["checked", "discard"]:
        raise HTTPException(status_code=400, detail="无效的审核状态")

    success_count = 0
    failed_count = 0

    for image_id in batch_data.image_ids:
        try:
            result = await db.execute(
                select(DatasetImage).where(DatasetImage.id == image_id)
            )
            image = result.scalar_one_or_none()

            if not image or image.check_status != "pending":
                failed_count += 1
                continue

            image.check_status = batch_data.status
            image.checker_id = current_user.id
            image.checked_at = datetime.now()

            if batch_data.status == "checked":
                image.status = "checked"
            else:
                image.status = "discarded"

            success_count += 1

        except Exception as e:
            logger.error(f"审核图片 {image_id} 失败: {e}")
            failed_count += 1

    await db.commit()

    return {
        "total": len(batch_data.image_ids),
        "success": success_count,
        "failed": failed_count
    }


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除图片"""
    result = await db.execute(
        select(DatasetImage).where(DatasetImage.id == image_id)
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 删除文件
    if os.path.exists(image.file_path):
        os.remove(image.file_path)

    # 删除数据库记录
    await db.delete(image)
    await db.commit()

    logger.info(f"图片已删除: {image_id}")

    return {"message": "删除成功"}


@router.get("/stats/overview")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取图片统计信息"""
    # 尝试从缓存获取
    cache_key = "image_stats"
    cached = await cache_service.get(cache_key)
    if cached:
        logger.debug("统计信息缓存命中")
        return cached

    # 缓存未命中，查询数据库
    logger.debug("统计信息缓存未命中，查询数据库")

    # 总数
    total_result = await db.execute(select(func.count(DatasetImage.id)))
    total = total_result.scalar()

    # 各状态统计
    status_stats = {}
    for status in ["uploading", "parsing", "parsed", "checked", "discarded"]:
        result = await db.execute(
            select(func.count(DatasetImage.id))
            .where(DatasetImage.status == status)
        )
        status_stats[status] = result.scalar()

    # 今日上传
    today = datetime.now().date()
    today_result = await db.execute(
        select(func.count(DatasetImage.id))
        .where(func.date(DatasetImage.created_at) == today)
    )
    today_count = today_result.scalar()

    result = {
        "total": total,
        "status_stats": status_stats,
        "today_upload": today_count,
    }

    # 写入缓存（5分钟过期）
    await cache_service.set(cache_key, result, expire=300)

    return result
