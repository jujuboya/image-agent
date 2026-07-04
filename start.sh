#!/bin/bash

# 图片数据集智能采集Agent系统 - 启动脚本

echo "==================================="
echo "图片数据集智能采集Agent系统"
echo "==================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装Docker，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未安装Docker Compose，请先安装Docker Compose"
    exit 1
fi

# 创建必要的目录
mkdir -p backend/uploads/temp
mkdir -p backend/uploads/dataset
mkdir -p backend/uploads/discard
mkdir -p backend/uploads/export

echo "正在启动服务..."
echo ""

# 启动所有服务
docker-compose up -d

echo ""
echo "==================================="
echo "服务启动完成！"
echo "==================================="
echo ""
echo "访问地址:"
echo "  - 前端: http://localhost"
echo "  - 后端API: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - RabbitMQ管理: http://localhost:15672"
echo "  - MinIO控制台: http://localhost:9001"
echo ""
echo "默认管理员账号:"
echo "  - 用户名: admin"
echo "  - 密码: admin123"
echo ""
echo "==================================="
