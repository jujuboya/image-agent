# -*- coding: utf-8 -*-
"""
服务层单元测试
测试图片服务和导出服务
"""

import asyncio
import csv
import io
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# 测试图片服务
def test_image_service_import():
    """测试1: 图片服务导入"""
    print("\n=== Test 1: Image Service Import ===")
    try:
        from services.image_service import image_service, ImageService
        assert image_service is not None, "image_service should not be None"
        assert isinstance(image_service, ImageService), "image_service should be an instance of ImageService"
        assert hasattr(image_service, 'get_image_list'), "ImageService should have get_image_list method"
        assert hasattr(image_service, 'get_image_detail'), "ImageService should have get_image_detail method"
        print("PASS: Image service imports correctly")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_export_service_import():
    """测试2: 导出服务导入"""
    print("\n=== Test 2: Export Service Import ===")
    try:
        from services.export_service import export_service, ExportService
        assert export_service is not None, "export_service should not be None"
        assert isinstance(export_service, ExportService), "export_service should be an instance of ExportService"
        assert hasattr(export_service, 'export_csv'), "ExportService should have export_csv method"
        print("PASS: Export service imports correctly")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_export_csv_basic():
    """测试3: CSV导出基本功能"""
    print("\n=== Test 3: CSV Export Basic ===")
    try:
        from services.export_service import export_service

        # 创建模拟图片对象
        mock_label = MagicMock()
        mock_label.year = 2024
        mock_label.month = 6
        mock_label.day = 15
        mock_label.hour = 14
        mock_label.season = "夏"
        mock_label.time_period = "下午"
        mock_label.day_type = "工作日"
        mock_label.weather = "晴"
        mock_label.temperature = 28.5
        mock_label.humidity = 65.0
        mock_label.light = "正常"
        mock_label.shoot_angle = "平视"
        mock_label.scene_scale = "中景"
        mock_label.clarity = "清晰"
        mock_label.exposure = "正常"
        mock_label.scene_type = "城区"
        mock_label.device_type = "手机"
        mock_label.province = "北京市"
        mock_label.city = "北京市"
        mock_label.district = "海淀区"
        mock_label.address = "中关村大街1号"
        mock_label.longitude = 116.3
        mock_label.latitude = 39.9

        mock_image = MagicMock()
        mock_image.id = 1
        mock_image.original_filename = "test.jpg"
        mock_image.width = 1920
        mock_image.height = 1080
        mock_image.labels = mock_label

        # 执行导出
        csv_content = export_service.export_csv([mock_image], "test_version")

        # 验证CSV内容
        assert len(csv_content) > 0, "CSV content should not be empty"

        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 2, f"CSV should have 2 rows (header + 1 data), got {len(rows)}"

        # 验证表头
        headers = rows[0]
        assert "image_id" in headers, "Headers should contain 'image_id'"
        assert "filename" in headers, "Headers should contain 'filename'"
        assert "scene_type" in headers, "Headers should contain 'scene_type'"
        assert "weather" in headers, "Headers should contain 'weather'"
        assert "longitude" in headers, "Headers should contain 'longitude'"
        assert "latitude" in headers, "Headers should contain 'latitude'"

        # 验证数据
        data_row = rows[1]
        assert data_row[0] == "1", f"image_id should be '1', got '{data_row[0]}'"
        assert data_row[1] == "test.jpg", f"filename should be 'test.jpg', got '{data_row[1]}'"
        assert data_row[2] == "1920", f"width should be '1920', got '{data_row[2]}'"
        assert data_row[3] == "1080", f"height should be '1080', got '{data_row[3]}'"

        print("PASS: CSV export works correctly")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_export_csv_no_labels():
    """测试4: CSV导出 - 无标签"""
    print("\n=== Test 4: CSV Export No Labels ===")
    try:
        from services.export_service import export_service

        # 创建无标签的模拟图片对象
        mock_image = MagicMock()
        mock_image.id = 2
        mock_image.original_filename = "no_label.jpg"
        mock_image.width = 800
        mock_image.height = 600
        mock_image.labels = None

        # 执行导出
        csv_content = export_service.export_csv([mock_image], "test_version")

        # 验证CSV内容
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 2, f"CSV should have 2 rows, got {len(rows)}"

        # 验证数据行的标签字段都是空的
        data_row = rows[1]
        assert data_row[0] == "2", f"image_id should be '2', got '{data_row[0]}'"
        assert data_row[1] == "no_label.jpg", f"filename should be 'no_label.jpg', got '{data_row[1]}'"
        # 标签字段应该是空字符串（None被写为空）
        assert data_row[4] == "", f"year should be empty, got '{data_row[4]}'"

        print("PASS: CSV export with no labels works correctly")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_export_csv_multiple_images():
    """测试5: CSV导出 - 多张图片"""
    print("\n=== Test 5: CSV Export Multiple Images ===")
    try:
        from services.export_service import export_service

        # 创建多张模拟图片
        images = []
        for i in range(3):
            mock_image = MagicMock()
            mock_image.id = i + 1
            mock_image.original_filename = f"image_{i+1}.jpg"
            mock_image.width = 100 * (i + 1)
            mock_image.height = 100 * (i + 1)
            mock_image.labels = None
            images.append(mock_image)

        # 执行导出
        csv_content = export_service.export_csv(images, "test_version")

        # 验证CSV内容
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 4, f"CSV should have 4 rows (header + 3 data), got {len(rows)}"

        # 验证每行数据
        for i in range(3):
            data_row = rows[i + 1]
            assert data_row[0] == str(i + 1), f"Row {i+1} image_id should be '{i+1}', got '{data_row[0]}'"
            assert data_row[1] == f"image_{i+1}.jpg", f"Row {i+1} filename should be 'image_{i+1}.jpg', got '{data_row[1]}'"

        print("PASS: CSV export with multiple images works correctly")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_image_service_has_async_methods():
    """测试6: 图片服务方法签名"""
    print("\n=== Test 6: Image Service Method Signatures ===")
    try:
        from services.image_service import ImageService
        import inspect

        # 检查方法是否是异步的
        assert inspect.iscoroutinefunction(ImageService.get_image_list), "get_image_list should be async"
        assert inspect.iscoroutinefunction(ImageService.get_image_detail), "get_image_detail should be async"

        # 检查方法签名
        sig_list = inspect.signature(ImageService.get_image_list)
        params_list = list(sig_list.parameters.keys())
        assert 'db' in params_list, "get_image_list should have 'db' parameter"
        assert 'page' in params_list, "get_image_list should have 'page' parameter"
        assert 'page_size' in params_list, "get_image_list should have 'page_size' parameter"
        assert 'status' in params_list, "get_image_list should have 'status' parameter"
        assert 'check_status' in params_list, "get_image_list should have 'check_status' parameter"
        assert 'keyword' in params_list, "get_image_list should have 'keyword' parameter"

        sig_detail = inspect.signature(ImageService.get_image_detail)
        params_detail = list(sig_detail.parameters.keys())
        assert 'db' in params_detail, "get_image_detail should have 'db' parameter"
        assert 'image_id' in params_detail, "get_image_detail should have 'image_id' parameter"

        print("PASS: Image service method signatures are correct")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_csv_headers_match_original():
    """测试7: CSV表头与原始实现匹配"""
    print("\n=== Test 7: CSV Headers Match Original ===")
    try:
        from services.export_service import export_service

        # 创建一个完整的模拟图片
        mock_label = MagicMock()
        mock_label.year = None
        mock_label.month = None
        mock_label.day = None
        mock_label.hour = None
        mock_label.season = None
        mock_label.time_period = None
        mock_label.day_type = None
        mock_label.weather = None
        mock_label.temperature = None
        mock_label.humidity = None
        mock_label.light = None
        mock_label.shoot_angle = None
        mock_label.scene_scale = None
        mock_label.clarity = None
        mock_label.exposure = None
        mock_label.scene_type = None
        mock_label.device_type = None
        mock_label.province = None
        mock_label.city = None
        mock_label.district = None
        mock_label.address = None
        mock_label.longitude = None
        mock_label.latitude = None

        mock_image = MagicMock()
        mock_image.id = 1
        mock_image.original_filename = "test.jpg"
        mock_image.width = 100
        mock_image.height = 100
        mock_image.labels = mock_label

        # 执行导出
        csv_content = export_service.export_csv([mock_image], "test")

        # 验证表头包含所有预期字段
        expected_headers = [
            "image_id", "filename", "width", "height",
            "year", "month", "day", "hour", "season", "time_period", "day_type",
            "weather", "temperature", "humidity", "light",
            "shoot_angle", "scene_scale", "clarity", "exposure",
            "scene_type", "device_type",
            "province", "city", "district", "address",
            "longitude", "latitude",
        ]

        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        actual_headers = rows[0]

        for header in expected_headers:
            assert header in actual_headers, f"CSV header should contain '{header}'"

        assert len(actual_headers) == len(expected_headers), \
            f"CSV should have {len(expected_headers)} columns, got {len(actual_headers)}"

        print("PASS: CSV headers match expected format")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Service Layer Unit Tests")
    print("=" * 60)

    results = []
    results.append(("Image Service Import", test_image_service_import()))
    results.append(("Export Service Import", test_export_service_import()))
    results.append(("CSV Export Basic", test_export_csv_basic()))
    results.append(("CSV Export No Labels", test_export_csv_no_labels()))
    results.append(("CSV Export Multiple Images", test_export_csv_multiple_images()))
    results.append(("Image Service Method Signatures", test_image_service_has_async_methods()))
    results.append(("CSV Headers Match Original", test_csv_headers_match_original()))

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
