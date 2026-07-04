# -*- coding: utf-8 -*-
"""
上传模块测试脚本
测试单张/批量图片上传、格式校验、MD5去重
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
TEST_USERNAME = "uploadtester"
TEST_PASSWORD = "test123"


def create_test_image(filename: str, size: tuple = (100, 100)):
    """创建唯一的测试图片（随机像素内容）"""
    # Generate random pixel data to ensure unique MD5
    img = Image.new("RGB", size)
    pixels = img.load()
    for i in range(size[0]):
        for j in range(size[1]):
            pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img.save(filename)
    return filename


def create_test_file(filename: str, content: str = "This is not an image"):
    """创建非图片测试文件"""
    with open(filename, "w") as f:
        f.write(content)
    return filename


def get_auth_token():
    """获取认证Token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None


def test_single_upload(token: str):
    """测试1: 单张图片上传"""
    print("\n=== Test 1: Single Image Upload ===")
    filename = create_test_image("test_single.jpg")

    try:
        with open(filename, "rb") as f:
            response = requests.post(
                f"{BASE_URL}/api/upload/image",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (filename, f, "image/jpeg")},
            )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "image_id" in data, "Response should contain image_id"
        assert "uuid" in data, "Response should contain uuid"
        assert data["filename"] == filename, f"Filename mismatch: {data['filename']} != {filename}"
        assert data["status"] == "parsing", f"Status should be 'parsing', got '{data['status']}'"
        assert "message" in data, "Response should contain message"

        print("PASS: Single image upload works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        os.remove(filename) if os.path.exists(filename) else None


def test_batch_upload(token: str):
    """测试2: 批量图片上传"""
    print("\n=== Test 2: Batch Image Upload ===")
    filenames = [
        create_test_image("test_batch1.jpg"),
        create_test_image("test_batch2.jpg"),
    ]

    try:
        files = []
        for fn in filenames:
            files.append(("files", (fn, open(fn, "rb"), "image/jpeg")))

        response = requests.post(
            f"{BASE_URL}/api/upload/batch",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        # Close file handles
        for _, (_, fh, _) in files:
            fh.close()

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data["total"] == 2, f"Total should be 2, got {data['total']}"
        assert data["success"] == 2, f"Success should be 2, got {data['success']}"
        assert data["failed"] == 0, f"Failed should be 0, got {data['failed']}"
        assert len(data["results"]) == 2, f"Results length should be 2, got {len(data['results'])}"

        for result in data["results"]:
            assert result["status"] == "parsing", f"Status should be 'parsing', got '{result['status']}'"

        print("PASS: Batch image upload works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        for fn in filenames:
            os.remove(fn) if os.path.exists(fn) else None


def test_format_validation(token: str):
    """测试3: 文件格式校验"""
    print("\n=== Test 3: File Format Validation ===")
    filename = create_test_file("test_invalid.txt")

    try:
        with open(filename, "rb") as f:
            response = requests.post(
                f"{BASE_URL}/api/upload/image",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (filename, f, "text/plain")},
            )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "detail" in data, "Response should contain detail"
        assert "不支持的文件格式" in data["detail"], f"Error message should mention unsupported format"

        print("PASS: File format validation works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        os.remove(filename) if os.path.exists(filename) else None


def test_md5_dedup(token: str):
    """测试4: MD5去重功能"""
    print("\n=== Test 4: MD5 Deduplication ===")

    # Create a unique image
    filename1 = create_test_image("test_dedup1.jpg")

    try:
        # Upload first image
        with open(filename1, "rb") as f:
            response1 = requests.post(
                f"{BASE_URL}/api/upload/image",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (filename1, f, "image/jpeg")},
            )

        print(f"First upload status: {response1.status_code}")
        assert response1.status_code == 200, f"First upload should succeed, got {response1.status_code}"

        # Copy the file to create a duplicate with same content
        filename2 = "test_dedup2.jpg"
        import shutil
        shutil.copy2(filename1, filename2)

        # Upload duplicate image
        with open(filename2, "rb") as f:
            response2 = requests.post(
                f"{BASE_URL}/api/upload/image",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (filename2, f, "image/jpeg")},
            )

        print(f"Duplicate upload status: {response2.status_code}")
        data = response2.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}"
        assert "图片已存在" in data["detail"], f"Error should mention image already exists"

        print("PASS: MD5 deduplication works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        os.remove(filename1) if os.path.exists(filename1) else None
        os.remove(filename2) if os.path.exists(filename2) else None


def test_batch_mixed_files(token: str):
    """测试5: 批量上传混合文件"""
    print("\n=== Test 5: Batch Upload with Mixed Files ===")
    valid_file = create_test_image("test_batch_valid.jpg")
    invalid_file = create_test_file("test_batch_invalid.txt")

    try:
        files = [
            ("files", (valid_file, open(valid_file, "rb"), "image/jpeg")),
            ("files", (invalid_file, open(invalid_file, "rb"), "text/plain")),
        ]

        response = requests.post(
            f"{BASE_URL}/api/upload/batch",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        # Close file handles
        for _, (_, fh, _) in files:
            fh.close()

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data["total"] == 2, f"Total should be 2, got {data['total']}"

        # Check that valid file succeeded and invalid file failed
        valid_results = [r for r in data["results"] if r["filename"] == valid_file]
        invalid_results = [r for r in data["results"] if r["filename"] == invalid_file]

        assert len(valid_results) == 1, "Should have one valid result"
        assert len(invalid_results) == 1, "Should have one invalid result"
        assert valid_results[0]["status"] == "parsing", "Valid file should have status 'parsing'"
        assert invalid_results[0]["status"] == "failed", "Invalid file should have status 'failed'"

        print("PASS: Batch upload with mixed files works correctly")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        os.remove(valid_file) if os.path.exists(valid_file) else None
        os.remove(invalid_file) if os.path.exists(invalid_file) else None


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Upload Module Test Suite")
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
    results.append(("Single Image Upload", test_single_upload(token)))
    results.append(("Batch Image Upload", test_batch_upload(token)))
    results.append(("File Format Validation", test_format_validation(token)))
    results.append(("MD5 Deduplication", test_md5_dedup(token)))
    results.append(("Batch Mixed Files", test_batch_mixed_files(token)))

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
