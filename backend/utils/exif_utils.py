# -*- coding: utf-8 -*-
"""
EXIF元数据解析工具
提取图片的拍摄时间、GPS、相机参数等信息
"""

import io
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

import logging

logger = logging.getLogger(__name__)


class ExifUtils:
    """EXIF解析工具类"""

    @staticmethod
    def read_exif(file_path: str) -> Dict[str, Any]:
        """
        读取图片EXIF数据

        Args:
            file_path: 图片文件路径

        Returns:
            EXIF数据字典
        """
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)

            exif_data = {}
            for tag, value in tags.items():
                # 清理标签名
                clean_tag = tag.split(' ')[-1] if ' ' in tag else tag
                exif_data[clean_tag] = str(value)

            return exif_data
        except Exception as e:
            logger.warning(f"读取EXIF失败: {e}")
            return {}

    @staticmethod
    def extract_datetime(exif_data: Dict[str, Any]) -> Optional[datetime]:
        """
        从EXIF提取拍摄时间

        Args:
            exif_data: EXIF数据字典

        Returns:
            拍摄时间datetime对象
        """
        # 尝试多个时间字段
        time_fields = [
            'DateTimeOriginal',
            'DateTimeDigitized',
            'DateTime',
        ]

        for field in time_fields:
            time_str = exif_data.get(field)
            if time_str:
                try:
                    # EXIF时间格式: 2024:01:15 14:30:00
                    return datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    continue

        return None

    @staticmethod
    def extract_gps(exif_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """
        从EXIF提取GPS坐标

        Args:
            exif_data: EXIF数据字典

        Returns:
            (经度, 纬度) 元组
        """
        try:
            # 获取GPS纬度
            lat_tag = exif_data.get('GPSLatitude')
            lat_ref = exif_data.get('GPSLatitudeRef', 'N')
            lon_tag = exif_data.get('GPSLongitude')
            lon_ref = exif_data.get('GPSLongitudeRef', 'E')

            if not lat_tag or not lon_tag:
                return None

            def parse_dms(dms_str: str) -> float:
                """解析度分秒格式"""
                # 格式: [deg, min, sec]
                dms_str = dms_str.strip('[]')
                parts = [p.strip() for p in dms_str.split(',')]
                if len(parts) >= 3:
                    # 处理分数格式
                    def to_float(s):
                        if '/' in s:
                            num, den = s.split('/')
                            return float(num) / float(den)
                        return float(s)

                    degrees = to_float(parts[0])
                    minutes = to_float(parts[1])
                    seconds = to_float(parts[2])
                    return degrees + minutes / 60 + seconds / 3600
                return 0.0

            latitude = parse_dms(lat_tag)
            longitude = parse_dms(lon_tag)

            # 处理南纬和西经
            if lat_ref == 'S':
                latitude = -latitude
            if lon_ref == 'W':
                longitude = -longitude

            return (longitude, latitude)

        except Exception as e:
            logger.warning(f"解析GPS失败: {e}")
            return None

    @staticmethod
    def extract_camera_info(exif_data: Dict[str, Any]) -> Dict[str, str]:
        """
        提取相机信息

        Args:
            exif_data: EXIF数据字典

        Returns:
            相机信息字典
        """
        return {
            'make': exif_data.get('ImageMake', '').strip(),
            'model': exif_data.get('ImageModel', '').strip(),
            'software': exif_data.get('ImageSoftware', '').strip(),
            'focal_length': exif_data.get('FocalLength', ''),
            'aperture': exif_data.get('FNumber', ''),
            'iso': exif_data.get('ISOSpeedRatings', ''),
            'exposure_time': exif_data.get('ExposureTime', ''),
            'flash': exif_data.get('Flash', ''),
        }

    @staticmethod
    def extract_image_info(file_path: str) -> Dict[str, Any]:
        """
        提取图片基本信息（尺寸、格式等）

        Args:
            file_path: 图片文件路径

        Returns:
            图片信息字典
        """
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': img.fp.seek(0, 2) if hasattr(img.fp, 'seek') else 0,
                }
        except Exception as e:
            logger.warning(f"读取图片信息失败: {e}")
            return {}

    @staticmethod
    def get_season(month: int) -> str:
        """
        根据月份获取季节

        Args:
            month: 月份

        Returns:
            季节名称
        """
        if month in [3, 4, 5]:
            return "春"
        elif month in [6, 7, 8]:
            return "夏"
        elif month in [9, 10, 11]:
            return "秋"
        else:
            return "冬"

    @staticmethod
    def get_time_period(hour: int) -> str:
        """
        根据小时获取时段

        Args:
            hour: 小时

        Returns:
            时段名称
        """
        if 0 <= hour < 6:
            return "凌晨"
        elif 6 <= hour < 11:
            return "上午"
        elif 11 <= hour < 14:
            return "中午"
        elif 14 <= hour < 18:
            return "下午"
        elif 18 <= hour < 20:
            return "傍晚"
        else:
            return "夜晚"

    @staticmethod
    def is_weekday(dt: datetime) -> str:
        """
        判断是否工作日

        Args:
            dt: 日期时间

        Returns:
            "工作日" 或 "节假日"
        """
        # 简单判断，实际可接入节假日API
        if dt.weekday() < 5:
            return "工作日"
        return "节假日"

    @staticmethod
    def detect_device_type(make: str, model: str) -> str:
        """
        根据品牌型号检测设备类型

        Args:
            make: 品牌
            model: 型号

        Returns:
            设备类型
        """
        make_lower = make.lower()
        model_lower = model.lower()

        # 手机品牌
        phone_brands = ['apple', 'samsung', 'huawei', 'xiaomi', 'oppo', 'vivo', 'oneplus', 'google']
        if any(brand in make_lower for brand in phone_brands):
            return "手机"

        # 无人机
        drone_keywords = ['dji', 'mavic', 'phantom', 'drone']
        if any(kw in make_lower or kw in model_lower for kw in drone_keywords):
            return "无人机"

        # 工业相机
        industrial_keywords = ['flir', 'basler', 'ids', 'industrial', 'machine vision']
        if any(kw in make_lower or kw in model_lower for kw in industrial_keywords):
            return "工业相机"

        # 监控摄像头
        surveillance_keywords = ['hikvision', 'dahua', 'axis', 'surveillance', 'cctv']
        if any(kw in make_lower or kw in model_lower for kw in surveillance_keywords):
            return "监控"

        # 默认为单反/数码相机
        if make:
            return "单反"

        return "其他"

    @classmethod
    def parse_all(cls, file_path: str) -> Dict[str, Any]:
        """
        解析图片所有EXIF信息

        Args:
            file_path: 图片文件路径

        Returns:
            完整解析结果
        """
        exif_data = cls.read_exif(file_path)
        capture_time = cls.extract_datetime(exif_data)
        gps = cls.extract_gps(exif_data)
        camera = cls.extract_camera_info(exif_data)
        image_info = cls.extract_image_info(file_path)

        result = {
            'exif_raw': exif_data,
            'capture_time': capture_time,
            'gps': gps,
            'camera': camera,
            'image_info': image_info,
        }

        # 从时间提取维度标签
        if capture_time:
            result['year'] = capture_time.year
            result['month'] = capture_time.month
            result['day'] = capture_time.day
            result['hour'] = capture_time.hour
            result['season'] = cls.get_season(capture_time.month)
            result['time_period'] = cls.get_time_period(capture_time.hour)
            result['day_type'] = cls.is_weekday(capture_time)

        # 设备类型
        if camera.get('make') or camera.get('model'):
            result['device_type'] = cls.detect_device_type(
                camera.get('make', ''),
                camera.get('model', '')
            )

        return result
