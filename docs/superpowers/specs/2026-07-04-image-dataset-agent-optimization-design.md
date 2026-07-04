# 图片数据集智能采集Agent系统 - 优化设计文档

## 1. 项目概述

### 1.1 项目目标
优化和完善现有图片数据集智能采集Agent系统，确保核心功能稳定，提升性能、代码质量和AI能力。

### 1.2 优化范围
- **功能测试和bug修复**：确保所有功能正常工作
- **性能优化**：提升系统性能和并发能力
- **代码质量提升**：改善代码结构、测试覆盖和文档
- **AI能力增强**：集成PyTorch预训练模型，提升识别精度

### 1.3 技术栈
| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue3 + Vite + Element Plus | Vue 3.4+ |
| 后端 | Python FastAPI | 0.109+ |
| 数据库 | MySQL | 8.0 |
| 缓存 | Redis | 7 |
| 消息队列 | RabbitMQ | 3.x |
| AI模型 | PyTorch + torchvision | 2.x |

---

## 2. 阶段划分

### 2.1 阶段1：核心功能稳定（第1周）
**目标**：确保上传、解析、导出等核心功能稳定工作

**任务清单**：
- [ ] 功能测试：测试所有API接口
- [ ] Bug修复：修复发现的问题
- [ ] 错误处理：完善异常处理机制
- [ ] 日志优化：添加详细日志记录

**里程碑**：所有核心功能通过测试

### 2.2 阶段2：性能优化（第2周）
**目标**：提升系统性能和并发能力

**任务清单**：
- [ ] 数据库优化：添加索引、优化查询
- [ ] 缓存策略：集成Redis缓存
- [ ] 并发处理：优化异步任务队列
- [ ] 前端性能：优化加载速度和渲染性能

**里程碑**：性能指标达到预期

### 2.3 阶段3：代码质量提升（第3周前半）
**目标**：提升代码可维护性和可读性

**任务清单**：
- [ ] 代码重构：优化代码结构
- [ ] 单元测试：添加测试用例
- [ ] 文档完善：更新API文档和注释
- [ ] 代码审查：检查代码规范

**里程碑**：代码质量达到标准

### 2.4 阶段4：AI能力增强（第3周后半）
**目标**：集成PyTorch模型，提升AI识别精度

**任务清单**：
- [ ] 模型集成：集成预训练模型
- [ ] 场景识别：优化场景分类
- [ ] 图像分析：提升图像质量检测
- [ ] 性能优化：优化模型推理速度

**里程碑**：AI识别精度达到预期

---

## 3. 阶段1详细设计：核心功能稳定

### 3.1 功能测试清单

| 模块 | 测试项 | 预期结果 |
|------|--------|----------|
| **认证模块** | 注册、登录、JWT验证 | 正常返回token，权限校验有效 |
| **上传模块** | 单张上传、批量上传、格式校验 | 文件正确保存，MD5去重有效 |
| **Agent解析** | EXIF解析、GPS逆编码、天气匹配 | 标签正确生成，元数据完整 |
| **图片管理** | 列表查询、详情获取、审核功能 | 分页正确，筛选有效，审核状态更新 |
| **数据集导出** | YOLO/COCO/VOC/JSON/CSV导出 | 文件格式正确，数据完整 |

### 3.2 Bug修复策略

```python
# 错误处理示例
try:
    result = await agent_service.parse_image(file_path, image_id)
except Exception as e:
    logger.error(f"图片解析失败: {e}")
    # 更新状态为失败
    image.status = "uploading"
    await db.commit()
    # 返回友好错误信息
    raise HTTPException(status_code=500, detail="图片解析失败，请重试")
```

### 3.3 日志优化

```python
# 结构化日志
logger.info(f"图片上传成功", extra={
    "image_id": image.id,
    "filename": file.filename,
    "file_size": len(content),
    "user_id": current_user.id
})
```

### 3.4 测试方法

1. **手动测试**：使用Postman或curl测试API
2. **自动化测试**：编写pytest测试用例
3. **集成测试**：测试端到端流程

---

## 4. 阶段2详细设计：性能优化

### 4.1 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_image_status ON dataset_image(status);
CREATE INDEX idx_image_created ON dataset_image(created_at);
CREATE INDEX idx_label_scene ON dataset_label(scene_type);
CREATE INDEX idx_label_weather ON dataset_label(weather);
```

### 4.2 Redis缓存策略

```python
# 缓存配置
REDIS_CONFIG = {
    "host": "redis",
    "port": 6379,
    "db": 0,
    "decode_responses": True
}

# 缓存使用示例
async def get_image_stats():
    cache_key = "image_stats"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 查询数据库
    stats = await db.execute(select(func.count(DatasetImage.id)))
    await redis.setex(cache_key, 300, json.dumps(stats))  # 缓存5分钟
    return stats
```

### 4.3 异步任务队列优化

```python
# 使用RabbitMQ处理异步任务
async def process_image_async(image_id: int, file_path: str):
    """异步处理图片"""
    try:
        # 发送到队列
        await queue_service.publish("image_parse", {
            "image_id": image_id,
            "file_path": file_path
        })
    except Exception as e:
        logger.error(f"任务发布失败: {e}")
        # 降级为本地处理
        background_tasks.add_task(parse_image_local, image_id, file_path)
```

### 4.4 前端性能优化

```typescript
// 图片懒加载
const loadImage = (url: string) => {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.src = url
  })
}

// 虚拟滚动
<virtual-list
  :data="images"
  :item-height="200"
  :buffer="5"
/>
```

---

## 5. 阶段3详细设计：代码质量提升

### 5.1 代码重构策略

```python
# 重构前：所有逻辑在一个文件
# 重构后：职责分离

# services/image_service.py
class ImageService:
    """图片服务"""
    async def upload_image(self, file: UploadFile, user: SysUser):
        """上传图片"""
        pass
    
    async def get_image_list(self, filters: dict):
        """获取图片列表"""
        pass

# services/agent_service.py
class AgentService:
    """Agent解析服务"""
    async def parse_image(self, file_path: str):
        """解析图片"""
        pass

# services/export_service.py
class ExportService:
    """导出服务"""
    async def export_yolo(self, images: list):
        """导出YOLO格式"""
        pass
```

### 5.2 单元测试框架

```python
# tests/test_upload.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_upload_image(client):
    """测试图片上传"""
    with open("test.jpg", "rb") as f:
        response = await client.post(
            "/api/upload/image",
            files={"file": ("test.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 200
    assert response.json()["status"] == "parsing"
```

### 5.3 API文档完善

```python
@router.post("/upload/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="图片文件"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """
    上传单张图片
    
    - **file**: 支持格式: jpg, jpeg, png, bmp, tiff, webp
    - **返回**: 图片ID、UUID、状态
    
    **示例**:
    ```bash
    curl -X POST "http://localhost:8000/api/upload/image" \
         -H "Authorization: Bearer <token>" \
         -F "file=@image.jpg"
    ```
    """
```

### 5.4 代码规范检查

```bash
# 使用flake8检查代码风格
flake8 backend/ --max-line-length=100

# 使用black格式化代码
black backend/ --line-length=100

# 使用mypy检查类型
mypy backend/ --ignore-missing-imports
```

---

## 6. 阶段4详细设计：AI能力增强

### 6.1 PyTorch模型集成

```python
# services/ai_service.py
import torch
import torchvision.models as models
from torchvision import transforms
from PIL import Image

class AIService:
    """AI服务"""
    
    def __init__(self):
        # 加载预训练模型
        self.model = models.resnet50(pretrained=True)
        self.model.eval()
        
        # 图像预处理
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # 场景类别
        self.scene_categories = [
            '城区', '乡村', '道路', '厂区', '田野',
            '室内', '山区', '水域', '森林', '沙漠', '雪地'
        ]
    
    async def recognize_scene(self, image_path: str) -> dict:
        """场景识别"""
        try:
            # 加载图像
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.transform(image).unsqueeze(0)
            
            # 推理
            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
            
            # 获取Top-5预测
            top5_prob, top5_idx = torch.topk(probabilities, 5)
            
            return {
                'scene_type': self.scene_categories[top5_idx[0].item()],
                'confidence': top5_prob[0].item(),
                'predictions': [
                    {
                        'category': self.scene_categories[idx.item()],
                        'confidence': prob.item()
                    }
                    for prob, idx in zip(top5_prob, top5_idx)
                ]
            }
        except Exception as e:
            logger.error(f"场景识别失败: {e}")
            return {'scene_type': '其他', 'confidence': 0.0}
```

### 6.2 图像质量检测优化

```python
# utils/quality_utils.py
import cv2
import numpy as np

class QualityDetector:
    """图像质量检测器"""
    
    def detect_blur(self, image_path: str) -> float:
        """检测模糊程度（拉普拉斯方差）"""
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        return laplacian_var
    
    def detect_exposure(self, image_path: str) -> dict:
        """检测曝光情况"""
        image = cv2.imread(image_path)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        brightness = hsv[:, :, 2].mean()
        
        if brightness < 50:
            return {'status': '欠曝', 'value': brightness}
        elif brightness > 200:
            return {'status': '过曝', 'value': brightness}
        else:
            return {'status': '正常', 'value': brightness}
    
    def detect_noise(self, image_path: str) -> float:
        """检测噪点水平"""
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        noise = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        return np.mean(np.abs(image.astype(float) - noise.astype(float)))
```

### 6.3 模型性能优化

```python
# 模型量化
model_quantized = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)

# ONNX导出
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    opset_version=11,
    input_names=['input'],
    output_names=['output']
)

# 使用ONNX Runtime推理
import onnxruntime as ort
session = ort.InferenceSession("model.onnx")
```

---

## 7. Docker部署优化

### 7.1 服务组成

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| frontend | nginx:alpine | 80 | 前端静态资源 |
| backend | python:3.11-slim | 8000 | 后端API服务 |
| mysql | mysql:8.0 | 3306 | 数据库 |
| redis | redis:7-alpine | 6379 | 缓存 |
| rabbitmq | rabbitmq:3-management | 5672, 15672 | 消息队列 |

### 7.2 环境变量配置

```env
# .env
MYSQL_ROOT_PASSWORD=your_password
MYSQL_DATABASE=image_dataset
REDIS_PASSWORD=your_redis_password
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=your_rabbitmq_password
WEATHER_API_KEY=your_weather_api_key
```

### 7.3 启动命令

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

---

## 8. 验收标准

### 8.1 功能验收
- [ ] 图片上传（单张/批量）
- [ ] EXIF解析
- [ ] GPS逆编码
- [ ] 天气匹配
- [ ] 图像质量检测
- [ ] 场景识别
- [ ] 人工审核
- [ ] 数据集导出（YOLO/COCO/VOC/JSON/CSV）

### 8.2 性能验收
- [ ] 支持万级图片批量上传
- [ ] 异步解析不阻塞前端
- [ ] 图片解析时间 < 10秒
- [ ] API响应时间 < 500ms

### 8.3 安全验收
- [ ] 文件格式校验
- [ ] MD5去重
- [ ] JWT认证
- [ ] 权限分级

### 8.4 AI验收
- [ ] 场景识别准确率 > 80%
- [ ] 图像质量检测准确率 > 90%
- [ ] 模型推理时间 < 2秒

---

## 9. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| AI模型精度不足 | 高 | 提供人工修正功能，持续优化模型 |
| 天气API不稳定 | 中 | 实现降级估算方案 |
| 大文件上传超时 | 中 | 分片上传 + 断点续传 |
| 数据库性能瓶颈 | 中 | 添加索引 + 读写分离 |
| 模型推理速度慢 | 中 | 模型量化 + ONNX优化 |

---

## 10. 时间安排

| 阶段 | 时间 | 交付物 |
|------|------|--------|
| 阶段1：核心功能稳定 | 第1周 | 测试报告、Bug修复列表 |
| 阶段2：性能优化 | 第2周 | 性能测试报告、优化方案 |
| 阶段3：代码质量提升 | 第3周前半 | 代码审查报告、测试覆盖率 |
| 阶段4：AI能力增强 | 第3周后半 | AI模型集成报告、精度测试 |

---

**设计文档已完成，请审查。有需要修改的地方吗？**
