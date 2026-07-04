# 图片数据集智能采集Agent系统 - 设计文档

## 1. 项目概述

### 1.1 系统定位
面向AI训练、科研场景的全自动结构化图片数据集采集Agent，实现图片上传、自动多维度打标、智能分类归档、人工校验、数据集导出、版本管理全流程自动化。

### 1.2 核心特性
- AI自动识别标签
- 人工审核纠错
- 标准化层级目录存储
- 全链路溯源
- 行业标准数据集导出

### 1.3 技术栈
| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue3 + Vite + Element Plus | Vue 3.4+ |
| 后端 | Python FastAPI | 0.109+ |
| 数据库 | MySQL | 8.0 |
| 缓存 | Redis | 7 |
| 消息队列 | RabbitMQ | 3.x |
| AI模型 | PyTorch + torchvision | 2.x |

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (80端口)                        │
│                    前端静态资源 + API反向代理                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务 (8000)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 上传服务  │ │ 标签服务  │ │ 审核服务  │ │ 导出服务  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │  MySQL   │   │  Redis   │   │ RabbitMQ │
        │  业务数据 │   │  缓存    │   │ 任务队列  │
        └──────────┘   └──────────┘   └──────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent 智能解析服务                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ EXIF解析  │ │ GPS逆编码 │ │ 天气匹配  │ │ 场景识别  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 四层架构
1. **接入层**：前端页面、文件上传接口、权限校验
2. **业务层**：上传服务、标签管理、审核服务、数据集导出服务
3. **Agent智能层**：EXIF解析、地理逆编码、历史天气匹配、图像质量检测、场景识别
4. **存储层**：本地文件系统、MySQL、Redis缓存

## 3. 数据库设计

### 3.1 用户表 sys_user
```sql
CREATE TABLE sys_user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    nickname VARCHAR(50),
    email VARCHAR(100),
    role ENUM('admin', 'editor', 'viewer') DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3.2 图片主表 dataset_image
```sql
CREATE TABLE dataset_image (
    id INT PRIMARY KEY AUTO_INCREMENT,
    image_uuid VARCHAR(36) NOT NULL UNIQUE,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_md5 VARCHAR(32) NOT NULL,
    file_format VARCHAR(10) NOT NULL,
    width INT,
    height INT,
    status ENUM('uploading', 'parsing', 'parsed', 'checked', 'discarded') DEFAULT 'uploading',
    check_status ENUM('pending', 'checked', 'discard') DEFAULT 'pending',
    metadata_json JSON,
    dataset_path VARCHAR(500),
    uploader_id INT,
    checker_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    parsed_at DATETIME,
    checked_at DATETIME,
    FOREIGN KEY (uploader_id) REFERENCES sys_user(id),
    FOREIGN KEY (checker_id) REFERENCES sys_user(id)
);
```

### 3.3 图片标签表 dataset_label
```sql
CREATE TABLE dataset_label (
    id INT PRIMARY KEY AUTO_INCREMENT,
    image_id INT NOT NULL UNIQUE,
    -- 时间维度
    year INT,
    month INT,
    day INT,
    hour INT,
    season ENUM('春', '夏', '秋', '冬'),
    time_period ENUM('凌晨', '上午', '中午', '下午', '傍晚', '夜晚'),
    day_type ENUM('工作日', '节假日'),
    -- 环境天气
    weather ENUM('晴', '多云', '阴', '小雨', '大雨', '雾', '雪', '沙尘'),
    temperature FLOAT,
    humidity FLOAT,
    light ENUM('强光', '正常', '弱光', '逆光'),
    -- 拍摄维度
    shoot_angle ENUM('俯拍', '平视', '仰拍'),
    scene_scale ENUM('远景', '中景', '近景', '特写'),
    clarity ENUM('清晰', '轻微模糊', '严重模糊'),
    exposure ENUM('正常', '过曝', '欠曝'),
    -- 场景设备
    scene_type ENUM('城区', '乡村', '道路', '厂区', '田野', '室内', '山区', '水域', '森林', '沙漠', '雪地', '其他'),
    device_type ENUM('手机', '工业相机', '单反', '无人机', '监控', '其他'),
    -- 地理位置
    longitude FLOAT,
    latitude FLOAT,
    province VARCHAR(50),
    city VARCHAR(50),
    district VARCHAR(50),
    address VARCHAR(255),
    -- AI识别结果
    ai_scene_labels JSON,
    ai_objects JSON,
    ai_quality_score FLOAT,
    -- 元信息
    source ENUM('auto', 'manual', 'mixed') DEFAULT 'auto',
    creator_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES dataset_image(id) ON DELETE CASCADE,
    FOREIGN KEY (creator_id) REFERENCES sys_user(id)
);
```

### 3.4 数据集版本表 dataset_version
```sql
CREATE TABLE dataset_version (
    id INT PRIMARY KEY AUTO_INCREMENT,
    version_name VARCHAR(50) NOT NULL,
    version_code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    total_images INT DEFAULT 0,
    export_format ENUM('yolo', 'coco', 'voc', 'json', 'csv'),
    export_path VARCHAR(500),
    status ENUM('creating', 'ready', 'exported', 'archived') DEFAULT 'creating',
    creator_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES sys_user(id)
);
```

## 4. API设计

### 4.1 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户

### 4.2 上传接口
- `POST /api/upload/image` - 单张上传
- `POST /api/upload/batch` - 批量上传

### 4.3 标签接口
- `GET /api/label/enums` - 获取枚举值
- `GET /api/label/{image_id}` - 获取标签
- `PUT /api/label/update` - 更新标签

### 4.4 图片接口
- `GET /api/image/list` - 图片列表
- `GET /api/image/{id}` - 图片详情
- `POST /api/image/check` - 审核图片
- `DELETE /api/image/{id}` - 删除图片

### 4.5 数据集接口
- `GET /api/dataset/versions` - 版本列表
- `POST /api/dataset/export` - 导出数据集
- `GET /api/dataset/stats` - 统计信息

## 5. Agent智能解析流程

### 5.1 解析流程
```
用户上传图片
    ↓
保存到临时目录
    ↓
发送到RabbitMQ队列
    ↓
Agent消费任务
    ↓
┌─────────────────────────────────────┐
│ 1. EXIF解析                         │
│    - 拍摄时间、相机参数、GPS经纬度    │
├─────────────────────────────────────┤
│ 2. 时间维度解析                      │
│    - 季节、时段、工作日/节假日        │
├─────────────────────────────────────┤
│ 3. GPS逆编码                        │
│    - 省、市、区、详细地址             │
├─────────────────────────────────────┤
│ 4. 天气匹配                         │
│    - 调用历史天气API                  │
│    - 天气类型、温度、湿度             │
├─────────────────────────────────────┤
│ 5. 图像质量检测                      │
│    - 清晰度（拉普拉斯方差）           │
│    - 曝光（亮度均值）                 │
├─────────────────────────────────────┤
│ 6. 场景识别（PyTorch）               │
│    - 预训练模型识别场景               │
│    - 生成视觉标签                     │
├─────────────────────────────────────┤
│ 7. 生成标准化标签                     │
│    - 写入数据库                       │
│    - 生成元数据JSON                   │
│    - 移动到归档目录                   │
└─────────────────────────────────────┘
```

### 5.2 目录归档规则
```
uploads/dataset/
├── 2026/
│   ├── 07/
│   │   ├── 夏_上午/
│   │   │   ├── 晴/
│   │   │   │   ├── 城区/
│   │   │   │   │   ├── image001.jpg
│   │   │   │   │   └── image001.json
```

## 6. 前端页面设计

### 6.1 页面结构
- 登录页
- 主布局（侧边栏 + 内容区）
  - 数据看板
  - 图片上传
  - 图片管理
  - 人工审核
  - 数据集管理

### 6.2 UI设计原则
使用 `frontend-design` 技能，选择：
- **风格**：科技感 + 专业感
- **配色**：深色主题 + 蓝色点缀
- **字体**：现代感无衬线字体
- **动画**：流畅的过渡效果

## 7. Docker部署

### 7.1 服务组成
| 服务 | 镜像 | 端口 |
|------|------|------|
| frontend | nginx:alpine | 80 |
| backend | python:3.11-slim | 8000 |
| mysql | mysql:8.0 | 3306 |
| redis | redis:7-alpine | 6379 |
| rabbitmq | rabbitmq:3-management | 5672, 15672 |

### 7.2 启动命令
```bash
docker-compose up -d
```

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

### 8.3 安全验收
- [ ] 文件格式校验
- [ ] MD5去重
- [ ] JWT认证
- [ ] 权限分级

---

**设计文档已完成，请审查。有需要修改的地方吗？**
