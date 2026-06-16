<script setup>
import { ref } from 'vue';

const logs = ref([
  { id: 1, user: '张三', action: '登录系统', module: '系统', time: '2025-06-08 14:30:25', ip: '192.168.1.100', status: '成功' },
  { id: 2, user: '李四', action: '创建角色', module: '权限管理', time: '2025-06-08 14:28:12', ip: '192.168.1.101', status: '成功' },
  { id: 3, user: '王五', action: '编辑成员信息', module: '成员管理', time: '2025-06-08 14:25:45', ip: '192.168.1.102', status: '成功' },
  { id: 4, user: '赵六', action: '创建活动', module: '活动管理', time: '2025-06-08 14:22:30', ip: '192.168.1.103', status: '成功' },
  { id: 5, user: '钱七', action: '借用物资', module: '物资管理', time: '2025-06-08 14:18:55', ip: '192.168.1.104', status: '成功' },
  { id: 6, user: '孙八', action: '分配角色', module: '权限管理', time: '2025-06-08 14:15:20', ip: '192.168.1.105', status: '成功' },
  { id: 7, user: '周九', action: '导出数据', module: '系统', time: '2025-06-08 14:10:35', ip: '192.168.1.106', status: '成功' },
  { id: 8, user: '吴十', action: '登录失败', module: '系统', time: '2025-06-08 14:05:18', ip: '192.168.1.200', status: '失败' },
  { id: 9, user: '郑十一', action: '审批活动', module: '活动管理', time: '2025-06-08 13:58:42', ip: '192.168.1.107', status: '成功' },
  { id: 10, user: '张三', action: '退出系统', module: '系统', time: '2025-06-08 13:55:10', ip: '192.168.1.100', status: '成功' }
]);

const searchQuery = ref('');
const selectedModule = ref('全部');
const selectedStatus = ref('全部');

const modules = ['全部', '系统', '成员管理', '活动管理', '物资管理', '团务管理', '党务管理', '权限管理'];
const statuses = ['全部', '成功', '失败'];

const filteredLogs = ref(logs.value);

const filterLogs = () => {
  filteredLogs.value = logs.value.filter(log => {
    const matchQuery = !searchQuery.value || 
      log.user.includes(searchQuery.value) || 
      log.action.includes(searchQuery.value);
    const matchModule = selectedModule.value === '全部' || log.module === selectedModule.value;
    const matchStatus = selectedStatus.value === '全部' || log.status === selectedStatus.value;
    return matchQuery && matchModule && matchStatus;
  });
};

const stats = [
  { label: '今日操作', value: 156 },
  { label: '成功操作', value: 150 },
  { label: '失败操作', value: 6 },
  { label: '活跃用户', value: 23 }
];
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>操作审计日志</h1>
    </header>
    
    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.label" class="stat-item">
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">{{ stat.label }}</div>
      </div>
    </div>
    
    <div class="filter-bar">
      <div class="filter-item">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索用户或操作..." 
          class="search-input"
          @input="filterLogs"
        />
      </div>
      <div class="filter-item">
        <select v-model="selectedModule" class="filter-select" @change="filterLogs">
          <option v-for="m in modules" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>
      <div class="filter-item">
        <select v-model="selectedStatus" class="filter-select" @change="filterLogs">
          <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
    </div>
    
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>操作</th>
            <th>模块</th>
            <th>时间</th>
            <th>IP地址</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in filteredLogs" :key="log.id">
            <td>{{ log.user }}</td>
            <td>{{ log.action }}</td>
            <td><span class="module-tag">{{ log.module }}</span></td>
            <td>{{ log.time }}</td>
            <td>{{ log.ip }}</td>
            <td><span class="status-tag" :class="log.status">{{ log.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="pagination">
      <span class="page-info">共 {{ filteredLogs.length }} 条记录</span>
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
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 24px;
  color: #1a1a1a;
  font-weight: 600;
  font-family: 'Microsoft YaHei', sans-serif;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-item {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666666;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.filter-item {
  flex: 1;
}

.search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.filter-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  background: #ffffff;
}

.table-container {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 14px 16px;
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

.module-tag {
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
  font-weight: 500;
}

.status-tag.成功 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.失败 {
  background: #fff1f0;
  color: #ff4d4f;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.page-info {
  font-size: 14px;
  color: #666666;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-bar {
    flex-direction: column;
  }
}
</style>
