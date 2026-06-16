# API接口使用说明

## 概述

本系统提供完整的REST API接口，供Vue前端网站调用，支持所有管理模块的增删改查操作。

## API基础信息

- **基础URL**：`http://127.0.0.1:8000/api/`
- **数据格式**：JSON
- **认证方式**：无需认证（开发环境）
- **跨域支持**：已配置CORS

## API端点列表

### 成员管理模块

#### 学生会成员
- **列表**：`GET /api/members/`
- **详情**：`GET /api/members/{id}/`
- **创建**：`POST /api/members/`
- **更新**：`PUT /api/members/{id}/`
- **部分更新**：`PATCH /api/members/{id}/`
- **删除**：`DELETE /api/members/{id}/`
- **统计**：`GET /api/members/statistics/`

**查询参数**：
- `department`：按部门筛选
- `status`：按状态筛选（在职/离职）
- `search`：搜索（姓名、部门、电话）

**创建示例**：
```json
POST /api/members/
{
    "name": "张三",
    "gender": "男",
    "student_id": "2022001001",
    "department": "主席团",
    "position": "主席",
    "role": "主席团",
    "grade": "2022级",
    "class_name": "计算机2022级1班",
    "counselor_name": "王老师",
    "counselor_phone": "13912345678",
    "phone": "13812341234",
    "email": "zhangsan@stu.edu.cn",
    "join_date": "2022-09-01",
    "status": "在职"
}
```

### 活动管理模块

#### 活动
- **列表**：`GET /api/activities/`
- **详情**：`GET /api/activities/{id}/`
- **创建**：`POST /api/activities/`
- **更新**：`PUT /api/activities/{id}/`
- **删除**：`DELETE /api/activities/{id}/`
- **统计**：`GET /api/activities/statistics/`

**查询参数**：
- `type`：按类型筛选（文体类/学术类/公益类/交流类/其他）
- `status`：按状态筛选（未开始/进行中/已结束）
- `search`：搜索（活动名称）

**创建示例**：
```json
POST /api/activities/
{
    "name": "春季运动会",
    "type": "文体类",
    "description": "全校春季运动会",
    "start_time": "2025-04-15T08:00:00Z",
    "end_time": "2025-04-15T18:00:00Z",
    "location": "操场",
    "organizer": "体育部",
    "leader": "李老师",
    "participants_count": 500,
    "status": "未开始"
}
```

### 物资管理模块

#### 物资
- **列表**：`GET /api/materials/`
- **详情**：`GET /api/materials/{id}/`
- **创建**：`POST /api/materials/`
- **更新**：`PUT /api/materials/{id}/`
- **删除**：`DELETE /api/materials/{id}/`
- **统计**：`GET /api/materials/statistics/`

#### 物资借用
- **列表**：`GET /api/material-borrows/`
- **详情**：`GET /api/material-borrows/{id}/`
- **创建**：`POST /api/material-borrows/`
- **更新**：`PUT /api/material-borrows/{id}/`
- **删除**：`DELETE /api/material-borrows/{id}/`
- **归还**：`POST /api/material-borrows/{id}/return_borrow/`

### 团务管理模块

#### 团员
- **列表**：`GET /api/league-members/`
- **详情**：`GET /api/league-members/{id}/`
- **创建**：`POST /api/league-members/`
- **更新**：`PUT /api/league-members/{id}/`
- **删除**：`DELETE /api/league-members/{id}/`
- **统计**：`GET /api/league-members/statistics/`

#### 青马班
- **列表**：`GET /api/qingma-classes/`
- **详情**：`GET /api/qingma-classes/{id}/`
- **创建**：`POST /api/qingma-classes/`
- **更新**：`PUT /api/qingma-classes/{id}/`
- **删除**：`DELETE /api/qingma-classes/{id}/`
- **统计**：`GET /api/qingma-classes/statistics/`

#### 青马班学员
- **列表**：`GET /api/qingma-students/`
- **详情**：`GET /api/qingma-students/{id}/`
- **创建**：`POST /api/qingma-students/`
- **更新**：`PUT /api/qingma-students/{id}/`
- **删除**：`DELETE /api/qingma-students/{id}/`
- **统计**：`GET /api/qingma-students/statistics/`

#### 青马班课程
- **列表**：`GET /api/qingma-courses/`
- **详情**：`GET /api/qingma-courses/{id}/`
- **创建**：`POST /api/qingma-courses/`
- **更新**：`PUT /api/qingma-courses/{id}/`
- **删除**：`DELETE /api/qingma-courses/{id}/`

#### 团支部
- **列表**：`GET /api/league-branches/`
- **详情**：`GET /api/league-branches/{id}/`
- **创建**：`POST /api/league-branches/`
- **更新**：`PUT /api/league-branches/{id}/`
- **删除**：`DELETE /api/league-branches/{id}/`
- **批量缴费**：`POST /api/league-branches/{id}/batch_pay/`

#### 团费记录
- **列表**：`GET /api/fee-records/`
- **详情**：`GET /api/fee-records/{id}/`
- **创建**：`POST /api/fee-records/`
- **更新**：`PUT /api/fee-records/{id}/`
- **删除**：`DELETE /api/fee-records/{id}/`

### 党务管理模块

#### 党员
- **列表**：`GET /api/party-members/`
- **详情**：`GET /api/party-members/{id}/`
- **创建**：`POST /api/party-members/`
- **更新**：`PUT /api/party-members/{id}/`
- **删除**：`DELETE /api/party-members/{id}/`
- **统计**：`GET /api/party-members/statistics/`

#### 入党积极分子
- **列表**：`GET /api/activists/`
- **详情**：`GET /api/activists/{id}/`
- **创建**：`POST /api/activists/`
- **更新**：`PUT /api/activists/{id}/`
- **删除**：`DELETE /api/activists/{id}/`
- **统计**：`GET /api/activists/statistics/`

#### 培养记录
- **列表**：`GET /api/cultivation-records/`
- **详情**：`GET /api/cultivation-records/{id}/`
- **创建**：`POST /api/cultivation-records/`
- **更新**：`PUT /api/cultivation-records/{id}/`
- **删除**：`DELETE /api/cultivation-records/{id}/`

#### 发展对象
- **列表**：`GET /api/developing-members/`
- **详情**：`GET /api/developing-members/{id}/`
- **创建**：`POST /api/developing-members/`
- **更新**：`PUT /api/developing-members/{id}/`
- **删除**：`DELETE /api/developing-members/{id}/`
- **统计**：`GET /api/developing-members/statistics/`

#### 考察记录
- **列表**：`GET /api/inspection-records/`
- **详情**：`GET /api/inspection-records/{id}/`
- **创建**：`POST /api/inspection-records/`
- **更新**：`PUT /api/inspection-records/{id}/`
- **删除**：`DELETE /api/inspection-records/{id}/`

#### 预备党员
- **列表**：`GET /api/probationary-members/`
- **详情**：`GET /api/probationary-members/{id}/`
- **创建**：`POST /api/probationary-members/`
- **更新**：`PUT /api/probationary-members/{id}/`
- **删除**：`DELETE /api/probationary-members/{id}/`
- **提交转正**：`POST /api/probationary-members/{id}/submit_regularization/`
- **审批转正**：`POST /api/probationary-members/{id}/approve_regularization/`
- **统计**：`GET /api/probationary-members/statistics/`

#### 党员发展申请
- **列表**：`GET /api/development-applications/`
- **详情**：`GET /api/development-applications/{id}/`
- **创建**：`POST /api/development-applications/`
- **更新**：`PUT /api/development-applications/{id}/`
- **删除**：`DELETE /api/development-applications/{id}/`
- **审批通过**：`POST /api/development-applications/{id}/approve/`
- **审批拒绝**：`POST /api/development-applications/{id}/reject/`
- **统计**：`GET /api/development-applications/statistics/`

#### 审批记录
- **列表**：`GET /api/approval-records/`
- **详情**：`GET /api/approval-records/{id}/`
- **创建**：`POST /api/approval-records/`
- **更新**：`PUT /api/approval-records/{id}/`
- **删除**：`DELETE /api/approval-records/{id}/`

## Vue前端调用示例

### 使用fetch

```javascript
// 获取成员列表
const response = await fetch('http://127.0.0.1:8000/api/members/');
const data = await response.json();

// 创建成员
const response = await fetch('http://127.0.0.1:8000/api/members/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        name: '张三',
        gender: '男',
        student_id: '2022001001',
        department: '主席团',
        position: '主席',
        role: '主席团',
        grade: '2022级',
        class_name: '计算机2022级1班',
        counselor_name: '王老师',
        counselor_phone: '13912345678',
        phone: '13812341234',
        email: 'zhangsan@stu.edu.cn',
        join_date: '2022-09-01',
        status: '在职'
    })
});
const result = await response.json();

// 更新成员
const response = await fetch('http://127.0.0.1:8000/api/members/1/', {
    method: 'PUT',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        ...memberData,
        position: '副主席'
    })
});

// 删除成员
await fetch('http://127.0.0.1:8000/api/members/1/', {
    method: 'DELETE'
});

// 获取统计数据
const response = await fetch('http://127.0.0.1:8000/api/members/statistics/');
const stats = await response.json();
```

### 使用axios

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    timeout: 10000
});

// 获取成员列表
const { data } = await api.get('/members/');

// 创建成员
const { data } = await api.post('/members/', {
    name: '张三',
    gender: '男',
    student_id: '2022001001',
    department: '主席团',
    // ...
});

// 获取统计数据
const { data } = await api.get('/members/statistics/');
```

## 响应格式

### 成功响应
```json
{
    "id": 1,
    "name": "张三",
    "gender": "男",
    "student_id": "2022001001",
    "department": "主席团",
    "position": "主席",
    "role": "主席团",
    "grade": "2022级",
    "class_name": "计算机2022级1班",
    "counselor_name": "王老师",
    "counselor_phone": "13912345678",
    "phone": "13812341234",
    "email": "zhangsan@stu.edu.cn",
    "join_date": "2022-09-01",
    "status": "在职",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
}
```

### 列表响应（分页）
```json
{
    "count": 100,
    "next": "http://127.0.0.1:8000/api/members/?page=2",
    "previous": null,
    "results": [
        { /* 成员数据 */ }
    ]
}
```

### 错误响应
```json
{
    "name": ["这个字段是必填项。"],
    "student_id": ["学号已存在。"]
}
```

## 注意事项

1. **日期格式**：使用 ISO 8601 格式（YYYY-MM-DDTHH:MM:SSZ）
2. **学号唯一性**：学号字段在成员表中是唯一的，不能重复
3. **外键关系**：创建学员等数据时，需要先创建父级数据（如青马班）
4. **自动更新**：部分操作会自动更新关联数据（如创建借用记录会减少库存）
5. **分页**：列表API默认每页20条数据
6. **CORS**：已配置允许所有来源（开发环境）

## 测试API

启动服务器后，可以访问以下地址测试API：
- API根地址：http://127.0.0.1:8000/api/
- Django Admin：http://127.0.0.1:8000/admin/
