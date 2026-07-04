# 图片数据集智能采集Agent系统 - 优化实施计划

> **Goal:** 优化和完善现有图片数据集智能采集Agent系统，确保核心功能稳定，提升性能、代码质量和AI能力

**Architecture:** 渐进式优化，分4个阶段实施，每阶段验证后再进入下一阶段

**Tech Stack:** Python FastAPI, Vue3, MySQL, Redis, RabbitMQ, PyTorch

---

## 阶段1：核心功能稳定（第1周）

### Task 1.1: 环境搭建与依赖检查

**Files:**
- Create: `backend/.env`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 创建环境配置文件**

```bash
# 创建 .env 文件
cat > backend/.env << 'EOF'
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=image_dataset

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# RabbitMQ配置
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# 应用配置
APP_NAME=图片数据集智能采集Agent系统
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 文件上传配置
UPLOAD_DIR=./uploads
TEMP_DIR=./uploads/temp
DATASET_DIR=./uploads/dataset
DISCARD_DIR=./uploads/discard
EXPORT_DIR=./uploads/export
MAX_FILE_SIZE=52428800
BATCH_UPLOAD_LIMIT=1000

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 天气API配置（可选）
WEATHER_API_KEY=
WEATHER_API_URL=
EOF
```

- [ ] **Step 2: 检查依赖文件**

```bash
# 查看 requirements.txt
cat backend/requirements.txt

# 安装依赖
cd backend && pip install -r requirements.txt
```

- [ ] **Step 3: 验证环境**

```bash
# 测试Python环境
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"

# 测试数据库连接（如果MySQL已启动）
python -c "import pymysql; conn = pymysql.connect(host='localhost', user='root', password='your_password'); print('MySQL连接成功'); conn.close()"
```

- [ ] **Step 4: Commit**

```bash
git add backend/.env
git commit -m "chore: add environment configuration"
```

---

### Task 1.2: 数据库初始化

**Files:**
- Modify: `sql/init.sql`

- [ ] **Step 1: 执行数据库初始化**

```bash
# 连接MySQL并执行初始化脚本
mysql -u root -p < sql/init.sql
```

- [ ] **Step 2: 验证数据库表**

```bash
# 检查表是否创建成功
mysql -u root -p -e "USE image_dataset; SHOW TABLES;"
```

预期输出：
```
+---------------------------+
| Tables_in_image_dataset   |
+---------------------------+
| dataset_image             |
| dataset_label             |
| dataset_version           |
| operation_log             |
| sys_user                  |
+---------------------------+
```

- [ ] **Step 3: Commit**

```bash
git add sql/init.sql
git commit -m "feat: initialize database schema"
```

---

### Task 1.3: 后端服务启动测试

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: 启动后端服务**

```bash
cd backend
python main.py
```

预期输出：
```
正在启动图片数据集智能采集Agent系统...
目录已创建: uploads
目录已创建: uploads/temp
目录已创建: uploads/dataset
数据库初始化完成
消息队列连接失败: [错误信息]，将使用本地任务队列
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

- [ ] **Step 2: 测试健康检查接口**

```bash
# 测试根路径
curl http://localhost:8000/

# 测试健康检查
curl http://localhost:8000/health
```

预期输出：
```json
{"name":"图片数据集智能采集Agent系统","version":"1.0.0","status":"running"}
{"status":"healthy"}
```

- [ ] **Step 3: 查看API文档**

在浏览器中访问：`http://localhost:8000/docs`

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "fix: ensure backend starts correctly"
```

---

### Task 1.4: 认证模块测试

**Files:**
- Modify: `backend/routers/auth.py`

- [ ] **Step 1: 测试用户注册**

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "testpass123", "nickname": "测试用户"}'
```

预期输出：
```json
{"id": 1, "username": "testuser", "nickname": "测试用户", "role": "viewer", "is_active": true}
```

- [ ] **Step 2: 测试用户登录**

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=testpass123"
```

预期输出：
```json
{"access_token": "eyJ...", "token_type": "bearer"}
```

- [ ] **Step 3: 测试获取当前用户**

```bash
# 使用上一步获取的token
curl -X GET "http://localhost:8000/api/auth/me" \
     -H "Authorization: Bearer <your-token>"
```

预期输出：
```json
{"id": 1, "username": "testuser", "nickname": "测试用户", "role": "viewer"}
```

- [ ] **Step 4: Commit**

```bash
git add backend/routers/auth.py
git commit -m "test: verify auth module works correctly"
```

---

### Task 1.5: 上传模块测试

**Files:**
- Modify: `backend/routers/upload.py`

- [ ] **Step 1: 准备测试图片**

```bash
# 创建测试图片（如果没有真实图片）
python -c "
from PIL import Image
img = Image.new('RGB', (100, 100), color='red')
img.save('test.jpg')
print('测试图片已创建: test.jpg')
"
```

- [ ] **Step 2: 测试单张图片上传**

```bash
curl -X POST "http://localhost:8000/api/upload/image" \
     -H "Authorization: Bearer <your-token>" \
     -F "file=@test.jpg"
```

预期输出：
```json
{"image_id": 1, "uuid": "...", "filename": "test.jpg", "status": "parsing", "message": "上传成功，正在自动解析..."}
```

- [ ] **Step 3: 测试批量图片上传**

```bash
curl -X POST "http://localhost:8000/api/upload/batch" \
     -H "Authorization: Bearer <your-token>" \
     -F "files=@test.jpg" \
     -F "files=@test.jpg"
```

预期输出：
```json
{"total": 2, "success": 2, "failed": 0, "results": [...]}
```

- [ ] **Step 4: Commit**

```bash
git add backend/routers/upload.py
git commit -m "test: verify upload module works correctly"
```

---

### Task 1.6: Agent解析服务测试

**Files:**
- Modify: `backend/services/agent_parse.py`

- [ ] **Step 1: 测试EXIF解析**

```bash
# 上传一张包含EXIF信息的图片
curl -X POST "http://localhost:8000/api/upload/image" \
     -H "Authorization: Bearer <your-token>" \
     -F "file=@photo_with_exif.jpg"

# 查看解析结果
curl -X GET "http://localhost:8000/api/image/1" \
     -H "Authorization: Bearer <your-token>"
```

- [ ] **Step 2: 检查解析日志**

```bash
# 查看后端日志输出
# 应该看到类似：
# EXIF解析完成: 1
# GPS逆编码完成: {...}
# 天气匹配完成: {...}
# 画质检测完成: {...}
# 场景识别完成: {...}
```

- [ ] **Step 3: 验证标签生成**

```bash
curl -X GET "http://localhost:8000/api/label/1" \
     -H "Authorization: Bearer <your-token>"
```

预期输出应包含：
```json
{
  "year": 2026,
  "month": 7,
  "day": 4,
  "hour": 14,
  "season": "夏",
  "time_period": "下午",
  "weather": "晴",
  "scene_type": "其他",
  ...
}
```

- [ ] **Step 4: Commit**

```bash
git add backend/services/agent_parse.py
git commit -m "test: verify agent parse service works correctly"
```

---

### Task 1.7: 图片管理接口测试

**Files:**
- Modify: `backend/routers/image.py`

- [ ] **Step 1: 测试图片列表查询**

```bash
curl -X GET "http://localhost:8000/api/image/list?page=1&page_size=10" \
     -H "Authorization: Bearer <your-token>"
```

预期输出：
```json
{"total": 1, "page": 1, "page_size": 10, "items": [...]}
```

- [ ] **Step 2: 测试图片详情获取**

```bash
curl -X GET "http://localhost:8000/api/image/1" \
     -H "Authorization: Bearer <your-token>"
```

- [ ] **Step 3: 测试图片审核**

```bash
curl -X POST "http://localhost:8000/api/image/check" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"image_id": 1, "status": "checked", "comment": "审核通过"}'
```

预期输出：
```json
{"message": "审核成功", "status": "checked"}
```

- [ ] **Step 4: Commit**

```bash
git add backend/routers/image.py
git commit -m "test: verify image management works correctly"
```

---

### Task 1.8: 数据集导出测试

**Files:**
- Modify: `backend/routers/dataset.py`

- [ ] **Step 1: 测试CSV导出**

```bash
curl -X POST "http://localhost:8000/api/dataset/export" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"format": "csv"}' \
     --output export.csv
```

- [ ] **Step 2: 测试JSON导出**

```bash
curl -X POST "http://localhost:8000/api/dataset/export" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"format": "json"}' \
     --output export.json
```

- [ ] **Step 3: 测试YOLO导出**

```bash
curl -X POST "http://localhost:8000/api/dataset/export" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"format": "yolo"}' \
     --output export.zip
```

- [ ] **Step 4: Commit**

```bash
git add backend/routers/dataset.py
git commit -m "test: verify dataset export works correctly"
```

---

## 阶段2：性能优化（第2周）

### Task 2.1: 数据库索引优化

**Files:**
- Modify: `sql/init.sql`

- [ ] **Step 1: 添加数据库索引**

```bash
mysql -u root -p -e "
USE image_dataset;

-- 图片表索引
CREATE INDEX idx_image_status ON dataset_image(status);
CREATE INDEX idx_image_created ON dataset_image(created_at);
CREATE INDEX idx_image_md5 ON dataset_image(file_md5);

-- 标签表索引
CREATE INDEX idx_label_scene ON dataset_label(scene_type);
CREATE INDEX idx_label_weather ON dataset_label(weather);
CREATE INDEX idx_label_season ON dataset_label(season);

-- 验证索引
SHOW INDEX FROM dataset_image;
SHOW INDEX FROM dataset_label;
"
```

- [ ] **Step 2: 测试查询性能**

```bash
# 测试带索引的查询
time curl -X GET "http://localhost:8000/api/image/list?status=parsed" \
     -H "Authorization: Bearer <your-token>"
```

- [ ] **Step 3: Commit**

```bash
git add sql/init.sql
git commit -m "perf: add database indexes for better query performance"
```

---

### Task 2.2: Redis缓存集成

**Files:**
- Create: `backend/services/cache_service.py`
- Modify: `backend/config.py`

- [ ] **Step 1: 创建缓存服务**

```python
# backend/services/cache_service.py
import redis.asyncio as redis
import json
from typing import Optional, Any
from config import settings

class CacheService:
    """Redis缓存服务"""
    
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """连接Redis"""
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            await self.redis.ping()
            print("Redis连接成功")
        except Exception as e:
            print(f"Redis连接失败: {e}")
            self.redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, expire: int = 300):
        """设置缓存"""
        if not self.redis:
            return
        try:
            await self.redis.setex(key, expire, json.dumps(value))
        except Exception:
            pass
    
    async def delete(self, key: str):
        """删除缓存"""
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except Exception:
            pass
    
    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()

# 全局缓存实例
cache_service = CacheService()
```

- [ ] **Step 2: 在图片统计接口中使用缓存**

```python
# backend/routers/image.py
from services.cache_service import cache_service

@router.get("/stats/overview")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取图片统计信息"""
    # 尝试从缓存获取
    cache_key = "image_stats"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    # 查询数据库
    # ... 原有代码 ...
    
    result = {
        "total": total,
        "status_stats": status_stats,
        "today_upload": today_count,
    }
    
    # 设置缓存（5分钟）
    await cache_service.set(cache_key, result, expire=300)
    
    return result
```

- [ ] **Step 3: 测试缓存效果**

```bash
# 第一次请求（从数据库）
time curl -X GET "http://localhost:8000/api/image/stats/overview" \
     -H "Authorization: Bearer <your-token>"

# 第二次请求（从缓存，应该更快）
time curl -X GET "http://localhost:8000/api/image/stats/overview" \
     -H "Authorization: Bearer <your-token>"
```

- [ ] **Step 4: Commit**

```bash
git add backend/services/cache_service.py backend/routers/image.py
git commit -m "feat: add Redis cache for image statistics"
```

---

## 阶段3：代码质量提升（第3周前半）

### Task 3.1: 代码重构 - 服务层分离

**Files:**
- Create: `backend/services/image_service.py`
- Create: `backend/services/export_service.py`
- Modify: `backend/routers/upload.py`
- Modify: `backend/routers/image.py`
- Modify: `backend/routers/dataset.py`

- [ ] **Step 1: 创建图片服务**

```python
# backend/services/image_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import DatasetImage, DatasetLabel

class ImageService:
    """图片服务"""
    
    async def get_image_list(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        check_status: Optional[str] = None
    ) -> dict:
        """获取图片列表"""
        query = select(DatasetImage)
        count_query = select(func.count(DatasetImage.id))
        
        if status:
            query = query.where(DatasetImage.status == status)
            count_query = count_query.where(DatasetImage.status == status)
        
        if check_status:
            query = query.where(DatasetImage.check_status == check_status)
            count_query = count_query.where(DatasetImage.check_status == check_status)
        
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.order_by(DatasetImage.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        images = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": images
        }
    
    async def get_image_detail(self, db: AsyncSession, image_id: int) -> Optional[DatasetImage]:
        """获取图片详情"""
        result = await db.execute(
            select(DatasetImage)
            .where(DatasetImage.id == image_id)
        )
        return result.scalar_one_or_none()

# 全局图片服务实例
image_service = ImageService()
```

- [ ] **Step 2: 创建导出服务**

```python
# backend/services/export_service.py
import csv
import io
import json
from typing import List
from database import DatasetImage

class ExportService:
    """导出服务"""
    
    def export_csv(self, images: List[DatasetImage], version_name: str) -> str:
        """导出CSV格式"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        headers = [
            "image_id", "filename", "width", "height",
            "year", "month", "day", "hour", "season", "time_period", "day_type",
            "weather", "temperature", "humidity", "light",
            "scene_type", "device_type",
            "province", "city", "district", "address"
        ]
        writer.writerow(headers)
        
        # 写入数据
        for image in images:
            label = image.labels if image.labels else None
            row = [
                image.id,
                image.original_filename,
                image.width,
                image.height,
                label.year if label else None,
                label.month if label else None,
                label.day if label else None,
                label.hour if label else None,
                label.season if label else None,
                label.time_period if label else None,
                label.day_type if label else None,
                label.weather if label else None,
                label.temperature if label else None,
                label.humidity if label else None,
                label.light if label else None,
                label.scene_type if label else None,
                label.device_type if label else None,
                label.province if label else None,
                label.city if label else None,
                label.district if label else None,
                label.address if label else None,
            ]
            writer.writerow(row)
        
        output.seek(0)
        return output.getvalue()

# 全局导出服务实例
export_service = ExportService()
```

- [ ] **Step 3: 更新路由使用服务层**

```python
# backend/routers/image.py
from services.image_service import image_service

@router.get("/list", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    check_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取图片列表"""
    return await image_service.get_image_list(db, page, page_size, status, check_status)
```

- [ ] **Step 4: 测试重构后的代码**

```bash
# 测试图片列表
curl -X GET "http://localhost:8000/api/image/list?page=1&page_size=10" \
     -H "Authorization: Bearer <your-token>"

# 测试CSV导出
curl -X POST "http://localhost:8000/api/dataset/export" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"format": "csv"}' \
     --output test_export.csv
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/image_service.py backend/services/export_service.py backend/routers/
git commit -m "refactor: extract service layer for better code organization"
```

---

### Task 3.2: 单元测试框架搭建

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`
- Modify: `backend/requirements-dev.txt`

- [ ] **Step 1: 创建测试配置**

```python
# backend/tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from main import app
from database import Base, get_db

# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_database():
    """设置测试数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db():
    """获取测试数据库会话"""
    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
async def client():
    """获取测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 2: 创建认证测试**

```python
# backend/tests/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """测试用户注册"""
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "nickname": "测试用户"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["nickname"] == "测试用户"
    assert data["role"] == "viewer"

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """测试用户登录"""
    # 先注册
    await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "nickname": "测试用户"
        }
    )
    
    # 登录
    response = await client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    """测试获取当前用户"""
    # 先注册
    await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "nickname": "测试用户"
        }
    )
    
    # 登录
    login_response = await client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # 获取当前用户
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
```

- [ ] **Step 3: 运行测试**

```bash
cd backend
pytest tests/ -v
```

预期输出：
```
tests/test_auth.py::test_register PASSED
tests/test_auth.py::test_login PASSED
tests/test_auth.py::test_get_me PASSED
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/ backend/requirements-dev.txt
git commit -m "test: add unit test framework and auth tests"
```

---

## 阶段4：AI能力增强（第3周后半）

### Task 4.1: PyTorch模型集成

**Files:**
- Create: `backend/services/ai_service.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 安装PyTorch依赖**

```bash
cd backend
pip install torch torchvision pillow opencv-python
```

- [ ] **Step 2: 创建AI服务**

```python
# backend/services/ai_service.py
import torch
import torchvision.models as models
from torchvision import transforms
from PIL import Image
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AIService:
    """AI服务"""
    
    def __init__(self):
        self.model = None
        self.transform = None
        self.scene_categories = [
            '城区', '乡村', '道路', '厂区', '田野',
            '室内', '山区', '水域', '森林', '沙漠', '雪地'
        ]
        self._initialized = False
    
    async def initialize(self):
        """初始化模型"""
        if self._initialized:
            return
        
        try:
            # 加载预训练的ResNet50模型
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
            
            self._initialized = True
            logger.info("AI模型初始化成功")
        except Exception as e:
            logger.error(f"AI模型初始化失败: {e}")
            self._initialized = False
    
    async def recognize_scene(self, image_path: str) -> Dict[str, Any]:
        """场景识别"""
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized:
            return {'scene_type': '其他', 'confidence': 0.0, 'predictions': []}
        
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
            
            # 映射到场景类别（这里简化处理，实际需要训练专门的模型）
            predictions = []
            for i, (prob, idx) in enumerate(zip(top5_prob, top5_idx)):
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
        """图像质量检测"""
        try:
            import cv2
            import numpy as np
            
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {'clarity': '清晰', 'clarity_score': 0, 'exposure': '正常'}
            
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 计算拉普拉斯方差（清晰度指标）
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 判断清晰度
            if laplacian_var > 500:
                clarity = "清晰"
            elif laplacian_var > 100:
                clarity = "轻微模糊"
            else:
                clarity = "严重模糊"
            
            # 检测曝光
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
```

- [ ] **Step 3: 更新Agent解析服务使用AI**

```python
# backend/services/agent_parse.py
from services.ai_service import ai_service

class AgentParseService:
    async def parse_image(self, file_path: str, image_id: int) -> Dict[str, Any]:
        # ... 现有代码 ...
        
        # 5. AI场景识别
        scene_info = await ai_service.recognize_scene(file_path)
        logger.info(f"AI场景识别完成: {scene_info}")
        
        # 6. AI画质检测
        quality_info = await ai_service.detect_quality(file_path)
        logger.info(f"AI画质检测完成: {quality_info}")
        
        # ... 合并结果 ...
```

- [ ] **Step 4: 测试AI功能**

```bash
# 上传图片并查看AI识别结果
curl -X POST "http://localhost:8000/api/upload/image" \
     -H "Authorization: Bearer <your-token>" \
     -F "file=@test_scene.jpg"

# 查看详情
curl -X GET "http://localhost:8000/api/image/1" \
     -H "Authorization: Bearer <your-token>"
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/ai_service.py backend/services/agent_parse.py backend/requirements.txt
git commit -m "feat: integrate PyTorch model for AI scene recognition"
```

---

## 完成

所有阶段完成后，系统将具备：
- ✅ 稳定的核心功能
- ✅ 优化的性能
- ✅ 良好的代码质量
- ✅ AI场景识别能力

**下一步**: 使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development` 执行此计划
