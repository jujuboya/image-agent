# -*- coding: utf-8 -*-
"""
认证模块单元测试
测试用户注册、登录和获取当前用户信息
"""

import pytest
from httpx import AsyncClient


async def test_register(client: AsyncClient):
    """测试用户注册"""
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "nickname": "测试用户"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["nickname"] == "测试用户"
    assert data["role"] == "viewer"


async def test_login(client: AsyncClient):
    """测试用户登录"""
    # 先注册
    await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "nickname": "测试用户"
        }
    )

    # 登录
    response = await client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_get_me(client: AsyncClient):
    """测试获取当前用户"""
    # 先注册
    await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "nickname": "测试用户"
        }
    )

    # 登录
    login_response = await client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]

    # 获取当前用户
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
