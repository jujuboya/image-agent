# -*- coding: utf-8 -*-
"""
AI服务单元测试
测试场景识别和图像质量检测功能
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import torch
import numpy as np
from PIL import Image
from torchvision import transforms

from services.ai_service import AIService, ai_service


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """创建独立的AI服务实例（避免污染全局状态）"""
    return AIService()


@pytest.fixture
def sample_image_path(tmp_path):
    """创建一张随机纹理的测试图片，返回其路径"""
    img = Image.new("RGB", (640, 480))
    pixels = img.load()
    for i in range(640):
        for j in range(480):
            pixels[i, j] = (i % 256, j % 256, (i + j) % 256)
    path = str(tmp_path / "test_image.jpg")
    img.save(path, "JPEG")
    return path


@pytest.fixture
def dark_image_path(tmp_path):
    """创建一张暗色图片（用于测试曝光检测 - 欠曝）"""
    img = Image.new("RGB", (100, 100), color=(10, 10, 10))
    path = str(tmp_path / "dark_image.jpg")
    img.save(path, "JPEG")
    return path


@pytest.fixture
def bright_image_path(tmp_path):
    """创建一张亮色图片（用于测试曝光检测 - 过曝）"""
    img = Image.new("RGB", (100, 100), color=(240, 240, 240))
    path = str(tmp_path / "bright_image.jpg")
    img.save(path, "JPEG")
    return path


@pytest.fixture
def sharp_image_path(tmp_path):
    """创建一张清晰图片（有高频纹理）"""
    img = Image.new("RGB", (200, 200))
    pixels = img.load()
    for i in range(200):
        for j in range(200):
            # 高频棋盘格纹理，产生高拉普拉斯方差
            if (i // 2 + j // 2) % 2 == 0:
                pixels[i, j] = (255, 255, 255)
            else:
                pixels[i, j] = (0, 0, 0)
    path = str(tmp_path / "sharp_image.jpg")
    img.save(path, "JPEG")
    return path


# ==================== AIService初始化测试 ====================

class TestAIServiceInit:
    """测试AI服务初始化"""

    def test_initial_state_not_initialized(self, service):
        """测试初始状态：未初始化"""
        assert service._initialized is False
        assert service.model is None
        assert service.transform is None

    def test_scene_categories_defined(self, service):
        """测试场景类别列表已定义"""
        assert len(service.scene_categories) == 11
        assert '城区' in service.scene_categories
        assert '乡村' in service.scene_categories
        assert '水域' in service.scene_categories
        assert '雪地' in service.scene_categories

    @pytest.mark.asyncio
    async def test_initialize_loads_model(self, service):
        """测试初始化加载模型"""
        await service.initialize()
        assert service._initialized is True
        assert service.model is not None
        assert service.transform is not None

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, service):
        """测试重复初始化是幂等的"""
        await service.initialize()
        first_model = service.model
        await service.initialize()
        assert service.model is first_model  # 同一实例

    @pytest.mark.asyncio
    async def test_initialize_failure_sets_uninitialized(self):
        """测试初始化失败时状态保持未初始化"""
        svc = AIService()
        with patch('services.ai_service.models.resnet50', side_effect=RuntimeError("load failed")):
            await svc.initialize()
        assert svc._initialized is False
        assert svc.model is None

    def test_global_instance_exists(self):
        """测试全局ai_service实例存在"""
        assert ai_service is not None
        assert isinstance(ai_service, AIService)


# ==================== 场景识别测试 ====================

class TestRecognizeScene:
    """测试场景识别功能"""

    @pytest.mark.asyncio
    async def test_recognize_scene_returns_dict(self, service, sample_image_path):
        """测试场景识别返回正确格式的字典"""
        result = await service.recognize_scene(sample_image_path)
        assert isinstance(result, dict)
        assert 'scene_type' in result
        assert 'confidence' in result
        assert 'predictions' in result

    @pytest.mark.asyncio
    async def test_recognize_scene_type_is_valid(self, service, sample_image_path):
        """测试场景类型是预定义类别之一"""
        result = await service.recognize_scene(sample_image_path)
        assert result['scene_type'] in service.scene_categories

    @pytest.mark.asyncio
    async def test_recognize_scene_confidence_range(self, service, sample_image_path):
        """测试置信度在0-1范围内"""
        result = await service.recognize_scene(sample_image_path)
        assert 0.0 <= result['confidence'] <= 1.0

    @pytest.mark.asyncio
    async def test_recognize_scene_predictions_format(self, service, sample_image_path):
        """测试预测列表格式正确"""
        result = await service.recognize_scene(sample_image_path)
        predictions = result['predictions']
        assert isinstance(predictions, list)
        assert len(predictions) <= 5  # Top-5
        for pred in predictions:
            assert 'category' in pred
            assert 'confidence' in pred
            assert pred['category'] in service.scene_categories
            assert 0.0 <= pred['confidence'] <= 1.0

    @pytest.mark.asyncio
    async def test_recognize_scene_auto_initializes(self, sample_image_path):
        """测试未初始化时自动初始化"""
        svc = AIService()
        assert svc._initialized is False
        result = await svc.recognize_scene(sample_image_path)
        assert svc._initialized is True
        assert 'scene_type' in result

    @pytest.mark.asyncio
    async def test_recognize_scene_invalid_path_returns_fallback(self, service):
        """测试无效路径返回降级结果"""
        result = await service.recognize_scene("/nonexistent/path/image.jpg")
        assert result['scene_type'] == '其他'
        assert result['confidence'] == 0.0
        assert result['predictions'] == []


# ==================== 图像质量检测测试 ====================

class TestDetectQuality:
    """测试图像质量检测功能"""

    @pytest.mark.asyncio
    async def test_detect_quality_returns_dict(self, service, sample_image_path):
        """测试质量检测返回正确格式的字典"""
        result = await service.detect_quality(sample_image_path)
        assert isinstance(result, dict)
        assert 'clarity' in result
        assert 'clarity_score' in result
        assert 'exposure' in result
        assert 'brightness' in result

    @pytest.mark.asyncio
    async def test_detect_quality_clarity_valid(self, service, sample_image_path):
        """测试清晰度是合法值"""
        result = await service.detect_quality(sample_image_path)
        valid_clarity = ["清晰", "轻微模糊", "严重模糊"]
        assert result['clarity'] in valid_clarity

    @pytest.mark.asyncio
    async def test_detect_quality_exposure_valid(self, service, sample_image_path):
        """测试曝光是合法值"""
        result = await service.detect_quality(sample_image_path)
        valid_exposure = ["正常", "过曝", "欠曝"]
        assert result['exposure'] in valid_exposure

    @pytest.mark.asyncio
    async def test_detect_quality_clarity_score_positive(self, service, sample_image_path):
        """测试清晰度分数为非负数"""
        result = await service.detect_quality(sample_image_path)
        assert result['clarity_score'] >= 0

    @pytest.mark.asyncio
    async def test_detect_quality_brightness_range(self, service, sample_image_path):
        """测试亮度在合理范围内"""
        result = await service.detect_quality(sample_image_path)
        assert 0 <= result['brightness'] <= 255

    @pytest.mark.asyncio
    async def test_detect_quality_sharp_image(self, service, sharp_image_path):
        """测试清晰图片的清晰度评分较高"""
        result = await service.detect_quality(sharp_image_path)
        assert result['clarity'] == "清晰"
        assert result['clarity_score'] > 500

    @pytest.mark.asyncio
    async def test_detect_quality_dark_image_exposure(self, service, dark_image_path):
        """测试暗色图片的曝光检测为欠曝"""
        result = await service.detect_quality(dark_image_path)
        assert result['exposure'] == "欠曝"

    @pytest.mark.asyncio
    async def test_detect_quality_bright_image_exposure(self, service, bright_image_path):
        """测试亮色图片的曝光检测为过曝"""
        result = await service.detect_quality(bright_image_path)
        assert result['exposure'] == "过曝"

    @pytest.mark.asyncio
    async def test_detect_quality_invalid_path_returns_fallback(self, service):
        """测试无效路径返回降级结果"""
        result = await service.detect_quality("/nonexistent/path/image.jpg")
        assert result['clarity'] == '清晰'
        assert result['clarity_score'] == 0
        assert result['exposure'] == '正常'

    @pytest.mark.asyncio
    async def test_detect_quality_does_not_require_initialization(self, sample_image_path):
        """测试质量检测不需要模型初始化"""
        svc = AIService()
        assert svc._initialized is False
        result = await svc.detect_quality(sample_image_path)
        # 应该正常工作，不依赖模型
        assert 'clarity' in result


# ==================== Mock模型测试 ====================

class TestRecognizeSceneWithMockModel:
    """使用Mock模型测试场景识别的推理逻辑"""

    @pytest.mark.asyncio
    async def test_mock_model_top1_prediction_used(self, sample_image_path):
        """测试Mock模型的Top-1预测正确映射为scene_type"""
        svc = AIService()

        # 手动设置mock模型和transform
        mock_model = MagicMock()
        # 创建一个假的输出tensor，形状为[1, 1000]（ImageNet 1000类）
        fake_output = torch.zeros(1, 1000)
        fake_output[0, 0] = 10.0  # 第0类得分最高
        mock_model.return_value = fake_output
        mock_model.eval = MagicMock()

        svc.model = mock_model
        svc.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        svc._initialized = True

        result = await svc.recognize_scene(sample_image_path)
        # idx=0 -> 0 % 11 = 0 -> '城区'
        assert result['scene_type'] == '城区'
        assert result['confidence'] > 0

    @pytest.mark.asyncio
    async def test_mock_model_returns_five_predictions(self, sample_image_path):
        """测试Mock模型返回5个预测"""
        svc = AIService()

        mock_model = MagicMock()
        fake_output = torch.randn(1, 1000)
        mock_model.return_value = fake_output
        mock_model.eval = MagicMock()

        svc.model = mock_model
        svc.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        svc._initialized = True

        result = await svc.recognize_scene(sample_image_path)
        assert len(result['predictions']) == 5
