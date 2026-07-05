# -*- coding: utf-8 -*-
"""
数据库配置和模型定义
"""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, JSON,
    ForeignKey, Enum, Boolean, Index, BigInteger
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

from config import settings

import logging

logger = logging.getLogger(__name__)


# 创建异步引擎
def _engine_kwargs(database_url: str) -> dict:
    kwargs = {"echo": settings.DEBUG}
    if not database_url.startswith("sqlite"):
        kwargs.update(
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=False,  # Disabled due to aiomysql 0.2.0 compatibility issue
        )
    return kwargs


engine = create_async_engine(
    settings.get_database_url,
    **_engine_kwargs(settings.get_database_url),
)

# 创建异步会话工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")


# ==================== 用户表 ====================
class SysUser(Base):
    """用户表"""
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    nickname = Column(String(50), comment="昵称")
    email = Column(String(100), comment="邮箱")
    phone = Column(String(20), comment="手机号")
    avatar = Column(String(255), comment="头像URL")
    role = Column(
        Enum("admin", "editor", "viewer", name="user_role"),
        default="viewer",
        comment="角色"
    )
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    last_login = Column(DateTime, comment="最后登录时间")

    # 关系
    images = relationship("DatasetImage", foreign_keys="DatasetImage.uploader_id", back_populates="uploader")
    labels = relationship("DatasetLabel", back_populates="creator")

    __table_args__ = (
        Index("idx_user_role", "role"),
        {"comment": "用户表"}
    )


# ==================== 图片主表 ====================
class DatasetImage(Base):
    """图片主表"""
    __tablename__ = "dataset_image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_uuid = Column(String(36), unique=True, nullable=False, index=True, comment="图片UUID")
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    stored_filename = Column(String(255), nullable=False, comment="存储文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    file_md5 = Column(String(32), nullable=False, index=True, comment="文件MD5")
    file_format = Column(String(10), nullable=False, comment="文件格式")
    width = Column(Integer, comment="图片宽度")
    height = Column(Integer, comment="图片高度")

    # 状态
    status = Column(
        Enum("uploading", "parsing", "parsed", "labeling", "labeled",
             "checking", "checked", "discarded", name="image_status"),
        default="uploading",
        comment="状态"
    )
    check_status = Column(
        Enum("pending", "checked", "discard", name="check_status"),
        default="pending",
        comment="审核状态"
    )

    # 元数据
    metadata_json = Column(JSON, comment="完整元数据JSON")
    dataset_path = Column(String(500), comment="数据集归档路径")

    # 外键
    uploader_id = Column(Integer, ForeignKey("sys_user.id"), comment="上传者ID")
    checker_id = Column(Integer, ForeignKey("sys_user.id"), comment="审核者ID")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    parsed_at = Column(DateTime, comment="解析完成时间")
    checked_at = Column(DateTime, comment="审核时间")

    # 关系
    uploader = relationship("SysUser", foreign_keys=[uploader_id], back_populates="images")
    checker = relationship("SysUser", foreign_keys=[checker_id])
    labels = relationship("DatasetLabel", back_populates="image", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_image_status", "status"),
        Index("idx_image_check_status", "check_status"),
        Index("idx_image_created", "created_at"),
        Index("idx_image_uploader", "uploader_id"),
        {"comment": "图片主表"}
    )


# ==================== 图片标签表 ====================
class DatasetLabel(Base):
    """图片标签表"""
    __tablename__ = "dataset_label"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey("dataset_image.id", ondelete="CASCADE"), unique=True, nullable=False, comment="图片ID")

    # 时间维度
    year = Column(Integer, comment="年")
    month = Column(Integer, comment="月")
    day = Column(Integer, comment="日")
    hour = Column(Integer, comment="小时")
    season = Column(
        Enum("春", "夏", "秋", "冬", name="season"),
        comment="季节"
    )
    time_period = Column(
        Enum("凌晨", "上午", "中午", "下午", "傍晚", "夜晚", name="time_period"),
        comment="时段"
    )
    day_type = Column(
        Enum("工作日", "节假日", name="day_type"),
        comment="工作日/节假日"
    )

    # 环境天气
    weather = Column(
        Enum("晴", "多云", "阴", "小雨", "大雨", "雾", "雪", "沙尘", name="weather"),
        comment="天气"
    )
    temperature = Column(Float, comment="温度(℃)")
    humidity = Column(Float, comment="湿度(%)")
    light = Column(
        Enum("强光", "正常", "弱光", "逆光", name="light"),
        comment="光照"
    )

    # 拍摄维度
    shoot_angle = Column(
        Enum("俯拍", "平视", "仰拍", name="shoot_angle"),
        comment="拍摄角度"
    )
    scene_scale = Column(
        Enum("远景", "中景", "近景", "特写", name="scene_scale"),
        comment="画面景别"
    )
    clarity = Column(
        Enum("清晰", "轻微模糊", "严重模糊", name="clarity"),
        comment="清晰度"
    )
    exposure = Column(
        Enum("正常", "过曝", "欠曝", name="exposure"),
        comment="曝光"
    )

    # 场景设备
    scene_type = Column(
        Enum("城区", "乡村", "道路", "厂区", "田野", "室内",
             "山区", "水域", "森林", "沙漠", "雪地", "其他", name="scene_type"),
        comment="场景类型"
    )
    device_type = Column(
        Enum("手机", "工业相机", "单反", "无人机", "监控", "其他", name="device_type"),
        comment="设备类型"
    )
    device_brand = Column(String(50), comment="设备品牌")
    device_model = Column(String(100), comment="设备型号")

    # 地理位置
    longitude = Column(Float, comment="经度")
    latitude = Column(Float, comment="纬度")
    province = Column(String(50), comment="省")
    city = Column(String(50), comment="市")
    district = Column(String(50), comment="区")
    address = Column(String(255), comment="详细地址")

    # AI识别结果
    ai_scene_labels = Column(JSON, comment="AI场景识别标签")
    ai_objects = Column(JSON, comment="AI物体识别结果")
    ai_quality_score = Column(Float, comment="AI画质评分")

    # 标签来源
    source = Column(
        Enum("auto", "manual", "mixed", name="label_source"),
        default="auto",
        comment="标签来源"
    )
    creator_id = Column(Integer, ForeignKey("sys_user.id"), comment="创建/修改者ID")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系
    image = relationship("DatasetImage", back_populates="labels")
    creator = relationship("SysUser", back_populates="labels")

    __table_args__ = (
        Index("idx_label_season", "season"),
        Index("idx_label_weather", "weather"),
        Index("idx_label_scene", "scene_type"),
        Index("idx_label_location", "province", "city"),
        {"comment": "图片标签表"}
    )


# ==================== 数据集版本表 ====================
class DatasetVersion(Base):
    """数据集版本表"""
    __tablename__ = "dataset_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_name = Column(String(50), nullable=False, comment="版本名称")
    version_code = Column(String(20), nullable=False, unique=True, comment="版本号")
    description = Column(Text, comment="版本描述")

    # 统计信息
    total_images = Column(Integer, default=0, comment="总图片数")
    total_labels = Column(Integer, default=0, comment="总标签数")
    label_distribution = Column(JSON, comment="标签分布统计")

    # 筛选条件
    filter_conditions = Column(JSON, comment="筛选条件")

    # 导出信息
    export_format = Column(
        Enum("yolo", "coco", "voc", "json", "csv", name="export_format"),
        comment="导出格式"
    )
    export_path = Column(String(500), comment="导出文件路径")
    export_size = Column(BigInteger, comment="导出文件大小")

    # 状态
    status = Column(
        Enum("creating", "ready", "exported", "archived", name="version_status"),
        default="creating",
        comment="状态"
    )

    # 外键
    creator_id = Column(Integer, ForeignKey("sys_user.id"), comment="创建者ID")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系
    creator = relationship("SysUser")

    __table_args__ = (
        Index("idx_version_status", "status"),
        Index("idx_version_created", "created_at"),
        {"comment": "数据集版本表"}
    )


# ==================== 操作日志表 ====================
class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"), comment="操作者ID")
    action = Column(String(50), nullable=False, comment="操作类型")
    target_type = Column(String(50), comment="目标类型")
    target_id = Column(Integer, comment="目标ID")
    detail = Column(JSON, comment="操作详情")
    ip_address = Column(String(50), comment="IP地址")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关系
    user = relationship("SysUser")

    __table_args__ = (
        Index("idx_log_action", "action"),
        Index("idx_log_created", "created_at"),
        {"comment": "操作日志表"}
    )
