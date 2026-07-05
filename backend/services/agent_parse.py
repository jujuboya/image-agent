# -*- coding: utf-8 -*-
"""
Agent自动解析服务
核心功能：EXIF解析、GPS逆编码、天气匹配、场景识别、画质检测
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from geopy.geocoders import Nominatim

from config import settings, LabelEnums
from services.ai_service import ai_service
from utils.exif_utils import ExifUtils
from utils.file_utils import FileUtils

import logging

logger = logging.getLogger(__name__)


class AgentParseService:
    """Agent自动解析服务"""

    def __init__(self):
        self.geocoder = Nominatim(user_agent="image_dataset_agent", timeout=10)
        self._weather_cache = {}

    async def parse_image(self, file_path: str, image_id: int) -> Dict[str, Any]:
        """
        解析图片，提取所有维度标签

        Args:
            file_path: 图片文件路径
            image_id: 图片ID

        Returns:
            解析结果字典
        """
        logger.info(f"开始解析图片: {file_path}")

        # 1. EXIF解析
        exif_result = ExifUtils.parse_all(file_path)
        logger.info(f"EXIF解析完成: {image_id}")

        # 2. GPS逆编码
        location_info = {}
        if exif_result.get('gps'):
            location_info = await self.reverse_geocode(*exif_result['gps'])
            logger.info(f"GPS逆编码完成: {location_info}")

        # 3. 天气匹配
        weather_info = {}
        if exif_result.get('capture_time') and exif_result.get('gps'):
            weather_info = await self.get_weather(
                exif_result['capture_time'],
                *exif_result['gps']
            )
            logger.info(f"天气匹配完成: {weather_info}")

        # 4. AI画质检测
        quality_info = await ai_service.detect_quality(file_path)
        logger.info(f"AI画质检测完成: {quality_info}")

        # 5. AI场景识别
        ai_scene = await ai_service.recognize_scene(file_path)
        logger.info(f"AI场景识别完成: {ai_scene}")

        # 转换AI场景结果为统一格式（兼容generate_standard_labels）
        scene_info = {
            'scene_type': ai_scene.get('scene_type', '其他'),
            'ai_labels': [
                {'category': p['category'], 'confidence': p['confidence']}
                for p in ai_scene.get('predictions', [])
            ],
            'objects': [],
            'confidence': ai_scene.get('confidence', 0.0),
        }

        # 合并结果
        result = {
            **exif_result,
            'location': location_info,
            'weather': weather_info,
            'quality': quality_info,
            'scene': scene_info,
            'parsed_at': datetime.now().isoformat(),
        }

        # 生成标准化标签
        labels = self.generate_standard_labels(result)
        result['labels'] = labels

        # 生成元数据JSON
        metadata = self.generate_metadata(file_path, result)
        result['metadata'] = metadata

        logger.info(f"图片解析完成: {image_id}")
        return result

    async def reverse_geocode(self, longitude: float, latitude: float) -> Dict[str, str]:
        """
        GPS逆编码，获取地址信息

        Args:
            longitude: 经度
            latitude: 纬度

        Returns:
            地址信息字典
        """
        try:
            # 在线程池中运行同步操作
            loop = asyncio.get_event_loop()
            location = await loop.run_in_executor(
                None,
                lambda: self.geocoder.reverse(f"{latitude}, {longitude}", language="zh")
            )

            if location and location.raw.get('address'):
                address = location.raw['address']
                return {
                    'province': address.get('state', ''),
                    'city': address.get('city', ''),
                    'district': address.get('suburb', address.get('county', '')),
                    'address': location.address,
                    'full_address': location.address,
                }
        except Exception as e:
            logger.warning(f"GPS逆编码失败: {e}")

        return {
            'province': '',
            'city': '',
            'district': '',
            'address': '',
        }

    async def get_weather(
        self,
        capture_time: datetime,
        longitude: float,
        latitude: float
    ) -> Dict[str, Any]:
        """
        获取历史天气

        Args:
            capture_time: 拍摄时间
            longitude: 经度
            latitude: 纬度

        Returns:
            天气信息
        """
        # 检查缓存
        cache_key = f"{capture_time.strftime('%Y-%m-%d')}_{latitude}_{longitude}"
        if cache_key in self._weather_cache:
            return self._weather_cache[cache_key]

        # 如果没有配置天气API，返回基于时间的估算
        if not settings.WEATHER_API_KEY:
            return self._estimate_weather(capture_time)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.WEATHER_API_URL,
                    params={
                        'key': settings.WEATHER_API_KEY,
                        'q': f"{latitude},{longitude}",
                        'dt': capture_time.strftime('%Y-%m-%d'),
                        'hour': capture_time.hour,
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    forecast = data.get('forecast', {}).get('forecastday', [{}])[0]
                    hour_data = forecast.get('hour', [{}])[capture_time.hour] if capture_time.hour < 24 else {}

                    weather_info = {
                        'weather': self._map_weather_code(hour_data.get('condition', {}).get('code', 0)),
                        'temperature': hour_data.get('temp_c', None),
                        'humidity': hour_data.get('humidity', None),
                        'light': self._estimate_light(capture_time.hour),
                    }

                    # 缓存结果
                    self._weather_cache[cache_key] = weather_info
                    return weather_info

        except Exception as e:
            logger.warning(f"获取天气失败: {e}")

        return self._estimate_weather(capture_time)

    def _estimate_weather(self, capture_time: datetime) -> Dict[str, Any]:
        """
        基于时间估算天气（无API时的降级方案）

        Args:
            capture_time: 拍摄时间

        Returns:
            估算的天气信息
        """
        # 简单估算，实际应接入天气API
        return {
            'weather': '晴',  # 默认
            'temperature': None,
            'humidity': None,
            'light': self._estimate_light(capture_time.hour),
        }

    def _estimate_light(self, hour: int) -> str:
        """
        估算光照条件

        Args:
            hour: 小时

        Returns:
            光照条件
        """
        if 6 <= hour < 10:
            return "正常"
        elif 10 <= hour < 16:
            return "强光"
        elif 16 <= hour < 18:
            return "正常"
        elif 18 <= hour < 20:
            return "弱光"
        else:
            return "弱光"

    def _map_weather_code(self, code: int) -> str:
        """
        映射天气代码到中文

        Args:
            code: 天气代码

        Returns:
            天气中文名
        """
        # 简化映射，实际应根据API文档
        weather_map = {
            1000: "晴",
            1003: "多云",
            1006: "阴",
            1009: "阴",
            1030: "雾",
            1063: "小雨",
            1066: "雪",
            1069: "雪",
            1072: "小雨",
            1087: "大雨",
            1114: "雪",
            1117: "雪",
            1135: "雾",
            1147: "雾",
            1150: "小雨",
            1153: "小雨",
            1168: "小雨",
            1171: "大雨",
            1180: "小雨",
            1183: "小雨",
            1186: "小雨",
            1189: "小雨",
            1192: "大雨",
            1195: "大雨",
            1198: "小雨",
            1201: "大雨",
            1204: "雪",
            1207: "雪",
            1210: "雪",
            1213: "雪",
            1216: "雪",
            1219: "雪",
            1222: "雪",
            1225: "雪",
            1237: "雪",
            1240: "小雨",
            1243: "大雨",
            1246: "大雨",
            1249: "雪",
            1252: "雪",
            1255: "雪",
            1258: "雪",
            1261: "雪",
            1264: "雪",
            1273: "大雨",
            1276: "大雨",
            1279: "雪",
            1282: "雪",
        }
        return weather_map.get(code, "晴")

    def detect_quality(self, file_path: str) -> Dict[str, Any]:
        """
        检测图片画质

        Args:
            file_path: 图片文件路径

        Returns:
            画质信息
        """
        try:
            from PIL import Image
            import numpy as np

            with Image.open(file_path) as img:
                # 转换为灰度图
                gray = img.convert('L')
                img_array = np.array(gray)

                # 计算拉普拉斯方差（清晰度指标）
                laplacian_var = self._calculate_laplacian_variance(img_array)

                # 判断清晰度
                if laplacian_var > 500:
                    clarity = "清晰"
                elif laplacian_var > 100:
                    clarity = "轻微模糊"
                else:
                    clarity = "严重模糊"

                # 检测曝光
                mean_brightness = img_array.mean()
                if mean_brightness < 50:
                    exposure = "欠曝"
                elif mean_brightness > 200:
                    exposure = "过曝"
                else:
                    exposure = "正常"

                return {
                    'clarity': clarity,
                    'clarity_score': float(laplacian_var),
                    'exposure': exposure,
                    'brightness': float(mean_brightness),
                }

        except Exception as e:
            logger.warning(f"画质检测失败: {e}")
            return {
                'clarity': '清晰',
                'clarity_score': 0,
                'exposure': '正常',
                'brightness': 128,
            }

    def _calculate_laplacian_variance(self, img_array) -> float:
        """
        计算拉普拉斯方差

        Args:
            img_array: 图像数组

        Returns:
            拉普拉斯方差
        """
        import numpy as np

        # 简化的拉普拉斯算子
        laplacian_kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])

        # 简单卷积实现
        h, w = img_array.shape
        result = np.zeros_like(img_array, dtype=float)

        for i in range(1, h - 1):
            for j in range(1, w - 1):
                result[i, j] = np.sum(
                    img_array[i-1:i+2, j-1:j+2] * laplacian_kernel
                )

        return float(np.var(result))

    def detect_scene_simple(self, file_path: str) -> Dict[str, Any]:
        """
        简单场景识别（基于图像特征）

        Args:
            file_path: 图片文件路径

        Returns:
            场景信息
        """
        try:
            from PIL import Image
            import numpy as np

            with Image.open(file_path) as img:
                img_array = np.array(img.convert('RGB'))

                # 简单的基于颜色分布的场景判断
                mean_color = img_array.mean(axis=(0, 1))

                # 蓝天检测（蓝色通道较高）
                if mean_color[2] > mean_color[0] and mean_color[2] > mean_color[1]:
                    scene_hint = "户外"
                # 室内检测（整体较暗）
                elif img_array.mean() < 100:
                    scene_hint = "室内"
                else:
                    scene_hint = "其他"

                return {
                    'scene_type': scene_hint,
                    'ai_labels': [],
                    'objects': [],
                }

        except Exception as e:
            logger.warning(f"场景识别失败: {e}")
            return {
                'scene_type': '其他',
                'ai_labels': [],
                'objects': [],
            }

    def generate_standard_labels(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成标准化标签

        Args:
            parse_result: 解析结果

        Returns:
            标准化标签字典
        """
        labels = {}

        # 时间维度
        labels['year'] = parse_result.get('year')
        labels['month'] = parse_result.get('month')
        labels['day'] = parse_result.get('day')
        labels['hour'] = parse_result.get('hour')
        labels['season'] = parse_result.get('season')
        labels['time_period'] = parse_result.get('time_period')
        labels['day_type'] = parse_result.get('day_type')

        # 环境天气
        weather = parse_result.get('weather', {})
        labels['weather'] = weather.get('weather')
        labels['temperature'] = weather.get('temperature')
        labels['humidity'] = weather.get('humidity')
        labels['light'] = weather.get('light')

        # 拍摄维度
        quality = parse_result.get('quality', {})
        labels['clarity'] = quality.get('clarity')
        labels['exposure'] = quality.get('exposure')

        # 拍摄角度和景别（基于图像分析）
        image_info = parse_result.get('image_info', {})
        width = image_info.get('width', 0)
        height = image_info.get('height', 0)

        # 根据图片宽高比判断拍摄角度
        if width and height:
            aspect_ratio = width / height
            if aspect_ratio > 1.5:
                labels['shoot_angle'] = '平视'  # 宽屏照片通常是平视
            elif aspect_ratio < 0.75:
                labels['shoot_angle'] = '仰拍'  # 竖屏照片可能是仰拍
            else:
                labels['shoot_angle'] = '平视'  # 默认平视
        else:
            labels['shoot_angle'] = '平视'

        # 根据图片分辨率判断景别
        if width and height:
            total_pixels = width * height
            if total_pixels > 8000000:  # 800万像素以上
                labels['scene_scale'] = '远景'
            elif total_pixels > 2000000:  # 200万像素以上
                labels['scene_scale'] = '中景'
            else:
                labels['scene_scale'] = '近景'
        else:
            labels['scene_scale'] = '中景'

        # 场景设备
        scene = parse_result.get('scene', {})
        labels['scene_type'] = scene.get('scene_type')
        labels['device_type'] = parse_result.get('device_type')

        camera = parse_result.get('camera', {})
        labels['device_brand'] = camera.get('make')
        labels['device_model'] = camera.get('model')

        # 地理位置
        location = parse_result.get('location', {})
        labels['longitude'] = parse_result.get('gps', (None, None))[0] if parse_result.get('gps') else None
        labels['latitude'] = parse_result.get('gps', (None, None))[1] if parse_result.get('gps') else None
        labels['province'] = location.get('province')
        labels['city'] = location.get('city')
        labels['district'] = location.get('district')
        labels['address'] = location.get('address')

        # AI识别
        labels['ai_scene_labels'] = scene.get('ai_labels', [])
        labels['ai_objects'] = scene.get('objects', [])
        labels['ai_quality_score'] = quality.get('clarity_score')

        return labels

    def generate_metadata(
        self,
        file_path: str,
        parse_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成完整元数据

        Args:
            file_path: 文件路径
            parse_result: 解析结果

        Returns:
            元数据字典
        """
        import os

        file_stat = os.stat(file_path)

        return {
            'file': {
                'original_name': os.path.basename(file_path),
                'size': file_stat.st_size,
                'md5': FileUtils.calculate_md5(file_path),
                'format': parse_result.get('image_info', {}).get('format'),
                'width': parse_result.get('image_info', {}).get('width'),
                'height': parse_result.get('image_info', {}).get('height'),
            },
            'capture': {
                'datetime': parse_result.get('capture_time', '').isoformat() if parse_result.get('capture_time') else None,
                'year': parse_result.get('year'),
                'month': parse_result.get('month'),
                'day': parse_result.get('day'),
                'hour': parse_result.get('hour'),
                'season': parse_result.get('season'),
                'time_period': parse_result.get('time_period'),
                'day_type': parse_result.get('day_type'),
            },
            'camera': parse_result.get('camera', {}),
            'location': {
                'gps': parse_result.get('gps'),
                'address': parse_result.get('location', {}),
            },
            'weather': parse_result.get('weather', {}),
            'quality': parse_result.get('quality', {}),
            'scene': parse_result.get('scene', {}),
            'labels': parse_result.get('labels', {}),
            'parsed_at': parse_result.get('parsed_at'),
            'version': '1.0',
        }


# 全局Agent服务实例
agent_service = AgentParseService()
