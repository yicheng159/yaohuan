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
- Django 4.2
- Django REST Framework
- PostgreSQL

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- Railway CLI (可选)
- Docker & Docker Compose (可选)

### 使用 Railway + Vercel 部署（推荐）

#### 步骤1：部署后端到 Railway

1. 访问 https://railway.app 并登录（推荐使用GitHub账号）

2. 创建新项目：
   - 点击 **New Project** → **Deploy from GitHub repo**
   - 选择 `yicheng159/yaohuan` 仓库

3. 添加 PostgreSQL 数据库：
   - 进入项目 → **Add Plugins** → **PostgreSQL**
   - Railway会自动设置 `DATABASE_URL` 环境变量

4. 配置环境变量：
   - 进入项目 Settings → Environment Variables
   - 添加以下变量：
   ```
   SECRET_KEY=随机密钥（使用随机字符串生成器）
   DEBUG=False
   ALLOWED_HOSTS=*
   ```

5. Railway会自动检测Django并开始部署

6. 记录后端URL（类似 `https://yaohuan-backend.up.railway.app`）

#### 步骤2：部署前端到 Vercel

1. 访问 https://vercel.com 并登录

2. 导入项目：
   - 点击 **Add New** → **Project**
   - 导入 `yicheng159/yaohuan`
   - 设置 Root Directory 为 `frontend`

3. 配置环境变量：
   ```
   VITE_API_BASE_URL=你的Railway后端URL/api
   ```

4. 点击 **Deploy**

5. 记录前端URL（类似 `https://yaohuan.vercel.app`）

#### 步骤3：配置CORS

回到 Railway，在环境变量中添加：
```
CORS_ALLOWED_ORIGINS=https://你的Vercel项目.vercel.app,http://localhost:5173
CSRF_TRUSTED_ORIGINS=https://你的Vercel项目.vercel.app,http://localhost:5173
```

#### 步骤4：创建管理员账户

在 Railway 中打开 Shell 终端：
```bash
python manage.py createsuperuser
```

## 部署后访问地址

| 服务 | 地址 |
|------|------|
| 前端 (Vercel) | https://yaohuan.vercel.app |
| 后端API (Railway) | https://yaohuan-backend.railway.app/api/ |
| Django管理后台 (Railway) | https://yaohuan-backend.railway.app/admin/ |

## 使用 Docker Compose 部署

如果要在自己的服务器上部署：

```bash
git clone https://github.com/yicheng159/yaohuan.git
cd yaohuan
docker-compose up -d
```

## 手动部署

### 后端设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动服务器
python manage.py runserver
```

### 前端设置

```bash
cd frontend
npm install
npm run dev    # 开发模式
npm run build  # 生产构建
```

## 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| SECRET_KEY | Django安全密钥 | 随机字符串 |
| DEBUG | 调试模式 | False |
| ALLOWED_HOSTS | 允许的主机 | * |
| DATABASE_URL | PostgreSQL连接 | 自动由Railway设置 |
| CORS_ALLOWED_ORIGINS | 允许的跨域来源 | 前端URL |

## 默认测试账户

> ⚠️ 部署后请立即修改密码

- 用户名：admin
- 密码：admin123

## 项目结构

```
yaohuan/
├── frontend/              # Vue 3 前端项目
│   ├── src/
│   │   ├── components/     # 公共组件
│   │   ├── views/         # 页面视图
│   │   ├── router/        # 路由配置
│   │   └── utils/         # 工具函数
│   ├── Dockerfile
│   └── nginx.conf
├── management/            # Django 应用
│   ├── models.py          # 数据模型
│   ├── views.py           # 视图逻辑
│   └── urls.py            # 路由定义
├── myproject/             # Django 项目配置
├── docker-compose.yml     # Docker 编排
├── Dockerfile             # 后端 Docker 配置
└── requirements.txt       # Python 依赖
```

## 许可证

MIT License
