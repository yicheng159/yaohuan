# 瑶欢党务管理系统

一个基于 Vue.js + Django REST Framework 的前后端分离党务管理系统。

## 功能特性

- 权限管理系统（角色、权限、数据字典）
- 成员管理（成员信息、团务管理、党务管理）
- 活动管理
- 物资管理
- 审批流程管理
- 数据字典自定义

## 技术栈

**前端：**
- Vue 3
- Vue Router 4
- Element Plus
- Vite

**后端：**
- Django 5.0
- Django REST Framework
- PostgreSQL

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- Docker & Docker Compose (可选)

### 使用 Docker Compose 部署（推荐）

1. 克隆项目
```bash
git clone https://github.com/yicheng159/yaohuan.git
cd yaohuan
```

2. 启动服务
```bash
docker-compose up -d
```

3. 访问应用
- 前端：http://localhost
- 后端API：http://localhost:8000/api/
- Django管理后台：http://localhost:8000/admin/

### 手动部署

#### 后端设置

1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，修改相关配置
```

4. 数据库迁移
```bash
python manage.py migrate
```

5. 创建超级用户
```bash
python manage.py createsuperuser
```

6. 启动服务器
```bash
# 开发环境
python manage.py runserver

# 生产环境
gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application
```

#### 前端设置

1. 安装依赖
```bash
cd frontend
npm install
```

2. 开发模式
```bash
npm run dev
```

3. 生产构建
```bash
npm run build
```

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SECRET_KEY | Django密钥 | (必需) |
| DEBUG | 调试模式 | False |
| ALLOWED_HOSTS | 允许的主机 | localhost |
| DATABASE_URL | 数据库连接 | SQLite |
| CORS_ALLOWED_ORIGINS | 允许的CORS来源 | * |

## 默认账户

- 用户名：admin
- 密码：admin123

## 部署到服务器

### Docker 部署

```bash
# 拉取代码
git clone https://github.com/yicheng159/yaohuan.git
cd yaohuan

# 修改环境配置
vim .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### Nginx + Gunicorn 部署

1. 构建前端
```bash
cd frontend
npm install
npm run build
```

2. 配置 Nginx（参考 `frontend/nginx.conf`）

3. 配置 Gunicorn
```bash
gunicorn --bind 0.0.0.0:8000 --workers 3 myproject.wsgi:application
```

## 网络访问说明

部署后，其他电脑可通过以下地址访问：

- `http://服务器IP:端口/` - 前端
- `http://服务器IP:8000/api/` - 后端API
- `http://服务器IP:8000/admin/` - 管理后台

确保服务器防火墙开放相应端口（80, 8000）。

## 项目结构

```
yaohuan/
├── frontend/           # 前端Vue项目
│   ├── src/
│   │   ├── components/  # Vue组件
│   │   ├── views/        # 页面视图
│   │   ├── router/      # 路由配置
│   │   └── utils/        # 工具函数
│   ├── Dockerfile
│   └── nginx.conf
├── management/         # Django应用
│   ├── models.py       # 数据模型
│   ├── views.py        # 视图
│   └── urls.py         # 路由
├── myproject/          # Django项目配置
├── docker-compose.yml  # Docker编排
├── Dockerfile          # 后端Docker配置
└── requirements.txt    # Python依赖
```

## 许可证

MIT License
