<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import * as XLSX from 'xlsx';
import { hasPermission } from '../../utils/permission';

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 团支部数据
const branches = ref([]);

// 加载状态
const isLoading = ref(false);

// 从API获取团支部数据
const fetchBranches = async () => {
  isLoading.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/league-branches/`);
    if (response.ok) {
      const data = await response.json();
      if (data.results && data.results.length > 0) {
        branches.value = data.results.map(b => ({
          id: b.id,
          name: b.name,
          code: b.code,
          monthlyFee: b.monthly_fee || 6,
          expectedCount: b.expected_count || 0,
          paidCount: b.paid_count || 0,
          remark: b.remark || ''
        }));
      } else if (Array.isArray(data) && data.length > 0) {
        branches.value = data.map(b => ({
          id: b.id,
          name: b.name,
          code: b.code,
          monthlyFee: b.monthly_fee || 6,
          expectedCount: b.expected_count || 0,
          paidCount: b.paid_count || 0,
          remark: b.remark || ''
        }));
      } else {
        branches.value = [];
      }
      filterBranches();
    } else {
      console.error('API请求失败:', response.status);
      showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
    }
  } catch (error) {
    console.error('加载团支部数据失败:', error);
    showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
  } finally {
    isLoading.value = false;
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchBranches();
});

// 统计数据
const stats = computed(() => {
  const totalBranches = branches.value.length;
  const totalExpected = branches.value.reduce((sum, b) => sum + b.expectedCount, 0);
  const totalPaid = branches.value.reduce((sum, b) => sum + b.paidCount, 0);
  const rate = totalExpected > 0 ? ((totalPaid / totalExpected) * 100).toFixed(1) + '%' : '0%';
  
  return [
    { label: '团支部总数', value: totalBranches, icon: '🏢' },
    { label: '应交总人数', value: totalExpected, icon: '👥' },
    { label: '已交总人数', value: totalPaid, icon: '✓' },
    { label: '缴费率', value: rate, icon: '%' }
  ];
});

// 分页相关
const currentPage = ref(1);
const pageSize = 10;
const totalPages = computed(() => Math.ceil(filteredBranches.value.length / pageSize));

// 批量选择相关
const selectedBranchIds = ref([]);

// 是否全选
const isAllSelected = computed(() => {
  return paginatedBranches.value.length > 0 && 
         paginatedBranches.value.every(b => selectedBranchIds.value.includes(b.id));
});

// 切换全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    paginatedBranches.value.forEach(b => {
      const index = selectedBranchIds.value.indexOf(b.id);
      if (index !== -1) {
        selectedBranchIds.value.splice(index, 1);
      }
    });
  } else {
    paginatedBranches.value.forEach(b => {
      if (!selectedBranchIds.value.includes(b.id)) {
        selectedBranchIds.value.push(b.id);
      }
    });
  }
};

// 切换单个选择
const toggleSelect = (branchId, event) => {
  event.stopPropagation();
  const index = selectedBranchIds.value.indexOf(branchId);
  if (index === -1) {
    selectedBranchIds.value.push(branchId);
  } else {
    selectedBranchIds.value.splice(index, 1);
  }
};

// 批量删除
const deleteSelected = async () => {
  if (selectedBranchIds.value.length === 0) {
    showErrorMessage('请先选择要删除的团支部');
    return;
  }
  
  if (confirm(`确定要删除选中的 ${selectedBranchIds.value.length} 个团支部吗？`)) {
    isLoading.value = true;
    let successCount = 0;
    
    try {
      for (const id of selectedBranchIds.value) {
        const response = await fetch(`${API_BASE_URL}/league-branches/${id}/`, {
          method: 'DELETE',
        });
        if (response.ok || response.status === 204) {
          successCount++;
          branches.value = branches.value.filter(b => b.id !== id);
        }
      }
      
      selectedBranchIds.value = [];
      filterBranches();
      showSuccessMessage(`成功删除 ${successCount} 个团支部！`);
    } catch (error) {
      console.error('批量删除失败:', error);
      showErrorMessage('批量删除失败，请重试');
    } finally {
      isLoading.value = false;
    }
  }
};

// 当前页数据
const paginatedBranches = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredBranches.value.slice(start, end);
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

// 搜索
const searchQuery = ref('');

// 过滤团支部
const filteredBranches = ref(branches.value);

// 模态框控制
const showAddModal = ref(false);
const showEditModal = ref(false);
const showImportModal = ref(false);
const showDetailModal = ref(false);
const showSuccess = ref(false);
const showError = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

// 当前编辑的团支部
const currentBranch = ref({
  id: null,
  name: '',
  code: '',
  monthlyFee: 6,
  expectedCount: 0,
  paidCount: 0,
  remark: ''
});

// 详情团支部
const detailBranch = ref(null);

// 表单验证错误
const formErrors = ref({});

// 导入数据
const importedData = ref([]);
const importPreview = ref([]);
const importErrors = ref([]);

// 当前编辑的团支部索引
const editingBranchId = ref(null);

// 过滤团支部
const filterBranches = () => {
  filteredBranches.value = branches.value.filter(b => {
    const matchSearch = !searchQuery.value || 
      b.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
      b.code.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      b.id.toString().includes(searchQuery.value);
    return matchSearch;
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
const viewDetail = (branch) => {
  detailBranch.value = branch;
  showDetailModal.value = true;
};

// 重置筛选
const resetFilters = () => {
  searchQuery.value = '';
  filterBranches();
};

// 验证表单
const validateForm = () => {
  const errors = {};
  
  if (!currentBranch.value.name || currentBranch.value.name.trim() === '') {
    errors.name = '请输入团支部名称';
  }
  
  if (!currentBranch.value.code || currentBranch.value.code.trim() === '') {
    errors.code = '请输入团支部编号';
  }
  
  if (!currentBranch.value.monthlyFee || currentBranch.value.monthlyFee < 0) {
    errors.monthlyFee = '请输入正确的缴费金额';
  }
  
  if (!currentBranch.value.expectedCount || currentBranch.value.expectedCount < 0) {
    errors.expectedCount = '请输入正确的应交人数';
  }
  
  if (currentBranch.value.paidCount < 0) {
    errors.paidCount = '已交人数不能为负数';
  }
  
  if (currentBranch.value.paidCount > currentBranch.value.expectedCount) {
    errors.paidCount = '已交人数不能大于应交人数';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
};

// 打开添加模态框
const openAddModal = () => {
  currentBranch.value = {
    id: null,
    name: '',
    code: '',
    monthlyFee: 6,
    expectedCount: 0,
    paidCount: 0,
    remark: ''
  };
  formErrors.value = {};
  showAddModal.value = true;
};

// 打开编辑模态框
const openEditModal = (branch) => {
  currentBranch.value = { ...branch };
  editingBranchId.value = branch.id;
  formErrors.value = {};
  showEditModal.value = true;
};

// 添加团支部
const addBranch = async () => {
  if (!validateForm()) return;
  
  try {
    const apiData = {
      name: currentBranch.value.name,
      code: currentBranch.value.code,
      monthly_fee: currentBranch.value.monthlyFee,
      expected_count: currentBranch.value.expectedCount,
      paid_count: currentBranch.value.paidCount,
      remark: currentBranch.value.remark || ''
    };
    
    const response = await fetch(`${API_BASE_URL}/league-branches/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const newBranch = await response.json();
      branches.value.unshift({
        id: newBranch.id,
        name: newBranch.name,
        code: newBranch.code,
        monthlyFee: newBranch.monthly_fee || 6,
        expectedCount: newBranch.expected_count || 0,
        paidCount: newBranch.paid_count || 0,
        remark: newBranch.remark || ''
      });
      
      showSuccessMessage('团支部添加成功！');
      showAddModal.value = false;
      filterBranches();
    } else {
      const error = await response.json();
      showErrorMessage('添加失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('添加团支部失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }
};

// 编辑团支部
const editBranch = async () => {
  if (!validateForm()) return;
  
  try {
    const apiData = {
      name: currentBranch.value.name,
      code: currentBranch.value.code,
      monthly_fee: currentBranch.value.monthlyFee,
      expected_count: currentBranch.value.expectedCount,
      paid_count: currentBranch.value.paidCount,
      remark: currentBranch.value.remark || ''
    };
    
    const response = await fetch(`${API_BASE_URL}/league-branches/${editingBranchId.value}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const updatedBranch = await response.json();
      const index = branches.value.findIndex(b => b.id === editingBranchId.value);
      if (index !== -1) {
        branches.value[index] = {
          id: updatedBranch.id,
          name: updatedBranch.name,
          code: updatedBranch.code,
          monthlyFee: updatedBranch.monthly_fee || 6,
          expectedCount: updatedBranch.expected_count || 0,
          paidCount: updatedBranch.paid_count || 0,
          remark: updatedBranch.remark || ''
        };
      }
      
      showSuccessMessage('团支部信息更新成功！');
    } else {
      const error = await response.json();
      showErrorMessage('更新失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('更新团支部失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }
  
  showEditModal.value = false;
  filterBranches();
};

// 删除团支部
const deleteBranch = async (branch) => {
  if (confirm(`确定要删除团支部「${branch.name}」吗？`)) {
    try {
      const response = await fetch(`${API_BASE_URL}/league-branches/${branch.id}/`, {
        method: 'DELETE',
      });
      
      if (response.ok || response.status === 204) {
        branches.value = branches.value.filter(b => b.id !== branch.id);
        showSuccessMessage('团支部删除成功！');
        filterBranches();
      } else {
        showErrorMessage('删除失败');
      }
    } catch (error) {
      console.error('删除团支部失败:', error);
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

// 处理文件上传
const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
    showErrorMessage('请上传Excel文件（.xlsx或.xls格式）');
    return;
  }
  
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      
      if (jsonData.length === 0) {
        showErrorMessage('Excel文件中没有数据');
        return;
      }
      
      // 验证数据格式
      importErrors.value = [];
      importPreview.value = [];
      
      jsonData.forEach((row, index) => {
        const errors = [];
        
        if (!row['团支部名称']) errors.push('团支部名称不能为空');
        if (!row['团支部编号']) errors.push('团支部编号不能为空');
        if (!row['每月缴费金额'] || row['每月缴费金额'] < 0) errors.push('每月缴费金额必须大于等于0');
        if (!row['应交人数'] || row['应交人数'] < 0) errors.push('应交人数必须大于等于0');
        if (row['已交人数'] && row['已交人数'] < 0) errors.push('已交人数不能为负数');
        if (row['已交人数'] && row['应交人数'] && row['已交人数'] > row['应交人数']) errors.push('已交人数不能大于应交人数');
        
        importPreview.value.push({
          row: index + 1,
          name: row['团支部名称'] || '',
          code: row['团支部编号'] || '',
          monthlyFee: row['每月缴费金额'] || 6,
          expectedCount: row['应交人数'] || 0,
          paidCount: row['已交人数'] || 0,
          remark: row['备注'] || '',
          errors: errors
        });
        
        if (errors.length > 0) {
          importErrors.value.push({
            row: index + 1,
            errors: errors
          });
        }
      });
      
      importedData.value = jsonData;
      showImportModal.value = true;
    } catch (error) {
      showErrorMessage('解析Excel文件失败，请检查文件格式');
      console.error(error);
    }
  };
  reader.readAsArrayBuffer(file);
};

// 确认导入
const confirmImport = async () => {
  if (importErrors.value.length > 0) {
    if (!confirm(`发现 ${importErrors.value.length} 条数据存在错误，是否继续导入有效数据？`)) {
      return;
    }
  }
  
  isLoading.value = true;
  let successCount = 0;
  let failCount = 0;
  
  try {
    for (const item of importPreview.value) {
      if (item.errors.length === 0) {
        const apiData = {
          name: item.name,
          code: item.code,
          monthly_fee: item.monthlyFee,
          expected_count: item.expectedCount,
          paid_count: item.paidCount,
          remark: item.remark || ''
        };
        
        const response = await fetch(`${API_BASE_URL}/league-branches/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(apiData)
        });
        
        if (response.ok) {
          const newBranch = await response.json();
          branches.value.push({
            id: newBranch.id,
            name: newBranch.name,
            code: newBranch.code,
            monthlyFee: newBranch.monthly_fee || 6,
            expectedCount: newBranch.expected_count || 0,
            paidCount: newBranch.paid_count || 0,
            remark: newBranch.remark || ''
          });
          successCount++;
        } else {
          failCount++;
        }
      }
    }
    
    showSuccessMessage(`成功导入 ${successCount} 个团支部！失败 ${failCount} 个`);
    showImportModal.value = false;
    filterBranches();
  } catch (error) {
    console.error('导入失败:', error);
    showErrorMessage('导入失败，请稍后重试');
  } finally {
    isLoading.value = false;
  }
};

// 导出Excel
const exportToExcel = () => {
  try {
    const exportData = filteredBranches.value.map(b => ({
      '团支部名称': b.name,
      '团支部编号': b.code,
      '每月缴费金额': b.monthlyFee,
      '应交人数': b.expectedCount,
      '已交人数': b.paidCount,
      '缴费率': b.expectedCount > 0 ? ((b.paidCount / b.expectedCount) * 100).toFixed(1) + '%' : '0%',
      '备注': b.remark || ''
    }));
    
    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '团支部信息');
    
    const fileName = `团支部信息_${new Date().toISOString().split('T')[0]}.xlsx`;
    XLSX.writeFile(workbook, fileName);
    
    showSuccessMessage('数据导出成功！');
  } catch (error) {
    showErrorMessage('导出失败，请重试');
    console.error(error);
  }
};

// 下载导入模板
const downloadTemplate = () => {
  const templateData = [
    {
      '团支部名称': '计算机学院团支部',
      '团支部编号': 'CST001',
      '每月缴费金额': 6,
      '应交人数': 150,
      '已交人数': 145,
      '备注': '示例团支部'
    }
  ];
  
  const worksheet = XLSX.utils.json_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '模板');
  
  const fileName = '团支部导入模板.xlsx';
  XLSX.writeFile(workbook, fileName);
};

// 计算缴费率
const calculateRate = (branch) => {
  if (branch.expectedCount === 0) return '0%';
  return ((branch.paidCount / branch.expectedCount) * 100).toFixed(1) + '%';
};
</script>

<template>
  <div class="page-container">
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
      <h1>团支部管理</h1>
    </header>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.label" class="stat-item">
        <div class="stat-icon">{{ stat.icon }}</div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-group search-group">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索团支部名称、编号..." 
          class="search-input"
          @input="filterBranches"
        />
      </div>
      <button v-if="searchQuery" class="btn btn-text" @click="resetFilters">重置筛选</button>
    </div>
    
    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="result-count">共 {{ filteredBranches.length }} 条结果</span>
        <span v-if="selectedBranchIds.length > 0" class="selected-count">已选择 {{ selectedBranchIds.length }} 条</span>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedBranchIds.length > 0 && hasPermission('league:delete')" class="btn btn-danger" @click="deleteSelected">批量删除</button>
        <button v-if="hasPermission('league:edit')" class="btn btn-secondary" @click="downloadTemplate">下载模板</button>
        <label v-if="hasPermission('league:edit')" class="btn btn-secondary upload-btn">
          <span>批量导入</span>
          <input type="file" accept=".xlsx,.xls" @change="handleFileUpload" style="display: none;">
        </label>
        <button v-if="hasPermission('league:edit')" class="btn btn-secondary" @click="exportToExcel">导出数据</button>
        <button v-if="hasPermission('league:add')" class="btn btn-primary" @click="openAddModal">新增团支部</button>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    
    <!-- 数据表格 -->
    <div class="table-container">
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="isAllSelected" @change="toggleSelectAll" />
                </label>
              </th>
              <th>ID</th>
              <th>团支部名称</th>
              <th>团支部编号</th>
              <th>每月缴费金额</th>
              <th>应交人数</th>
              <th>已交人数</th>
              <th>缴费率</th>
              <th>备注</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="branch in paginatedBranches" :key="branch.id" @click="viewDetail(branch)" class="clickable-row" :class="{ selected: selectedBranchIds.includes(branch.id) }">
              <td @click.stop>
                <label class="checkbox-label">
                  <input type="checkbox" :checked="selectedBranchIds.includes(branch.id)" @change="toggleSelect(branch.id, $event)" />
                </label>
              </td>
              <td>{{ branch.id }}</td>
              <td><span class="name-tag">{{ branch.name }}</span></td>
              <td><span class="code-tag">{{ branch.code }}</span></td>
              <td>¥{{ branch.monthlyFee }}</td>
              <td>{{ branch.expectedCount }}</td>
              <td><span class="paid-count">{{ branch.paidCount }}</span></td>
              <td>
                <span class="rate-tag" :class="{ high: parseFloat(calculateRate(branch)) >= 95, medium: parseFloat(calculateRate(branch)) >= 80 && parseFloat(calculateRate(branch)) < 95, low: parseFloat(calculateRate(branch)) < 80 }">
                  {{ calculateRate(branch) }}
                </span>
              </td>
              <td>{{ branch.remark || '-' }}</td>
              <td @click.stop>
                <button class="action-btn view" @click="viewDetail(branch)">查看</button>
                <button v-if="hasPermission('league:edit')" class="action-btn edit" @click="openEditModal(branch)">编辑</button>
                <button v-if="hasPermission('league:delete')" class="action-btn delete" @click="deleteBranch(branch)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-if="filteredBranches.length === 0" class="empty-state">
        <p>暂无团支部数据</p>
      </div>
    </div>
    
    <!-- 分页 -->
    <div v-if="totalPages > 0" class="pagination">
      <div class="pagination-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ filteredBranches.length }} 条记录
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
    
    <!-- 添加模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>新增团支部</h3>
          <button class="close-btn" @click="showAddModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>团支部名称 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentBranch.name" 
                class="form-input" 
                :class="{ 'error': formErrors.name }"
                placeholder="请输入团支部名称"
              />
              <span v-if="formErrors.name" class="error-text">{{ formErrors.name }}</span>
            </div>
            <div class="form-item">
              <label>团支部编号 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentBranch.code" 
                class="form-input" 
                :class="{ 'error': formErrors.code }"
                placeholder="请输入团支部编号"
              />
              <span v-if="formErrors.code" class="error-text">{{ formErrors.code }}</span>
            </div>
            <div class="form-item">
              <label>每月缴费金额 <span class="required">*</span></label>
              <input 
                type="number" 
                v-model="currentBranch.monthlyFee" 
                class="form-input" 
                :class="{ 'error': formErrors.monthlyFee }"
                min="0"
                step="0.5"
              />
              <span v-if="formErrors.monthlyFee" class="error-text">{{ formErrors.monthlyFee }}</span>
            </div>
            <div class="form-item">
              <label>应交人数 <span class="required">*</span></label>
              <input 
                type="number" 
                v-model="currentBranch.expectedCount" 
                class="form-input" 
                :class="{ 'error': formErrors.expectedCount }"
                min="0"
              />
              <span v-if="formErrors.expectedCount" class="error-text">{{ formErrors.expectedCount }}</span>
            </div>
            <div class="form-item">
              <label>已交人数</label>
              <input 
                type="number" 
                v-model="currentBranch.paidCount" 
                class="form-input" 
                :class="{ 'error': formErrors.paidCount }"
                min="0"
              />
              <span v-if="formErrors.paidCount" class="error-text">{{ formErrors.paidCount }}</span>
            </div>
            <div class="form-item full-width">
              <label>备注</label>
              <textarea 
                v-model="currentBranch.remark" 
                class="form-textarea" 
                placeholder="请输入备注信息"
              ></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="addBranch">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 编辑模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑团支部</h3>
          <button class="close-btn" @click="showEditModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>团支部名称 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentBranch.name" 
                class="form-input" 
                :class="{ 'error': formErrors.name }"
                placeholder="请输入团支部名称"
              />
              <span v-if="formErrors.name" class="error-text">{{ formErrors.name }}</span>
            </div>
            <div class="form-item">
              <label>团支部编号 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentBranch.code" 
                class="form-input" 
                :class="{ 'error': formErrors.code }"
                placeholder="请输入团支部编号"
              />
              <span v-if="formErrors.code" class="error-text">{{ formErrors.code }}</span>
            </div>
            <div class="form-item">
              <label>每月缴费金额 <span class="required">*</span></label>
              <input 
                type="number" 
                v-model="currentBranch.monthlyFee" 
                class="form-input" 
                :class="{ 'error': formErrors.monthlyFee }"
                min="0"
                step="0.5"
              />
              <span v-if="formErrors.monthlyFee" class="error-text">{{ formErrors.monthlyFee }}</span>
            </div>
            <div class="form-item">
              <label>应交人数 <span class="required">*</span></label>
              <input 
                type="number" 
                v-model="currentBranch.expectedCount" 
                class="form-input" 
                :class="{ 'error': formErrors.expectedCount }"
                min="0"
              />
              <span v-if="formErrors.expectedCount" class="error-text">{{ formErrors.expectedCount }}</span>
            </div>
            <div class="form-item">
              <label>已交人数</label>
              <input 
                type="number" 
                v-model="currentBranch.paidCount" 
                class="form-input" 
                :class="{ 'error': formErrors.paidCount }"
                min="0"
              />
              <span v-if="formErrors.paidCount" class="error-text">{{ formErrors.paidCount }}</span>
            </div>
            <div class="form-item full-width">
              <label>备注</label>
              <textarea 
                v-model="currentBranch.remark" 
                class="form-textarea" 
                placeholder="请输入备注信息"
              ></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditModal = false">取消</button>
          <button class="btn btn-primary" @click="editBranch">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-content detail-modal" v-if="detailBranch">
        <div class="modal-header">
          <h3>团支部详情</h3>
          <button class="close-btn" @click="showDetailModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-header">
            <div class="detail-icon">🏢</div>
            <div class="detail-basic">
              <h2 class="detail-name">{{ detailBranch.name }}</h2>
              <p class="detail-code">编号：{{ detailBranch.code }}</p>
              <span class="rate-badge" :class="{ high: parseFloat(calculateRate(detailBranch)) >= 95 }">
                缴费率：{{ calculateRate(detailBranch) }}
              </span>
            </div>
          </div>
          <div class="detail-info">
            <div class="info-grid">
              <div class="info-item">
                <label>ID</label>
                <span>{{ detailBranch.id }}</span>
              </div>
              <div class="info-item">
                <label>每月缴费金额</label>
                <span class="fee-value">¥{{ detailBranch.monthlyFee }}</span>
              </div>
              <div class="info-item">
                <label>应交人数</label>
                <span>{{ detailBranch.expectedCount }}</span>
              </div>
              <div class="info-item">
                <label>已交人数</label>
                <span class="paid-value">{{ detailBranch.paidCount }}</span>
              </div>
              <div class="info-item">
                <label>未交人数</label>
                <span class="unpaid-value">{{ detailBranch.expectedCount - detailBranch.paidCount }}</span>
              </div>
              <div class="info-item">
                <label>缴费率</label>
                <span class="rate-tag" :class="{ high: parseFloat(calculateRate(detailBranch)) >= 95 }">
                  {{ calculateRate(detailBranch) }}
                </span>
              </div>
              <div class="info-item full-width" v-if="detailBranch.remark">
                <label>备注</label>
                <span>{{ detailBranch.remark }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal = false">关闭</button>
          <button class="btn btn-primary" @click="openEditModal(detailBranch); showDetailModal = false">编辑信息</button>
        </div>
      </div>
    </div>
    
    <!-- 批量导入模态框 -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal-content large-modal">
        <div class="modal-header">
          <h3>批量导入团支部</h3>
          <button class="close-btn" @click="showImportModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="importErrors.length > 0" class="error-summary">
            <strong>发现 {{ importErrors.length }} 条数据错误：</strong>
            <ul>
              <li v-for="err in importErrors" :key="err.row">
                第 {{ err.row }} 行：{{ err.errors.join('；') }}
              </li>
            </ul>
          </div>
          <div class="preview-info">共 {{ importPreview.length }} 条数据</div>
          <div class="table-scroll">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>行号</th>
                  <th>团支部名称</th>
                  <th>团支部编号</th>
                  <th>每月缴费金额</th>
                  <th>应交人数</th>
                  <th>已交人数</th>
                  <th>备注</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in importPreview" :key="item.row" :class="{ 'error-row': item.errors.length > 0 }">
                  <td>{{ item.row }}</td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.code }}</td>
                  <td>¥{{ item.monthlyFee }}</td>
                  <td>{{ item.expectedCount }}</td>
                  <td>{{ item.paidCount }}</td>
                  <td>{{ item.remark || '-' }}</td>
                  <td>
                    <span v-if="item.errors.length > 0" class="error-status">错误</span>
                    <span v-else class="success-status">正常</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showImportModal = false">取消</button>
          <button class="btn btn-primary" @click="confirmImport">确认导入</button>
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
  font-weight: 600;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: #ffffff;
  color: #666;
  border: 1px solid #e8e8e8;
}

.btn-secondary:hover {
  background: #f5f5f5;
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

.upload-btn {
  position: relative;
  overflow: hidden;
  cursor: pointer;
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
  margin-bottom: 24px;
}

.table-scroll {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 900px;
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
  border-top-color: #667eea;
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
  border-color: #667eea;
  color: #667eea;
}

.page-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
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

.name-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.code-tag {
  padding: 4px 12px;
  background: #f6ffed;
  color: #52c41a;
  border-radius: 4px;
  font-size: 12px;
}

.paid-count {
  color: #52c41a;
  font-weight: 500;
}

.rate-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.rate-tag.high {
  background: #f6ffed;
  color: #52c41a;
}

.rate-tag.medium {
  background: #fff7e6;
  color: #fa8c16;
}

.rate-tag.low {
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

.action-btn.view {
  background: #e6f7ff;
  color: #1890ff;
}

.action-btn.view:hover {
  background: #bae7ff;
}

.action-btn.edit {
  background: #fff7e6;
  color: #fa8c16;
}

.action-btn.edit:hover {
  background: #ffe7ba;
}

.action-btn.delete {
  background: #fff1f0;
  color: #ff4d4f;
}

.action-btn.delete:hover {
  background: #ffa39e;
}

.empty-state {
  padding: 48px;
  text-align: center;
  color: #999;
}

/* 模态框样式 */
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
  padding: 20px;
}

.modal-content {
  background: #ffffff;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.large-modal {
  max-width: 900px;
}

.detail-modal {
  max-width: 700px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-header h3 {
  font-size: 20px;
  margin: 0;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
}

/* 表单样式 */
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
  font-weight: 500;
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
  box-sizing: border-box;
}

.form-textarea {
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  min-height: 80px;
  resize: vertical;
  box-sizing: border-box;
  width: 100%;
}

.form-input.error,
.form-select.error {
  border-color: #ff4d4f;
}

.error-text {
  font-size: 12px;
  color: #ff4d4f;
}

/* 详情样式 */
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

.detail-code {
  font-size: 16px;
  margin: 0;
  opacity: 0.9;
}

.rate-badge {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  font-size: 14px;
  width: fit-content;
}

.rate-badge.high {
  background: rgba(82, 196, 26, 0.3);
}

.detail-info {
  padding: 0 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 6px;
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

.fee-value {
  color: #667eea;
}

.paid-value {
  color: #52c41a;
}

.unpaid-value {
  color: #ff4d4f;
}

/* 导入预览样式 */
.error-summary {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 16px;
}

.error-summary strong {
  color: #ff4d4f;
  font-size: 14px;
}

.error-summary ul {
  margin: 8px 0 0 20px;
  font-size: 13px;
  color: #666666;
}

.preview-info {
  font-size: 14px;
  color: #666666;
  margin-bottom: 12px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
}

.preview-table th,
.preview-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.preview-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333333;
}

.error-row {
  background: #fff2f0;
}

.error-status {
  color: #ff4d4f;
  font-weight: 500;
}

.success-status {
  color: #52c41a;
  font-weight: 500;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .modal-content {
    max-width: 95%;
  }
}

@media (max-width: 640px) {
  .page-container {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input {
    width: 100%;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>