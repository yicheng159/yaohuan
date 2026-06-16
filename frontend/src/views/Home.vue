<script setup>import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();
const stats = ref([
 { title: '成员总数', value: '--', icon: '👥', api: '/api/members/statistics/', field: 'total' },
 { title: '活动场次', value: '--', icon: '📅', api: '/api/activities/statistics/', field: 'total' },
 { title: '物资库存', value: '--', icon: '📦', api: '/api/materials/statistics/', field: 'total_quantity' },
 { title: '党员人数', value: '--', icon: '♥', api: '/api/party-members/statistics/', field: 'total' }
]);
const recentActivities = ref([]);
const loading = ref(false);
const lastUpdateTime = ref('');
let refreshInterval = null;
const formatNumber = (num) => {
 if (num === null || num === undefined)
 return '--';
 return num.toLocaleString();
};
const fetchStats = async () => {
 const token = localStorage.getItem('token');
 for (const stat of stats.value) {
 try {
 const response = await fetch(stat.api, {
 headers: {
 'Authorization': `Bearer ${token}`
 }
 });
 if (response.ok) {
 const data = await response.json();
 stat.value = formatNumber(data[stat.field]);
 }
 }
 catch (error) {
 console.error(`获取${stat.title}失败:`, error);
 }
 }
};
const fetchActivities = async () => {
 const token = localStorage.getItem('token');
 try {
 const response = await fetch('/api/activities/?limit=5', {
 headers: {
 'Authorization': `Bearer ${token}`
 }
 });
 if (response.ok) {
 const data = await response.json();
 recentActivities.value = data.results.map(activity => ({
 name: activity.name,
 date: activity.start_time?.split('T')[0] || '--',
 status: activity.status,
 participants: activity.participants_count || 0
 }));
 }
 }
 catch (error) {
 console.error('获取活动列表失败:', error);
 }
};
const refreshData = () => {
 loading.value = true;
 Promise.all([fetchStats(), fetchActivities()]).then(() => {
 loading.value = false;
 lastUpdateTime.value = new Date().toLocaleString('zh-CN');
 });
};
const startAutoRefresh = () => {
 refreshInterval = setInterval(() => {
 refreshData();
 }, 30000); // 每30秒自动刷新
};
const stopAutoRefresh = () => {
 if (refreshInterval) {
 clearInterval(refreshInterval);
 refreshInterval = null;
 }
};
const shortcuts = ref([
 { key: '1', label: '成员管理', path: '/members', description: '跳转到成员管理页面' },
 { key: '2', label: '活动管理', path: '/activities', description: '跳转到活动管理页面' },
 { key: '3', label: '物资管理', path: '/materials', description: '跳转到物资管理页面' },
 { key: '4', label: '团员管理', path: '/league/members', description: '跳转到团员管理页面' },
 { key: '5', label: '党员管理', path: '/party/members', description: '跳转到党员管理页面' },
 { key: 'r', label: '刷新数据', action: 'refresh', description: '刷新页面数据' },
 { key: 'h', label: '返回首页', path: '/', description: '返回首页' },
]);
const showShortcuts = ref(false);
const handleKeydown = (event) => {
 if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
 return;
 }
 const key = event.key.toLowerCase();
 const shortcut = shortcuts.value.find(s => s.key === key);
 if (shortcut) {
 event.preventDefault();
 if (shortcut.path) {
 router.push(shortcut.path);
 } else if (shortcut.action === 'refresh') {
 refreshData();
 }
 }
 if (event.key === '?') {
 event.preventDefault();
 showShortcuts.value = !showShortcuts.value;
 }
};
const navigateTo = (path) => {
 router.push(path);
};
const quickActions = ref([
 { name: '发布活动', icon: '+', path: '/activities', shortcut: 'A' },
 { name: '添加成员', icon: '👤', path: '/members', shortcut: 'M' },
 { name: '申请物资', icon: '📋', path: '/materials', shortcut: 'I' },
 { name: '通知公告', icon: '🔔', path: '/', shortcut: 'N' },
]);
onMounted(() => {
 refreshData();
 startAutoRefresh();
 window.addEventListener('keydown', handleKeydown);
});
onUnmounted(() => {
 stopAutoRefresh();
 window.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <div class="home-page">
    <header class="page-header">
      <div class="header-content">
        <h1>学生会管理系统</h1>
        <p class="subtitle">欢迎使用</p>
      </div>
      <button 
        class="refresh-btn" 
        :class="{ loading }"
        @click="refreshData"
      >
        <span class="refresh-icon">{{ loading ? '⏳' : '🔄' }}</span>
        <span class="refresh-text">{{ loading ? '刷新中...' : '刷新' }}</span>
      </button>
    </header>
    
    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.title" class="stat-card">
        <span class="stat-icon">{{ stat.icon }}</span>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-title">{{ stat.title }}</div>
        </div>
      </div>
    </div>
    
    <div class="content-row">
      <div class="activity-section">
        <div class="section-header">
          <h2 class="section-title">近期活动</h2>
          <span class="update-time">
            最后更新: {{ lastUpdateTime || '--' }}
          </span>
        </div>
        <div class="activity-list">
          <div v-for="activity in recentActivities" :key="activity.name" class="activity-item">
            <div class="activity-info">
              <h3>{{ activity.name }}</h3>
              <p>{{ activity.date }} · {{ activity.participants }}人参与</p>
            </div>
            <span class="activity-status" :class="activity.status">
              {{ activity.status }}
            </span>
          </div>
          <div v-if="recentActivities.length === 0" class="empty-state">
            <p>暂无活动数据</p>
          </div>
        </div>
      </div>
      
      <div class="quick-section">
        <div class="section-header">
          <h2 class="section-title">快捷操作</h2>
          <button class="shortcuts-toggle" @click="showShortcuts = !showShortcuts">
            按 ? 查看快捷键
          </button>
        </div>
        <div class="quick-grid">
          <button class="quick-btn" v-for="action in quickActions" :key="action.name" @click="navigateTo(action.path)">
            <span class="quick-icon">{{ action.icon }}</span>
            <span class="quick-text">{{ action.name }}</span>
            <span class="quick-shortcut">{{ action.shortcut }}</span>
          </button>
        </div>
      </div>
      
      <div v-if="showShortcuts" class="shortcuts-panel">
        <div class="shortcuts-header">
          <h3>快捷键列表</h3>
          <button class="close-btn" @click="showShortcuts = false">×</button>
        </div>
        <div class="shortcuts-list">
          <div v-for="shortcut in shortcuts" :key="shortcut.key" class="shortcut-item">
            <span class="shortcut-key">{{ shortcut.key }}</span>
            <span class="shortcut-label">{{ shortcut.label }}</span>
            <span class="shortcut-desc">{{ shortcut.description }}</span>
          </div>
        </div>
        <div class="shortcuts-footer">
          <p>按 <span class="key-hint">?</span> 键切换快捷键面板</p>
        </div>
      </div>
      
      <div class="quick-section">
        <h2 class="section-title">功能入口</h2>
        <div class="quick-grid">
          <button class="quick-btn" @click="navigateTo('/members')">
            <span class="quick-icon">👥</span>
            <span class="quick-text">添加成员</span>
          </button>
          <button class="quick-btn">
            <span class="quick-icon">📋</span>
            <span class="quick-text">申请物资</span>
          </button>
          <button class="quick-btn">
            <span class="quick-icon">🔔</span>
            <span class="quick-text">通知公告</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="welcome-section">
      <div class="welcome-card">
        <div class="welcome-content">
          <h2>欢迎使用</h2>
          <p>学生会管理系统致力于为学生会工作提供高效、便捷的数字化管理平台，提升工作效率和团队协作能力。</p>
          <div class="welcome-features">
            <div class="feature-item">
              <span class="feature-icon">✓</span>
              <span>成员管理系统化</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✓</span>
              <span>活动策划智能化</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✓</span>
              <span>物资调配高效化</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✓</span>
              <span>党务团务规范化</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  padding: 32px;
  min-height: 100vh;
  background: #fafafa;
}

.page-header {
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  font-size: 24px;
  color: #1a1a1a;
  margin-bottom: 6px;
  font-weight: 600;
  font-family: 'Microsoft YaHei', sans-serif;
}

.subtitle {
  font-size: 14px;
  color: #666666;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #ffffff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 14px;
  color: #666666;
}

.refresh-btn:hover:not(.loading) {
  background: #f5f5f5;
  border-color: #1890ff;
  color: #1890ff;
}

.refresh-btn.loading {
  cursor: not-allowed;
  opacity: 0.6;
}

.refresh-icon {
  font-size: 16px;
}

.refresh-text {
  font-size: 13px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 28px;
  opacity: 0.8;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.stat-title {
  font-size: 14px;
  color: #666666;
}

.content-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 32px;
}

.activity-section,
.quick-section {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Microsoft YaHei', sans-serif;
}

.update-time {
  font-size: 12px;
  color: #999999;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.activity-info h3 {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.activity-info p {
  font-size: 13px;
  color: #666666;
}

.activity-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.activity-status.进行中 {
  background: #e6f7ff;
  color: #1890ff;
}

.activity-status.已结束 {
  background: #f5f5f5;
  color: #666666;
}

.activity-status.未开始 {
  background: #fff7e6;
  color: #fa8c16;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999999;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.quick-btn:hover {
  background: #f5f5f5;
  border-color: #d9d9d9;
}

.quick-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.quick-text {
  font-size: 13px;
  color: #333333;
}

.quick-shortcut {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 11px;
  color: #999999;
}

.quick-btn {
  position: relative;
}

.shortcuts-toggle {
  font-size: 12px;
  color: #1890ff;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.15s ease;
}

.shortcuts-toggle:hover {
  background: rgba(24, 144, 255, 0.1);
}

.shortcuts-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  padding: 24px;
  width: 480px;
  max-height: 80vh;
  overflow-y: auto;
  z-index: 1000;
}

.shortcuts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.shortcuts-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  color: #666666;
  cursor: pointer;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: #e8e8e8;
  color: #333333;
}

.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: #fafafa;
  border-radius: 6px;
}

.shortcut-key {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1890ff;
  color: #ffffff;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  font-family: monospace;
}

.shortcut-label {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

.shortcut-desc {
  font-size: 13px;
  color: #999999;
}

.shortcuts-footer {
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  text-align: center;
}

.shortcuts-footer p {
  font-size: 13px;
  color: #999999;
  margin: 0;
}

.key-hint {
  display: inline-block;
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}

.welcome-section {
  margin-top: 20px;
}

.welcome-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 28px;
}

.welcome-content h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 12px;
  font-family: 'Microsoft YaHei', sans-serif;
}

.welcome-content p {
  font-size: 14px;
  line-height: 1.6;
  color: #666666;
  margin-bottom: 20px;
}

.welcome-features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #333333;
}

.feature-icon {
  color: #52c41a;
  font-size: 14px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .content-row {
    grid-template-columns: 1fr;
  }
}
</style>