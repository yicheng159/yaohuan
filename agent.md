# Django + Vue 项目 Agent 文档

## 项目概述

这是一个基于 Django 4.x 和 Vue 3.x 的全栈 Web 应用项目，采用前后端分离架构，集成了 SimpleUI 后台管理系统。

## 技术栈

### 后端
- **框架**: Django 4.2.30
- **后台管理**: SimpleUI
- **数据库**: SQLite3
- **Python**: 3.8+

### 前端
- **框架**: Vue 3.5.34
- **构建工具**: Vite 8.0.12
- **插件**: @vitejs/plugin-vue 6.0.6

## 项目结构

```
e:\1111/
├── frontend/                      # Vue 前端项目
│   ├── src/
│   │   ├── App.vue               # 主应用组件
│   │   ├── main.js               # 入口文件
│   │   ├── components/           # Vue 组件
│   │   └── assets/               # 静态资源
│   ├── vite.config.js            # Vite 配置
│   └── package.json              # 前端依赖
├── myproject/                     # Django 项目目录
│   ├── settings.py               # Django 配置文件
│   ├── urls.py                   # URL 路由配置
│   ├── views.py                  # 视图函数
│   └── static/
│       └── dist/                 # Vue 构建输出目录
├── myapp/                         # Django 应用
├── venv/                          # Python 虚拟环境
├── manage.py                      # Django 管理脚本
└── db.sqlite3                     # SQLite 数据库
```

## 核心文件说明

### 后端配置

**[myproject/settings.py](file:///e:\1111\myproject\settings.py)**
- `INSTALLED_APPS`: 包含 'simpleui' 和 Django 内置应用
- `TEMPLATES`: 模板目录指向 `myproject/static/dist`
- `STATICFILES_DIRS`: 静态文件目录配置
- `LANGUAGE_CODE`: 已设置为 'zh-hans'（中文）

**[myproject/urls.py](file:///e:\1111\myproject\urls.py)**
- `/admin/`: Django 后台管理路由
- `''` 和 `re_path(r'^.*$')`: 所有其他路由指向 Vue 前端

### 前端配置

**[frontend/vite.config.js](file:///e:\1111\frontend\vite.config.js)**
- `build.outDir`: 构建输出到 `../myproject/static/dist`
- `server.proxy`: 配置代理，将 `/api`、`/admin`、`/static` 请求代理到后端 8000 端口

**[frontend/src/App.vue](file:///e:\1111\frontend\src\App.vue)**
- 主应用组件，包含首页布局
- 展示项目核心功能卡片
- 提供后台管理入口链接

## 开发环境搭建

### 后端环境

1. **激活虚拟环境**
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat
```

2. **启动 Django 服务**
```bash
python manage.py runserver
```

服务将在 http://localhost:8000 启动

### 前端环境

1. **进入前端目录**
```bash
cd frontend
```

2. **安装依赖**
```bash
npm install
```

3. **开发模式启动**
```bash
npm run dev
```

开发服务器将在 http://localhost:5173 启动

4. **构建生产版本**
```bash
npm run build
```

构建产物将输出到 `../myproject/static/dist`

## 后台管理

### 访问地址
http://localhost:8000/admin

### 超级管理员账号
- 用户名: `admin`
- 密码: `yhxsh`
- 邮箱: `2111292662@qq.com`

### 功能特性
- SimpleUI 美化界面
- 中文语言支持
- 用户认证和权限管理

## 开发工作流

### 前端开发

1. 在 `frontend/src/` 目录下修改 Vue 组件
2. 运行 `npm run dev` 实时预览
3. 满意后运行 `npm run build` 构建
4. 刷新浏览器 http://localhost:8000 查看更新

### 后端开发

1. 在 `myapp/` 目录下添加模型、视图等
2. 运行 `python manage.py makemigrations` 创建迁移
3. 运行 `python manage.py migrate` 应用迁移
4. Django 开发服务器会自动重载

## 常用命令

### Django 命令
```bash
# 创建超级用户
python manage.py createsuperuser

# 创建数据库迁移
python manage.py makemigrations

# 应用数据库迁移
python manage.py migrate

# 启动开发服务器
python manage.py runserver

# 进入 Django Shell
python manage.py shell
```

### 前端命令
```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 部署说明

### 静态文件配置

当前开发环境配置：
- `DEBUG = True`
- 静态文件通过 Django 开发服务器提供

生产环境建议：
1. 设置 `DEBUG = False`
2. 配置 `ALLOWED_HOSTS`
3. 使用 Nginx 或 CDN 提供静态文件
4. 配置 `STATIC_ROOT` 并运行 `collectstatic`

### 数据库

当前使用 SQLite 数据库，适合开发和小型应用。生产环境建议：
- PostgreSQL
- MySQL
- MariaDB

## 注意事项

1. **SECRET_KEY**: 生产环境请更换为强随机密钥
2. **DEBUG**: 生产环境必须设为 False
3. **数据库迁移**: 修改模型后记得创建和应用迁移
4. **前端构建**: 修改 Vue 代码后需要重新构建才能在 Django 中看到效果
5. **虚拟环境**: 始终在激活的虚拟环境中运行后端命令

## 相关文档

- [Django 官方文档](https://docs.djangoproject.com/)
- [Vue 3 官方文档](https://cn.vuejs.org/)
- [Vite 官方文档](https://cn.vitejs.dev/)
- [SimpleUI 文档](https://simpleui.72wo.com/)
