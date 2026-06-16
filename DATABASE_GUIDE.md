# 数据库使用说明

## 概述

本系统使用 SQLite 数据库存储所有管理数据，已经过迁移并创建了完整的数据库表结构。

## 数据库位置

数据库文件位于：`e:\1111\db.sqlite3`

## 数据表列表

### 成员管理模块
- **members** - 学生会成员表

### 活动管理模块
- **activities** - 活动信息表

### 物资管理模块
- **materials** - 物资信息表
- **material_borrows** - 物资借用记录表
- **material_borrow_items** - 借用物资明细表

### 团务管理模块
- **league_members** - 团员信息表
- **qingma_classes** - 青马班表
- **qingma_students** - 青马班学员表
- **qingma_courses** - 青马班课程表
- **league_branches** - 团支部表
- **fee_records** - 团费缴费记录表

### 党务管理模块
- **party_members** - 党员信息表
- **activists** - 入党积极分子表
- **cultivation_records** - 培养记录表
- **developing_members** - 发展对象表
- **inspection_records** - 考察记录表
- **probationary_members** - 预备党员表
- **development_applications** - 党员发展申请表
- **approval_records** - 审批记录表

## 使用方法

### 方式一：Django Shell

```bash
cd e:\1111
.\venv\Scripts\python.exe manage.py shell
```

在 shell 中导入 db_utils 模块：

```python
from db_utils import *
```

### 方式二：直接使用 Django ORM

```bash
cd e:\1111
.\venv\Scripts\python.exe manage.py shell
```

#### 基本操作示例

**1. 查询数据**
```python
# 查询所有成员
Member.objects.all()

# 查询单个成员
Member.objects.get(id=1)

# 条件查询
Member.objects.filter(department='主席团')
```

**2. 创建数据**
```python
# 创建成员
Member.objects.create(
    name='张三',
    gender='男',
    student_id='2022001001',
    department='主席团',
    position='主席',
    role='主席团',
    grade='2022级',
    class_name='计算机2022级1班',
    counselor_name='王老师',
    counselor_phone='13912345678',
    phone='13812341234',
    email='zhangsan@stu.edu.cn',
    join_date='2022-09-01',
    status='在职'
)

# 创建活动
Activity.objects.create(
    name='春季运动会',
    type='文体类',
    description='全校春季运动会',
    start_time='2025-04-15 08:00:00',
    end_time='2025-04-15 18:00:00',
    location='操场',
    organizer='体育部',
    leader='李老师',
    participants_count=500,
    status='未开始'
)
```

**3. 更新数据**
```python
# 更新成员
member = Member.objects.get(id=1)
member.position = '副主席'
member.save()
```

**4. 删除数据**
```python
# 删除成员
member = Member.objects.get(id=1)
member.delete()
```

**5. 统计分析**
```python
# 统计成员数量
Member.objects.count()

# 分组统计
from django.db.models import Count
Member.objects.values('department').annotate(count=Count('id'))
```

### 方式三：使用 db_utils 工具函数

```python
from db_utils import *

# 创建成员
create_member(
    name='张三',
    department='主席团',
    position='主席',
    ...
)

# 获取所有成员
get_all_members()

# 统计数据
count_members()
get_statistics()
```

## 数据库管理命令

### 查看所有数据表
```bash
.\venv\Scripts\python.exe manage.py migrate --fake
```

### 重置数据库（谨慎使用）
```bash
.\venv\Scripts\python.exe manage.py flush
```

### 导出数据
```python
import json
from management.models import Member

members = Member.objects.all().values()
data = list(members)

with open('members.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 导入数据
```python
import json
from management.models import Member

with open('members.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    Member.objects.create(**item)
```

## 注意事项

1. **数据备份**：在进行数据库操作前，建议备份数据库文件 `db.sqlite3`
2. **外键关系**：部分表之间存在外键关系，删除时需注意
3. **时间字段**：日期时间字段需要使用正确的格式
4. **唯一字段**：学号等字段设置了唯一约束，不能重复

## 后台管理

系统已配置 Django Admin，可以直接在后台管理数据：

1. 启动服务器：`.\venv\Scripts\python.exe manage.py runserver`
2. 访问后台：`http://127.0.0.1:8000/admin/`
3. 使用超级管理员账号登录

## 数据库迁移

如果需要修改数据模型：

```bash
# 创建迁移文件
.\venv\Scripts\python.exe manage.py makemigrations

# 执行迁移
.\venv\Scripts\python.exe manage.py migrate
```
