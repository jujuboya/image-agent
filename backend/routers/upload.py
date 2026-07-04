# -*- coding: utf-8 -*-
"""
图片上传路由
"""

import asyncio
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db, DatasetImage, DatasetLabel, SysUser
from routers.auth import get_current_user
from services.agent_parse import agent_service
from utils.file_utils import FileUtils, ImageValidator

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 数据模型 ====================
class UploadResponse(BaseModel):
    image_id: int
    uuid: str
    filename: str
    status: str
    message: str


class BatchUploadResponse(BaseModel):
    total: int
    success: int
    failed: int
    results: List[UploadResponse]


# ==================== 路由 ====================
@router.post("/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """
    上传单张图片

    - 支持格式: jpg, jpeg, png, bmp, tiff, webp
    - 最大大小: 50MB
    - 自动触发Agent异步解析
    """
    # 验证文件
    content = await file.read()
    is_valid, error_msg = FileUtils.validate_file(file.filename, len(content))
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # 生成UUID和文件名
    image_uuid = FileUtils.generate_uuid()
    stored_filename = FileUtils.get_stored_filename(file.filename, image_uuid)
    temp_path = str(settings.TEMP_DIR / stored_filename)

    # 保存到临时目录
    success = await FileUtils.save_upload_file(content, temp_path)
    if not success:
        raise HTTPException(status_code=500, detail="文件保存失败")

    # 验证图片有效性
    is_valid_image, error_msg = ImageValidator.is_valid_image(temp_path)
    if not is_valid_image:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail=error_msg)

    # 计算MD5
    file_md5 = FileUtils.calculate_md5(temp_path)

    # 检查是否重复
    from sqlalchemy import select
    result = await db.execute(
        select(DatasetImage).where(DatasetImage.file_md5 == file_md5)
    )
    existing = result.scalar_one_or_none()
    if existing:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail="图片已存在")

    # 获取图片尺寸
    dimensions = ImageValidator.get_image_dimensions(temp_path)

    # 创建数据库记录
    image = DatasetImage(
        image_uuid=image_uuid,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=temp_path,
        file_size=len(content),
        file_md5=file_md5,
        file_format=FileUtils.get_file_extension(file.filename),
        width=dimensions[0] if dimensions else None,
        height=dimensions[1] if dimensions else None,
        status="parsing",
        uploader_id=current_user.id,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    # 创建空标签记录
    label = DatasetLabel(image_id=image.id, source="auto")
    db.add(label)
    await db.commit()

    # 异步触发Agent解析
    if background_tasks:
        background_tasks.add_task(
            process_image_async,
            image.id,
            temp_path,
        )

    logger.info(f"图片上传成功: {file.filename} -> {image_uuid}")

    return UploadResponse(
        image_id=image.id,
        uuid=image_uuid,
        filename=file.filename,
        status="parsing",
        message="上传成功，正在自动解析..."
    )


@router.post("/batch", response_model=BatchUploadResponse)
async def upload_batch(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """
    批量上传图片

    - 单次最多1000张
    - 异步处理，立即返回
    """
    if len(files) > settings.BATCH_UPLOAD_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"单次最多上传{settings.BATCH_UPLOAD_LIMIT}张图片"
        )

    results = []
    success_count = 0
    failed_count = 0

    for file in files:
        try:
            # 读取文件内容
            content = await file.read()

            # 验证文件
            is_valid, error_msg = FileUtils.validate_file(file.filename, len(content))
            if not is_valid:
                results.append(UploadResponse(
                    image_id=0,
                    uuid="",
                    filename=file.filename,
                    status="failed",
                    message=error_msg
                ))
                failed_count += 1
                continue

            # 生成UUID和文件名
            image_uuid = FileUtils.generate_uuid()
            stored_filename = FileUtils.get_stored_filename(file.filename, image_uuid)
            temp_path = str(settings.TEMP_DIR / stored_filename)

            # 保存文件
            success = await FileUtils.save_upload_file(content, temp_path)
            if not success:
                results.append(UploadResponse(
                    image_id=0,
                    uuid="",
                    filename=file.filename,
                    status="failed",
                    message="文件保存失败"
                ))
                failed_count += 1
                continue

            # 验证图片
            is_valid_image, error_msg = ImageValidator.is_valid_image(temp_path)
            if not is_valid_image:
                os.remove(temp_path)
                results.append(UploadResponse(
                    image_id=0,
                    uuid="",
                    filename=file.filename,
                    status="failed",
                    message=error_msg
                ))
                failed_count += 1
                continue

            # 计算MD5
            file_md5 = FileUtils.calculate_md5(temp_path)

            # 检查重复
            from sqlalchemy import select
            result = await db.execute(
                select(DatasetImage).where(DatasetImage.file_md5 == file_md5)
            )
            if result.scalar_one_or_none():
                os.remove(temp_path)
                results.append(UploadResponse(
                    image_id=0,
                    uuid="",
                    filename=file.filename,
                    status="failed",
                    message="图片已存在"
                ))
                failed_count += 1
                continue

            # 获取尺寸
            dimensions = ImageValidator.get_image_dimensions(temp_path)

            # 创建记录
            image = DatasetImage(
                image_uuid=image_uuid,
                original_filename=file.filename,
                stored_filename=stored_filename,
                file_path=temp_path,
                file_size=len(content),
                file_md5=file_md5,
                file_format=FileUtils.get_file_extension(file.filename),
                width=dimensions[0] if dimensions else None,
                height=dimensions[1] if dimensions else None,
                status="parsing",
                uploader_id=current_user.id,
            )
            db.add(image)
            await db.flush()

            # 创建标签
            label = DatasetLabel(image_id=image.id, source="auto")
            db.add(label)

            results.append(UploadResponse(
                image_id=image.id,
                uuid=image_uuid,
                filename=file.filename,
                status="parsing",
                message="上传成功"
            ))
            success_count += 1

        except Exception as e:
            logger.error(f"处理文件 {file.filename} 失败: {e}")
            results.append(UploadResponse(
                image_id=0,
                uuid="",
                filename=file.filename,
                status="failed",
                message=str(e)
            ))
            failed_count += 1

    await db.commit()

    # 批量异步处理
    if background_tasks and success_count > 0:
        for result in results:
            if result.status == "parsing":
                image = await db.get(DatasetImage, result.image_id)
                if image:
                    background_tasks.add_task(
                        process_image_async,
                        image.id,
                        image.file_path,
                    )

    logger.info(f"批量上传完成: 成功{success_count}张，失败{failed_count}张")

    return BatchUploadResponse(
        total=len(files),
        success=success_count,
        failed=failed_count,
        results=results
    )


async def process_image_async(image_id: int, file_path: str):
    """
    异步处理图片（Agent解析）

    Args:
        image_id: 图片ID
        file_path: 文件路径
    """
    from database import async_session

    try:
        # 解析图片
        parse_result = await agent_service.parse_image(file_path, image_id)

        async with async_session() as db:
            # 更新图片状态
            image = await db.get(DatasetImage, image_id)
            if image:
                image.status = "parsed"
                image.parsed_at = datetime.now()
                image.metadata_json = parse_result.get('metadata')

                # 生成归档路径
                labels = parse_result.get('labels', {})
                from config import generate_dataset_path
                dataset_path = generate_dataset_path(labels)
                image.dataset_path = dataset_path

                # 更新标签
                label_result = await db.execute(
                    select(DatasetLabel).where(DatasetLabel.image_id == image_id)
                )
                label = label_result.scalar_one_or_none()

                if label:
                    # 更新标签字段
                    for key, value in labels.items():
                        if hasattr(label, key) and value is not None:
                            setattr(label, key, value)
                    label.source = "auto"

                # 移动文件到正式目录
                from config import settings
                import shutil
                final_path = str(settings.DATASET_DIR / dataset_path / image.stored_filename)
                os.makedirs(os.path.dirname(final_path), exist_ok=True)
                shutil.move(file_path, final_path)
                image.file_path = final_path

                await db.commit()
                logger.info(f"图片处理完成: {image_id}")

    except Exception as e:
        logger.error(f"图片处理失败 {image_id}: {e}")
        # 更新状态为失败
        try:
            async with async_session() as db:
                image = await db.get(DatasetImage, image_id)
                if image:
                    image.status = "uploading"  # 回退状态
                    await db.commit()
        except Exception:
            pass


from sqlalchemy import select
