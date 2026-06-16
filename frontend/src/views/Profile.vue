<script setup>
import { ref } from 'vue';

const user = ref({
  name: '张三',
  avatar: '👤',
  department: '计算机学院',
  grade: '2022级',
  position: '学生会主席',
  phone: '138****1234',
  email: 'zhangsan@stu.edu.cn',
  joinDate: '2022-09-01',
  status: '在职',
  role: '主席团'
});

const editMode = ref(false);

const toggleEdit = () => {
  editMode.value = !editMode.value;
};

const saveProfile = () => {
  editMode.value = false;
};

const resetPassword = () => {
  alert('密码重置功能');
};
</script>

<template>
  <div class="profile-page">
    <header class="page-header">
      <h1>个人信息</h1>
    </header>
    
    <div class="profile-container">
      <div class="profile-card">
        <div class="profile-header">
          <div class="avatar-section">
            <span class="avatar-large">{{ user.avatar }}</span>
            <button class="upload-btn">更换头像</button>
          </div>
          <div class="basic-info">
            <h2 class="user-name">{{ user.name }}</h2>
            <div class="user-role">{{ user.department }} · {{ user.grade }}</div>
            <div class="user-position">{{ user.position }}</div>
          </div>
          <div class="action-buttons">
            <button class="btn btn-primary" @click="toggleEdit">
              {{ editMode ? '取消' : '编辑资料' }}
            </button>
            <button class="btn btn-secondary" @click="resetPassword">修改密码</button>
          </div>
        </div>
        
        <div class="profile-content">
          <div class="info-section">
            <h3 class="section-title">基本信息</h3>
            <div class="info-grid">
              <div class="info-item">
                <label>部门</label>
                <span>{{ user.role }}</span>
              </div>
              <div class="info-item">
                <label>职位</label>
                <span>{{ user.position }}</span>
              </div>
              <div class="info-item">
                <label>年级</label>
                <span>{{ user.grade }}</span>
              </div>
              <div class="info-item">
                <label>学院</label>
                <span>{{ user.department }}</span>
              </div>
              <div class="info-item">
                <label>联系电话</label>
                <span>{{ user.phone }}</span>
              </div>
              <div class="info-item">
                <label>邮箱</label>
                <span>{{ user.email }}</span>
              </div>
              <div class="info-item">
                <label>加入时间</label>
                <span>{{ user.joinDate }}</span>
              </div>
              <div class="info-item">
                <label>状态</label>
                <span class="status-tag">{{ user.status }}</span>
              </div>
            </div>
          </div>
          
          <div class="info-section">
            <h3 class="section-title">职责说明</h3>
            <div class="description-box">
              <p>负责学生会全面工作，统筹协调各部门活动开展，代表学生会与学校各部门沟通对接，组织召开学生会全体会议，制定年度工作计划和工作总结。</p>
            </div>
          </div>
          
          <div v-if="editMode" class="edit-section">
            <h3 class="section-title">编辑资料</h3>
            <div class="form-grid">
              <div class="form-item">
                <label>姓名</label>
                <input type="text" :value="user.name" class="form-input" />
              </div>
              <div class="form-item">
                <label>职位</label>
                <input type="text" :value="user.position" class="form-input" />
              </div>
              <div class="form-item">
                <label>联系电话</label>
                <input type="text" :value="user.phone" class="form-input" />
              </div>
              <div class="form-item">
                <label>邮箱</label>
                <input type="email" :value="user.email" class="form-input" />
              </div>
            </div>
            <button class="btn btn-primary save-btn" @click="saveProfile">保存修改</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  padding: 32px;
  min-height: 100vh;
  background: #fafafa;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 24px;
  color: #1a1a1a;
  font-weight: 600;
  font-family: 'Microsoft YaHei', sans-serif;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
}

.profile-header {
  padding: 32px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 24px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.avatar-large {
  font-size: 72px;
  display: block;
}

.upload-btn {
  padding: 6px 16px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  background: #fafafa;
  color: #666666;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.upload-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.basic-info {
  flex: 1;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.user-role {
  font-size: 14px;
  color: #666666;
  margin-bottom: 4px;
}

.user-position {
  font-size: 14px;
  color: #1890ff;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: #1890ff;
  color: #ffffff;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-secondary {
  background: #ffffff;
  color: #1890ff;
  border: 1px solid #1890ff;
}

.btn-secondary:hover {
  background: #e6f7ff;
}

.profile-content {
  padding: 24px 32px;
}

.info-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.info-item label {
  font-size: 14px;
  color: #666666;
}

.info-item span {
  font-size: 14px;
  color: #333333;
}

.status-tag {
  padding: 4px 12px;
  background: #f6ffed;
  color: #52c41a;
  border-radius: 4px;
  font-size: 12px;
}

.description-box {
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.description-box p {
  font-size: 14px;
  line-height: 1.6;
  color: #666666;
}

.edit-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  font-size: 14px;
  color: #666666;
}

.form-input {
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  color: #333333;
}

.save-btn {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    text-align: center;
  }
  
  .action-buttons {
    margin-top: 16px;
  }
  
  .info-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
