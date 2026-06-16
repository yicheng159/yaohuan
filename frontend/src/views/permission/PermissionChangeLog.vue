<script setup>
import { ref, onMounted, computed } from 'vue';
import { apiFetch } from '../../utils/api';

const logs = ref([]);
const loading = ref(false);
const statistics = ref({
  today_count: 0,
  total_count: 0,
  operation_stats: {}
});

const filters = ref({
  operation_type: '',
  target_type: '',
  operator_name: '',
  start_date: '',
  end_date: ''
});

const operationTypes = [
  { value: '', label: '全部' },
  { value: 'create_role', label: '创建角色' },
  { value: 'edit_role', label: '编辑角色' },
  { value: 'delete_role', label: '删除角色' },
  { value: 'assign_role', label: '分配角色' },
  { value: 'remove_role', label: '移除角色' },
  { value: 'change_permissions', label: '修改权限' },
  { value: 'create_user', label: '创建用户' },
  { value: 'edit_user', label: '编辑用户' },
  { value: 'delete_user', label: '删除用户' }
];

const targetTypes = [
  { value: '', label: '全部' },
  { value: '角色', label: '角色' },
  { value: '用户', label: '用户' }
];

const fetchLogs = async () => {
  loading.value = true;
  try {
    let url = '/api/permission-change-logs/';
    const params = [];

    if (filters.value.operation_type) {
      params.push(`operation_type=${filters.value.operation_type}`);
    }
    if (filters.value.target_type) {
      params.push(`target_type=${filters.value.target_type}`);
    }
    if (filters.value.operator_name) {
      params.push(`operator_name=${filters.value.operator_name}`);
    }
    if (filters.value.start_date) {
      params.push(`created_at__gte=${filters.value.start_date}`);
    }
    if (filters.value.end_date) {
      params.push(`created_at__lte=${filters.value.end_date}`);
    }

    if (params.length > 0) {
      url += '?' + params.join('&');
    }

    const response = await apiFetch(url);
    if (response.ok) {
      const data = await response.json();
      logs.value = data.results || data;
    }
  } catch (error) {
    console.error('获取权限变更日志失败:', error);
  } finally {
    loading.value = false;
  }
};

const fetchStatistics = async () => {
  try {
    const response = await apiFetch('/api/permission-change-logs/statistics/');
    if (response.ok) {
      const data = await response.json();
      statistics.value = data.data;
    }
  } catch (error) {
    console.error('获取统计数据失败:', error);
  }
};

const resetFilters = () => {
  filters.value = {
    operation_type: '',
    target_type: '',
    operator_name: '',
    start_date: '',
    end_date: ''
  };
  fetchLogs();
};

const formatDateTime = (datetime) => {
  if (!datetime) return '--';
  return datetime.replace('T', ' ').split('.')[0];
};

const getOperationTypeLabel = (type) => {
  const found = operationTypes.find(t => t.value === type);
  return found ? found.label : type;
};

const viewDetail = (log) => {
  let detail = `操作人: ${log.operator_name || log.operator_student_id || '未知'}\n`;
  detail += `操作类型: ${getOperationTypeLabel(log.operation_type)}\n`;
  detail += `目标: ${log.target_type} - ${log.target_name}\n`;
  detail += `操作时间: ${formatDateTime(log.created_at)}\n`;
  detail += `IP地址: ${log.ip_address || '未知'}\n\n`;

  if (log.change_detail) {
    detail += `变更详情: ${log.change_detail}\n\n`;
  }

  if (log.before_value) {
    try {
      const before = JSON.parse(log.before_value);
      detail += `变更前:\n${JSON.stringify(before, null, 2)}\n\n`;
    } catch {
      detail += `变更前: ${log.before_value}\n\n`;
    }
  }

  if (log.after_value) {
    try {
      const after = JSON.parse(log.after_value);
      detail += `变更后:\n${JSON.stringify(after, null, 2)}`;
    } catch {
      detail += `变更后: ${log.after_value}`;
    }
  }

  alert(detail);
};

onMounted(() => {
  fetchLogs();
  fetchStatistics();
});
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>权限变更日志</h1>
    </header>

    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{{ statistics.today_count }}</div>
        <div class="stat-label">今日变更</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ statistics.total_count }}</div>
        <div class="stat-label">总变更数</div>
      </div>
      <div class="stat-item stat-wide">
        <div class="stat-title">操作类型统计</div>
        <div class="stat-details">
          <span v-for="(count, name) in statistics.operation_stats" :key="name" class="detail-item">
            {{ name }}: {{ count }}
          </span>
        </div>
      </div>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <label>操作类型</label>
          <select v-model="filters.operation_type" @change="fetchLogs">
            <option v-for="type in operationTypes" :key="type.value" :value="type.value">
              {{ type.label }}
            </option>
          </select>
        </div>
        <div class="filter-item">
          <label>目标类型</label>
          <select v-model="filters.target_type" @change="fetchLogs">
            <option v-for="type in targetTypes" :key="type.value" :value="type.value">
              {{ type.label }}
            </option>
          </select>
        </div>
        <div class="filter-item">
          <label>操作人</label>
          <input type="text" v-model="filters.operator_name" placeholder="输入操作人姓名" @keyup.enter="fetchLogs" />
        </div>
        <div class="filter-item">
          <label>开始日期</label>
          <input type="date" v-model="filters.start_date" @change="fetchLogs" />
        </div>
        <div class="filter-item">
          <label>结束日期</label>
          <input type="date" v-model="filters.end_date" @change="fetchLogs" />
        </div>
        <button class="btn btn-secondary" @click="resetFilters">重置</button>
      </div>
    </div>

    <div class="table-container">
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>操作人</th>
            <th>操作类型</th>
            <th>目标类型</th>
            <th>目标名称</th>
            <th>变更详情</th>
            <th>IP地址</th>
            <th>操作时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td>{{ log.operator_name || log.operator_student_id || '--' }}</td>
            <td>
              <span class="operation-tag" :class="log.operation_type">
                {{ getOperationTypeLabel(log.operation_type) }}
              </span>
            </td>
            <td>{{ log.target_type || '--' }}</td>
            <td>{{ log.target_name || '--' }}</td>
            <td class="detail-cell">{{ log.change_detail || '--' }}</td>
            <td>{{ log.ip_address || '--' }}</td>
            <td>{{ formatDateTime(log.created_at) }}</td>
            <td>
              <button class="action-btn view" @click="viewDetail(log)">查看详情</button>
            </td>
          </tr>
          <tr v-if="logs.length === 0">
            <td colspan="8" class="empty-state">暂无权限变更日志</td>
          </tr>
        </tbody>
      </table>
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

.stat-wide {
  grid-column: span 1;
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

.stat-title {
  font-size: 16px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 12px;
}

.stat-details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.detail-item {
  font-size: 13px;
  color: #666666;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
}

.filter-section {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item label {
  font-size: 13px;
  color: #666666;
}

.filter-item select,
.filter-item input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  min-width: 150px;
}

.filter-item input[type="date"] {
  min-width: 140px;
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.btn-secondary {
  background: #ffffff;
  color: #1890ff;
  border: 1px solid #1890ff;
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

.detail-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999999;
}

.operation-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: #f0f0f0;
  color: #666666;
}

.operation-tag.create_role,
.operation-tag.create_user {
  background: #e6f7ff;
  color: #1890ff;
}

.operation-tag.edit_role,
.operation-tag.edit_user,
.operation-tag.change_permissions {
  background: #fff7e6;
  color: #fa8c16;
}

.operation-tag.delete_role,
.operation-tag.delete_user {
  background: #fff1f0;
  color: #ff4d4f;
}

.operation-tag.assign_role {
  background: #f6ffed;
  color: #52c41a;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.action-btn.view {
  background: #e6f7ff;
  color: #1890ff;
}
</style>