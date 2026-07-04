# 图片数据集智能采集Agent系统

面向AI训练、科研场景的全自动结构化图片数据集采集Agent，实现图片上传、自动多维度打标、智能分类归档、人工校验、数据集导出、版本管理全流程自动化。

## 核心特性

- **AI自动识别标签** - 时间、季节、天气、地理位置、拍摄角度、光照、画质、场景全自动解析
- **人工审核纠错** - 支持单张/批量改标、标签审核、样本废弃
- **标准化层级目录存储** - 根据标签自动生成规范目录，无需人工整理
- **全链路溯源** - 记录上传、解析、修改、审核全日志
- **行业标准数据集导出** - 支持YOLO、COCO、VOC、JSON、CSV格式

## 技术栈

### 后端
- Python FastAPI
- SQLAlchemy (异步ORM)
- Redis (缓存)
- RabbitMQ (消息队列)
- MinIO (对象存储)
- Pillow + ExifRead (图像处理)

### 前端
- Vue 3 + TypeScript
- Vite
- Element Plus
- ECharts

### 数据库
- MySQL 8.0
- Redis 7

## 快速开始

### 方式一：Docker Compose (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd image-dataset-agent

# 启动所有服务
chmod +x start.sh
./start.sh
```

### 方式二：手动启动

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库等信息

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install --registry=https://registry.npmmirror.com

# 启动开发服务器
npm run dev
```

## 访问地址

- 前端: http://localhost
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- RabbitMQ管理: http://localhost:15672
- MinIO控制台: http://localhost:9001

## 默认账号

- 用户名: admin
- 密码: admin123

## 项目结构

```
image-dataset-agent/
├── backend/                # 后端服务
│   ├── main.py            # 主入口
│   ├── config.py          # 配置文件
│   ├── database.py        # 数据库模型
│   ├── routers/           # API路由
│   ├── services/          # 业务服务
│   ├── utils/             # 工具类
│   └── requirements.txt   # Python依赖
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── api/          # API接口
│   │   ├── layouts/      # 布局组件
│   │   ├── views/        # 页面组件
│   │   └── router/       # 路由配置
│   └── package.json      # Node依赖
├── sql/                   # 数据库脚本
├── docker-compose.yml     # Docker配置
└── README.md              # 项目说明
```

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看Swagger API文档。

### 主要接口

- `POST /api/auth/login` - 用户登录
- `POST /api/upload/image` - 上传图片
- `POST /api/upload/batch` - 批量上传
- `GET /api/image/list` - 获取图片列表
- `POST /api/image/check` - 审核图片
- `PUT /api/label/update` - 更新标签
- `POST /api/dataset/export` - 导出数据集

## 数据库设计

### 主要表

- `sys_user` - 用户表
- `dataset_image` - 图片主表
- `dataset_label` - 图片标签表
- `dataset_version` - 数据集版本表
- `operation_log` - 操作日志表

## 标签维度

### 时间维度
- 年、月、日、小时
- 季节（春/夏/秋/冬）
- 时段（凌晨/上午/中午/下午/傍晚/夜晚）
- 工作日/节假日

### 环境天气
- 天气类型（晴/多云/阴/小雨/大雨/雾/雪/沙尘）
- 温度、湿度
- 光照（强光/正常/弱光/逆光）

### 拍摄维度
- 拍摄角度（俯拍/平视/仰拍）
- 画面景别（远景/中景/近景/特写）
- 清晰度（清晰/轻微模糊/严重模糊）
- 曝光（正常/过曝/欠曝）

### 场景设备
- 场景类型（城区/乡村/道路/厂区/田野/室内等）
- 设备类型（手机/工业相机/单反/无人机/监控）
- GPS地理位置（省市区街道）

## 许可证

MIT License
