<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 借用记录数据
const borrowRecords = ref([]);

// 加载状态
const isLoading = ref(false);

// 从API加载借用记录数据
const fetchBorrowRecords = async () => {
  isLoading.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/material-borrows/`);
    if (response.ok) {
      const data = await response.json();
      if (data.results && data.results.length > 0) {
        borrowRecords.value = data.results.map(record => ({
          id: record.id,
          borrowerName: record.borrower || '',
          borrowerPhone: record.borrower_phone || '',
          borrowDate: record.borrow_date || '',
          expectedReturnDate: record.expected_return_date || '',
          actualReturnDate: record.actual_return_date || '',
          status: record.status || '借用中',
          purpose: record.purpose || '',
          remarks: record.remarks || '',
          materialId: record.material_id || '',
          materialName: record.material_name || '',
          createdAt: record.created_at || '',
          updatedAt: record.updated_at || ''
        }));
      } else if (Array.isArray(data)) {
        borrowRecords.value = data.map(record => ({
          id: record.id,
          borrowerName: record.borrower || '',
          borrowerPhone: record.borrower_phone || '',
          borrowDate: record.borrow_date || '',
          expectedReturnDate: record.expected_return_date || '',
          actualReturnDate: record.actual_return_date || '',
          status: record.status || '借用中',
          purpose: record.purpose || '',
          remarks: record.remarks || '',
          materialId: record.material_id || '',
          materialName: record.material_name || '',
          createdAt: record.created_at || '',
          updatedAt: record.updated_at || ''
        }));
      } else {
        borrowRecords.value = [];
      }
      filterRecords();
    } else {
      console.error('API请求失败:', response.status);
      showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
    }
  } catch (error) {
    console.error('加载借用记录数据失败:', error);
    showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
  } finally {
    isLoading.value = false;
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchBorrowRecords();
});

// 统计数据
const stats = computed(() => {
  const total = borrowRecords.value.length;
  const borrowing = borrowRecords.value.filter(r => r.status === '借用中').length;
  const returned = borrowRecords.value.filter(r => r.status === '已归还').length;
  const overdue = borrowRecords.value.filter(r => {
    if (r.status !== '借用中') return false;
    const today = new Date();
    const expectedDate = new Date(r.expectedReturnDate);
    return expectedDate < today;
  }).length;
  
  return [
    { label: '总借用数', value: total },
    { label: '借用中', value: borrowing },
    { label: '已归还', value: returned },
    { label: '逾期数量', value: overdue }
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
        const response = await fetch(`${API_BASE_URL}/material-borrows/${id}/`, {
          method: 'DELETE',
        });
        if (response.ok || response.status === 204) {
          successCount++;
          borrowRecords.value = borrowRecords.value.filter(r => r.id !== id);
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
  status: '全部',
  dateRange: ''
});

// 状态列表
const statuses = ['全部', '借用中', '已归还', '已逾期'];

// 搜索
const searchQuery = ref('');

// 过滤记录
const filteredRecords = ref(borrowRecords.value);

// 模态框控制
const showAddModal = ref(false);
const showEditModal = ref(false);
const showDetailModal = ref(false);
const showDeleteConfirm = ref(false);
const showSuccess = ref(false);
const showError = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

// 当前编辑的记录
const currentRecord = ref({
  id: null,
  borrowerName: '',
  borrowerPhone: '',
  borrowDate: new Date().toISOString().split('T')[0],
  expectedReturnDate: '',
  actualReturnDate: '',
  status: '借用中',
  purpose: '',
  remarks: '',
  materialId: '',
  materialName: ''
});

// 详情记录
const detailRecord = ref(null);

// 待删除记录
const recordToDelete = ref(null);

// 表单验证错误
const formErrors = ref({});

// 当前编辑的记录ID
const editingRecordId = ref(null);

// 过滤记录
const filterRecords = () => {
  filteredRecords.value = borrowRecords.value.filter(r => {
    const matchStatus = filters.value.status === '全部' || 
      (filters.value.status === '已逾期' && r.status === '借用中' && new Date(r.expectedReturnDate) < new Date()) ||
      (filters.value.status !== '已逾期' && r.status === filters.value.status);
    const matchSearch = !searchQuery.value || 
      r.borrowerName.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
      r.id.toString().includes(searchQuery.value) ||
      r.borrowerPhone.includes(searchQuery.value) ||
      r.purpose.toLowerCase().includes(searchQuery.value.toLowerCase());
    return matchStatus && matchSearch;
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
    status: '全部',
    dateRange: ''
  };
  searchQuery.value = '';
  filterRecords();
};

// 验证表单
const validateForm = () => {
  const errors = {};
  
  if (!currentRecord.value.borrowerName || currentRecord.value.borrowerName.trim() === '') {
    errors.borrowerName = '请输入借用人员姓名';
  }
  
  if (!currentRecord.value.borrowerPhone) {
    errors.borrowerPhone = '请输入联系电话';
  } else if (!/^1[3-9]\d{9}$/.test(currentRecord.value.borrowerPhone)) {
    errors.borrowerPhone = '请输入有效的手机号码';
  }
  
  if (!currentRecord.value.borrowDate) {
    errors.borrowDate = '请选择借用日期';
  }
  
  if (!currentRecord.value.expectedReturnDate) {
    errors.expectedReturnDate = '请选择预计归还日期';
  }
  
  if (!currentRecord.value.purpose || currentRecord.value.purpose.trim() === '') {
    errors.purpose = '请输入借用用途';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
};

// 打开添加模态框
const openAddModal = () => {
  currentRecord.value = {
    id: null,
    borrowerName: '',
    borrowerPhone: '',
    borrowDate: new Date().toISOString().split('T')[0],
    expectedReturnDate: '',
    actualReturnDate: '',
    status: '借用中',
    purpose: '',
    remarks: '',
    materialId: '',
    materialName: ''
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

// 添加记录
const addRecord = async () => {
  if (!validateForm()) return;
  
  try {
    const apiData = {
      borrower_name: currentRecord.value.borrowerName,
      borrower_phone: currentRecord.value.borrowerPhone,
      borrow_date: currentRecord.value.borrowDate,
      expected_return_date: currentRecord.value.expectedReturnDate,
      actual_return_date: currentRecord.value.actualReturnDate || null,
      status: currentRecord.value.status,
      purpose: currentRecord.value.purpose,
      remarks: currentRecord.value.remarks || '',
      material_id: currentRecord.value.materialId || '',
      material_name: currentRecord.value.materialName || ''
    };
    
    const response = await fetch(`${API_BASE_URL}/material-borrows/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const newRecord = await response.json();
      borrowRecords.value.unshift({
        id: newRecord.id,
        borrowerName: newRecord.borrower_name || '',
        borrowerPhone: newRecord.borrower_phone || '',
        borrowDate: newRecord.borrow_date || '',
        expectedReturnDate: newRecord.expected_return_date || '',
        actualReturnDate: newRecord.actual_return_date || '',
        status: newRecord.status || '借用中',
        purpose: newRecord.purpose || '',
        remarks: newRecord.remarks || '',
        materialId: newRecord.material_id || '',
        materialName: newRecord.material_name || '',
        createdAt: newRecord.created_at || '',
        updatedAt: newRecord.updated_at || ''
      });
      
      showSuccessMessage('借用记录添加成功！');
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
      borrower_name: currentRecord.value.borrowerName,
      borrower_phone: currentRecord.value.borrowerPhone,
      borrow_date: currentRecord.value.borrowDate,
      expected_return_date: currentRecord.value.expectedReturnDate,
      actual_return_date: currentRecord.value.actualReturnDate || null,
      status: currentRecord.value.status,
      purpose: currentRecord.value.purpose,
      remarks: currentRecord.value.remarks || '',
      material_id: currentRecord.value.materialId || '',
      material_name: currentRecord.value.materialName || ''
    };
    
    const response = await fetch(`${API_BASE_URL}/material-borrows/${editingRecordId.value}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const updatedRecord = await response.json();
      const index = borrowRecords.value.findIndex(r => r.id === editingRecordId.value);
      if (index !== -1) {
        borrowRecords.value[index] = {
          id: updatedRecord.id,
          borrowerName: updatedRecord.borrower_name || '',
          borrowerPhone: updatedRecord.borrower_phone || '',
          borrowDate: updatedRecord.borrow_date || '',
          expectedReturnDate: updatedRecord.expected_return_date || '',
          actualReturnDate: updatedRecord.actual_return_date || '',
          status: updatedRecord.status || '借用中',
          purpose: updatedRecord.purpose || '',
          remarks: updatedRecord.remarks || '',
          materialId: updatedRecord.material_id || '',
          materialName: updatedRecord.material_name || '',
          createdAt: updatedRecord.created_at || '',
          updatedAt: updatedRecord.updated_at || ''
        };
      }
      
      showSuccessMessage('记录更新成功！');
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

// 归还物资
const returnMaterial = async (record) => {
  if (confirm(`确定要将「${record.borrowerName}」借用的物资标记为已归还吗？`)) {
    try {
      const response = await fetch(`${API_BASE_URL}/material-borrows/${record.id}/return_borrow/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        const index = borrowRecords.value.findIndex(r => r.id === record.id);
        const actualReturnDate = result.data?.actual_return_date || new Date().toISOString().split('T')[0];
        if (index !== -1) {
          borrowRecords.value[index].status = '已归还';
          borrowRecords.value[index].actualReturnDate = actualReturnDate;
        }
        // 更新详情弹窗数据
        if (detailRecord.value && detailRecord.value.id === record.id) {
          detailRecord.value.status = '已归还';
          detailRecord.value.actualReturnDate = actualReturnDate;
        }
        showSuccessMessage('物资归还成功！');
        filterRecords();
      } else {
        showErrorMessage('归还失败');
      }
    } catch (error) {
      console.error('归还物资失败:', error);
      showErrorMessage('网络错误，请稍后重试');
    }
  }
};

// 打开删除确认模态框
const openDeleteConfirm = (record) => {
  recordToDelete.value = record;
  showDeleteConfirm.value = true;
};

// 删除记录
const deleteRecord = async () => {
  if (!recordToDelete.value) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}/material-borrows/${recordToDelete.value.id}/`, {
      method: 'DELETE',
    });
    
    if (response.ok || response.status === 204) {
      borrowRecords.value = borrowRecords.value.filter(r => r.id !== recordToDelete.value.id);
      showSuccessMessage('记录删除成功！');
      filterRecords();
    } else {
      showErrorMessage('删除失败');
    }
  } catch (error) {
    console.error('删除记录失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }
  
  showDeleteConfirm.value = false;
  recordToDelete.value = null;
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

// 判断是否逾期
const isOverdue = (record) => {
  if (record.status !== '借用中') return false;
  const today = new Date();
  const expectedDate = new Date(record.expectedReturnDate);
  return expectedDate < today;
};

// 获取状态显示
const getStatusDisplay = (record) => {
  if (record.status === '借用中' && isOverdue(record)) {
    return '已逾期';
  }
  return record.status;
};
</script>

<template>
  <div class="borrow-page">
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
      <h1>物资借用记录管理</h1>
    </header>
    
    <div class="stats-row">
      <div v-for="stat in stats" :key="stat.label" class="stat-item">
        <div class="stat-num">{{ stat.value }}</div>
        <div class="stat-label">{{ stat.label }}</div>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <label>状态：</label>
        <select v-model="filters.status" @change="filterRecords" class="filter-select" :class="{ active: filters.status !== '全部' }">
          <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div class="filter-group search-group">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索借用人员、电话、用途..." 
          class="search-input"
          @input="filterRecords"
        />
      </div>
      <button v-if="filters.status !== '全部' || searchQuery" class="btn btn-text" @click="resetFilters">重置筛选</button>
    </div>
    
    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="result-count">共 {{ filteredRecords.length }} 条结果</span>
        <span v-if="selectedRecordIds.length > 0" class="selected-count">已选择 {{ selectedRecordIds.length }} 条</span>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedRecordIds.length > 0" class="btn btn-danger" @click="deleteSelected">批量删除</button>
        <button class="btn btn-primary" @click="openAddModal">添加借用记录</button>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    
    <div class="table-container">
      <div class="table-scroll">
        <table class="borrow-table">
          <thead>
            <tr>
              <th>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="isAllSelected" @change="toggleSelectAll" />
                </label>
              </th>
              <th>ID</th>
              <th>借用人员</th>
              <th>联系电话</th>
              <th>借用日期</th>
              <th>预计归还日期</th>
              <th>状态</th>
              <th>借用用途</th>
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
              <td>{{ record.borrowerName }}</td>
              <td>{{ record.borrowerPhone }}</td>
              <td>{{ record.borrowDate }}</td>
              <td>{{ record.expectedReturnDate }}</td>
              <td>
                <span class="status-tag" :class="{
                  '借用中': record.status === '借用中' && !isOverdue(record),
                  '已归还': record.status === '已归还',
                  '已逾期': isOverdue(record)
                }">
                  {{ getStatusDisplay(record) }}
                </span>
              </td>
              <td>{{ record.purpose }}</td>
              <td @click.stop>
                <button class="action-btn view" @click="viewDetail(record)">查看</button>
                <button class="action-btn edit" @click="openEditModal(record)">编辑</button>
                <button v-if="record.status === '借用中'" class="action-btn return" @click="returnMaterial(record)">归还</button>
                <button class="action-btn delete" @click="openDeleteConfirm(record)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
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
    
    <!-- 添加借用记录模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加借用记录</h3>
          <button class="close-btn" @click="showAddModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>借用人员 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.borrowerName" 
                class="form-input" 
                :class="{ 'error': formErrors.borrowerName }"
                placeholder="请输入借用人员姓名"
              />
              <span v-if="formErrors.borrowerName" class="error-text">{{ formErrors.borrowerName }}</span>
            </div>
            <div class="form-item">
              <label>联系电话 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.borrowerPhone" 
                class="form-input" 
                :class="{ 'error': formErrors.borrowerPhone }"
                placeholder="13812345678"
              />
              <span v-if="formErrors.borrowerPhone" class="error-text">{{ formErrors.borrowerPhone }}</span>
            </div>
            <div class="form-item">
              <label>借用日期 <span class="required">*</span></label>
              <input 
                type="date" 
                v-model="currentRecord.borrowDate" 
                class="form-input" 
                :class="{ 'error': formErrors.borrowDate }"
              />
              <span v-if="formErrors.borrowDate" class="error-text">{{ formErrors.borrowDate }}</span>
            </div>
            <div class="form-item">
              <label>预计归还日期 <span class="required">*</span></label>
              <input 
                type="date" 
                v-model="currentRecord.expectedReturnDate" 
                class="form-input" 
                :class="{ 'error': formErrors.expectedReturnDate }"
              />
              <span v-if="formErrors.expectedReturnDate" class="error-text">{{ formErrors.expectedReturnDate }}</span>
            </div>
            <div class="form-item">
              <label>借用用途 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.purpose" 
                class="form-input" 
                :class="{ 'error': formErrors.purpose }"
                placeholder="请输入借用用途"
              />
              <span v-if="formErrors.purpose" class="error-text">{{ formErrors.purpose }}</span>
            </div>
            <div class="form-item">
              <label>物资名称</label>
              <input 
                type="text" 
                v-model="currentRecord.materialName" 
                class="form-input" 
                placeholder="请输入物资名称"
              />
            </div>
            <div class="form-item full-width">
              <label>备注</label>
              <textarea 
                v-model="currentRecord.remarks" 
                class="form-textarea" 
                placeholder="请输入备注信息"
                rows="3"
              ></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="addRecord">添加</button>
        </div>
      </div>
    </div>
    
    <!-- 编辑借用记录模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑借用记录</h3>
          <button class="close-btn" @click="showEditModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>借用人员 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.borrowerName" 
                class="form-input" 
                :class="{ 'error': formErrors.borrowerName }"
              />
              <span v-if="formErrors.borrowerName" class="error-text">{{ formErrors.borrowerName }}</span>
            </div>
            <div class="form-item">
              <label>联系电话 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.borrowerPhone" 
                class="form-input" 
                :class="{ 'error': formErrors.borrowerPhone }"
              />
              <span v-if="formErrors.borrowerPhone" class="error-text">{{ formErrors.borrowerPhone }}</span>
            </div>
            <div class="form-item">
              <label>借用日期 <span class="required">*</span></label>
              <input 
                type="date" 
                v-model="currentRecord.borrowDate" 
                class="form-input" 
                :class="{ 'error': formErrors.borrowDate }"
              />
              <span v-if="formErrors.borrowDate" class="error-text">{{ formErrors.borrowDate }}</span>
            </div>
            <div class="form-item">
              <label>预计归还日期 <span class="required">*</span></label>
              <input 
                type="date" 
                v-model="currentRecord.expectedReturnDate" 
                class="form-input" 
                :class="{ 'error': formErrors.expectedReturnDate }"
              />
              <span v-if="formErrors.expectedReturnDate" class="error-text">{{ formErrors.expectedReturnDate }}</span>
            </div>
            <div class="form-item">
              <label>实际归还日期</label>
              <input 
                type="date" 
                v-model="currentRecord.actualReturnDate" 
                class="form-input" 
              />
            </div>
            <div class="form-item">
              <label>状态</label>
              <select v-model="currentRecord.status" class="form-select">
                <option value="借用中">借用中</option>
                <option value="已归还">已归还</option>
              </select>
            </div>
            <div class="form-item">
              <label>借用用途 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentRecord.purpose" 
                class="form-input" 
                :class="{ 'error': formErrors.purpose }"
              />
              <span v-if="formErrors.purpose" class="error-text">{{ formErrors.purpose }}</span>
            </div>
            <div class="form-item">
              <label>物资名称</label>
              <input 
                type="text" 
                v-model="currentRecord.materialName" 
                class="form-input" 
              />
            </div>
            <div class="form-item full-width">
              <label>备注</label>
              <textarea 
                v-model="currentRecord.remarks" 
                class="form-textarea" 
                rows="3"
              ></textarea>
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
          <h3>借用记录详情</h3>
          <button class="close-btn" @click="showDetailModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-header">
            <div class="detail-icon">📋</div>
            <div class="detail-basic">
              <h2 class="detail-name">{{ detailRecord.borrowerName }}</h2>
              <p class="detail-phone">联系电话：{{ detailRecord.borrowerPhone }}</p>
              <span class="status-tag" :class="{
                '借用中': detailRecord.status === '借用中' && !isOverdue(detailRecord),
                '已归还': detailRecord.status === '已归还',
                '已逾期': isOverdue(detailRecord)
              }">
                {{ getStatusDisplay(detailRecord) }}
              </span>
            </div>
          </div>
          <div class="detail-info">
            <div class="info-grid">
              <div class="info-item">
                <label>记录ID</label>
                <span>{{ detailRecord.id }}</span>
              </div>
              <div class="info-item">
                <label>借用日期</label>
                <span>{{ detailRecord.borrowDate }}</span>
              </div>
              <div class="info-item">
                <label>预计归还日期</label>
                <span>{{ detailRecord.expectedReturnDate }}</span>
              </div>
              <div class="info-item">
                <label>实际归还日期</label>
                <span>{{ detailRecord.actualReturnDate || '未归还' }}</span>
              </div>
              <div class="info-item">
                <label>借用用途</label>
                <span>{{ detailRecord.purpose }}</span>
              </div>
              <div class="info-item">
                <label>物资名称</label>
                <span>{{ detailRecord.materialName || '-' }}</span>
              </div>
              <div class="info-item full-width">
                <label>备注</label>
                <span>{{ detailRecord.remarks || '无' }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal = false">关闭</button>
          <button v-if="detailRecord.status === '借用中'" class="btn btn-success" @click="returnMaterial(detailRecord); showDetailModal = false">归还物资</button>
          <button class="btn btn-primary" @click="openEditModal(detailRecord); showDetailModal = false">编辑信息</button>
        </div>
      </div>
    </div>
    
    <!-- 删除确认模态框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal-content delete-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="close-btn" @click="showDeleteConfirm = false">×</button>
        </div>
        <div class="modal-body">
          <div class="delete-warning">
            <span class="warning-icon">⚠️</span>
            <p>确定要删除借用人员「{{ recordToDelete?.borrowerName }}」的借用记录吗？</p>
            <p class="warning-text">此操作不可恢复，请谨慎操作。</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn btn-danger" @click="deleteRecord">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.borrow-page {
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
  grid-template-columns: repeat(4, 1fr);
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
  min-width: 120px;
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

.result-count {
  font-size: 14px;
  color: #666666;
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

.btn-success {
  background: #52c41a;
  color: #ffffff;
}

.btn-success:hover {
  background: #73d13d;
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

.selected-count {
  font-size: 14px;
  color: #1890ff;
  font-weight: 500;
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

.borrow-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1000px;
}

.borrow-table th,
.borrow-table td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.borrow-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333333;
  font-size: 14px;
}

.borrow-table td {
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

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.借用中 {
  background: #e6f7ff;
  color: #1890ff;
}

.status-tag.已归还 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.已逾期 {
  background: #fff2f0;
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

.action-btn.view {
  background: #f0f0f0;
  color: #666666;
}

.action-btn.view:hover {
  background: #d9d9d9;
}

.action-btn.edit {
  background: #e6f7ff;
  color: #1890ff;
}

.action-btn.edit:hover {
  background: #bae7ff;
}

.action-btn.return {
  background: #f6ffed;
  color: #52c41a;
}

.action-btn.return:hover {
  background: #d9f7be;
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
  width: 800px;
  max-height: 90vh;
  overflow: hidden;
}

.detail-modal {
  width: 700px;
}

.delete-modal {
  width: 500px;
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
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item.full-width {
  grid-column: 1 / -1;
}

.form-item label {
  font-size: 14px;
  color: #333333;
}

.form-item label .required {
  color: #ff4d4f;
}

.form-input,
.form-select,
.form-textarea {
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.form-input.error,
.form-select.error {
  border-color: #ff4d4f;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
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

.detail-name {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #ffffff;
}

.detail-phone {
  font-size: 14px;
  margin: 0;
  opacity: 0.9;
}

.detail-header .status-tag {
  width: fit-content;
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.detail-info {
  padding: 0 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item.full-width {
  grid-column: 1 / -1;
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

.delete-warning {
  text-align: center;
  padding: 20px;
}

.warning-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.delete-warning p {
  font-size: 16px;
  color: #333333;
  margin: 8px 0;
}

.warning-text {
  color: #999999 !important;
  font-size: 14px !important;
}

@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    width: 95%;
  }
  
  .detail-modal {
    width: 95%;
  }
  
  .delete-modal {
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
}
</style>