<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import * as XLSX from 'xlsx';
import { hasPermission } from '../../utils/permission';

// API基础URL
const API_BASE_URL = '/api';

// 获取token
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

// 培养记录数据
const records = ref([]);

// 积极分子列表（用于筛选）
const activists = ref([]);

// 加载状态
const isLoading = ref(false);

// 从API获取培养记录数据
const fetchRecords = async () => {
  isLoading.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/cultivation-records/`, {
      headers: getAuthHeaders()
    });
    if (response.ok) {
      const data = await response.json();
      if (data.results && data.results.length > 0) {
        records.value = data.results.map(r => ({
          id: r.id,
          activistId: r.activist,
          activistName: r.activist_name || '',
          activity: r.activity || '',
          cultivationDate: r.cultivation_date || '',
          content: r.content || '',
          cultivator: r.cultivator || '',
          evaluation: r.evaluation || ''
        }));
      } else if (Array.isArray(data) && data.length > 0) {
        records.value = data.map(r => ({
          id: r.id,
          activistId: r.activist,
          activistName: r.activist_name || '',
          activity: r.activity || '',
          cultivationDate: r.cultivation_date || '',
          content: r.content || '',
          cultivator: r.cultivator || '',
          evaluation: r.evaluation || ''
        }));
      } else {
        records.value = [];
      }
      filterRecords();
    } else {
      console.error('API请求失败:', response.status);
      showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
    }
  } catch (error) {
    console.error('加载培养记录数据失败:', error);
    showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
  } finally {
    isLoading.value = false;
  }
};

// 从API获取积极分子列表（用于筛选）
const fetchActivists = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/activists/`, {
      headers: getAuthHeaders()
    });
    if (response.ok) {
      const data = await response.json();
      if (data.results && data.results.length > 0) {
        activists.value = data.results.map(a => ({
          id: a.id,
          name: a.name
        }));
      } else if (Array.isArray(data) && data.length > 0) {
        activists.value = data.map(a => ({
          id: a.id,
          name: a.name
        }));
      } else {
        activists.value = [];
      }
    }
  } catch (error) {
    console.error('加载积极分子列表失败:', error);
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchRecords();
  fetchActivists();
});

// 统计数据
const stats = computed(() => {
  const total = records.value.length;
  const currentMonth = new Date().toISOString().slice(0, 7);
  const thisMonthRecords = records.value.filter(r => r.cultivationDate && r.cultivationDate.startsWith(currentMonth)).length;
  
  // 统计培养人数量（去重）
  const cultivatorsSet = new Set(records.value.map(r => r.cultivator).filter(c => c));
  const cultivatorCount = cultivatorsSet.size;
  
  return [
    { label: '培养记录总数', value: total, icon: '📝' },
    { label: '本月培养次数', value: thisMonthRecords, icon: '📅' },
    { label: '培养人数量', value: cultivatorCount, icon: '👨‍🏫' }
  ];
});

// 分页相关
const currentPage = ref(1);
const pageSize = 10;
const totalPages = computed(() => Math.ceil(filteredRecords.value.length / pageSize));

// 批量选择相关
const selectedRecordIds = ref([]);

// 是否全选
const isAllSelected = computed(() => {
  return paginatedRecords.value.length > 0 && 
         paginatedRecords.value.every(r => selectedRecordIds.value.includes(r.id));
});

// 切换全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    paginatedRecords.value.forEach(r => {
      const index = selectedRecordIds.value.indexOf(r.id);
      if (index !== -1) {
        selectedRecordIds.value.splice(index, 1);
      }
    });
  } else {
    paginatedRecords.value.forEach(r => {
      if (!selectedRecordIds.value.includes(r.id)) {
        selectedRecordIds.value.push(r.id);
      }
    });
  }
};

// 切换单个选择
const toggleSelect = (recordId, event) => {
  event.stopPropagation();
  const index = selectedRecordIds.value.indexOf(recordId);
  if (index === -1) {
    selectedRecordIds.value.push(recordId);
  } else {
    selectedRecordIds.value.splice(index, 1);
  }
};

// 批量删除
const deleteSelected = async () => {
  if (selectedRecordIds.value.length === 0) {
    showErrorMessage('请先选择要删除的记录');
    return;
  }
  
  if (confirm(`确定要删除选中的 ${selectedRecordIds.value.length} 条记录吗？`)) {
    isLoading.value = true;
    let successCount = 0;
    
    try {
      for (const id of selectedRecordIds.value) {
        const response = await fetch(`${API_BASE_URL}/cultivation-records/${id}/`, {
          method: 'DELETE',
          headers: getAuthHeaders()
        });
        if (response.ok || response.status === 204) {
          successCount++;
          records.value = records.value.filter(r => r.id !== id);
        }
      }
      
      selectedRecordIds.value = [];
      filterRecords();
      showSuccessMessage(`成功删除 ${successCount} 条记录！`);
    } catch (error) {
      console.error('批量删除失败:', error);
      showErrorMessage('批量删除失败，请重试');
    } finally {
      isLoading.value = false;
    }
  }
};

// 当前页数据
const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredRecords.value.slice(start, end);
});

// 可见页码
const visiblePages = computed(() => {
  const pages = [];
  const total = totalPages.value;
  const current = currentPage.value;
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    if (current <= 3) {
      for (let i = 1; i <= 5; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total);
    } else if (current >= total - 2) {
      pages.push(1);
      pages.push('...');
      for (let i = total - 4; i <= total; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);
      pages.push('...');
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total);
    }
  }
  
  return pages;
});

// 筛选条件
const filters = ref({
  activist: ''
});

// 搜索
const searchQuery = ref('');

// 过滤后的记录
const filteredRecords = ref([]);

// 模态框控制
const showAddModal = ref(false);
const showEditModal = ref(false);
const showDetailModal = ref(false);
const showSuccess = ref(false);
const showError = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

// 当前编辑的记录
const currentRecord = ref({
  id: null,
  activistId: null,
  activistName: '',
  activity: '',
  cultivationDate: '',
  content: '',
  cultivator: '',
  evaluation: ''
});

// 详情记录
const detailRecord = ref(null);

// 表单验证错误
const formErrors = ref({});

// 当前编辑的记录ID
const editingRecordId = ref(null);

// 过滤记录
const filterRecords = () => {
  filteredRecords.value = records.value.filter(r => {
    const matchActivist = !filters.value.activist || r.activistId === filters.value.activist;
    const matchSearch = !searchQuery.value || 
      r.activistName.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      r.activity.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      r.cultivator.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      r.content.toLowerCase().includes(searchQuery.value.toLowerCase());
    return matchActivist && matchSearch;
  });
  currentPage.value = 1;
  scrollToTop();
};

// 滚动到顶部
const scrollToTop = () => {
  nextTick(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
};

// 分页控制
const goToPage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  isLoading.value = true;
  setTimeout(() => {
    currentPage.value = page;
    scrollToTop();
    isLoading.value = false;
  }, 200);
};

const prevPage = () => {
  goToPage(currentPage.value - 1);
};

const nextPage = () => {
  goToPage(currentPage.value + 1);
};

// 查看详情
const viewDetail = (record) => {
  detailRecord.value = record;
  showDetailModal.value = true;
};

// 重置筛选
const resetFilters = () => {
  filters.value = {
    activist: ''
  };
  searchQuery.value = '';
  filterRecords();
};

// 验证表单
const validateForm = () => {
  const errors = {};
  
  if (!currentRecord.value.activistId) {
    errors.activistId = '请选择积极分子';
  }
  
  if (!currentRecord.value.activity || currentRecord.value.activity.trim() === '') {
    errors.activity = '请输入培养活动';
  }
  
  if (!currentRecord.value.cultivationDate) {
    errors.cultivationDate = '请选择培养时间';
  }
  
  if (!currentRecord.value.content || currentRecord.value.content.trim() === '') {
    errors.content = '请输入培养内容';
  }
  
  if (!currentRecord.value.cultivator || currentRecord.value.cultivator.trim() === '') {
    errors.cultivator = '请输入培养人';
  }
  
  if (!currentRecord.value.evaluation || currentRecord.value.evaluation.trim() === '') {
    errors.evaluation = '请输入培养人评价';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
};

// 打开添加模态框
const openAddModal = () => {
  currentRecord.value = {
    id: null,
    activistId: null,
    activistName: '',
    activity: '',
    cultivationDate: new Date().toISOString().split('T')[0],
    content: '',
    cultivator: '',
    evaluation: ''
  };
  formErrors.value = {};
  showAddModal.value = true;
};

// 打开编辑模态框
const openEditModal = (record) => {
  currentRecord.value = { ...record };
  editingRecordId.value = record.id;
  formErrors.value = {};
  showEditModal.value = true;
};

// 选择积极分子时更新姓名
const onActivistChange = (activistId) => {
  const activist = activists.value.find(a => a.id === activistId);
  if (activist) {
    currentRecord.value.activistName = activist.name;
  }
};

// 添加记录
const addRecord = async () => {
  if (!validateForm()) return;
  
  try {
    const apiData = {
      activist: currentRecord.value.activistId,
      activity: currentRecord.value.activity,
      cultivation_date: currentRecord.value.cultivationDate,
      content: currentRecord.value.content,
      cultivator: currentRecord.value.cultivator,
      evaluation: currentRecord.value.evaluation
    };
    
    const response = await fetch(`${API_BASE_URL}/cultivation-records/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const newRecord = await response.json();
      records.value.unshift({
        id: newRecord.id,
        activistId: newRecord.activist_id,
        activistName: newRecord.activist_name || '',
        activity: newRecord.activity || '',
        cultivationDate: newRecord.cultivation_date || '',
        content: newRecord.content || '',
        cultivator: newRecord.cultivator || '',
        evaluation: newRecord.evaluation || ''
      });
      
      showSuccessMessage('培养记录添加成功！');
      showAddModal.value = false;
      filterRecords();
    } else {
      const error = await response.json();
      showErrorMessage('添加失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('添加记录失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }
};

// 编辑记录
const editRecord = async () => {
  if (!validateForm()) return;
  
  try {
    const apiData = {
      activist: currentRecord.value.activistId,
      activity: currentRecord.value.activity,
      cultivation_date: currentRecord.value.cultivationDate,
      content: currentRecord.value.content,
      cultivator: currentRecord.value.cultivator,
      evaluation: currentRecord.value.evaluation
    };
    
    const response = await fetch(`${API_BASE_URL}/cultivation-records/${editingRecordId.value}/`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const updatedRecord = await response.json();
      const index = records.value.findIndex(r => r.id === editingRecordId.value);
      if (index !== -1) {
        records.value[index] = {
          id: updatedRecord.id,
          activistId: updatedRecord.activist_id,
          activistName: updatedRecord.activist_name || '',
          activity: updatedRecord.activity || '',
          cultivationDate: updatedRecord.cultivation_date || '',
          content: updatedRecord.content || '',
          cultivator: updatedRecord.cultivator || '',
          evaluation: updatedRecord.evaluation || ''
        };
      }
      
      showSuccessMessage('培养记录更新成功！');
    } else {
      const error = await response.json();
      showErrorMessage('更新失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('更新记录失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }
  
  showEditModal.value = false;
  filterRecords();
};

// 删除记录
const deleteRecord = async (record) => {
  if (confirm(`确定要删除「${record.activistName}」的培养记录吗？`)) {
    try {
      const response = await fetch(`${API_BASE_URL}/cultivation-records/${record.id}/`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      if (response.ok || response.status === 204) {
        records.value = records.value.filter(r => r.id !== record.id);
        showSuccessMessage('记录删除成功！');
        filterRecords();
      } else {
        showErrorMessage('删除失败');
      }
    } catch (error) {
      console.error('删除记录失败:', error);
      showErrorMessage('网络错误，请稍后重试');
    }
  }
};

// 显示成功消息
const showSuccessMessage = (msg) => {
  successMessage.value = msg;
  showSuccess.value = true;
  setTimeout(() => {
    showSuccess.value = false;
  }, 3000);
};

// 显示错误消息
const showErrorMessage = (msg) => {
  errorMessage.value = msg;
  showError.value = true;
  setTimeout(() => {
    showError.value = false;
  }, 3000);
};

// 导出Excel
const exportToExcel = () => {
  try {
    const exportData = filteredRecords.value.map(r => ({
      '积极分子姓名': r.activistName,
      '培养活动': r.activity,
      '培养时间': r.cultivationDate,
      '培养内容': r.content,
      '培养人': r.cultivator,
      '培养人评价': r.evaluation
    }));
    
    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '培养记录');
    
    // 设置列宽
    worksheet['!cols'] = [
      { wch: 12 }, { wch: 20 }, { wch: 12 }, { wch: 40 }, { wch: 10 }, { wch: 40 }
    ];
    
    const fileName = `入党积极分子培养记录_${new Date().toISOString().split('T')[0]}.xlsx`;
    XLSX.writeFile(workbook, fileName);
    
    showSuccessMessage('数据导出成功！');
  } catch (error) {
    showErrorMessage('导出失败，请重试');
    console.error(error);
  }
};
</script>

<template>
  <div class="cultivation-page">
    <!-- 成功提示 -->
    <div v-if="showSuccess" class="success-toast">
      <span class="icon">✓</span>
      <span>{{ successMessage }}</span>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="showError" class="error-toast">
      <span class="icon">✕</span>
      <span>{{ errorMessage }}</span>
    </div>
    
    <header class="page-header">
      <h1>入党积极分子培养记录管理</h1>
    </header>
    
    <!-- 统计卡片 -->
    <div class="stats-row">
      <div v-for="stat in stats" :key="stat.label" class="stat-item">
        <div class="stat-icon">{{ stat.icon }}</div>
        <div class="stat-content">
          <div class="stat-num">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <label>积极分子：</label>
        <select v-model="filters.activist" @change="filterRecords" class="filter-select" :class="{ active: filters.activist }">
          <option value="">全部积极分子</option>
          <option v-for="a in activists" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
      </div>
      <div class="filter-group search-group">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索积极分子姓名、培养活动、培养人..." 
          class="search-input"
          @input="filterRecords"
        />
      </div>
      <button v-if="filters.activist || searchQuery" class="btn btn-text" @click="resetFilters">重置筛选</button>
    </div>
    
    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="result-count">共 {{ filteredRecords.length }} 条结果</span>
        <span v-if="selectedRecordIds.length > 0" class="selected-count">已选择 {{ selectedRecordIds.length }} 条</span>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedRecordIds.length > 0 && hasPermission('party:delete')" class="btn btn-danger" @click="deleteSelected">批量删除</button>
        <button v-if="hasPermission('party:edit')" class="btn btn-secondary" @click="exportToExcel">导出数据</button>
        <button v-if="hasPermission('party:add')" class="btn btn-primary" @click="openAddModal">添加记录</button>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    
    <div class="table-container">
      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="isAllSelected" @change="toggleSelectAll" />
                </label>
              </th>
              <th>ID</th>
              <th>积极分子姓名</th>
              <th>培养活动</th>
              <th>培养时间</th>
              <th>培养内容</th>
              <th>培养人</th>
              <th>培养人评价</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in paginatedRecords" :key="record.id" @click="viewDetail(record)" class="clickable-row" :class="{ selected: selectedRecordIds.includes(record.id) }">
              <td @click.stop>
                <label class="checkbox-label">
                  <input type="checkbox" :checked="selectedRecordIds.includes(record.id)" @change="toggleSelect(record.id, $event)" />
                </label>
              </td>
              <td>{{ record.id }}</td>
              <td><span class="activist-tag">{{ record.activistName }}</span></td>
              <td>{{ record.activity }}</td>
              <td>{{ record.cultivationDate }}</td>
              <td class="content-cell">{{ record.content }}</td>
              <td><span class="cultivator-tag">{{ record.cultivator }}</span></td>
              <td class="evaluation-cell">{{ record.evaluation }}</td>
              <td @click.stop>
                <button v-if="hasPermission('party:edit')" class="action-btn edit" @click="openEditModal(record)">编辑</button>
                <button v-if="hasPermission('party:delete')" class="action-btn delete" @click="deleteRecord(record)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 空状态 -->
      <div v-if="filteredRecords.length === 0 && !isLoading" class="empty-state">
        <p>暂无培养记录数据</p>
      </div>
    </div>
    
    <!-- 分页 -->
    <div v-if="totalPages > 0" class="pagination">
      <div class="pagination-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ filteredRecords.length }} 条记录
      </div>
      <div class="pagination-controls">
        <button class="page-btn" @click="prevPage" :disabled="currentPage === 1">上一页</button>
        <button 
          v-for="page in visiblePages" 
          :key="page" 
          class="page-btn" 
          :class="{ active: page === currentPage, ellipsis: page === '...' }"
          @click="page !== '...' && goToPage(page)"
        >
          {{ page }}
        </button>
        <button class="page-btn" @click="nextPage" :disabled="currentPage === totalPages">下一页</button>
      </div>
    </div>
    
    <!-- 添加记录模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加培养记录</h3>
          <button class="close-btn" @click="showAddModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item full-width">
              <label>积极分子 <span class="required">*</span></label>
              <select 
                v-model="currentRecord.activistId" 
                class="form-select" 
                :class="{ 'error': formErrors.activistId }"
                @change="onActivistChange(currentRecord.activistId)"
              >
                <option value="">请选择积极分子</option>
                <option v-for="a in activists" :key="a.id" :value="a.id">{{ a.name }}</option>
              </select>
              <span v-if="formErrors.activistId" class="error-text">{{ formErrors.activistId }}</span>
            </div>
            <div class="form-item">
              <label>培养活动 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.activity" 
                class="form-input" 
                :class="{ 'error': formErrors.activity }"
                placeholder="如：入党积极分子培训班、社会实践活动等"
              />
              <span v-if="formErrors.activity" class="error-text">{{ formErrors.activity }}</span>
            </div>
            <div class="form-item">
              <label>培养时间 <span class="required">*</span></label>
              <input 
                type="date" 
                v-model="currentRecord.cultivationDate" 
                class="form-input" 
                :class="{ 'error': formErrors.cultivationDate }"
              />
              <span v-if="formErrors.cultivationDate" class="error-text">{{ formErrors.cultivationDate }}</span>
            </div>
            <div class="form-item full-width">
              <label>培养内容 <span class="required">*</span></label>
              <textarea 
                v-model="currentRecord.content" 
                class="form-textarea" 
                :class="{ 'error': formErrors.content }"
                placeholder="详细描述培养活动内容"
                rows="3"
              ></textarea>
              <span v-if="formErrors.content" class="error-text">{{ formErrors.content }}</span>
            </div>
            <div class="form-item">
              <label>培养人 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.cultivator" 
                class="form-input" 
                :class="{ 'error': formErrors.cultivator }"
                placeholder="培养人姓名"
              />
              <span v-if="formErrors.cultivator" class="error-text">{{ formErrors.cultivator }}</span>
            </div>
            <div class="form-item full-width">
              <label>培养人评价 <span class="required">*</span></label>
              <textarea 
                v-model="currentRecord.evaluation" 
                class="form-textarea" 
                :class="{ 'error': formErrors.evaluation }"
                placeholder="培养人对该活动的评价"
                rows="3"
              ></textarea>
              <span v-if="formErrors.evaluation" class="error-text">{{ formErrors.evaluation }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="addRecord">添加</button>
        </div>
      </div>
    </div>
    
    <!-- 编辑记录模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑培养记录</h3>
          <button class="close-btn" @click="showEditModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item full-width">
              <label>积极分子 <span class="required">*</span></label>
              <select 
                v-model="currentRecord.activistId" 
                class="form-select" 
                :class="{ 'error': formErrors.activistId }"
                @change="onActivistChange(currentRecord.activistId)"
              >
                <option value="">请选择积极分子</option>
                <option v-for="a in activists" :key="a.id" :value="a.id">{{ a.name }}</option>
              </select>
              <span v-if="formErrors.activistId" class="error-text">{{ formErrors.activistId }}</span>
            </div>
            <div class="form-item">
              <label>培养活动 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.activity" 
                class="form-input" 
                :class="{ 'error': formErrors.activity }"
                placeholder="如：入党积极分子培训班、社会实践活动等"
              />
              <span v-if="formErrors.activity" class="error-text">{{ formErrors.activity }}</span>
            </div>
            <div class="form-item">
              <label>培养时间 <span class="required">*</span></label>
              <input 
                type="date" 
                v-model="currentRecord.cultivationDate" 
                class="form-input" 
                :class="{ 'error': formErrors.cultivationDate }"
              />
              <span v-if="formErrors.cultivationDate" class="error-text">{{ formErrors.cultivationDate }}</span>
            </div>
            <div class="form-item full-width">
              <label>培养内容 <span class="required">*</span></label>
              <textarea 
                v-model="currentRecord.content" 
                class="form-textarea" 
                :class="{ 'error': formErrors.content }"
                placeholder="详细描述培养活动内容"
                rows="3"
              ></textarea>
              <span v-if="formErrors.content" class="error-text">{{ formErrors.content }}</span>
            </div>
            <div class="form-item">
              <label>培养人 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.cultivator" 
                class="form-input" 
                :class="{ 'error': formErrors.cultivator }"
                placeholder="培养人姓名"
              />
              <span v-if="formErrors.cultivator" class="error-text">{{ formErrors.cultivator }}</span>
            </div>
            <div class="form-item full-width">
              <label>培养人评价 <span class="required">*</span></label>
              <textarea 
                v-model="currentRecord.evaluation" 
                class="form-textarea" 
                :class="{ 'error': formErrors.evaluation }"
                placeholder="培养人对该活动的评价"
                rows="3"
              ></textarea>
              <span v-if="formErrors.evaluation" class="error-text">{{ formErrors.evaluation }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditModal = false">取消</button>
          <button class="btn btn-primary" @click="editRecord">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-content detail-modal" v-if="detailRecord">
        <div class="modal-header">
          <h3>培养记录详情</h3>
          <button class="close-btn" @click="showDetailModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-header">
            <div class="detail-icon">📝</div>
            <div class="detail-basic">
              <h2 class="detail-title">{{ detailRecord.activity }}</h2>
              <p class="detail-subtitle">{{ detailRecord.activistName }} · {{ detailRecord.cultivationDate }}</p>
            </div>
          </div>
          <div class="detail-info">
            <div class="info-grid">
              <div class="info-item">
                <label>记录ID</label>
                <span>{{ detailRecord.id }}</span>
              </div>
              <div class="info-item">
                <label>积极分子姓名</label>
                <span class="activist-tag">{{ detailRecord.activistName }}</span>
              </div>
              <div class="info-item">
                <label>培养活动</label>
                <span>{{ detailRecord.activity }}</span>
              </div>
              <div class="info-item">
                <label>培养时间</label>
                <span>{{ detailRecord.cultivationDate }}</span>
              </div>
              <div class="info-item">
                <label>培养人</label>
                <span class="cultivator-tag">{{ detailRecord.cultivator }}</span>
              </div>
            </div>
            <div class="info-section">
              <h4 class="info-section-title">培养内容</h4>
              <p class="info-text">{{ detailRecord.content }}</p>
            </div>
            <div class="info-section">
              <h4 class="info-section-title">培养人评价</h4>
              <p class="info-text">{{ detailRecord.evaluation }}</p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal = false">关闭</button>
          <button class="btn btn-primary" @click="openEditModal(detailRecord); showDetailModal = false">编辑信息</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cultivation-page {
  padding: 32px;
  min-height: 100vh;
  background: #fafafa;
  position: relative;
}

.success-toast,
.error-toast {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: 8px;
  animation: slideDown 0.3s ease;
}

.success-toast {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #52c41a;
}

.error-toast {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  color: #ff4d4f;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
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

.stats-row {
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
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 28px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  color: #ffffff;
}

.stat-content {
  flex: 1;
}

.stat-num {
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
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  color: #666666;
  white-space: nowrap;
}

.filter-select {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  background: #ffffff;
  color: #333333;
  min-width: 150px;
  transition: all 0.2s;
}

.filter-select:focus {
  outline: none;
  border-color: #1890ff;
}

.filter-select.active {
  border-color: #1890ff;
  background: #e6f7ff;
}

.search-group {
  flex: 1;
  min-width: 250px;
}

.search-input {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  width: 100%;
}

.search-input:focus {
  outline: none;
  border-color: #1890ff;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.result-count {
  font-size: 14px;
  color: #666666;
}

.selected-count {
  font-size: 14px;
  color: #1890ff;
  font-weight: 500;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.btn-secondary {
  background: #ffffff;
  color: #1890ff;
  border: 1px solid #1890ff;
}

.btn-secondary:hover {
  background: #e6f7ff;
}

.btn-text {
  background: transparent;
  color: #1890ff;
  border: none;
  padding: 8px 16px;
}

.btn-text:hover {
  background: #e6f7ff;
}

.btn-danger {
  background: #ff4d4f;
  color: #ffffff;
}

.btn-danger:hover {
  background: #ff7875;
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.clickable-row.selected {
  background-color: #e6f7ff;
}

.table-container {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 32px;
}

.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1000px;
}

.records-table th,
.records-table td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.records-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333333;
  font-size: 14px;
}

.records-table td {
  font-size: 14px;
  color: #333333;
}

.clickable-row {
  cursor: pointer;
  transition: background-color 0.15s;
}

.clickable-row:hover {
  background-color: #f5f5f5;
}

.content-cell,
.evaluation-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-overlay {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.95);
  padding: 24px 48px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 2000;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f0f0f0;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  padding: 48px;
  text-align: center;
  color: #999;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-top: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.pagination-info {
  font-size: 14px;
  color: #666666;
}

.pagination-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #ffffff;
  color: #333333;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
  min-width: 40px;
}

.page-btn:hover:not(:disabled):not(.ellipsis) {
  border-color: #1890ff;
  color: #1890ff;
}

.page-btn.active {
  background: #1890ff;
  border-color: #1890ff;
  color: #ffffff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-btn.ellipsis {
  border: none;
  cursor: default;
  background: transparent;
}

.activist-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.cultivator-tag {
  padding: 4px 12px;
  background: #fff7e6;
  color: #fa8c16;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
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
  background: #ffa39e;
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
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
}

.detail-modal {
  width: 700px;
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
  max-height: 60vh;
  overflow-y: auto;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item.full-width {
  width: 100%;
}

.form-item label {
  font-size: 14px;
  color: #333333;
}

.form-item label .required {
  color: #ff4d4f;
}

.form-input,
.form-select {
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.form-textarea {
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
}

.form-input.error,
.form-select.error,
.form-textarea.error {
  border-color: #ff4d4f;
}

.error-text {
  font-size: 12px;
  color: #ff4d4f;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}

/* 详情模态框样式 */
.detail-header {
  display: flex;
  gap: 20px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  margin-bottom: 20px;
  color: #ffffff;
}

.detail-icon {
  font-size: 48px;
}

.detail-basic {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #ffffff;
}

.detail-subtitle {
  font-size: 14px;
  margin: 0;
  opacity: 0.9;
}

.detail-info {
  padding: 0 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item label {
  font-size: 13px;
  color: #999999;
  font-weight: 500;
}

.info-item span {
  font-size: 14px;
  color: #333333;
  font-weight: 500;
}

.info-section {
  margin-bottom: 16px;
}

.info-section-title {
  font-size: 14px;
  color: #667eea;
  font-weight: 600;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 2px solid #667eea;
}

.info-text {
  font-size: 14px;
  color: #333333;
  line-height: 1.6;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .modal-content {
    width: 95%;
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-group {
    min-width: 100%;
  }
}
</style>