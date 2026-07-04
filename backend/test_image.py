# -*- coding: utf-8 -*-
"""
图片管理接口测试脚本
测试图片列表、详情、审核、批量审核功能
"""

import requests
import json
import os
import sys
import time
import random
from pathlib import Path
from PIL import Image

# 配置
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "imagetestadmin"
TEST_PASSWORD = "test123456"


def create_test_image(filename: str, size: tuple = (100, 100)):
    """创建唯一的测试图片（随机像素内容）"""
    img = Image.new("RGB", size)
    pixels = img.load()
    for i in range(size[0]):
        for j in range(size[1]):
            pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img.save(filename)
    return filename


def get_auth_token():
    """获取认证Token"""
    # 先尝试注册
    requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "nickname": "Image Test Admin",
            "role": "admin"
        },
    )

    # 登录
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None


def upload_test_image(token: str, filename: str):
    """上传一张测试图片并返回image_id"""
    test_file = create_test_image(filename)

    with open(test_file, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (filename, f, "image/jpeg")},
        )

    os.remove(test_file)

    if response.status_code == 200:
        data = response.json()
        return data.get("image_id")
    return None


def test_image_list(token: str):
    """测试1: 图片列表查询"""
    print("\n=== Test 1: Image List Query ===")

    try:
        # Test basic list
        response = requests.get(
            f"{BASE_URL}/api/image/list",
            params={"page": 1, "page_size": 5},
            headers={"Authorization": f"Bearer {token}"},
        )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "total" in data, "Response should contain 'total'"
        assert "page" in data, "Response should contain 'page'"
        assert "page_size" in data, "Response should contain 'page_size'"
        assert "items" in data, "Response should contain 'items'"
        assert isinstance(data["items"], list), "Items should be a list"
        assert data["page"] == 1, f"Page should be 1, got {data['page']}"
        assert data["page_size"] == 5, f"Page size should be 5, got {data['page_size']}"
        assert data["total"] >= 0, "Total should be non-negative"

        print("PASS: Image list query works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_list_pagination(token: str):
    """测试2: 图片列表分页"""
    print("\n=== Test 2: Image List Pagination ===")

    try:
        # Get total count
        response1 = requests.get(
            f"{BASE_URL}/api/image/list",
            params={"page": 1, "page_size": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        data1 = response1.json()
        total = data1["total"]

        if total < 6:
            print("SKIP: Not enough images to test pagination")
            return True

        # Test page 2
        response2 = requests.get(
            f"{BASE_URL}/api/image/list",
            params={"page": 2, "page_size": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        data2 = response2.json()

        assert response2.status_code == 200, f"Expected 200, got {response2.status_code}"
        assert data2["page"] == 2, f"Page should be 2, got {data2['page']}"
        assert len(data2["items"]) <= 5, "Items per page should not exceed page_size"

        # Test page beyond total
        last_page = (total // 5) + 1
        response3 = requests.get(
            f"{BASE_URL}/api/image/list",
            params={"page": last_page + 1, "page_size": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        data3 = response3.json()
        assert len(data3["items"]) == 0, "Items should be empty for page beyond total"

        print("PASS: Image list pagination works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_list_filter(token: str):
    """测试3: 图片列表筛选"""
    print("\n=== Test 3: Image List Filtering ===")

    try:
        # Test status filter
        response = requests.get(
            f"{BASE_URL}/api/image/list",
            params={"page": 1, "page_size": 10, "status": "parsed"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # All returned items should have status "parsed"
        for item in data["items"]:
            assert item["status"] == "parsed", f"Item status should be 'parsed', got '{item['status']}'"

        # Test check_status filter
        response2 = requests.get(
            f"{BASE_URL}/api/image/list",
            params={"page": 1, "page_size": 10, "check_status": "pending"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data2 = response2.json()
        assert response2.status_code == 200, f"Expected 200, got {response2.status_code}"

        for item in data2["items"]:
            assert item["check_status"] == "pending", f"Item check_status should be 'pending', got '{item['check_status']}'"

        # Test keyword filter
        response3 = requests.get(
            f"{BASE_URL}/api/image/list",
            params={"page": 1, "page_size": 10, "keyword": "test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data3 = response3.json()
        assert response3.status_code == 200, f"Expected 200, got {response3.status_code}"

        print("PASS: Image list filtering works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_detail(token: str):
    """测试4: 图片详情获取"""
    print("\n=== Test 4: Image Detail ===")

    try:
        # First get a list to find an image ID
        list_response = requests.get(
            f"{BASE_URL}/api/image/list",
            params={"page": 1, "page_size": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        list_data = list_response.json()

        if not list_data["items"]:
            print("SKIP: No images available to test detail")
            return True

        image_id = list_data["items"][0]["id"]

        # Get detail
        response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data["id"] == image_id, f"ID should be {image_id}, got {data['id']}"
        assert "image_uuid" in data, "Response should contain 'image_uuid'"
        assert "original_filename" in data, "Response should contain 'original_filename'"
        assert "file_path" in data, "Response should contain 'file_path'"
        assert "file_size" in data, "Response should contain 'file_size'"
        assert "file_format" in data, "Response should contain 'file_format'"
        assert "status" in data, "Response should contain 'status'"
        assert "check_status" in data, "Response should contain 'check_status'"
        assert "metadata_json" in data, "Response should contain 'metadata_json'"
        assert "labels" in data, "Response should contain 'labels'"

        print("PASS: Image detail works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_detail_not_found(token: str):
    """测试5: 图片详情 - 不存在"""
    print("\n=== Test 5: Image Detail - Not Found ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/image/99999",
            headers={"Authorization": f"Bearer {token}"},
        )

        print(f"Status: {response.status_code}")
        data = response.json()

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        assert "detail" in data, "Response should contain 'detail'"

        print("PASS: Image detail not found works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_check(token: str):
    """测试6: 图片审核"""
    print("\n=== Test 6: Image Check ===")

    try:
        # Upload a new image to ensure we have a pending one
        image_id = upload_test_image(token, "test_check_img.jpg")
        if not image_id:
            print("SKIP: Could not upload test image")
            return True

        # Wait a moment for processing
        time.sleep(1)

        # Check the image
        response = requests.post(
            f"{BASE_URL}/api/image/check",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "image_id": image_id,
                "status": "checked",
                "comment": "Test review passed",
            },
        )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data["message"] == "审核成功", f"Message should be '审核成功', got '{data['message']}'"
        assert data["status"] == "checked", f"Status should be 'checked', got '{data['status']}'"

        # Verify the image status was updated
        detail_response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        detail_data = detail_response.json()
        assert detail_data["check_status"] == "checked", f"Check status should be 'checked', got '{detail_data['check_status']}'"

        print("PASS: Image check works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_check_discard(token: str):
    """测试7: 图片审核 - 废弃"""
    print("\n=== Test 7: Image Check - Discard ===")

    try:
        # Upload a new image
        image_id = upload_test_image(token, "test_discard_img.jpg")
        if not image_id:
            print("SKIP: Could not upload test image")
            return True

        time.sleep(1)

        # Discard the image
        response = requests.post(
            f"{BASE_URL}/api/image/check",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "image_id": image_id,
                "status": "discard",
                "comment": "Test discard",
            },
        )

        print(f"Status: {response.status_code}")
        data = response.json()

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data["message"] == "审核成功", f"Message should be '审核成功', got '{data['message']}'"
        assert data["status"] == "discard", f"Status should be 'discard', got '{data['status']}'"

        # Verify the image status was updated
        detail_response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        detail_data = detail_response.json()
        assert detail_data["check_status"] == "discard", f"Check status should be 'discard', got '{detail_data['check_status']}'"

        print("PASS: Image discard works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_check_already_checked(token: str):
    """测试8: 图片审核 - 重复审核"""
    print("\n=== Test 8: Image Check - Already Checked ===")

    try:
        # Upload and check an image
        image_id = upload_test_image(token, "test_recheck_img.jpg")
        if not image_id:
            print("SKIP: Could not upload test image")
            return True

        time.sleep(1)

        # First check
        response1 = requests.post(
            f"{BASE_URL}/api/image/check",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "image_id": image_id,
                "status": "checked",
            },
        )
        assert response1.status_code == 200, f"First check should succeed, got {response1.status_code}"

        # Second check (should fail)
        response2 = requests.post(
            f"{BASE_URL}/api/image/check",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "image_id": image_id,
                "status": "checked",
            },
        )

        print(f"Status: {response2.status_code}")
        data = response2.json()

        assert response2.status_code == 400, f"Expected 400, got {response2.status_code}"
        assert "已审核" in data["detail"], f"Error should mention already checked, got '{data['detail']}'"

        print("PASS: Image check already checked works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_check_invalid_status(token: str):
    """测试9: 图片审核 - 无效状态"""
    print("\n=== Test 9: Image Check - Invalid Status ===")

    try:
        response = requests.post(
            f"{BASE_URL}/api/image/check",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "image_id": 1,
                "status": "invalid_status",
            },
        )

        print(f"Status: {response.status_code}")
        data = response.json()

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "无效" in data["detail"], f"Error should mention invalid status, got '{data['detail']}'"

        print("PASS: Image check invalid status works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_image_check_not_found(token: str):
    """测试10: 图片审核 - 不存在"""
    print("\n=== Test 10: Image Check - Not Found ===")

    try:
        response = requests.post(
            f"{BASE_URL}/api/image/check",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "image_id": 99999,
                "status": "checked",
            },
        )

        print(f"Status: {response.status_code}")
        data = response.json()

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        assert "不存在" in data["detail"], f"Error should mention not found, got '{data['detail']}'"

        print("PASS: Image check not found works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_batch_check(token: str):
    """测试11: 批量审核"""
    print("\n=== Test 11: Batch Check ===")

    try:
        # Upload multiple images
        image_ids = []
        for i in range(3):
            img_id = upload_test_image(token, f"test_batch_check_{i}.jpg")
            if img_id:
                image_ids.append(img_id)
            time.sleep(0.5)

        if len(image_ids) < 2:
            print("SKIP: Could not upload enough test images")
            return True

        time.sleep(1)

        # Batch check
        response = requests.post(
            f"{BASE_URL}/api/image/batch-check",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "image_ids": image_ids,
                "status": "checked",
                "comment": "Batch review passed",
            },
        )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "total" in data, "Response should contain 'total'"
        assert "success" in data, "Response should contain 'success'"
        assert "failed" in data, "Response should contain 'failed'"
        assert data["total"] == len(image_ids), f"Total should be {len(image_ids)}, got {data['total']}"
        assert data["success"] == len(image_ids), f"Success should be {len(image_ids)}, got {data['success']}"
        assert data["failed"] == 0, f"Failed should be 0, got {data['failed']}"

        print("PASS: Batch check works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_stats_overview(token: str):
    """测试12: 统计概览"""
    print("\n=== Test 12: Stats Overview ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/image/stats/overview",
            headers={"Authorization": f"Bearer {token}"},
        )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "total" in data, "Response should contain 'total'"
        assert "status_stats" in data, "Response should contain 'status_stats'"
        assert "today_upload" in data, "Response should contain 'today_upload'"
        assert isinstance(data["status_stats"], dict), "status_stats should be a dict"

        print("PASS: Stats overview works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def test_unauthorized_access():
    """测试13: 未授权访问"""
    print("\n=== Test 13: Unauthorized Access ===")

    try:
        # No token
        response = requests.get(f"{BASE_URL}/api/image/list")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

        # Invalid token
        response2 = requests.get(
            f"{BASE_URL}/api/image/list",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response2.status_code == 401, f"Expected 401, got {response2.status_code}"

        print("PASS: Unauthorized access works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Image Management Test Suite")
    print("=" * 60)

    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("ERROR: Backend server is not healthy")
            sys.exit(1)
        print("Backend server is healthy")
    except requests.ConnectionError:
        print("ERROR: Cannot connect to backend server")
        sys.exit(1)

    # Get auth token
    token = get_auth_token()
    if not token:
        print("ERROR: Failed to get auth token")
        sys.exit(1)
    print(f"Auth token obtained: {token[:20]}...")

    # Run tests
    results = []
    results.append(("Image List Query", test_image_list(token)))
    results.append(("Image List Pagination", test_image_list_pagination(token)))
    results.append(("Image List Filtering", test_image_list_filter(token)))
    results.append(("Image Detail", test_image_detail(token)))
    results.append(("Image Detail Not Found", test_image_detail_not_found(token)))
    results.append(("Image Check", test_image_check(token)))
    results.append(("Image Check Discard", test_image_check_discard(token)))
    results.append(("Image Check Already Checked", test_image_check_already_checked(token)))
    results.append(("Image Check Invalid Status", test_image_check_invalid_status(token)))
    results.append(("Image Check Not Found", test_image_check_not_found(token)))
    results.append(("Batch Check", test_batch_check(token)))
    results.append(("Stats Overview", test_stats_overview(token)))
    results.append(("Unauthorized Access", test_unauthorized_access()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
