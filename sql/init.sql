-- 图片数据集智能采集Agent系统 - 数据库初始化脚本

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS image_dataset
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE image_dataset;

-- 用户表
CREATE TABLE IF NOT EXISTS sys_user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(128) NOT NULL COMMENT '密码哈希',
    nickname VARCHAR(50) COMMENT '昵称',
    email VARCHAR(100) COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    avatar VARCHAR(255) COMMENT '头像URL',
    role ENUM('admin', 'editor', 'viewer') DEFAULT 'viewer' COMMENT '角色',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_login DATETIME COMMENT '最后登录时间',
    INDEX idx_user_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 图片主表
CREATE TABLE IF NOT EXISTS dataset_image (
    id INT PRIMARY KEY AUTO_INCREMENT,
    image_uuid VARCHAR(36) NOT NULL UNIQUE COMMENT '图片UUID',
    original_filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    stored_filename VARCHAR(255) NOT NULL COMMENT '存储文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_size BIGINT NOT NULL COMMENT '文件大小(字节)',
    file_md5 VARCHAR(32) NOT NULL COMMENT '文件MD5',
    file_format VARCHAR(10) NOT NULL COMMENT '文件格式',
    width INT COMMENT '图片宽度',
    height INT COMMENT '图片高度',
    status ENUM('uploading', 'parsing', 'parsed', 'labeling', 'labeled', 'checking', 'checked', 'discarded') DEFAULT 'uploading' COMMENT '状态',
    check_status ENUM('pending', 'checked', 'discard') DEFAULT 'pending' COMMENT '审核状态',
    metadata_json JSON COMMENT '完整元数据JSON',
    dataset_path VARCHAR(500) COMMENT '数据集归档路径',
    uploader_id INT COMMENT '上传者ID',
    checker_id INT COMMENT '审核者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    parsed_at DATETIME COMMENT '解析完成时间',
    checked_at DATETIME COMMENT '审核时间',
    INDEX idx_image_uuid (image_uuid),
    INDEX idx_image_md5 (file_md5),
    INDEX idx_image_status (status),
    INDEX idx_image_check_status (check_status),
    INDEX idx_image_created (created_at),
    INDEX idx_image_uploader (uploader_id),
    FOREIGN KEY (uploader_id) REFERENCES sys_user(id),
    FOREIGN KEY (checker_id) REFERENCES sys_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片主表';

-- 图片标签表
CREATE TABLE IF NOT EXISTS dataset_label (
    id INT PRIMARY KEY AUTO_INCREMENT,
    image_id INT NOT NULL UNIQUE COMMENT '图片ID',
    year INT COMMENT '年',
    month INT COMMENT '月',
    day INT COMMENT '日',
    hour INT COMMENT '小时',
    season ENUM('春', '夏', '秋', '冬') COMMENT '季节',
    time_period ENUM('凌晨', '上午', '中午', '下午', '傍晚', '夜晚') COMMENT '时段',
    day_type ENUM('工作日', '节假日') COMMENT '工作日/节假日',
    weather ENUM('晴', '多云', '阴', '小雨', '大雨', '雾', '雪', '沙尘') COMMENT '天气',
    temperature FLOAT COMMENT '温度(℃)',
    humidity FLOAT COMMENT '湿度(%)',
    light ENUM('强光', '正常', '弱光', '逆光') COMMENT '光照',
    shoot_angle ENUM('俯拍', '平视', '仰拍') COMMENT '拍摄角度',
    scene_scale ENUM('远景', '中景', '近景', '特写') COMMENT '画面景别',
    clarity ENUM('清晰', '轻微模糊', '严重模糊') COMMENT '清晰度',
    exposure ENUM('正常', '过曝', '欠曝') COMMENT '曝光',
    scene_type ENUM('城区', '乡村', '道路', '厂区', '田野', '室内', '山区', '水域', '森林', '沙漠', '雪地', '其他') COMMENT '场景类型',
    device_type ENUM('手机', '工业相机', '单反', '无人机', '监控', '其他') COMMENT '设备类型',
    device_brand VARCHAR(50) COMMENT '设备品牌',
    device_model VARCHAR(100) COMMENT '设备型号',
    longitude FLOAT COMMENT '经度',
    latitude FLOAT COMMENT '纬度',
    province VARCHAR(50) COMMENT '省',
    city VARCHAR(50) COMMENT '市',
    district VARCHAR(50) COMMENT '区',
    address VARCHAR(255) COMMENT '详细地址',
    ai_scene_labels JSON COMMENT 'AI场景识别标签',
    ai_objects JSON COMMENT 'AI物体识别结果',
    ai_quality_score FLOAT COMMENT 'AI画质评分',
    source ENUM('auto', 'manual', 'mixed') DEFAULT 'auto' COMMENT '标签来源',
    creator_id INT COMMENT '创建/修改者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_label_season (season),
    INDEX idx_label_weather (weather),
    INDEX idx_label_scene (scene_type),
    INDEX idx_label_location (province, city),
    FOREIGN KEY (image_id) REFERENCES dataset_image(id) ON DELETE CASCADE,
    FOREIGN KEY (creator_id) REFERENCES sys_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片标签表';

-- 数据集版本表
CREATE TABLE IF NOT EXISTS dataset_version (
    id INT PRIMARY KEY AUTO_INCREMENT,
    version_name VARCHAR(50) NOT NULL COMMENT '版本名称',
    version_code VARCHAR(20) NOT NULL UNIQUE COMMENT '版本号',
    description TEXT COMMENT '版本描述',
    total_images INT DEFAULT 0 COMMENT '总图片数',
    total_labels INT DEFAULT 0 COMMENT '总标签数',
    label_distribution JSON COMMENT '标签分布统计',
    filter_conditions JSON COMMENT '筛选条件',
    export_format ENUM('yolo', 'coco', 'voc', 'json', 'csv') COMMENT '导出格式',
    export_path VARCHAR(500) COMMENT '导出文件路径',
    export_size BIGINT COMMENT '导出文件大小',
    status ENUM('creating', 'ready', 'exported', 'archived') DEFAULT 'creating' COMMENT '状态',
    creator_id INT COMMENT '创建者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_version_status (status),
    INDEX idx_version_created (created_at),
    FOREIGN KEY (creator_id) REFERENCES sys_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据集版本表';

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT COMMENT '操作者ID',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    target_type VARCHAR(50) COMMENT '目标类型',
    target_id INT COMMENT '目标ID',
    detail JSON COMMENT '操作详情',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_log_action (action),
    INDEX idx_log_created (created_at),
    FOREIGN KEY (user_id) REFERENCES sys_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- 插入默认管理员用户（密码: admin123）
INSERT INTO sys_user (username, password_hash, nickname, role) VALUES
('admin', '$2b$12$LJ3m4ys3Lz0YBNOURq0Y3OjCfKJmKPOJYqDTPVCKzLOBhZMHfW7K.', '系统管理员', 'admin')
ON DUPLICATE KEY UPDATE username=username;
