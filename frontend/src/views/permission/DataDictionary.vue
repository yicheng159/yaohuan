<script setup>
import { ref, onMounted, computed } from 'vue';
import { apiFetch } from '../../utils/api';
import { hasPermission } from '../../utils/permission';

const dictionaries = ref([]);
const categories = ref([]);
const loading = ref(false);
const showModal = ref(false);
const isEdit = ref(false);
const searchKeyword = ref('');
const selectedCategory = ref('');

const currentItem = ref({
  id: null,
  category: '',
  code: '',
  name: '',
  sort_order: 0,
  is_active: true,
  description: ''
});

const filteredDictionaries = computed(() => {
  let result = dictionaries.value;
  if (selectedCategory.value) {
    result = result.filter(item => item.category === selectedCategory.value);
  }
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(item => 
      item.name.toLowerCase().includes(keyword) ||
      item.code.toLowerCase().includes(keyword) ||
      item.description.toLowerCase().includes(keyword)
    );
  }
  return result;
});

const groupedDictionaries = computed(() => {
  const groups = {};
  filteredDictionaries.value.forEach(item => {
    if (!groups[item.category]) {
      groups[item.category] = {
        name: getCategoryName(item.category),
        items: []
      };
    }
    groups[item.category].items.push(item);
  });
  return groups;
});

function getCategoryName(category) {
  const categoryMap = {
    'education': '学历',
    'college': '学院',
    'department': '部门',
    'position': '职务',
    'ethnicity': '民族',
    'party_status': '党员状态',
    'league_status': '团员状态',
    'activity_type': '活动类型',
    'material_category': '物资分类',
    'custom': '自定义'
  };
  return categoryMap[category] || category;
}

async function fetchDictionaries() {
  loading.value = true;
  try {
    const response = await apiFetch('/api/data-dictionaries/');
    if (response.ok) {
      const data = await response.json();
      dictionaries.value = data.results || data.data || [];
    }
  } catch (error) {
    console.error('获取数据字典失败:', error);
  } finally {
    loading.value = false;
  }
}

async function fetchCategories() {
  try {
    const response = await apiFetch('/api/data-dictionaries/categories/');
    if (response.ok) {
      const data = await response.json();
      categories.value = data.data || [];
    }
  } catch (error) {
    console.error('获取分类失败:', error);
  }
}

function openAddModal() {
  isEdit.value = false;
  currentItem.value = {
    id: null,
    category: '',
    code: '',
    name: '',
    sort_order: 0,
    is_active: true,
    description: ''
  };
  showModal.value = true;
}

function openEditModal(item) {
  isEdit.value = true;
  currentItem.value = { ...item };
  showModal.value = true;
}

async function saveItem() {
  if (!currentItem.value.category || !currentItem.value.code || !currentItem.value.name) {
    alert('请填写必填字段');
    return;
  }

  try {
    let response;
    if (isEdit.value) {
      response = await apiFetch(`/api/data-dictionaries/${currentItem.value.id}/`, {
        method: 'PUT',
        body: JSON.stringify(currentItem.value)
      });
    } else {
      response = await apiFetch('/api/data-dictionaries/', {
        method: 'POST',
        body: JSON.stringify(currentItem.value)
      });
    }

    if (response.ok) {
      showModal.value = false;
      fetchDictionaries();
      fetchCategories();
    }
  } catch (error) {
    console.error('保存失败:', error);
    alert('保存失败');
  }
}

async function deleteItem(id, name) {
  if (!confirm(`确定要删除 "${name}" 吗？`)) return;

  try {
    const response = await apiFetch(`/api/data-dictionaries/${id}/`, {
      method: 'DELETE'
    });
    if (response.ok) {
      fetchDictionaries();
      fetchCategories();
    }
  } catch (error) {
    console.error('删除失败:', error);
    alert('删除失败');
  }
}

async function toggleStatus(item) {
  const originalStatus = item.is_active;
  item.is_active = !item.is_active;
  
  try {
    const response = await apiFetch(`/api/data-dictionaries/${item.id}/`, {
      method: 'PUT',
      body: JSON.stringify(item)
    });
    if (!response.ok) {
      item.is_active = originalStatus;
      alert('状态切换失败');
    }
  } catch (error) {
    item.is_active = originalStatus;
    alert('状态切换失败');
  }
}

onMounted(() => {
  fetchDictionaries();
  fetchCategories();
});
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>数据字典管理</h1>
      <p class="subtitle">管理学历、学院、部门等系统可配置选项</p>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <select v-model="selectedCategory" class="form-select">
          <option value="">全部分类</option>
          <option v-for="cat in categories" :key="cat[0]" :value="cat[0]">
            {{ cat[1] }}
          </option>
        </select>
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索名称或编码..."
          class="search-input"
        />
        <button class="btn btn-secondary" @click="selectedCategory = ''; searchKeyword = ''">重置</button>
      </div>
      <div class="toolbar-right">
        <button v-if="hasPermission('menu:edit')" class="btn btn-primary" @click="openAddModal">添加字典项</button>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
    </div>

    <div v-for="(group, category) in groupedDictionaries" :key="category" class="dictionary-group">
      <h2 class="group-title">{{ group.name }}</h2>
      <table class="data-table">
        <thead>
          <tr>
            <th>编码</th>
            <th>名称</th>
            <th>排序</th>
            <th>状态</th>
            <th>描述</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in group.items" :key="item.id">
            <td>{{ item.code }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.sort_order }}</td>
            <td>
              <span :class="['status-badge', item.is_active ? 'active' : 'inactive']">
                {{ item.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td>{{ item.description || '-' }}</td>
            <td>
              <button v-if="hasPermission('menu:edit')" class="action-btn edit" @click="openEditModal(item)">编辑</button>
              <button v-if="hasPermission('menu:edit')" class="action-btn status" @click="toggleStatus(item)">
                {{ item.is_active ? '禁用' : '启用' }}
              </button>
              <button v-if="hasPermission('menu:edit')" class="action-btn delete" @click="deleteItem(item.id, item.name)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="filteredDictionaries.length === 0 && !loading" class="empty-state">
      <p>暂无数据</p>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content">
        <h3>{{ isEdit ? '编辑字典项' : '添加字典项' }}</h3>
        
        <div class="form-group">
          <label>分类 <span class="required">*</span></label>
          <select v-model="currentItem.category" class="form-select">
            <option value="">请选择分类</option>
            <option v-for="cat in categories" :key="cat[0]" :value="cat[0]">
              {{ cat[1] }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>编码 <span class="required">*</span></label>
          <input v-model="currentItem.code" type="text" class="form-input" placeholder="如: bachelor" :disabled="isEdit" />
        </div>

        <div class="form-group">
          <label>名称 <span class="required">*</span></label>
          <input v-model="currentItem.name" type="text" class="form-input" placeholder="如: 本科" />
        </div>

        <div class="form-group">
          <label>排序</label>
          <input v-model.number="currentItem.sort_order" type="number" class="form-input" placeholder="数字越小越靠前" />
        </div>

        <div class="form-group">
          <label>描述</label>
          <input v-model="currentItem.description" type="text" class="form-input" placeholder="可选描述" />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="currentItem.is_active" type="checkbox" />
            启用
          </label>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="saveItem">{{ isEdit ? '保存' : '添加' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0 0 5px 0;
}

.subtitle {
  color: #666;
  margin: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.toolbar-left {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.form-select {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-input {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 200px;
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #667eea;
  color: white;
}

.btn-primary:hover {
  background-color: #5a6fd6;
}

.btn-secondary {
  background-color: #e0e0e0;
  color: #333;
}

.btn-secondary:hover {
  background-color: #d0d0d0;
}

.dictionary-group {
  margin-bottom: 30px;
}

.group-title {
  font-size: 18px;
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #667eea;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-badge.inactive {
  background-color: #ffebee;
  color: #c62828;
}

.action-btn {
  padding: 5px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  margin-right: 5px;
  transition: background-color 0.2s;
}

.action-btn.edit {
  background-color: #fff3e0;
  color: #e65100;
}

.action-btn.edit:hover {
  background-color: #ffe0b2;
}

.action-btn.status {
  background-color: #e3f2fd;
  color: #1565c0;
}

.action-btn.status:hover {
  background-color: #bbdefb;
}

.action-btn.delete {
  background-color: #ffebee;
  color: #c62828;
}

.action-btn.delete:hover {
  background-color: #ffcdd2;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 24px;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin: 0 0 20px 0;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
}

.required {
  color: #c62828;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255,255,255,0.8);
  display: flex;
  justify-content: center;
  align-items: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>