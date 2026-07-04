# -*- coding: utf-8 -*-
"""
导出服务 - 提供CSV导出功能
"""

import csv
import io
from typing import List

from database import DatasetImage

import logging

logger = logging.getLogger(__name__)


class ExportService:
    """导出服务"""

    def export_csv(self, images: List[DatasetImage], version_name: str) -> str:
        """
        导出CSV格式

        Args:
            images: 图片列表（需包含labels关系）
            version_name: 版本名称

        Returns:
            CSV字符串内容
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头
        headers = [
            "image_id", "filename", "width", "height",
            "year", "month", "day", "hour", "season", "time_period", "day_type",
            "weather", "temperature", "humidity", "light",
            "shoot_angle", "scene_scale", "clarity", "exposure",
            "scene_type", "device_type",
            "province", "city", "district", "address",
            "longitude", "latitude",
        ]
        writer.writerow(headers)

        # 写入数据
        for image in images:
            label = image.labels if image.labels else None
            row = [
                image.id,
                image.original_filename,
                image.width,
                image.height,
                label.year if label else None,
                label.month if label else None,
                label.day if label else None,
                label.hour if label else None,
                label.season if label else None,
                label.time_period if label else None,
                label.day_type if label else None,
                label.weather if label else None,
                label.temperature if label else None,
                label.humidity if label else None,
                label.light if label else None,
                label.shoot_angle if label else None,
                label.scene_scale if label else None,
                label.clarity if label else None,
                label.exposure if label else None,
                label.scene_type if label else None,
                label.device_type if label else None,
                label.province if label else None,
                label.city if label else None,
                label.district if label else None,
                label.address if label else None,
                label.longitude if label else None,
                label.latitude if label else None,
            ]
            writer.writerow(row)

        output.seek(0)
        return output.getvalue()


# 全局导出服务实例
export_service = ExportService()
