# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Image Dataset Agent System (图片数据集智能采集Agent系统) - An automated image dataset collection platform for AI training and research. It handles image upload, multi-dimensional auto-labeling (time, weather, GPS, scene), human review, and dataset export in industry-standard formats (YOLO, COCO, VOC, JSON, CSV).

## Development Commands

### Backend (Python FastAPI)

```bash
cd backend

# Install dependencies (use Tsinghua mirror for China)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests (uses SQLite, no external services needed)
pytest tests/ -v

# Run single test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Frontend (Vue 3 + TypeScript)

```bash
cd frontend

# Install dependencies (use npmmirror for China)
npm install --registry=https://registry.npmmirror.com

# Development server (port 3000, proxies /api to localhost:8000)
npm run dev

# Type check + build
npm run build

# Preview production build
npm run preview
```

### Docker (Full Stack)

```bash
# Start all services (backend, frontend, MySQL, Redis, RabbitMQ, MinIO)
./start.sh

# Stop all services
./stop.sh
```

## Architecture

### Backend (`backend/`)

**Entry point:** `main.py` - FastAPI application with lifespan management

**Layer structure:**
- `routers/` - API endpoints (auth, upload, label, image, dataset)
- `services/` - Business logic (image_service, agent_parse, ai_service, cache_service, queue_service, export_service)
- `database.py` - SQLAlchemy async models and session management
- `config.py` - Pydantic Settings + LabelEnums (all tag dimension enums)
- `utils/` - EXIF parsing, file operations

**Key services:**
- `agent_parse.py` - Core pipeline: EXIF extraction → GPS reverse geocoding → weather lookup → AI scene recognition → quality detection → label generation
- `ai_service.py` - PyTorch ResNet50 for scene classification, OpenCV for quality metrics (Laplacian variance for sharpness, HSV brightness for exposure)
- `cache_service.py` - Redis caching with graceful degradation (works without Redis)

**Configuration:** Environment variables via `.env` file (see `backend/.env.example`). Settings loaded through `pydantic-settings`.

**Database:** MySQL 8.0 with async driver (aiomysql). Models use SQLAlchemy 2.0 declarative style with `DeclarativeBase`.

### Frontend (`frontend/src/`)

**Stack:** Vue 3 + TypeScript + Vite + Element Plus + Pinia + ECharts

**Structure:**
- `api/index.ts` - Axios instance with interceptors (JWT auth, error handling) + all API functions
- `views/` - Page components (Dashboard, Upload, Images, ImageDetail, Review, Dataset, Login)
- `layouts/MainLayout.vue` - Main app shell with sidebar navigation
- `router/index.ts` - Vue Router with auth guard (checks localStorage token)

**UI:** Dark theme by default with CSS custom properties. Supports light/dark theme toggle via `data-theme` attribute.

**Auto-imports:** Element Plus components and APIs are auto-imported via `unplugin-auto-import` and `unplugin-vue-components`.

### Database Schema

Five main tables:
- `sys_user` - Users with roles (admin/editor/viewer)
- `dataset_image` - Image records with status workflow: uploading → parsing → parsed → checking → checked/discarded
- `dataset_label` - Multi-dimensional labels (time, weather, scene, device, GPS, AI results)
- `dataset_version` - Versioned dataset snapshots
- `operation_log` - Audit trail

### Data Flow

1. Upload → file stored in `uploads/temp/`
2. Agent parse pipeline extracts EXIF, GPS, weather, AI scene/quality
3. Labels stored in `dataset_label`, directory path auto-generated from labels
4. Human review: approve → move to `uploads/dataset/{path}/`, reject → move to `uploads/discard/`
5. Export: filter images → generate YOLO/COCO/VOC/JSON/CSV

## Key Design Decisions

- **Async throughout:** FastAPI + SQLAlchemy async + aiomysql. All DB operations use `async/await`.
- **Graceful degradation:** Redis and RabbitMQ are optional. System falls back to no-cache and local task queue.
- **Tests use SQLite:** `backend/tests/conftest.py` overrides DB dependency to use `aiosqlite` - no MySQL needed for testing.
- **Chinese UI:** Element Plus configured with `zh-cn` locale. All labels and enums use Chinese values.
- **Label enums defined in config:** `LabelEnums` class in `config.py` defines all valid tag values. Database uses MySQL ENUM columns matching these values.

## Access Points

- Frontend: http://localhost
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Default credentials: admin / admin123
