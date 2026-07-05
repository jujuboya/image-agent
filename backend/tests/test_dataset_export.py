# -*- coding: utf-8 -*-
"""Dataset export behavior tests."""

from datetime import datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database import DatasetImage, DatasetLabel


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/auth/register",
        json={
            "username": "exporter",
            "password": "testpass123",
            "nickname": "Exporter",
        },
    )
    response = await client.post(
        "/api/auth/login",
        data={
            "username": "exporter",
            "password": "testpass123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_checked_image(db: AsyncSession) -> None:
    image = DatasetImage(
        image_uuid="export-test-image",
        original_filename="sample.jpg",
        stored_filename="sample.jpg",
        file_path="missing/sample.jpg",
        file_size=1024,
        file_md5="0" * 32,
        file_format=".jpg",
        width=640,
        height=480,
        status="checked",
        check_status="checked",
        checked_at=datetime.now(),
    )
    db.add(image)
    await db.flush()
    db.add(
        DatasetLabel(
            image_id=image.id,
            season="秋",
            weather="晴",
            scene_type="室内",
        )
    )
    await db.commit()


async def test_json_export_creates_version_record(client: AsyncClient, db: AsyncSession):
    headers = await _auth_headers(client)
    await _create_checked_image(db)

    response = await client.post(
        "/api/dataset/export",
        headers=headers,
        json={
            "format": "json",
            "version_name": "review-export",
            "filters": {"scene_type": "室内"},
        },
    )

    assert response.status_code == 200

    versions_response = await client.get("/api/dataset/versions", headers=headers)
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert len(versions) == 1
    assert versions[0]["version_name"] == "review-export"
    assert versions[0]["export_format"] == "json"
    assert versions[0]["total_images"] == 1
    assert versions[0]["status"] == "ready"
