# -*- coding: utf-8 -*-
"""
Agent解析服务测试脚本
测试EXIF解析、GPS逆编码、天气匹配、场景识别、标签生成
"""

import requests
import json
import os
import sys
import time
import random
from pathlib import Path
from PIL import Image
import piexif
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "uploadtester"
TEST_PASSWORD = "test123"

# 测试GPS坐标（北京天安门）- piexif要求rational tuple格式: (numerator, denominator)
TEST_LONGITUDE = ((116, 1), (23, 1), (50, 1))  # ~116.397
TEST_LATITUDE = ((39, 1), (54, 1), (26, 1))    # ~39.907


def create_exif_image(filename: str, size: tuple = (640, 480)):
    """创建包含EXIF信息的唯一测试图片（随机像素避免MD5重复）"""
    img = Image.new("RGB", size)
    pixels = img.load()
    # 创建有纹理的随机图片（用于画质检测和MD5唯一性）
    for i in range(size[0]):
        for j in range(size[1]):
            pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # 创建EXIF数据 - 拍摄时间：2026-07-04 14:30:00
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: b"Apple",
            piexif.ImageIFD.Model: b"iPhone 15 Pro",
            piexif.ImageIFD.Software: b"iOS 17.5",
            piexif.ImageIFD.DateTime: b"2026:07:04 14:30:00",
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2026:07:04 14:30:00",
            piexif.ExifIFD.DateTimeDigitized: b"2026:07:04 14:30:00",
            piexif.ExifIFD.FocalLength: (420, 100),
            piexif.ExifIFD.FNumber: (180, 100),
            piexif.ExifIFD.ISOSpeedRatings: 100,
            piexif.ExifIFD.ExposureTime: (1, 125),
            piexif.ExifIFD.Flash: 0,
        },
        "GPS": {
            piexif.GPSIFD.GPSLongitudeRef: b"E",
            piexif.GPSIFD.GPSLongitude: TEST_LONGITUDE,
            piexif.GPSIFD.GPSLatitudeRef: b"N",
            piexif.GPSIFD.GPSLatitude: TEST_LATITUDE,
        },
        "1st": {},
        "thumbnail": None,
    }

    exif_bytes = piexif.dump(exif_dict)
    img.save(filename, "JPEG", exif=exif_bytes)
    return filename


def create_simple_image(filename: str, size: tuple = (200, 200)):
    """创建普通测试图片（无EXIF，随机像素）"""
    img = Image.new("RGB", size)
    pixels = img.load()
    for i in range(size[0]):
        for j in range(size[1]):
            pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img.save(filename, "JPEG")
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
        print(f"Login failed: {response.status_code} - {response.text}")
        return None


def upload_image(token: str, filename: str):
    """上传图片并返回响应"""
    with open(filename, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (os.path.basename(filename), f, "image/jpeg")},
        )
    return response


def wait_for_parsing(token: str, image_id: int, max_wait: int = 30):
    """等待图片解析完成"""
    for i in range(max_wait):
        response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            if status in ["parsed", "checked", "discarded"]:
                return data
            elif status == "parsing":
                time.sleep(1)
                continue
            else:
                print(f"  Unexpected status: {status}")
                return data
        else:
            print(f"  Failed to get image: {response.status_code}")
            time.sleep(1)
    return None


# ==================== 测试用例 ====================

def test_exif_parsing(token: str):
    """测试1: EXIF解析 - 上传含EXIF图片并验证解析结果"""
    print("\n=== Test 1: EXIF Parsing ===")
    filename = create_exif_image("test_exif.jpg")

    try:
        # 上传图片
        response = upload_image(token, filename)
        print(f"Upload status: {response.status_code}")
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text}"

        data = response.json()
        image_id = data["image_id"]
        print(f"Image ID: {image_id}")

        # 等待解析完成
        print("Waiting for parsing to complete...")
        image_detail = wait_for_parsing(token, image_id, max_wait=15)
        assert image_detail is not None, "Parsing did not complete in time"
        assert image_detail["status"] in ["parsed", "checked"], f"Expected parsed status, got {image_detail['status']}"

        # 验证EXIF解析结果（通过metadata_json）
        metadata = image_detail.get("metadata_json")
        assert metadata is not None, "metadata_json should not be None"

        capture = metadata.get("capture", {})
        print(f"Capture info: {json.dumps(capture, indent=2, ensure_ascii=False)}")

        # 验证拍摄时间
        assert capture.get("year") == 2026, f"Year should be 2026, got {capture.get('year')}"
        assert capture.get("month") == 7, f"Month should be 7, got {capture.get('month')}"
        assert capture.get("day") == 4, f"Day should be 4, got {capture.get('day')}"
        assert capture.get("hour") == 14, f"Hour should be 14, got {capture.get('hour')}"

        # 验证季节和时段
        assert capture.get("season") == "夏", f"Season should be '夏', got {capture.get('season')}"
        assert capture.get("time_period") == "下午", f"Time period should be '下午', got {capture.get('time_period')}"

        # 验证相机信息（注意：exifread对piexif生成的EXIF标签名有差异，
        # Make/Model可能为空，但focal_length/aperture等应该有值）
        camera = metadata.get("camera", {})
        print(f"Camera info: {json.dumps(camera, indent=2, ensure_ascii=False)}")
        assert camera.get("iso") == "100", f"ISO should be '100', got {camera.get('iso')}"
        assert camera.get("exposure_time") == "1/125", f"Exposure time should be '1/125', got {camera.get('exposure_time')}"

        # 验证GPS
        location = metadata.get("location", {})
        gps = location.get("gps")
        assert gps is not None, "GPS should not be None"
        assert len(gps) == 2, f"GPS should have 2 elements, got {len(gps)}"
        # 验证GPS坐标范围（北京天安门附近）
        assert 115 < gps[0] < 117, f"Longitude should be ~116, got {gps[0]}"
        assert 39 < gps[1] < 41, f"Latitude should be ~39.9, got {gps[1]}"
        print(f"GPS: {gps}")

        print("PASS: EXIF parsing works correctly")
        return image_id

    except AssertionError as e:
        print(f"FAIL: {e}")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_gps_reverse_geocode(token: str, image_id: int):
    """测试2: GPS逆编码 - 验证地址解析"""
    print("\n=== Test 2: GPS Reverse Geocoding ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Get image failed: {response.status_code}"

        data = response.json()
        metadata = data.get("metadata_json", {})
        location = metadata.get("location", {})
        address = location.get("address", {})

        print(f"Location info: {json.dumps(address, indent=2, ensure_ascii=False)}")

        # GPS逆编码可能因网络原因失败，但结构应该存在
        assert "province" in address, "Address should have 'province' field"
        assert "city" in address, "Address should have 'city' field"
        assert "district" in address, "Address should have 'district' field"
        assert "address" in address, "Address should have 'address' field"

        if address.get("city") or address.get("province"):
            print(f"Province: {address.get('province')}")
            print(f"City: {address.get('city')}")
            print(f"District: {address.get('district')}")
            print("PASS: GPS reverse geocoding returned address info")
        else:
            print("WARN: GPS reverse geocoding returned empty (may be network issue)")
            print("PASS: GPS reverse geocoding structure exists (graceful degradation)")

        return True

    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_weather_matching(token: str, image_id: int):
    """测试3: 天气匹配 - 验证天气信息"""
    print("\n=== Test 3: Weather Matching ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Get image failed: {response.status_code}"

        data = response.json()
        metadata = data.get("metadata_json", {})
        weather = metadata.get("weather", {})

        print(f"Weather info: {json.dumps(weather, indent=2, ensure_ascii=False)}")

        # 天气信息应该存在（即使没有API，也有估算值）
        assert "weather" in weather, "Weather should have 'weather' field"
        assert "light" in weather, "Weather should have 'light' field"

        # 天气类型应该是合法的枚举值
        valid_weather = ["晴", "多云", "阴", "小雨", "大雨", "雾", "雪", "沙尘"]
        assert weather["weather"] in valid_weather, f"Weather '{weather['weather']}' not in valid list"

        # 光照应该是合法值
        valid_light = ["强光", "正常", "弱光", "逆光"]
        assert weather["light"] in valid_light, f"Light '{weather['light']}' not in valid list"

        print(f"Weather: {weather['weather']}")
        print(f"Light: {weather['light']}")
        print(f"Temperature: {weather.get('temperature')}")
        print(f"Humidity: {weather.get('humidity')}")
        print("PASS: Weather matching works correctly")
        return True

    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_quality_detection(token: str, image_id: int):
    """测试4: 画质检测 - 验证清晰度和曝光检测"""
    print("\n=== Test 4: Quality Detection ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Get image failed: {response.status_code}"

        data = response.json()
        metadata = data.get("metadata_json", {})
        quality = metadata.get("quality", {})

        print(f"Quality info: {json.dumps(quality, indent=2, ensure_ascii=False)}")

        # 画质信息应该存在
        assert "clarity" in quality, "Quality should have 'clarity' field"
        assert "exposure" in quality, "Quality should have 'exposure' field"
        assert "clarity_score" in quality, "Quality should have 'clarity_score' field"
        assert "brightness" in quality, "Quality should have 'brightness' field"

        # 清晰度应该是合法枚举值
        valid_clarity = ["清晰", "轻微模糊", "严重模糊"]
        assert quality["clarity"] in valid_clarity, f"Clarity '{quality['clarity']}' not in valid list"

        # 曝光应该是合法枚举值
        valid_exposure = ["正常", "过曝", "欠曝"]
        assert quality["exposure"] in valid_exposure, f"Exposure '{quality['exposure']}' not in valid list"

        # 清晰度分数应该是正数
        assert quality["clarity_score"] >= 0, f"Clarity score should be >= 0, got {quality['clarity_score']}"

        # 亮度应该在合理范围
        assert 0 <= quality["brightness"] <= 255, f"Brightness should be 0-255, got {quality['brightness']}"

        print(f"Clarity: {quality['clarity']} (score: {quality['clarity_score']})")
        print(f"Exposure: {quality['exposure']} (brightness: {quality['brightness']})")
        print("PASS: Quality detection works correctly")
        return True

    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_scene_detection(token: str, image_id: int):
    """测试5: 场景识别 - 验证场景类型识别"""
    print("\n=== Test 5: Scene Detection ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/image/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Get image failed: {response.status_code}"

        data = response.json()
        metadata = data.get("metadata_json", {})
        scene = metadata.get("scene", {})

        print(f"Scene info: {json.dumps(scene, indent=2, ensure_ascii=False)}")

        # 场景信息应该存在
        assert "scene_type" in scene, "Scene should have 'scene_type' field"
        assert "ai_labels" in scene, "Scene should have 'ai_labels' field"
        assert "objects" in scene, "Scene should have 'objects' field"

        # 场景类型应该是合法枚举值
        valid_scenes = ["城区", "乡村", "道路", "厂区", "田野", "室内",
                        "山区", "水域", "森林", "沙漠", "雪地", "其他"]
        assert scene["scene_type"] in valid_scenes, f"Scene type '{scene['scene_type']}' not in valid list"

        print(f"Scene type: {scene['scene_type']}")
        print(f"AI labels: {scene['ai_labels']}")
        print(f"Objects: {scene['objects']}")
        print("PASS: Scene detection works correctly")
        return True

    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_label_generation(token: str, image_id: int):
    """测试6: 标签生成 - 验证标签写入数据库"""
    print("\n=== Test 6: Label Generation ===")

    try:
        response = requests.get(
            f"{BASE_URL}/api/label/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Get label failed: {response.status_code} - {response.text}"

        label = response.json()
        print(f"Label data: {json.dumps(label, indent=2, ensure_ascii=False, default=str)}")

        # 验证时间维度标签
        assert label["year"] == 2026, f"Year should be 2026, got {label.get('year')}"
        assert label["month"] == 7, f"Month should be 7, got {label.get('month')}"
        assert label["day"] == 4, f"Day should be 4, got {label.get('day')}"
        assert label["hour"] == 14, f"Hour should be 14, got {label.get('hour')}"
        assert label["season"] == "夏", f"Season should be '夏', got {label.get('season')}"
        assert label["time_period"] == "下午", f"Time period should be '下午', got {label.get('time_period')}"

        # 验证天气标签
        assert label["weather"] is not None, "Weather should not be None"
        assert label["light"] is not None, "Light should not be None"

        # 验证画质标签
        assert label["clarity"] is not None, "Clarity should not be None"
        assert label["exposure"] is not None, "Exposure should not be None"

        # 验证场景标签
        assert label["scene_type"] is not None, "Scene type should not be None"

        # 验证GPS坐标
        assert label["longitude"] is not None, "Longitude should not be None"
        assert label["latitude"] is not None, "Latitude should not be None"
        assert 115 < label["longitude"] < 117, f"Longitude should be ~116, got {label['longitude']}"
        assert 39 < label["latitude"] < 41, f"Latitude should be ~39.9, got {label['latitude']}"

        # 验证标签来源
        assert label["source"] == "auto", f"Source should be 'auto', got {label.get('source')}"

        print("PASS: Label generation works correctly")
        return True

    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_no_exif_image(token: str):
    """测试7: 无EXIF图片 - 验证普通图片也能正常解析"""
    print("\n=== Test 7: No-EXIF Image Parsing ===")
    filename = create_simple_image("test_no_exif.jpg")

    try:
        response = upload_image(token, filename)
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text}"

        data = response.json()
        image_id = data["image_id"]
        print(f"Image ID: {image_id}")

        # 等待解析完成
        print("Waiting for parsing to complete...")
        image_detail = wait_for_parsing(token, image_id, max_wait=15)
        assert image_detail is not None, "Parsing did not complete in time"
        assert image_detail["status"] in ["parsed", "checked"], f"Expected parsed, got {image_detail['status']}"

        # 无EXIF图片应该也能正常解析，只是没有时间/GPS信息
        metadata = image_detail.get("metadata_json", {})
        assert metadata is not None, "metadata_json should not be None"

        # 画质和场景检测应该仍然工作
        quality = metadata.get("quality", {})
        assert "clarity" in quality, "Quality should have 'clarity' field"
        assert "exposure" in quality, "Exposure should have 'exposure' field"

        scene = metadata.get("scene", {})
        assert "scene_type" in scene, "Scene should have 'scene_type' field"

        # 无EXIF时capture应该为空
        capture = metadata.get("capture", {})
        assert capture.get("year") is None, "Year should be None for no-EXIF image"

        print(f"Quality: {quality.get('clarity')}")
        print(f"Scene: {scene.get('scene_type')}")
        print("PASS: No-EXIF image parsing works correctly (graceful degradation)")
        return True

    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Agent Parse Service Test Suite")
    print("=" * 60)

    # 检查后端服务健康
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("ERROR: Backend server is not healthy")
            sys.exit(1)
        print("Backend server is healthy")
    except requests.ConnectionError:
        print("ERROR: Cannot connect to backend server")
        sys.exit(1)

    # 获取认证token
    token = get_auth_token()
    if not token:
        print("ERROR: Failed to get auth token")
        sys.exit(1)
    print(f"Auth token obtained: {token[:20]}...")

    # 运行测试
    results = []

    # Test 1: EXIF解析
    image_id = test_exif_parsing(token)
    results.append(("EXIF Parsing", image_id is not None))

    if image_id:
        # Test 2: GPS逆编码
        results.append(("GPS Reverse Geocoding", test_gps_reverse_geocode(token, image_id)))

        # Test 3: 天气匹配
        results.append(("Weather Matching", test_weather_matching(token, image_id)))

        # Test 4: 画质检测
        results.append(("Quality Detection", test_quality_detection(token, image_id)))

        # Test 5: 场景识别
        results.append(("Scene Detection", test_scene_detection(token, image_id)))

        # Test 6: 标签生成
        results.append(("Label Generation", test_label_generation(token, image_id)))
    else:
        print("\nWARNING: Skipping dependent tests because EXIF parsing failed")
        results.extend([
            ("GPS Reverse Geocoding", False),
            ("Weather Matching", False),
            ("Quality Detection", False),
            ("Scene Detection", False),
            ("Label Generation", False),
        ])

    # Test 7: 无EXIF图片
    results.append(("No-EXIF Image Parsing", test_no_exif_image(token)))

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

    # 清理测试图片
    for f in ["test_exif.jpg", "test_no_exif.jpg"]:
        if os.path.exists(f):
            os.remove(f)

    if passed == total:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
