<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const user = ref({
  name: '用户',
  avatar: '👤',
  position: '成员'
});

const showDropdown = ref(false);
const loading = ref(false);

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};

const navigateToProfile = () => {
  router.push('/profile');
  showDropdown.value = false;
};

const logout = async () => {
  loading.value = true;
  showDropdown.value = false;
  
  try {
    const token = localStorage.getItem('token');
    if (token) {
      await fetch('/api/logout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
    }
  } catch (error) {
    console.error('退出登录失败:', error);
  } finally {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    loading.value = false;
    router.push('/login');
  }
};

const loadUserInfo = () => {
  const userData = localStorage.getItem('user');
  if (userData) {
    try {
      const parsed = JSON.parse(userData);
      user.value.name = parsed.member_name || parsed.student_id || '用户';
      user.value.position = parsed.member_position || parsed.role_name || '成员';
    } catch (e) {
      console.error('解析用户信息失败:', e);
    }
  }
};

onMounted(() => {
  loadUserInfo();
});
</script>

<template>
  <header class="top-header">
    <div class="header-left">
      <span class="header-title">学生会管理系统</span>
    </div>
    <div class="header-right">
      <div class="user-menu" @click="toggleDropdown">
        <span class="user-avatar">{{ user.avatar }}</span>
        <div v-if="!showDropdown" class="user-info">
          <span class="user-name">{{ user.name }}</span>
          <span class="user-position">{{ user.position }}</span>
        </div>
        <span class="dropdown-arrow">{{ showDropdown ? '▲' : '▼' }}</span>
      </div>
      <div v-if="showDropdown" class="dropdown-menu">
        <button class="dropdown-item" @click.stop="navigateToProfile">
          <span>👤</span>
          <span>个人信息</span>
        </button>
        <button class="dropdown-item" @click.stop="logout">
          <span>🚪</span>
          <span>退出登录</span>
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.top-header {
  position: fixed;
  top: 0;
  left: 220px;
  right: 0;
  height: 60px;
  background: #ffffff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  z-index: 100;
  transition: left 0.2s ease;
}

.top-header.collapsed {
  left: 64px;
}

.header-left {
  flex: 1;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Microsoft YaHei', sans-serif;
}

.header-right {
  position: relative;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.user-menu:hover {
  background: #f5f5f5;
}

.user-avatar {
  font-size: 32px;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #333333;
}

.user-position {
  font-size: 12px;
  color: #666666;
}

.dropdown-arrow {
  font-size: 12px;
  color: #999999;
}

.dropdown-menu {
  position: absolute;
  top: 56px;
  right: 0;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 160px;
  padding: 8px 0;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #333333;
  transition: background-color 0.15s ease;
  text-align: left;
}

.dropdown-item:hover {
  background: #f5f5f5;
}

@media (max-width: 768px) {
  .user-info {
    display: none;
  }
}
</style>
