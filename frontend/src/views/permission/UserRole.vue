<script setup>
import { ref, onMounted, computed } from 'vue';

const members = ref([]);
const roles = ref([]);
const loading = ref(false);
const showModal = ref(false);
const showMemberSelector = ref(false);
const selectedMember = ref(null);
const selectedRole = ref(null);
const searchQuery = ref('');

const getToken = () => localStorage.getItem('token');

const fetchMembers = async () => {
  loading.value = true;
  try {
    const response = await fetch('/api/members/', {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      members.value = results;
    }
  } catch (error) {
    console.error('获取成员列表失败:', error);
  } finally {
    loading.value = false;
  }
};

const fetchRoles = async () => {
  try {
    const response = await fetch('/api/roles/', {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      roles.value = results;
    }
  } catch (error) {
    console.error('获取角色列表失败:', error);
  }
};

const filteredMembers = computed(() => {
  if (!searchQuery.value) return members.value;
  const query = searchQuery.value.toLowerCase();
  return members.value.filter(m => 
    m.name.toLowerCase().includes(query) || 
    m.student_id.toLowerCase().includes(query) ||
    m.department.toLowerCase().includes(query)
  );
});

const openMemberSelector = () => {
  showMemberSelector.value = true;
};

const selectMember = (member) => {
  selectedMember.value = member;
  showMemberSelector.value = false;
};

const openAssignModal = () => {
  if (!selectedMember.value) {
    alert('请先选择一个成员');
    return;
  }
  selectedRole.value = null;
  showModal.value = true;
};

const assignRole = async (role) => {
  selectedRole.value = role;
};

const confirmAssign = async () => {
  if (!selectedMember.value || !selectedRole.value) {
    alert('请选择成员和角色');
    return;
  }
  
  loading.value = true;
  try {
    const response = await fetch('/api/user-accounts/create_account/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        student_id: selectedMember.value.student_id,
        password: selectedMember.value.student_id, // 默认密码为学号
        role_id: selectedRole.value.id
      })
    });
    
    if (response.ok) {
      alert('角色分配成功！');
      showModal.value = false;
      selectedMember.value = null;
      selectedRole.value = null;
      fetchMembers(); // 刷新成员列表
    } else {
      const error = await response.json();
      alert(error.message || '分配失败');
    }
  } catch (error) {
    console.error('分配角色失败:', error);
    alert('分配失败');
  } finally {
    loading.value = false;
  }
};

const stats = computed(() => ({
  total: members.value.length,
  assigned: members.value.filter(m => m.account).length,
  unassigned: members.value.filter(m => !m.account).length
}));

onMounted(() => {
  fetchMembers();
  fetchRoles();
});
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>用户角色分配</h1>
      <button class="btn btn-primary" @click="openMemberSelector">+ 选择成员</button>
    </header>
    
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">成员总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.assigned }}</div>
        <div class="stat-label">已分配角色</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.unassigned }}</div>
        <div class="stat-label">未分配角色</div>
      </div>
    </div>
    
    <div v-if="selectedMember" class="selected-card">
      <div class="card-header">
        <span class="card-title">已选择成员</span>
        <button class="remove-btn" @click="selectedMember = null">×</button>
      </div>
      <div class="member-info">
        <span class="member-avatar">👤</span>
        <div class="member-details">
          <span class="member-name">{{ selectedMember.name }}</span>
          <span class="member-student-id">{{ selectedMember.student_id }}</span>
          <span class="member-department">{{ selectedMember.department }}</span>
        </div>
      </div>
      <button class="assign-btn" @click="openAssignModal">分配角色</button>
    </div>
    
    <div class="table-container">
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>学号</th>
            <th>姓名</th>
            <th>学院</th>
            <th>职位</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in filteredMembers" :key="member.id">
            <td>{{ member.student_id }}</td>
            <td>{{ member.name }}</td>
            <td><span class="dept-tag">{{ member.department }}</span></td>
            <td>{{ member.position || '--' }}</td>
            <td>
              <span class="status-tag" :class="member.account ? 'assigned' : 'unassigned'">
                {{ member.account ? '已分配' : '未分配' }}
              </span>
            </td>
            <td>
              <button 
                class="action-btn" 
                :class="{ active: selectedMember?.id === member.id }"
                @click="selectMember(member)"
              >
                {{ selectedMember?.id === member.id ? '已选择' : '选择' }}
              </button>
            </td>
          </tr>
          <tr v-if="filteredMembers.length === 0">
            <td colspan="6" class="empty-state">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="showMemberSelector" class="modal-overlay" @click="showMemberSelector = false">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>选择成员</h3>
          <button class="close-btn" @click="showMemberSelector = false">×</button>
        </div>
        <div class="modal-body">
          <div class="search-box">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索学号、姓名或学院..."
              class="search-input"
            />
          </div>
          <div class="member-list">
            <div 
              v-for="member in filteredMembers" 
              :key="member.id"
              class="member-item"
              @click="selectMember(member)"
            >
              <span class="item-avatar">👤</span>
              <div class="item-info">
                <span class="item-name">{{ member.name }}</span>
                <span class="item-detail">{{ member.student_id }} - {{ member.department }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showMemberSelector = false">取消</button>
        </div>
      </div>
    </div>
    
    <div v-if="showModal" class="modal-overlay" @click="showModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>分配角色</h3>
          <button class="close-btn" @click="showModal = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="selectedMember" class="user-info">
            <span class="user-avatar">👤</span>
            <div class="user-details">
              <span class="user-name">{{ selectedMember.name }}</span>
              <span class="user-student-id">{{ selectedMember.student_id }}</span>
            </div>
          </div>
          <div class="role-list">
            <button 
              v-for="role in roles" 
              :key="role.id"
              class="role-btn"
              :class="{ active: selectedRole?.id === role.id }"
              @click="assignRole(role)"
            >
              {{ role.name }}
            </button>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">取消</button>
          <button 
            class="btn btn-primary" 
            @click="confirmAssign" 
            :disabled="!selectedRole || loading"
          >
            {{ loading ? '分配中...' : '确认分配' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  padding: 32px;
  min-height: 100vh;
  background: #fafafa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 24px;
  color: #1a1a1a;
  font-weight: 600;
  font-family: 'Microsoft YaHei', sans-serif;
}

.btn {
  padding: 10px 24px;
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

.btn-primary:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #ffffff;
  color: #1890ff;
  border: 1px solid #1890ff;
}

.btn-secondary:hover {
  background: #e6f7ff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-item {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666666;
}

.selected-card {
  background: #ffffff;
  border: 2px solid #1890ff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 32px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-weight: 600;
  color: #1890ff;
}

.remove-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: #fff1f0;
  color: #ff4d4f;
  border-radius: 4px;
  font-size: 18px;
  cursor: pointer;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.member-avatar {
  font-size: 40px;
}

.member-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.member-student-id {
  font-size: 14px;
  color: #666666;
}

.member-department {
  font-size: 14px;
  color: #1890ff;
}

.assign-btn {
  padding: 10px 24px;
  background: #1890ff;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.assign-btn:hover {
  background: #40a9ff;
}

.table-container {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
}

.loading-state {
  padding: 40px;
  text-align: center;
  color: #999999;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.data-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333333;
  font-size: 14px;
}

.data-table td {
  font-size: 14px;
  color: #333333;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999999;
}

.dept-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.assigned {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.unassigned {
  background: #fffbe6;
  color: #faad14;
}

.action-btn {
  padding: 6px 12px;
  border: 1px solid #1890ff;
  border-radius: 4px;
  background: #ffffff;
  color: #1890ff;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: #e6f7ff;
}

.action-btn.active {
  background: #1890ff;
  color: #ffffff;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #ffffff;
  border-radius: 8px;
  width: 480px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content.large {
  width: 600px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #999999;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 24px;
}

.search-box {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #1890ff;
}

.member-list {
  max-height: 300px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.member-item:hover {
  background: #f5f5f5;
}

.item-avatar {
  font-size: 28px;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

.item-detail {
  font-size: 12px;
  color: #666666;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.user-avatar {
  font-size: 48px;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.user-student-id {
  font-size: 14px;
  color: #666666;
}

.role-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.role-btn {
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: #ffffff;
  font-size: 14px;
  color: #333333;
  cursor: pointer;
  transition: all 0.15s ease;
}

.role-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.role-btn.active {
  background: #e6f7ff;
  border-color: #1890ff;
  color: #1890ff;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}
</style>