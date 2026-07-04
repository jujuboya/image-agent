# -*- coding: utf-8 -*-
"""
数据集管理路由
"""

import json
import os
import zipfile
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings, LabelEnums
from database import get_db, DatasetImage, DatasetLabel, DatasetVersion, SysUser
from routers.auth import get_current_user
from services.export_service import export_service

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 数据模型 ====================
class ExportRequest(BaseModel):
    """导出请求"""
    format: str  # yolo, coco, voc, json, csv
    filters: Optional[dict] = None
    version_name: Optional[str] = None
    description: Optional[str] = None


class VersionResponse(BaseModel):
    """版本响应"""
    id: int
    version_name: str
    version_code: str
    description: Optional[str]
    total_images: int
    export_format: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 路由 ====================
@router.get("/versions", response_model=List[VersionResponse])
async def list_versions(
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取数据集版本列表"""
    result = await db.execute(
        select(DatasetVersion).order_by(DatasetVersion.created_at.desc())
    )
    return result.scalars().all()


@router.post("/export")
async def export_dataset(
    export_request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """
    导出数据集

    支持格式：YOLO, COCO, VOC, JSON, CSV
    """
    if export_request.format not in ["yolo", "coco", "voc", "json", "csv"]:
        raise HTTPException(status_code=400, detail="不支持的导出格式")

    # 构建查询
    query = (
        select(DatasetImage)
        .options(selectinload(DatasetImage.labels))
        .where(DatasetImage.check_status == "checked")
    )

    # 应用筛选条件
    if export_request.filters:
        filters = export_request.filters
        if filters.get("scene_type"):
            query = query.join(DatasetLabel).where(DatasetLabel.scene_type == filters["scene_type"])
        if filters.get("weather"):
            query = query.join(DatasetLabel).where(DatasetLabel.weather == filters["weather"])
        if filters.get("season"):
            query = query.join(DatasetLabel).where(DatasetLabel.season == filters["season"])

    result = await db.execute(query)
    images = result.scalars().all()

    if not images:
        raise HTTPException(status_code=400, detail="没有符合条件的图片")

    # 生成版本号
    version_code = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_name = export_request.version_name or f"v_{version_code}"

    # 根据格式导出
    if export_request.format == "csv":
        csv_content = export_service.export_csv(images, version_name)
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={version_name}.csv"
            }
        )
    elif export_request.format == "json":
        return await _export_json(images, version_name)
    elif export_request.format == "yolo":
        return await _export_yolo(images, db, version_name)
    elif export_request.format == "coco":
        return await _export_coco(images, db, version_name)
    elif export_request.format == "voc":
        return await _export_voc(images, db, version_name)


async def _export_json(images: list, version_name: str) -> StreamingResponse:
    """导出JSON格式"""
    data = []

    for image in images:
        label = image.labels if image.labels else None
        item = {
            "image_id": image.id,
            "filename": image.original_filename,
            "width": image.width,
            "height": image.height,
            "file_size": image.file_size,
            "file_format": image.file_format,
            "metadata": image.metadata_json,
            "labels": {
                "year": label.year if label else None,
                "month": label.month if label else None,
                "day": label.day if label else None,
                "hour": label.hour if label else None,
                "season": label.season if label else None,
                "time_period": label.time_period if label else None,
                "day_type": label.day_type if label else None,
                "weather": label.weather if label else None,
                "temperature": label.temperature if label else None,
                "humidity": label.humidity if label else None,
                "light": label.light if label else None,
                "shoot_angle": label.shoot_angle if label else None,
                "scene_scale": label.scene_scale if label else None,
                "clarity": label.clarity if label else None,
                "exposure": label.exposure if label else None,
                "scene_type": label.scene_type if label else None,
                "device_type": label.device_type if label else None,
                "location": {
                    "province": label.province if label else None,
                    "city": label.city if label else None,
                    "district": label.district if label else None,
                    "address": label.address if label else None,
                    "longitude": label.longitude if label else None,
                    "latitude": label.latitude if label else None,
                }
            }
        }
        data.append(item)

    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={version_name}.json"
        }
    )


async def _export_yolo(images: list, db: AsyncSession, version_name: str) -> FileResponse:
    """导出YOLO格式"""
    import tempfile
    import shutil

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    dataset_dir = os.path.join(temp_dir, version_name)

    # 创建目录结构
    os.makedirs(os.path.join(dataset_dir, "images", "train"), exist_ok=True)
    os.makedirs(os.path.join(dataset_dir, "images", "val"), exist_ok=True)
    os.makedirs(os.path.join(dataset_dir, "labels", "train"), exist_ok=True)
    os.makedirs(os.path.join(dataset_dir, "labels", "val"), exist_ok=True)

    # 收集所有场景类型作为类别
    scene_types = set()
    for image in images:
        if image.labels and image.labels.scene_type:
            scene_types.add(image.labels.scene_type)

    class_names = sorted(list(scene_types))
    class_map = {name: idx for idx, name in enumerate(class_names)}

    # 写入classes.txt
    with open(os.path.join(dataset_dir, "classes.txt"), "w", encoding="utf-8") as f:
        for name in class_names:
            f.write(f"{name}\n")

    # 分配训练集和验证集（80/20）
    split_idx = int(len(images) * 0.8)
    train_images = images[:split_idx]
    val_images = images[split_idx:]

    # 复制图片和生成标签
    for idx, image in enumerate(train_images):
        # 复制图片
        if os.path.exists(image.file_path):
            ext = os.path.splitext(image.original_filename)[1]
            dst_img = os.path.join(dataset_dir, "images", "train", f"{idx:06d}{ext}")
            shutil.copy2(image.file_path, dst_img)

            # 生成标签文件（简化版，实际需要检测框信息）
            label_file = os.path.join(dataset_dir, "labels", "train", f"{idx:06d}.txt")
            with open(label_file, "w") as f:
                if image.labels and image.labels.scene_type in class_map:
                    class_id = class_map[image.labels.scene_type]
                    # YOLO格式: class_id center_x center_y width height
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

    for idx, image in enumerate(val_images):
        if os.path.exists(image.file_path):
            ext = os.path.splitext(image.original_filename)[1]
            dst_img = os.path.join(dataset_dir, "images", "val", f"{idx:06d}{ext}")
            shutil.copy2(image.file_path, dst_img)

            label_file = os.path.join(dataset_dir, "labels", "val", f"{idx:06d}.txt")
            with open(label_file, "w") as f:
                if image.labels and image.labels.scene_type in class_map:
                    class_id = class_map[image.labels.scene_type]
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

    # 写入data.yaml
    yaml_content = f"""train: ./images/train
val: ./images/val

nc: {len(class_names)}
names: {class_names}
"""
    with open(os.path.join(dataset_dir, "data.yaml"), "w", encoding="utf-8") as f:
        f.write(yaml_content)

    # 打包成zip
    zip_path = os.path.join(settings.EXPORT_DIR, f"{version_name}.zip")
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)

    shutil.make_archive(
        os.path.join(settings.EXPORT_DIR, version_name),
        'zip',
        temp_dir
    )

    # 清理临时目录
    shutil.rmtree(temp_dir)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{version_name}.zip"
    )


async def _export_coco(images: list, db: AsyncSession, version_name: str) -> StreamingResponse:
    """导出COCO格式"""
    coco_data = {
        "info": {
            "description": "图片数据集智能采集Agent系统导出",
            "version": "1.0",
            "year": datetime.now().year,
            "date_created": datetime.now().isoformat()
        },
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": []
    }

    # 收集类别
    scene_types = set()
    for image in images:
        if image.labels and image.labels.scene_type:
            scene_types.add(image.labels.scene_type)

    class_names = sorted(list(scene_types))
    for idx, name in enumerate(class_names):
        coco_data["categories"].append({
            "id": idx + 1,
            "name": name,
            "supercategory": "scene"
        })

    class_map = {name: idx + 1 for idx, name in enumerate(class_names)}

    # 添加图片和标注
    for ann_id, image in enumerate(images, 1):
        coco_data["images"].append({
            "id": image.id,
            "file_name": image.original_filename,
            "width": image.width or 0,
            "height": image.height or 0,
        })

        if image.labels and image.labels.scene_type:
            coco_data["annotations"].append({
                "id": ann_id,
                "image_id": image.id,
                "category_id": class_map.get(image.labels.scene_type, 1),
                "bbox": [0, 0, image.width or 0, image.height or 0],
                "area": (image.width or 0) * (image.height or 0),
                "iscrowd": 0,
            })

    json_str = json.dumps(coco_data, ensure_ascii=False, indent=2)

    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={version_name}_coco.json"
        }
    )


async def _export_voc(images: list, db: AsyncSession, version_name: str) -> FileResponse:
    """导出VOC格式"""
    import tempfile
    import shutil
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom.minidom import parseString

    temp_dir = tempfile.mkdtemp()
    dataset_dir = os.path.join(temp_dir, version_name)

    # 创建目录结构
    os.makedirs(os.path.join(dataset_dir, "JPEGImages"), exist_ok=True)
    os.makedirs(os.path.join(dataset_dir, "Annotations"), exist_ok=True)
    os.makedirs(os.path.join(dataset_dir, "ImageSets", "Main"), exist_ok=True)

    # 写入图片列表
    train_list = []
    val_list = []

    split_idx = int(len(images) * 0.8)

    for idx, image in enumerate(images):
        # 复制图片
        if os.path.exists(image.file_path):
            dst_img = os.path.join(dataset_dir, "JPEGImages", image.original_filename)
            shutil.copy2(image.file_path, dst_img)

        # 生成XML标注
        root = Element("annotation")
        SubElement(root, "filename").text = image.original_filename

        size = SubElement(root, "size")
        SubElement(size, "width").text = str(image.width or 0)
        SubElement(size, "height").text = str(image.height or 0)
        SubElement(size, "depth").text = "3"

        if image.labels and image.labels.scene_type:
            obj = SubElement(root, "object")
            SubElement(obj, "name").text = image.labels.scene_type
            SubElement(obj, "pose").text = "Unspecified"
            SubElement(obj, "truncated").text = "0"
            SubElement(obj, "difficult").text = "0"

            bndbox = SubElement(obj, "bndbox")
            SubElement(bndbox, "xmin").text = "0"
            SubElement(bndbox, "ymin").text = "0"
            SubElement(bndbox, "xmax").text = str(image.width or 0)
            SubElement(bndbox, "ymax").text = str(image.height or 0)

        # 写入XML
        xml_str = parseString(tostring(root)).toprettyxml(indent="  ")
        xml_path = os.path.join(
            dataset_dir, "Annotations",
            os.path.splitext(image.original_filename)[0] + ".xml"
        )
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # 添加到列表
        name_without_ext = os.path.splitext(image.original_filename)[0]
        if idx < split_idx:
            train_list.append(name_without_ext)
        else:
            val_list.append(name_without_ext)

    # 写入ImageSets
    with open(os.path.join(dataset_dir, "ImageSets", "Main", "train.txt"), "w") as f:
        f.write("\n".join(train_list))

    with open(os.path.join(dataset_dir, "ImageSets", "Main", "val.txt"), "w") as f:
        f.write("\n".join(val_list))

    # 打包成zip
    zip_path = os.path.join(settings.EXPORT_DIR, f"{version_name}_voc.zip")
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)

    shutil.make_archive(
        os.path.join(settings.EXPORT_DIR, f"{version_name}_voc"),
        'zip',
        temp_dir
    )

    shutil.rmtree(temp_dir)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{version_name}_voc.zip"
    )


@router.get("/stats")
async def get_dataset_stats(
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取数据集统计信息"""
    # 总图片数
    total_result = await db.execute(
        select(func.count(DatasetImage.id))
        .where(DatasetImage.check_status == "checked")
    )
    total_images = total_result.scalar()

    # 场景分布
    scene_result = await db.execute(
        select(
            DatasetLabel.scene_type,
            func.count(DatasetLabel.id)
        )
        .group_by(DatasetLabel.scene_type)
    )
    scene_distribution = {row[0]: row[1] for row in scene_result.all() if row[0]}

    # 天气分布
    weather_result = await db.execute(
        select(
            DatasetLabel.weather,
            func.count(DatasetLabel.id)
        )
        .group_by(DatasetLabel.weather)
    )
    weather_distribution = {row[0]: row[1] for row in weather_result.all() if row[0]}

    # 季节分布
    season_result = await db.execute(
        select(
            DatasetLabel.season,
            func.count(DatasetLabel.id)
        )
        .group_by(DatasetLabel.season)
    )
    season_distribution = {row[0]: row[1] for row in season_result.all() if row[0]}

    return {
        "total_images": total_images,
        "scene_distribution": scene_distribution,
        "weather_distribution": weather_distribution,
        "season_distribution": season_distribution,
    }
