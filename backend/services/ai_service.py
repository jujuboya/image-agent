# -*- coding: utf-8 -*-
"""
AI服务模块
集成PyTorch预训练模型，提供场景识别和图像质量检测功能
"""

import logging
from typing import Dict, Any, List

import torch
import torchvision.models as models
from torchvision.models import ResNet50_Weights
from torchvision import transforms
from PIL import Image

logger = logging.getLogger(__name__)


class AIService:
    """AI服务，基于PyTorch ResNet50预训练模型"""

    def __init__(self):
        self.model = None
        self.transform = None
        self.scene_categories = [
            '城区', '乡村', '道路', '厂区', '田野',
            '室内', '山区', '水域', '森林', '沙漠', '雪地'
        ]
        self._initialized = False

    async def initialize(self):
        """初始化模型，加载预训练权重和图像预处理管道"""
        if self._initialized:
            return

        try:
            # 加载预训练的ResNet50模型（使用ImageNet V1权重）
            self.model = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
            self.model.eval()

            # 图像预处理流水线（与ImageNet训练时一致）
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])

            self._initialized = True
            logger.info("AI模型初始化成功")
        except Exception as e:
            logger.error(f"AI模型初始化失败: {e}")
            self._initialized = False

    async def recognize_scene(self, image_path: str) -> Dict[str, Any]:
        """
        场景识别：对输入图片进行场景分类

        Args:
            image_path: 图片文件路径

        Returns:
            包含scene_type, confidence, predictions的字典
        """
        if not self._initialized:
            await self.initialize()

        if not self._initialized:
            return {'scene_type': '其他', 'confidence': 0.0, 'predictions': []}

        try:
            # 加载并预处理图像
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.transform(image).unsqueeze(0)

            # 模型推理
            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)

            # 获取Top-5预测
            top5_prob, top5_idx = torch.topk(probabilities, 5)

            # 映射到场景类别（简化处理：通过模运算映射到自定义场景类别）
            predictions: List[Dict[str, Any]] = []
            for prob, idx in zip(top5_prob, top5_idx):
                category_idx = idx.item() % len(self.scene_categories)
                predictions.append({
                    'category': self.scene_categories[category_idx],
                    'confidence': prob.item()
                })

            return {
                'scene_type': predictions[0]['category'] if predictions else '其他',
                'confidence': predictions[0]['confidence'] if predictions else 0.0,
                'predictions': predictions
            }
        except Exception as e:
            logger.error(f"场景识别失败: {e}")
            return {'scene_type': '其他', 'confidence': 0.0, 'predictions': []}

    async def detect_quality(self, image_path: str) -> Dict[str, Any]:
        """
        图像质量检测：评估图片的清晰度和曝光情况

        Args:
            image_path: 图片文件路径

        Returns:
            包含clarity, clarity_score, exposure, brightness的字典
        """
        try:
            import cv2
            import numpy as np

            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {'clarity': '清晰', 'clarity_score': 0, 'exposure': '正常'}

            # 转换为灰度图，计算拉普拉斯方差（清晰度指标）
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            # 判断清晰度
            if laplacian_var > 500:
                clarity = "清晰"
            elif laplacian_var > 100:
                clarity = "轻微模糊"
            else:
                clarity = "严重模糊"

            # 检测曝光（基于HSV色彩空间的V通道亮度均值）
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            brightness = hsv[:, :, 2].mean()

            if brightness < 50:
                exposure = "欠曝"
            elif brightness > 200:
                exposure = "过曝"
            else:
                exposure = "正常"

            return {
                'clarity': clarity,
                'clarity_score': float(laplacian_var),
                'exposure': exposure,
                'brightness': float(brightness)
            }
        except Exception as e:
            logger.error(f"图像质量检测失败: {e}")
            return {'clarity': '清晰', 'clarity_score': 0, 'exposure': '正常'}


# 全局AI服务实例
ai_service = AIService()
