<script setup>
import { ref, onMounted, computed } from 'vue';
import { apiFetch } from '../../utils/api';

const permissions = ref([]);
const roles = ref([]);
const loading = ref(false);
const showModal = ref(false);
const isEdit = ref(false);
const currentPermission = ref({
  id: null,
  name: '',
  module: '',
  description: '',
  status: '启用'
});

const modules = ['系统', '成员', '活动', '物资', '团务', '党务'];

const allPermissionKeys = [
  { key: 'member:view', name: '成员查看', module: '成员管理' },
  { key: 'member:add', name: '成员添加', module: '成员管理' },
  { key: 'member:edit', name: '成员编辑', module: '成员管理' },
  { key: 'member:delete', name: '成员删除', module: '成员管理' },
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

const getToken = () => localStorage.getItem('token');

const fetchPermissions = () => {
  permissions.value = allPermissionKeys.map((p, index) => ({
    id: index + 1,
    name: p.name,
    key: p.key,
    module: p.module.split('管理')[0],
    description: `权限代码: ${p.key}`,
    status: '启用',
    createTime: '2025-01-01'
  }));
};

const fetchRoles = async () => {
  try {
    const response = await apiFetch('/api/roles/');
    if (response.ok) {
      const data = await response.json();
      roles.value = (data.results || data).map(role => ({
        ...role,
        permissions: typeof role.permissions === 'string' ? JSON.parse(role.permissions || '[]') : (role.permissions || [])
      }));
    }
  } catch (error) {
    console.error('获取角色列表失败:', error);
  }
};

const openCreateModal = () => {
  isEdit.value = false;
  currentPermission.value = {
    id: null,
    name: '',
    module: '',
    description: '',
    status: '启用'
  };
  showModal.value = true;
};

const openEditModal = (perm) => {
  isEdit.value = true;
  currentPermission.value = { ...perm };
  showModal.value = true;
};

const savePermission = () => {
  if (!currentPermission.value.name || !currentPermission.value.module) {
    alert('请填写权限名称和所属模块');
    return;
  }
  if (isEdit.value) {
    const index = permissions.value.findIndex(p => p.id === currentPermission.value.id);
    if (index !== -1) {
      permissions.value[index] = { ...currentPermission.value };
    }
  } else {
    const newId = Math.max(...permissions.value.map(p => p.id)) + 1;
    permissions.value.push({
      ...currentPermission.value,
      id: newId,
      key: `${currentPermission.value.module}:view`,
      createTime: new Date().toISOString().split('T')[0]
    });
  }
  showModal.value = false;
};

const toggleStatus = (perm) => {
  perm.status = perm.status === '启用' ? '禁用' : '启用';
};

const getRolesWithPermission = (permKey) => {
  return roles.value.filter(role => role.permissions.includes(permKey));
};

const toggleRolePermission = async (roleId, permKey) => {
  const role = roles.value.find(r => r.id === roleId);
  if (!role) return;

  const hasPermission = role.permissions.includes(permKey);
  if (hasPermission) {
    role.permissions = role.permissions.filter(p => p !== permKey);
  } else {
    role.permissions.push(permKey);
  }

  try {
    const response = await apiFetch(`/api/roles/${roleId}/`, {
      method: 'PUT',
      body: JSON.stringify({
        ...role,
        permissions: JSON.stringify(role.permissions)
      })
    });

    if (!response.ok) {
      const error = await response.json();
      alert(error.message || '更新失败');
      await fetchRoles();
    }
  } catch (error) {
    console.error('更新角色权限失败:', error);
    await fetchRoles();
  }
};

const groupedPermissions = () => {
  const groups = {};
  permissions.value.forEach(p => {
    const moduleName = p.module || '系统';
    if (!groups[moduleName]) {
      groups[moduleName] = [];
    }
    groups[moduleName].push(p);
  });
  return groups;
};

onMounted(() => {
  fetchPermissions();
  fetchRoles();
});
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>权限管理</h1>
      <button class="btn btn-primary" @click="openCreateModal">添加权限</button>
    </header>
    
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{{ permissions.length }}</div>
        <div class="stat-label">权限总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ modules.length }}</div>
        <div class="stat-label">权限模块</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ roles.length }}</div>
        <div class="stat-label">角色数量</div>
      </div>
    </div>
    
    <div class="permission-groups">
      <div v-for="(perms, module) in groupedPermissions()" :key="module" class="permission-group">
        <div class="group-header">
          <span class="group-name">{{ module }}</span>
          <span class="group-count">{{ perms.length }} 项权限</span>
        </div>
        <div class="group-content">
          <div v-for="perm in perms" :key="perm.id" class="permission-card">
            <div class="perm-info">
              <span class="perm-name">{{ perm.name }}</span>
              <span class="perm-desc">{{ perm.description }}</span>
            </div>
            <div class="perm-roles">
              <div class="roles-label">分配角色:</div>
              <div class="roles-list">
                <button
                  v-for="role in roles"
                  :key="role.id"
                  class="role-tag"
                  :class="{ assigned: role.permissions.includes(perm.key) }"
                  @click="toggleRolePermission(role.id, perm.key)"
                >
                  {{ role.name }}
                </button>
              </div>
            </div>
            <div class="perm-actions">
              <span class="status-tag" :class="perm.status" @click="toggleStatus(perm)">{{ perm.status }}</span>
              <button class="action-btn" @click="openEditModal(perm)">编辑</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showModal" class="modal-overlay" @click="showModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ isEdit ? '编辑权限' : '添加权限' }}</h3>
          <button class="close-btn" @click="showModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>权限名称 *</label>
            <input type="text" v-model="currentPermission.name" class="form-input" />
          </div>
          <div class="form-item">
            <label>所属模块 *</label>
            <select v-model="currentPermission.module" class="form-select">
              <option v-for="m in modules" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
          <div class="form-item">
            <label>权限描述</label>
            <textarea v-model="currentPermission.description" class="form-textarea"></textarea>
          </div>
          <div class="form-item">
            <label>状态</label>
            <div class="radio-group">
              <label><input type="radio" v-model="currentPermission.status" value="启用" /> 启用</label>
              <label><input type="radio" v-model="currentPermission.status" value="禁用" /> 禁用</label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="savePermission">{{ isEdit ? '保存修改' : '添加权限' }}</button>
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

.permission-groups {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.permission-group {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.group-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.group-count {
  font-size: 13px;
  color: #999999;
}

.group-content {
  padding: 16px;
}

.permission-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  background: #fafafa;
  border-radius: 6px;
  flex-wrap: wrap;
  gap: 12px;
}

.permission-card:last-child {
  margin-bottom: 0;
}

.perm-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 150px;
}

.perm-name {
  font-size: 14px;
  font-weight: 500;
  color: #333333;
}

.perm-desc {
  font-size: 12px;
  color: #999999;
}

.perm-roles {
  flex: 2;
  min-width: 200px;
}

.roles-label {
  font-size: 12px;
  color: #999999;
  margin-bottom: 4px;
}

.roles-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.role-tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  border: 1px solid #d9d9d9;
  background: #ffffff;
  color: #666666;
  cursor: pointer;
  transition: all 0.15s ease;
}

.role-tag:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.role-tag.assigned {
  background: #e6f7ff;
  color: #1890ff;
  border-color: #1890ff;
}

.perm-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}

.status-tag.启用 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.禁用 {
  background: #fff1f0;
  color: #ff4d4f;
}

.action-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  background: #e6f7ff;
  color: #1890ff;
  font-size: 13px;
  cursor: pointer;
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

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  font-size: 14px;
  color: #666666;
  margin-bottom: 8px;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
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

.radio-group {
  display: flex;
  gap: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}
</style>