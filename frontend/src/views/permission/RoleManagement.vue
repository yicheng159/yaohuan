<script setup>
import { ref, onMounted, computed } from 'vue';
import { apiFetch } from '../../utils/api';

const roles = ref([]);
const loading = ref(false);
const showModal = ref(false);
const isEdit = ref(false);
const currentRole = ref({
  id: null,
  name: '',
  description: '',
  is_active: true,
  permissions: []
});

const allPermissions = [
  { key: 'member:view', name: '成员查看', module: '成员管理' },
  { key: 'member:add', name: '成员添加', module: '成员管理' },
  { key: 'member:edit', name: '成员编辑', module: '成员管理' },
  { key: 'member:delete', name: '成员删除', module: '成员管理' },
  { key: 'member:import', name: '成员导入', module: '成员管理' },
  { key: 'member:export', name: '成员导出', module: '成员管理' },
  { key: 'activity:view', name: '活动查看', module: '活动管理' },
  { key: 'activity:add', name: '活动创建', module: '活动管理' },
  { key: 'activity:edit', name: '活动编辑', module: '活动管理' },
  { key: 'activity:delete', name: '活动删除', module: '活动管理' },
  { key: 'material:view', name: '物资查看', module: '物资管理' },
  { key: 'material:add', name: '物资添加', module: '物资管理' },
  { key: 'material:edit', name: '物资编辑', module: '物资管理' },
  { key: 'material:delete', name: '物资删除', module: '物资管理' },
  { key: 'league:view', name: '团务查看', module: '团务管理' },
  { key: 'league:add', name: '团务添加', module: '团务管理' },
  { key: 'league:edit', name: '团务编辑', module: '团务管理' },
  { key: 'league:delete', name: '团务删除', module: '团务管理' },
  { key: 'party:view', name: '党务查看', module: '党务管理' },
  { key: 'party:add', name: '党务添加', module: '党务管理' },
  { key: 'party:edit', name: '党务编辑', module: '党务管理' },
  { key: 'party:delete', name: '党务删除', module: '党务管理' },
  { key: 'role:view', name: '角色查看', module: '权限管理' },
  { key: 'role:add', name: '角色创建', module: '权限管理' },
  { key: 'role:edit', name: '角色编辑', module: '权限管理' },
  { key: 'role:delete', name: '角色删除', module: '权限管理' },
  { key: 'user:view', name: '用户查看', module: '权限管理' },
  { key: 'user:add', name: '用户创建', module: '权限管理' },
  { key: 'user:edit', name: '用户编辑', module: '权限管理' },
  { key: 'user:delete', name: '用户删除', module: '权限管理' },
  { key: 'log:view', name: '日志查看', module: '系统管理' },
  { key: 'menu:view', name: '菜单查看', module: '系统管理' },
  { key: 'menu:edit', name: '菜单编辑', module: '系统管理' }
];

const moduleGroups = computed(() => {
  const groups = {};
  allPermissions.forEach(p => {
    if (!groups[p.module]) {
      groups[p.module] = [];
    }
    groups[p.module].push(p);
  });
  return groups;
});

const getToken = () => localStorage.getItem('token');

const fetchRoles = async () => {
  loading.value = true;
  try {
    const response = await apiFetch('/api/roles/');
    if (response.ok) {
      const data = await response.json();
      // 处理分页数据
      const results = data.results || data;
      roles.value = results.map(role => ({
        ...role,
        permissions: typeof role.permissions === 'string' ? JSON.parse(role.permissions || '[]') : (role.permissions || [])
      }));
    }
  } catch (error) {
    console.error('获取角色列表失败:', error);
  } finally {
    loading.value = false;
  }
};

const openCreateModal = () => {
  isEdit.value = false;
  currentRole.value = {
    id: null,
    name: '',
    description: '',
    is_active: true,
    permissions: []
  };
  showModal.value = true;
};

const openEditModal = (role) => {
  isEdit.value = true;
  currentRole.value = {
    ...role,
    permissions: role.permissions || []
  };
  showModal.value = true;
};

const deleteRole = async (role) => {
  if (!confirm(`确定删除角色「${role.name}」吗？`)) {
    return;
  }
  try {
    const response = await apiFetch(`/api/roles/${role.id}/`, {
      method: 'DELETE',
    });
    if (response.ok) {
      await fetchRoles();
    }
  } catch (error) {
    console.error('删除角色失败:', error);
  }
};

const saveRole = async () => {
  if (!currentRole.value.name) {
    alert('请输入角色名称');
    return;
  }
  
  loading.value = true;
  try {
    const payload = {
      name: currentRole.value.name,
      description: currentRole.value.description,
      is_active: currentRole.value.is_active,
      permissions: JSON.stringify(currentRole.value.permissions)
    };
    
    const url = isEdit.value ? `/api/roles/${currentRole.value.id}/` : '/api/roles/';
    const method = isEdit.value ? 'PUT' : 'POST';
    
    const response = await apiFetch(url, {
      method: method,
      body: JSON.stringify(payload)
    });
    
    if (response.ok) {
      showModal.value = false;
      await fetchRoles();
    } else {
      const error = await response.json();
      alert(error.message || '保存失败');
    }
  } catch (error) {
    console.error('保存角色失败:', error);
    alert('保存失败');
  } finally {
    loading.value = false;
  }
};

const toggleModule = (module) => {
  const modulePerms = moduleGroups.value[module].map(p => p.key);
  const hasAll = modulePerms.every(p => currentRole.value.permissions.includes(p));
  
  if (hasAll) {
    currentRole.value.permissions = currentRole.value.permissions.filter(p => !modulePerms.includes(p));
  } else {
    modulePerms.forEach(p => {
      if (!currentRole.value.permissions.includes(p)) {
        currentRole.value.permissions.push(p);
      }
    });
  }
};

const stats = computed(() => ({
  total: roles.value.length,
  active: roles.value.filter(r => r.is_active).length,
  inactive: roles.value.filter(r => !r.is_active).length
}));

onMounted(() => {
  fetchRoles();
});
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>角色管理</h1>
      <button class="btn btn-primary" @click="openCreateModal">+ 创建角色</button>
    </header>
    
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">角色总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.active }}</div>
        <div class="stat-label">启用角色</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.inactive }}</div>
        <div class="stat-label">禁用角色</div>
      </div>
    </div>
    
    <div class="table-container">
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>角色名称</th>
            <th>描述</th>
            <th>状态</th>
            <th>权限数量</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roles" :key="role.id">
            <td>{{ role.name }}</td>
            <td>{{ role.description || '--' }}</td>
            <td>
              <span class="status-tag" :class="role.is_active ? 'active' : 'inactive'">
                {{ role.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td>{{ role.permissions?.length || 0 }}</td>
            <td>{{ role.created_at?.split('T')[0] || '--' }}</td>
            <td>
              <button class="action-btn edit" @click="openEditModal(role)">编辑</button>
              <button class="action-btn delete" @click="deleteRole(role)">删除</button>
            </td>
          </tr>
          <tr v-if="roles.length === 0">
            <td colspan="6" class="empty-state">暂无角色数据</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="showModal" class="modal-overlay" @click="showModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ isEdit ? '编辑角色' : '创建角色' }}</h3>
          <button class="close-btn" @click="showModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>角色名称 *</label>
            <input type="text" v-model="currentRole.name" class="form-input" placeholder="请输入角色名称" />
          </div>
          <div class="form-item">
            <label>角色描述</label>
            <textarea v-model="currentRole.description" class="form-textarea" placeholder="请输入角色描述"></textarea>
          </div>
          <div class="form-item">
            <label>状态</label>
            <div class="radio-group">
              <label class="radio-label">
                <input type="radio" v-model="currentRole.is_active" :value="true" />
                <span>启用</span>
              </label>
              <label class="radio-label">
                <input type="radio" v-model="currentRole.is_active" :value="false" />
                <span>禁用</span>
              </label>
            </div>
          </div>
          <div class="form-item">
            <label>权限分配</label>
            <div class="permission-tree">
              <div v-for="(perms, module) in moduleGroups" :key="module" class="permission-group">
                <div class="group-header">
                  <input 
                    type="checkbox" 
                    :checked="perms.every(p => currentRole.permissions.includes(p.key))"
                    @change="toggleModule(module)"
                  />
                  <span class="group-name">{{ module }}</span>
                </div>
                <div class="group-items">
                  <label v-for="perm in perms" :key="perm.key" class="permission-item">
                    <input type="checkbox" v-model="currentRole.permissions" :value="perm.key" />
                    <span>{{ perm.name }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="saveRole" :disabled="loading">
            {{ loading ? '保存中...' : (isEdit ? '保存修改' : '创建角色') }}
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

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.active {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.inactive {
  background: #fff1f0;
  color: #ff4d4f;
}

.action-btn {
  margin: 0 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s ease;
}

.action-btn.edit {
  background: #e6f7ff;
  color: #1890ff;
}

.action-btn.edit:hover {
  background: #bae7ff;
}

.action-btn.delete {
  background: #fff1f0;
  color: #ff4d4f;
}

.action-btn.delete:hover {
  background: #ffccc7;
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
  width: 600px;
  max-height: 80vh;
  overflow-y: auto;
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
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #999999;
  font-size: 24px;
  cursor: pointer;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f5f5f5;
}

.modal-body {
  padding: 24px;
}

.form-item {
  margin-bottom: 20px;
}

.form-item label {
  display: block;
  font-size: 14px;
  color: #333333;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.form-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.form-textarea {
  width: 100%;
  height: 80px;
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
}

.form-textarea:focus {
  outline: none;
  border-color: #1890ff;
}

.radio-group {
  display: flex;
  gap: 24px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.permission-tree {
  background: #fafafa;
  border-radius: 6px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.permission-group {
  margin-bottom: 16px;
}

.permission-group:last-child {
  margin-bottom: 0;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #333333;
  margin-bottom: 8px;
}

.group-name {
  font-size: 14px;
}

.group-items {
  padding-left: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666666;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}
</style>