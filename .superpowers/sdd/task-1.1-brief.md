# Task 1.1: 环境搭建与依赖检查

## 任务描述

创建环境配置文件，检查依赖，验证环境

## 文件清单

- Create: `backend/.env`
- Modify: `backend/requirements.txt`

## 步骤

### Step 1: 创建环境配置文件

创建 `backend/.env` 文件，内容如下：

```bash
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
```

### Step 2: 检查依赖文件

1. 查看 `backend/requirements.txt` 文件
2. 安装依赖：`cd backend && pip install -r requirements.txt`

### Step 3: 验证环境

1. 测试Python环境：`python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"`
2. 测试数据库连接（如果MySQL已启动）：`python -c "import pymysql; conn = pymysql.connect(host='localhost', user='root', password='your_password'); print('MySQL连接成功'); conn.close()"`

### Step 4: Commit

```bash
git add backend/.env
git commit -m "chore: add environment configuration"
```

## 验收标准

1. `backend/.env` 文件已创建，包含所有必要的环境变量
2. 依赖已安装，没有导入错误
3. Python环境正常，FastAPI可以导入
4. 数据库连接测试通过（如果MySQL已启动）

## 注意事项

- 如果MySQL未启动，数据库连接测试可以跳过
- 确保 `backend/.env` 文件不被提交到git（添加到 `.gitignore`）
- 如果 `requirements.txt` 中缺少依赖，需要补充
