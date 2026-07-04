# -*- coding: utf-8 -*-
"""
图片数据集智能采集Agent系统 - 主入口
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db
from routers import upload, label, image, dataset, auth
from services.queue_service import QueueService
from services.cache_service import cache_service

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("正在启动图片数据集智能采集Agent系统...")

    # 创建必要的目录
    for dir_path in [
        settings.UPLOAD_DIR,
        settings.TEMP_DIR,
        settings.DATASET_DIR,
        settings.DISCARD_DIR,
        settings.EXPORT_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"目录已创建: {dir_path}")

    # 初始化数据库
    await init_db()
    logger.info("数据库初始化完成")

    # 初始化Redis缓存
    await cache_service.connect()
    if cache_service.redis:
        logger.info("Redis缓存初始化完成")
    else:
        logger.warning("Redis不可用，将以无缓存模式运行")

    # 初始化消息队列
    try:
        queue_service = QueueService()
        await queue_service.connect()
        app.state.queue_service = queue_service
        logger.info("消息队列连接成功")
    except Exception as e:
        logger.warning(f"消息队列连接失败: {e}，将使用本地任务队列")
        app.state.queue_service = None

    yield

    # 清理资源
    await cache_service.close()
    if app.state.queue_service:
        await app.state.queue_service.close()
    logger.info("系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="面向AI训练、科研场景的全自动结构化图片数据集采集Agent",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(upload.router, prefix="/api/upload", tags=["上传"])
app.include_router(label.router, prefix="/api/label", tags=["标签"])
app.include_router(image.router, prefix="/api/image", tags=["图片"])
app.include_router(dataset.router, prefix="/api/dataset", tags=["数据集"])


@app.get("/")
async def root():
    """系统状态检查"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
    )
