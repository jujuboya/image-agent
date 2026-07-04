# -*- coding: utf-8 -*-
"""
测试配置 - 提供测试固件和数据库设置
使用SQLite进行测试，确保测试独立且不依赖外部MySQL服务
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from main import app
from database import Base, get_db


# 测试数据库URL（SQLite，无需外部服务）
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 创建独立的测试引擎（不使用连接池设置，兼容SQLite）
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """覆盖数据库依赖，使用测试数据库会话"""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 覆盖应用的数据库依赖，使所有路由使用测试数据库
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_database():
    """每个测试前创建所有表，测试后清理（确保测试隔离）"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db():
    """获取测试数据库会话"""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    """获取异步HTTP测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
