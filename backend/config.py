# -*- coding: utf-8 -*-
"""
核心配置文件
图片数据集智能采集Agent系统
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """系统配置"""

    # 应用配置
    APP_NAME: str = "图片数据集智能采集Agent系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "image_dataset"
    DATABASE_URL: Optional[str] = None

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def get_redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # RabbitMQ配置
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"

    @property
    def get_rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        )

    # MinIO对象存储配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "image-dataset"
    MINIO_SECURE: bool = False

    # 文件存储路径
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    TEMP_DIR: Path = UPLOAD_DIR / "temp"
    DATASET_DIR: Path = UPLOAD_DIR / "dataset"
    DISCARD_DIR: Path = UPLOAD_DIR / "discard"
    EXPORT_DIR: Path = UPLOAD_DIR / "export"

    # 文件上传限制
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    BATCH_UPLOAD_LIMIT: int = 1000  # 单次批量上传最大数量

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 天气API配置（可选）
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_API_URL: str = "https://api.weatherapi.com/v1/history.json"

    # AI模型配置
    SCENE_MODEL_PATH: Optional[str] = None  # 场景识别模型路径
    QUALITY_MODEL_PATH: Optional[str] = None  # 画质检测模型路径

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()


# 标签枚举定义
class LabelEnums:
    """标准化标签枚举"""

    # 季节
    SEASONS = ["春", "夏", "秋", "冬"]

    # 时段
    TIME_PERIODS = ["凌晨", "上午", "中午", "下午", "傍晚", "夜晚"]

    # 工作日/节假日
    DAY_TYPES = ["工作日", "节假日"]

    # 天气类型
    WEATHER_TYPES = ["晴", "多云", "阴", "小雨", "大雨", "雾", "雪", "沙尘"]

    # 光照条件
    LIGHT_CONDITIONS = ["强光", "正常", "弱光", "逆光"]

    # 拍摄角度
    SHOOT_ANGLES = ["俯拍", "平视", "仰拍"]

    # 画面景别
    SCENE_SCALES = ["远景", "中景", "近景", "特写"]

    # 清晰度
    CLARITY_LEVELS = ["清晰", "轻微模糊", "严重模糊"]

    # 曝光
    EXPOSURE_LEVELS = ["正常", "过曝", "欠曝"]

    # 场景类型
    SCENE_TYPES = [
        "城区", "乡村", "道路", "厂区", "田野", "室内",
        "山区", "水域", "森林", "沙漠", "雪地", "其他"
    ]

    # 拍摄设备
    DEVICE_TYPES = ["手机", "工业相机", "单反", "无人机", "监控", "其他"]

    # 审核状态
    CHECK_STATUS = {
        "pending": "待校验",
        "checked": "已通过",
        "discard": "已废弃"
    }

    # 图片状态
    IMAGE_STATUS = {
        "uploading": "上传中",
        "parsing": "解析中",
        "parsed": "已解析",
        "labeling": "标注中",
        "labeled": "已标注",
        "checking": "审核中",
        "checked": "已通过",
        "discarded": "已废弃"
    }


# 目录生成规则
def generate_dataset_path(labels: dict) -> str:
    """
    根据标签生成数据集目录路径
    格式: /年/月/季节_时段/天气/场景/
    """
    year = labels.get("year", "unknown")
    month = labels.get("month", "unknown")
    season = labels.get("season", "unknown")
    time_period = labels.get("time_period", "unknown")
    weather = labels.get("weather", "unknown")
    scene = labels.get("scene_type", "other")

    return f"{year}/{month}/{season}_{time_period}/{weather}/{scene}"
