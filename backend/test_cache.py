# -*- coding: utf-8 -*-
"""
缓存服务单元测试
测试Redis缓存服务的基本功能和降级行为
"""

import asyncio
import json
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from services.cache_service import CacheService


async def test_cache_connect():
    """测试1: Redis连接"""
    print("\n=== Test 1: Redis Connection ===")
    cache = CacheService()
    await cache.connect()

    if cache.redis:
        print("PASS: Redis连接成功")
        await cache.close()
        return True
    else:
        print("FAIL: Redis连接失败")
        return False


async def test_cache_set_get():
    """测试2: 缓存设置和获取"""
    print("\n=== Test 2: Cache Set/Get ===")
    cache = CacheService()
    await cache.connect()

    if not cache.redis:
        print("SKIP: Redis不可用")
        return True

    try:
        # 设置缓存
        test_data = {"total": 100, "status_stats": {"checked": 50}}
        await cache.set("test_key", test_data, expire=60)

        # 获取缓存
        result = await cache.get("test_key")
        assert result is not None, "缓存应该存在"
        assert result["total"] == 100, f"total应为100，实际为{result['total']}"
        assert result["status_stats"]["checked"] == 50, "status_stats.checked应为50"

        print("PASS: 缓存设置和获取正常")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        # 清理
        await cache.delete("test_key")
        await cache.close()


async def test_cache_miss():
    """测试3: 缓存未命中"""
    print("\n=== Test 3: Cache Miss ===")
    cache = CacheService()
    await cache.connect()

    if not cache.redis:
        print("SKIP: Redis不可用")
        return True

    try:
        # 获取不存在的键
        result = await cache.get("nonexistent_key_12345")
        assert result is None, "不存在的键应返回None"

        print("PASS: 缓存未命中返回None")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        await cache.close()


async def test_cache_delete():
    """测试4: 缓存删除"""
    print("\n=== Test 4: Cache Delete ===")
    cache = CacheService()
    await cache.connect()

    if not cache.redis:
        print("SKIP: Redis不可用")
        return True

    try:
        # 设置缓存
        await cache.set("delete_test", {"value": 42}, expire=60)

        # 确认存在
        result = await cache.get("delete_test")
        assert result is not None, "缓存应该存在"

        # 删除
        await cache.delete("delete_test")

        # 确认已删除
        result = await cache.get("delete_test")
        assert result is None, "缓存应该已被删除"

        print("PASS: 缓存删除正常")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        await cache.close()


async def test_cache_graceful_degradation():
    """测试5: 优雅降级（Redis不可用时）"""
    print("\n=== Test 5: Graceful Degradation ===")
    cache = CacheService()
    # 不连接Redis，模拟不可用状态

    try:
        # 获取应返回None
        result = await cache.get("any_key")
        assert result is None, "Redis不可用时get应返回None"

        # 设置应静默失败
        await cache.set("any_key", {"data": 1}, expire=60)

        # 删除应静默失败
        await cache.delete("any_key")

        # 关闭应正常
        await cache.close()

        print("PASS: Redis不可用时优雅降级正常")
        return True
    except Exception as e:
        print(f"FAIL: 降级时发生异常: {e}")
        return False


async def test_cache_expire():
    """测试6: 缓存过期"""
    print("\n=== Test 6: Cache Expiration ===")
    cache = CacheService()
    await cache.connect()

    if not cache.redis:
        print("SKIP: Redis不可用")
        return True

    try:
        # 设置2秒过期的缓存
        await cache.set("expire_test", {"value": 99}, expire=2)

        # 立即获取应存在
        result = await cache.get("expire_test")
        assert result is not None, "缓存应立即可用"
        assert result["value"] == 99, "值应为99"

        # 等待过期
        await asyncio.sleep(3)

        # 获取应返回None
        result = await cache.get("expire_test")
        assert result is None, "缓存应已过期"

        print("PASS: 缓存过期正常")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        await cache.close()


async def test_cache_complex_data():
    """测试7: 复杂数据结构"""
    print("\n=== Test 7: Complex Data Structure ===")
    cache = CacheService()
    await cache.connect()

    if not cache.redis:
        print("SKIP: Redis不可用")
        return True

    try:
        complex_data = {
            "total": 1234,
            "status_stats": {
                "uploading": 10,
                "parsing": 20,
                "parsed": 30,
                "checked": 100,
                "discarded": 5
            },
            "today_upload": 42,
            "nested": {
                "list": [1, 2, 3],
                "string": "hello",
                "bool": True,
                "null": None
            }
        }

        await cache.set("complex_test", complex_data, expire=60)
        result = await cache.get("complex_test")

        assert result is not None, "复杂数据应能正确缓存"
        assert result["total"] == 1234, "total应为1234"
        assert result["status_stats"]["checked"] == 100, "checked应为100"
        assert result["nested"]["list"] == [1, 2, 3], "嵌套列表应正确"
        assert result["nested"]["bool"] is True, "布尔值应正确"
        assert result["nested"]["null"] is None, "null值应正确"

        print("PASS: 复杂数据结构缓存正常")
        return True
    except AssertionError as e:
        print(f"FAIL: {e}")
        return False
    finally:
        await cache.delete("complex_test")
        await cache.close()


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("Cache Service Unit Tests")
    print("=" * 60)

    results = []
    results.append(("Redis Connection", await test_cache_connect()))
    results.append(("Cache Set/Get", await test_cache_set_get()))
    results.append(("Cache Miss", await test_cache_miss()))
    results.append(("Cache Delete", await test_cache_delete()))
    results.append(("Graceful Degradation", await test_cache_graceful_degradation()))
    results.append(("Cache Expiration", await test_cache_expire()))
    results.append(("Complex Data Structure", await test_cache_complex_data()))

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
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
