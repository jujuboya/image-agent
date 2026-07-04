# -*- coding: utf-8 -*-
"""
数据集导出测试脚本
测试CSV、JSON、YOLO格式导出功能
"""

import requests
import json
import os
import sys
import time
import random
import zipfile
import csv
import io
from pathlib import Path
from PIL import Image

# 配置
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "datasettestadmin"
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
            "nickname": "Dataset Test Admin",
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
    else:
        print(f"上传失败: {response.status_code} - {response.text}")
    return None


def wait_for_parsing(token: str, image_id: int, max_wait: int = 30):
    """等待图片解析完成"""
    for _ in range(max_wait):
        response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            data = response.json()
            if data["status"] in ["parsed", "checked"]:
                return True
        time.sleep(1)
    return False


def check_image(token: str, image_id: int):
    """审核图片"""
    response = requests.post(
        f"{BASE_URL}/api/image/check",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "image_id": image_id,
            "status": "checked",
            "comment": "Dataset export test",
        },
    )
    return response.status_code == 200


def update_label(token: str, image_id: int, labels: dict):
    """更新图片标签"""
    label_data = {"image_id": image_id, **labels}
    response = requests.put(
        f"{BASE_URL}/api/label/update",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=label_data,
    )
    return response.status_code == 200


def setup_test_data(token: str):
    """准备测试数据：上传图片、等待解析、审核、添加标签"""
    print("\n--- Setting up test data ---")
    image_ids = []

    # 上传3张测试图片
    for i in range(3):
        image_id = upload_test_image(token, f"test_export_{i}.jpg")
        if image_id:
            image_ids.append(image_id)
            print(f"  Uploaded image {i+1}: id={image_id}")

    if len(image_ids) < 2:
        print("ERROR: Could not upload enough test images")
        return []

    # 等待解析完成
    print("  Waiting for parsing...")
    parsed_ids = []
    for image_id in image_ids:
        if wait_for_parsing(token, image_id):
            parsed_ids.append(image_id)
            print(f"  Image {image_id} parsed")
        else:
            print(f"  Image {image_id} parsing timeout")

    if len(parsed_ids) < 2:
        print("ERROR: Not enough images parsed successfully")
        return []

    # 添加标签
    label_sets = [
        {"scene_type": "城区", "weather": "晴", "season": "夏", "light": "正常", "shoot_angle": "平视", "province": "北京市", "city": "北京市"},
        {"scene_type": "乡村", "weather": "多云", "season": "春", "light": "正常", "shoot_angle": "俯拍", "province": "河北省", "city": "保定市"},
        {"scene_type": "道路", "weather": "阴", "season": "秋", "light": "弱光", "shoot_angle": "平视", "province": "北京市", "city": "北京市"},
    ]

    for idx, image_id in enumerate(parsed_ids):
        labels = label_sets[idx % len(label_sets)]
        if update_label(token, image_id, labels):
            print(f"  Labels updated for image {image_id}: {labels['scene_type']}, {labels['weather']}")
        else:
            print(f"  WARNING: Failed to update labels for image {image_id}")

    # 审核图片
    checked_ids = []
    for image_id in parsed_ids:
        if check_image(token, image_id):
            checked_ids.append(image_id)
            print(f"  Image {image_id} checked (approved)")
        else:
            print(f"  WARNING: Failed to check image {image_id}")

    print(f"  Setup complete: {len(checked_ids)} images ready for export")
    return checked_ids


# ==================== 测试用例 ====================

def test_csv_export(token: str):
    """测试1: CSV导出"""
    print("\n=== Test 1: CSV Export ===")

    try:
        response = requests.post(
            f"{BASE_URL}/api/dataset/export",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"format": "csv"},
        )

        print(f"  Status: {response.status_code}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type", "").startswith("text/csv"), \
            f"Expected CSV content type, got {response.headers.get('content-type')}"

        # 验证Content-Disposition头
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp, f"Content-Disposition should contain 'attachment', got '{content_disp}'"
        assert ".csv" in content_disp, f"Content-Disposition should contain .csv, got '{content_disp}'"

        # 解析CSV内容
        csv_content = response.text
        assert len(csv_content) > 0, "CSV content should not be empty"

        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) >= 2, f"CSV should have at least header + 1 data row, got {len(rows)} rows"

        # 验证表头
        headers = rows[0]
        expected_headers = [
            "image_id", "filename", "width", "height",
            "year", "month", "day", "hour", "season", "time_period", "day_type",
            "weather", "temperature", "humidity", "light",
            "shoot_angle", "scene_scale", "clarity", "exposure",
            "scene_type", "device_type",
            "province", "city", "district", "address",
            "longitude", "latitude"
        ]
        for h in expected_headers:
            assert h in headers, f"CSV header should contain '{h}'"

        # 验证数据行有内容
        for row in rows[1:]:
            assert len(row) == len(headers), f"Data row should have same number of columns as header"
            assert row[0].isdigit(), f"image_id should be numeric, got '{row[0]}'"
            assert len(row[1]) > 0, f"filename should not be empty"

        # 保存CSV到文件
        output_path = "export.csv"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(csv_content)
        print(f"  CSV exported to: {output_path}")
        print(f"  Rows: {len(rows)} (1 header + {len(rows)-1} data)")
        print("  PASS: CSV export works correctly")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        return False


def test_json_export(token: str):
    """测试2: JSON导出"""
    print("\n=== Test 2: JSON Export ===")

    try:
        response = requests.post(
            f"{BASE_URL}/api/dataset/export",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"format": "json"},
        )

        print(f"  Status: {response.status_code}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type", "").startswith("application/json"), \
            f"Expected JSON content type, got {response.headers.get('content-type')}"

        # 验证Content-Disposition头
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp, f"Content-Disposition should contain 'attachment'"
        assert ".json" in content_disp, f"Content-Disposition should contain .json, got '{content_disp}'"

        # 解析JSON内容
        json_content = response.text
        assert len(json_content) > 0, "JSON content should not be empty"

        data = json.loads(json_content)
        assert isinstance(data, list), f"JSON should be an array, got {type(data)}"
        assert len(data) >= 1, f"JSON should have at least 1 item, got {len(data)}"

        # 验证每个item的结构
        for item in data:
            assert "image_id" in item, "Item should contain 'image_id'"
            assert "filename" in item, "Item should contain 'filename'"
            assert "width" in item, "Item should contain 'width'"
            assert "height" in item, "Item should contain 'height'"
            assert "labels" in item, "Item should contain 'labels'"
            assert isinstance(item["labels"], dict), "Labels should be a dict"

            # 验证labels子结构
            labels = item["labels"]
            assert "scene_type" in labels, "Labels should contain 'scene_type'"
            assert "weather" in labels, "Labels should contain 'weather'"
            assert "season" in labels, "Labels should contain 'season'"
            assert "location" in labels, "Labels should contain 'location'"
            assert isinstance(labels["location"], dict), "Location should be a dict"

        # 保存JSON到文件
        output_path = "export.json"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        print(f"  JSON exported to: {output_path}")
        print(f"  Items: {len(data)}")
        print("  PASS: JSON export works correctly")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"  FAIL: Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        return False


def test_yolo_export(token: str):
    """测试3: YOLO导出"""
    print("\n=== Test 3: YOLO Export ===")

    try:
        response = requests.post(
            f"{BASE_URL}/api/dataset/export",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"format": "yolo"},
        )

        print(f"  Status: {response.status_code}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type", "").startswith("application/zip"), \
            f"Expected ZIP content type, got {response.headers.get('content-type')}"

        # 验证Content-Disposition头
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp, f"Content-Disposition should contain 'attachment'"
        assert ".zip" in content_disp, f"Content-Disposition should contain .zip, got '{content_disp}'"

        # 保存ZIP到文件
        output_path = "export.zip"
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"  ZIP exported to: {output_path}")

        # 验证ZIP内容
        assert zipfile.is_zipfile(output_path), "Exported file should be a valid ZIP"

        with zipfile.ZipFile(output_path, 'r') as zf:
            names = zf.namelist()
            print(f"  ZIP entries: {len(names)}")

            # 验证YOLO目录结构
            has_images_train = any("images/train" in n for n in names)
            has_labels_train = any("labels/train" in n for n in names)
            has_classes = any("classes.txt" in n for n in names)
            has_yaml = any("data.yaml" in n for n in names)

            assert has_images_train, "ZIP should contain images/train directory"
            assert has_labels_train, "ZIP should contain labels/train directory"
            assert has_classes, "ZIP should contain classes.txt"
            assert has_yaml, "ZIP should contain data.yaml"

            # 验证data.yaml内容
            yaml_file = [n for n in names if n.endswith("data.yaml")][0]
            yaml_content = zf.read(yaml_file).decode("utf-8")
            assert "train:" in yaml_content, "data.yaml should contain 'train:'"
            assert "val:" in yaml_content, "data.yaml should contain 'val:'"
            assert "nc:" in yaml_content, "data.yaml should contain 'nc:'"
            assert "names:" in yaml_content, "data.yaml should contain 'names:'"

            # 验证classes.txt内容
            classes_file = [n for n in names if n.endswith("classes.txt")][0]
            classes_content = zf.read(classes_file).decode("utf-8")
            assert len(classes_content.strip()) > 0, "classes.txt should not be empty"

            # 验证标签文件格式
            label_files = [n for n in names if n.endswith(".txt") and "labels/" in n and "classes" not in n]
            for lf in label_files:
                label_content = zf.read(lf).decode("utf-8").strip()
                if label_content:  # 非空标签文件
                    parts = label_content.split()
                    assert len(parts) >= 5, f"YOLO label should have at least 5 values (class cx cy w h), got: {label_content}"

        print("  PASS: YOLO export works correctly")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except zipfile.BadZipFile as e:
        print(f"  FAIL: Invalid ZIP file: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        return False


def test_export_with_filters(token: str):
    """测试4: 带筛选条件导出"""
    print("\n=== Test 4: Export with Filters ===")

    try:
        # 测试带天气筛选的CSV导出
        response = requests.post(
            f"{BASE_URL}/api/dataset/export",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "format": "csv",
                "filters": {"weather": "晴"}
            },
        )

        print(f"  Status (weather filter): {response.status_code}")

        if response.status_code == 200:
            csv_content = response.text
            reader = csv.reader(io.StringIO(csv_content))
            rows = list(reader)
            print(f"  Filtered CSV rows: {len(rows)} (header + {len(rows)-1} data)")

            # 验证筛选结果
            if len(rows) > 1:
                weather_idx = rows[0].index("weather")
                for row in rows[1:]:
                    assert row[weather_idx] == "晴", \
                        f"Filtered results should only contain '晴' weather, got '{row[weather_idx]}'"
                print("  Filter verification passed")
            else:
                print("  No results for this filter (expected if no matching data)")
        elif response.status_code == 400:
            # 没有符合条件的图片也是可接受的
            data = response.json()
            print(f"  Filter returned 400: {data.get('detail', '')}")
            assert "没有符合条件" in data.get("detail", ""), "400 should indicate no matching data"
        else:
            raise AssertionError(f"Expected 200 or 400, got {response.status_code}")

        # 测试带场景类型筛选的JSON导出
        response2 = requests.post(
            f"{BASE_URL}/api/dataset/export",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "format": "json",
                "filters": {"scene_type": "城区"}
            },
        )

        print(f"  Status (scene_type filter): {response2.status_code}")

        if response2.status_code == 200:
            json_data = json.loads(response2.text)
            print(f"  Filtered JSON items: {len(json_data)}")

            # 验证筛选结果
            if len(json_data) > 0:
                for item in json_data:
                    assert item["labels"]["scene_type"] == "城区", \
                        f"Filtered results should only contain '城区' scene type, got '{item['labels']['scene_type']}'"
                print("  Scene type filter verification passed")
        elif response2.status_code == 400:
            data2 = response2.json()
            print(f"  Filter returned 400: {data2.get('detail', '')}")
            assert "没有符合条件" in data2.get("detail", ""), "400 should indicate no matching data"
        else:
            raise AssertionError(f"Expected 200 or 400, got {response2.status_code}")

        print("  PASS: Export with filters works correctly")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        return False


def test_unsupported_format(token: str):
    """测试5: 不支持的导出格式"""
    print("\n=== Test 5: Unsupported Format ===")

    try:
        response = requests.post(
            f"{BASE_URL}/api/dataset/export",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"format": "unsupported_format"},
        )

        print(f"  Status: {response.status_code}")

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "不支持" in data["detail"], f"Error should mention unsupported format, got '{data['detail']}'"

        print("  PASS: Unsupported format rejection works correctly")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        return False


def test_export_unauthorized():
    """测试6: 未授权访问"""
    print("\n=== Test 6: Unauthorized Export ===")

    try:
        # No token
        response = requests.post(
            f"{BASE_URL}/api/dataset/export",
            json={"format": "csv"},
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

        # Invalid token
        response2 = requests.post(
            f"{BASE_URL}/api/dataset/export",
            headers={"Authorization": "Bearer invalid_token"},
            json={"format": "csv"},
        )
        assert response2.status_code == 401, f"Expected 401, got {response2.status_code}"

        print("  PASS: Unauthorized access rejection works correctly")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        return False


def test_dataset_stats(token: str):
    """测试7: 数据集统计信息"""
    print("\n=== Test 7: Dataset Stats ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/dataset/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        print(f"  Status: {response.status_code}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "total_images" in data, "Response should contain 'total_images'"
        assert "scene_distribution" in data, "Response should contain 'scene_distribution'"
        assert "weather_distribution" in data, "Response should contain 'weather_distribution'"
        assert "season_distribution" in data, "Response should contain 'season_distribution'"

        assert isinstance(data["total_images"], int), "total_images should be an integer"
        assert isinstance(data["scene_distribution"], dict), "scene_distribution should be a dict"
        assert isinstance(data["weather_distribution"], dict), "weather_distribution should be a dict"
        assert isinstance(data["season_distribution"], dict), "season_distribution should be a dict"

        print(f"  Total images: {data['total_images']}")
        print(f"  Scene types: {list(data['scene_distribution'].keys())}")
        print(f"  Weather types: {list(data['weather_distribution'].keys())}")

        print("  PASS: Dataset stats works correctly")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        return False


def test_version_list(token: str):
    """测试8: 版本列表"""
    print("\n=== Test 8: Version List ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/dataset/versions",
            headers={"Authorization": f"Bearer {token}"},
        )

        print(f"  Status: {response.status_code}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert isinstance(data, list), "Response should be a list"

        print(f"  Versions: {len(data)}")

        print("  PASS: Version list works correctly")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Dataset Export Test Suite")
    print("=" * 60)

    # 检查服务器健康状态
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("ERROR: Backend server is not healthy")
            sys.exit(1)
        print("Backend server is healthy")
    except requests.ConnectionError:
        print("ERROR: Cannot connect to backend server")
        sys.exit(1)

    # 获取认证Token
    token = get_auth_token()
    if not token:
        print("ERROR: Failed to get auth token")
        sys.exit(1)
    print(f"Auth token obtained: {token[:20]}...")

    # 准备测试数据
    checked_ids = setup_test_data(token)

    # 运行测试
    results = []
    results.append(("CSV Export", test_csv_export(token)))
    results.append(("JSON Export", test_json_export(token)))
    results.append(("YOLO Export", test_yolo_export(token)))
    results.append(("Export with Filters", test_export_with_filters(token)))
    results.append(("Unsupported Format", test_unsupported_format(token)))
    results.append(("Unauthorized Export", test_export_unauthorized()))
    results.append(("Dataset Stats", test_dataset_stats(token)))
    results.append(("Version List", test_version_list(token)))

    # 汇总
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
