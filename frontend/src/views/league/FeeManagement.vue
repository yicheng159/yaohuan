<script setup>
import { ref, computed, onMounted } from 'vue';
import * as XLSX from 'xlsx';
import axios from 'axios';
import { hasPermission } from '../../utils/permission';

// API配置
const BRANCH_API = '/api/league-branches/';
const RECORD_API = '/api/fee-records/';

// Excel表头映射
const excelHeaders = [
  '姓名', '学号', '团支部编号', '缴费月份', '金额'
];

// Excel数据字段映射
const fieldMapping = {
  '姓名': 'name',
  '学号': 'studentId',
  '团支部编号': 'branchCode',
  '缴费月份': 'month',
  '金额': 'amount'
};

// 团支部数据
const branches = ref([]);
const loading = ref(false);

// 团费缴费记录
const records = ref([]);

// 统计数据
const stats = computed(() => {
  // 基于实际缴费记录动态计算
  const total = records.value.length;
  const paid = records.value.filter(r => r.status === '已缴').length;
  const unpaid = records.value.filter(r => r.status === '未缴').length;
  // 汇总所有团支部的实际收缴金额
  const amount = records.value
    .filter(r => r.status === '已缴')
    .reduce((sum, r) => sum + (r.amount || 0), 0);
  const rate = total > 0 ? ((paid / total) * 100).toFixed(1) + '%' : '0%';
  
  return [
    { label: '应交人数', value: total, icon: '👥' },
    { label: '已交人数', value: paid, icon: '✓' },
    { label: '未交人数', value: unpaid, icon: '✗' },
    { label: '收缴金额', value: '¥' + amount + ' 人民币', icon: '💰' }
  ];
});

// 模态框状态
const showBranchModal = ref(false);
const showRecordModal = ref(false);
const showBranchDetailModal = ref(false);
const isEdit = ref(false);
const currentBranch = ref(null);
const formErrors = ref({});
const activeView = ref('branches');

// 筛选状态
const selectedBranchId = ref('');
const searchQuery = ref('');
const statusFilter = ref('');

// 分页
const pageSize = 10;
const currentPage = ref(1);

// 表单数据
const branchFormData = ref({
  name: '',
  code: '',
  amount: 6,
  description: ''
});

const recordFormData = ref({
  branchId: '',
  name: '',
  studentId: '',
  amount: 6,
  month: ''
});

// 筛选后的团支部
const filteredBranches = computed(() => {
  return branches.value.filter(b => {
    return !searchQuery.value || 
      b.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      b.code.toLowerCase().includes(searchQuery.value.toLowerCase());
  });
});

// 筛选后的记录
const filteredRecords = computed(() => {
  return records.value.filter(r => {
    const matchBranch = !selectedBranchId.value || r.branchId === selectedBranchId.value;
    const matchSearch = !searchQuery.value || 
      r.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      r.studentId.includes(searchQuery.value);
    const matchStatus = !statusFilter.value || r.status === statusFilter.value;
    return matchBranch && matchSearch && matchStatus;
  });
});

// 分页后的记录
const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredRecords.value.slice(start, end);
});

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredRecords.value.length / pageSize);
});

// 获取团支部名称
function getBranchName(branchId) {
  const branch = branches.value.find(b => b.id === branchId);
  return branch ? branch.name : '';
}

// 计算团支部的收缴金额（汇总该团支部所有已缴记录的实际金额）
function getBranchCollectedAmount(branchId) {
  return records.value
    .filter(r => r.branchId === branchId && r.status === '已缴')
    .reduce((sum, r) => sum + (r.amount || 0), 0);
}

// 计算团支部的应交人数（基于实际缴费记录中的所有人数）
function getBranchTotalCount(branchId) {
  return records.value.filter(r => r.branchId === branchId).length;
}

// 计算团支部的已交人数
function getBranchPaidCount(branchId) {
  return records.value.filter(r => r.branchId === branchId && r.status === '已缴').length;
}

// 计算团支部的未交人数
function getBranchUnpaidCount(branchId) {
  return records.value.filter(r => r.branchId === branchId && r.status === '未缴').length;
}

// 计算团支部的收缴率
function getBranchRate(branchId) {
  const total = getBranchTotalCount(branchId);
  const paid = getBranchPaidCount(branchId);
  if (total === 0) return '0.0%';
  return ((paid / total) * 100).toFixed(1) + '%';
}

// 从后端获取团支部数据
async function fetchBranches() {
  loading.value = true;
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      console.warn('未找到token，请先登录');
      return;
    }
    const response = await axios.get(BRANCH_API, {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    const results = response.data.results || response.data;
    branches.value = results.map(item => ({
      id: item.id,
      name: item.name,
      code: item.code,
      total: item.total_members || 0,
      paid: item.paid_members || 0,
      unpaid: (item.total_members || 0) - (item.paid_members || 0),
      monthlyFee: parseFloat(item.monthly_fee) || 0,
      amount: (parseFloat(item.monthly_fee) || 0) * (item.paid_members || 0),
      rate: item.paid_members && item.total_members 
        ? ((item.paid_members / item.total_members) * 100).toFixed(1) + '%' 
        : '0.0%'
    }));
  } catch (error) {
    if (error.response && error.response.status === 403) {
      console.error('获取团支部数据失败: 403 权限不足或token已过期，请重新登录');
    } else {
      console.error('获取团支部数据失败:', error);
    }
  } finally {
    loading.value = false;
  }
}

// 从后端获取缴费记录
async function fetchRecords() {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      console.warn('未找到token，请先登录');
      return;
    }
    const response = await axios.get(RECORD_API, {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    const results = response.data.results || response.data;
    records.value = results.map(item => ({
      id: item.id,
      branchId: item.branch,
      name: item.name,
      studentId: item.student_id,
      amount: parseFloat(item.amount),
      month: item.month,
      status: item.status,
      payDate: item.pay_date
    }));
  } catch (error) {
    if (error.response && error.response.status === 403) {
      console.error('获取缴费记录失败: 403 权限不足或token已过期，请重新登录');
    } else {
      console.error('获取缴费记录失败:', error);
    }
  }
}

// 验证团支部表单
function validateBranchForm() {
  const errors = {};
  
  if (!branchFormData.value.name) errors.name = '请输入团支部名称';
  if (!branchFormData.value.code) errors.code = '请输入团支部编号';
  if (!branchFormData.value.amount || branchFormData.value.amount < 0) errors.amount = '请输入正确的缴费金额';
  
  // 检查编号是否重复
  if (branchFormData.value.code) {
    const exists = branches.value.some(b => 
      b.code === branchFormData.value.code && b.id !== currentBranch.value?.id
    );
    if (exists) errors.code = '该编号已存在';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 验证缴费记录表单
function validateRecordForm() {
  const errors = {};
  
  if (!recordFormData.value.branchId) errors.branchId = '请选择团支部';
  if (!recordFormData.value.name) errors.name = '请输入姓名';
  if (!recordFormData.value.studentId) errors.studentId = '请输入学号';
  if (!recordFormData.value.month) errors.month = '请选择缴费月份';
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 打开创建团支部模态框
function openCreateBranchModal() {
  isEdit.value = false;
  currentBranch.value = null;
  branchFormData.value = {
    name: '',
    code: '',
    amount: 6,
    description: ''
  };
  formErrors.value = {};
  showBranchModal.value = true;
}

// 打开编辑团支部模态框
function openEditBranchModal(branch) {
  isEdit.value = true;
  currentBranch.value = branch;
  branchFormData.value = { ...branch };
  formErrors.value = {};
  showBranchModal.value = true;
}

// 打开团支部详情
function openBranchDetailModal(branch) {
  currentBranch.value = branch;
  showBranchDetailModal.value = true;
}

// 保存团支部
async function saveBranch() {
  if (!validateBranchForm()) return;
  
  loading.value = true;
  try {
    const postData = {
      name: branchFormData.value.name,
      code: branchFormData.value.code,
      description: branchFormData.value.description || ''
    };
    
    if (isEdit.value) {
      await axios.put(`${BRANCH_API}${currentBranch.value.id}/`, postData, {
        headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
      });
    } else {
      await axios.post(BRANCH_API, postData, {
        headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
      });
    }
    
    await fetchBranches();
    showBranchModal.value = false;
  } catch (error) {
    console.error('保存团支部失败:', error);
    alert('保存失败: ' + (error.response?.data?.message || error.message));
  } finally {
    loading.value = false;
  }
}

// 删除团支部
async function deleteBranch(branch) {
  if (confirm(`确定要删除团支部「${branch.name}」吗？`)) {
    loading.value = true;
    try {
      await axios.delete(`${BRANCH_API}${branch.id}/`, {
        headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
      });
      await fetchBranches();
      records.value = records.value.filter(r => r.branchId !== branch.id);
    } catch (error) {
      console.error('删除团支部失败:', error);
      alert('删除失败: ' + (error.response?.data?.message || error.message));
    } finally {
      loading.value = false;
    }
  }
}

// 打开缴费模态框
function openRecordModal(branch = null) {
  recordFormData.value = {
    branchId: branch ? branch.id : '',
    name: '',
    studentId: '',
    amount: 6,
    month: new Date().toISOString().slice(0, 7)
  };
  formErrors.value = {};
  showRecordModal.value = true;
}

// 批量缴费
async function batchPay(branch) {
  if (confirm(`确定要为「${branch.name}」所有未缴费成员批量缴费吗？`)) {
    loading.value = true;
    try {
      const unpaidRecords = records.value.filter(r => r.branchId === branch.id && r.status === '未缴');
      
      for (const record of unpaidRecords) {
        await axios.patch(`${RECORD_API}${record.id}/`, {
          status: '已缴',
          pay_date: new Date().toISOString().split('T')[0]
        }, {
          headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        });
      }
      
      await fetchRecords();
      await fetchBranches();
      alert(`成功为 ${unpaidRecords.length} 名成员批量缴费！`);
    } catch (error) {
      console.error('批量缴费失败:', error);
      alert('批量缴费失败: ' + (error.response?.data?.message || error.message));
    } finally {
      loading.value = false;
    }
  }
}

// 单个缴费
async function payRecord(record) {
  if (confirm(`确定要为「${record.name}」缴费吗？`)) {
    loading.value = true;
    try {
      await axios.patch(`${RECORD_API}${record.id}/`, {
        status: '已缴',
        pay_date: new Date().toISOString().split('T')[0]
      }, {
        headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
      });
      
      await fetchRecords();
      await fetchBranches();
    } catch (error) {
      console.error('缴费失败:', error);
      alert('缴费失败: ' + (error.response?.data?.message || error.message));
    } finally {
      loading.value = false;
    }
  }
}

// 保存缴费记录
async function saveRecord() {
  if (!validateRecordForm()) return;
  
  loading.value = true;
  try {
    const postData = {
      name: recordFormData.value.name,
      student_id: recordFormData.value.studentId,
      branch: recordFormData.value.branchId,
      month: recordFormData.value.month,
      amount: recordFormData.value.amount,
      status: '已缴',
      pay_date: new Date().toISOString().split('T')[0]
    };
    
    await axios.post(RECORD_API, postData, {
      headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
    });
    
    await fetchRecords();
    await fetchBranches();
    showRecordModal.value = false;
  } catch (error) {
    console.error('保存缴费记录失败:', error);
    alert('保存失败: ' + (error.response?.data?.message || error.message));
  } finally {
    loading.value = false;
  }
}

// 分页操作
function prevPage() {
  if (currentPage.value > 1) currentPage.value--;
}

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++;
}

// 关闭模态框
function closeModal() {
  showBranchModal.value = false;
  showRecordModal.value = false;
  showBranchDetailModal.value = false;
  formErrors.value = {};
}

// 下载导入模板
function downloadFeeTemplate() {
  const templateData = [
    excelHeaders,
    ['张三', '2022001001', 'CST001', '2025-06', 6]
  ];
  
  const worksheet = XLSX.utils.aoa_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '缴费信息');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 8 }
  ];
  
  XLSX.writeFile(workbook, '团费缴费导入模板.xlsx');
}

// 导出缴费数据
function exportFeeData() {
  const exportData = filteredRecords.value.map(record => ({
    '姓名': record.name,
    '学号': record.studentId,
    '团支部': getBranchName(record.branchId),
    '团支部编号': branches.value.find(b => b.id === record.branchId)?.code || '',
    '缴费月份': record.month,
    '金额': record.amount,
    '状态': record.status,
    '缴费时间': record.payDate || '-'
  }));
  
  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '缴费记录');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 12 }, { wch: 18 }, { wch: 12 }, { wch: 12 }, { wch: 8 }, { wch: 8 }, { wch: 12 }
  ];
  
  const fileName = `团费缴费记录_${new Date().toISOString().split('T')[0]}.xlsx`;
  XLSX.writeFile(workbook, fileName);
}

// 页面加载时获取数据
onMounted(() => {
  fetchBranches();
  fetchRecords();
});

// 导入学费数据
async function handleFeeUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
    alert('请上传Excel文件（.xlsx或.xls格式）');
    event.target.value = '';
    return;
  }
  
  const reader = new FileReader();
  reader.onload = async (e) => {
    loading.value = true;
    try {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });
      
      if (jsonData.length < 2) {
        alert('Excel文件格式不正确，请使用下载的模板');
        event.target.value = '';
        return;
      }
      
      const headers = jsonData[0];
      if (!validateFeeHeaders(headers)) {
        alert('Excel表头格式不正确，请使用下载的模板');
        event.target.value = '';
        return;
      }
      
      let successCount = 0;
      let errorCount = 0;
      const newRecords = [];
      const errors = [];
      
      for (let i = 1; i < jsonData.length; i++) {
        const rowData = jsonData[i];
        if (rowData.length === 0 || !rowData[0]) continue;
        
        try {
          const record = parseFeeRowData(headers, rowData, i + 1);
          if (record) {
            newRecords.push(record);
            successCount++;
          } else {
            errorCount++;
            errors.push(`第${i + 1}行：必填字段缺失或团支部编号不存在`);
          }
        } catch (error) {
          errorCount++;
          errors.push(`第${i + 1}行：${error.message}`);
        }
      }
      
      // 批量保存到后端
      if (newRecords.length > 0) {
        for (const record of newRecords) {
          try {
            const postData = {
              name: record.name,
              student_id: record.studentId,
              branch: record.branchId,
              month: record.month,
              amount: record.amount,
              status: '已缴',
              pay_date: new Date().toISOString().split('T')[0]
            };
            await axios.post(RECORD_API, postData, {
              headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
          } catch (error) {
            errorCount++;
            successCount--;
            errors.push(`${record.name} (${record.studentId})：保存失败`);
          }
        }
        
        await fetchRecords();
        await fetchBranches();
      }
      
      if (errors.length > 0) {
        alert(`导入完成！成功：${successCount}条，失败：${errorCount}条\n\n失败详情：\n${errors.join('\n')}`);
      } else {
        alert(`导入完成！成功：${successCount}条，失败：${errorCount}条`);
      }
      
    } catch (error) {
      console.error('解析Excel文件失败:', error);
      alert('解析Excel文件失败，请检查文件格式');
    } finally {
      loading.value = false;
    }
    
    event.target.value = '';
  };
  
  reader.readAsArrayBuffer(file);
}

// 验证缴费表头
function validateFeeHeaders(headers) {
  if (!headers || headers.length < excelHeaders.length) return false;
  return excelHeaders.every((header, index) => headers[index] === header);
}

// 解析缴费行数据
function parseFeeRowData(headers, rowData, rowNum) {
  const record = {
    status: '已缴',
    payDate: new Date().toISOString().split('T')[0]
  };
  
  headers.forEach((header, index) => {
    const fieldName = fieldMapping[header];
    if (fieldName && rowData[index] !== undefined && rowData[index] !== null) {
      if (fieldName === 'amount') {
        record[fieldName] = parseFloat(rowData[index]) || 6;
      } else {
        record[fieldName] = String(rowData[index]).trim();
      }
    }
  });
  
  // 必填字段验证
  if (!record.name || !record.studentId || !record.branchCode || !record.month) {
    return null;
  }
  
  // 根据团支部编号查找团支部ID
  const branch = branches.value.find(b => b.code === record.branchCode);
  if (!branch) {
    throw new Error(`团支部编号不存在：${record.branchCode}`);
  }
  record.branchId = branch.id;
  delete record.branchCode; // 删除临时字段
  
  return record;
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>团费管理</h1>
    </header>
    
    <!-- 视图切换 -->
    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeView === 'branches' }" @click="activeView = 'branches'">团支部管理</button>
      <button class="tab-btn" :class="{ active: activeView === 'records' }" @click="activeView = 'records'">缴费记录</button>
    </div>
    
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
    
    <!-- 团支部管理视图 -->
    <div v-if="activeView === 'branches'" class="tab-content">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <input type="text" v-model="searchQuery" placeholder="搜索团支部名称或编号..." class="search-input" />
        </div>
        <div class="toolbar-right">
          <button v-if="hasPermission('league:edit')" class="btn btn-secondary" @click="openRecordModal()">添加缴费</button>
          <button v-if="hasPermission('league:add')" class="btn btn-primary" @click="openCreateBranchModal()">添加团支部</button>
        </div>
      </div>
      
      <!-- 团支部列表 -->
      <div class="cards-grid">
        <div v-for="branch in filteredBranches" :key="branch.id" class="branch-card">
          <div class="card-header">
            <div class="branch-info">
              <h3>{{ branch.name }}</h3>
              <span class="branch-code">{{ branch.code }}</span>
            </div>
            <span class="rate-badge" :class="{ high: parseFloat(getBranchRate(branch.id)) >= 95 }">
              {{ getBranchRate(branch.id) }}
            </span>
          </div>
          <div class="card-body">
            <div class="stat-row">
              <div class="stat-item-inline">
                <span class="label">应交人数</span>
                <span class="value">{{ getBranchTotalCount(branch.id) }}</span>
              </div>
              <div class="stat-item-inline">
                <span class="label">已交人数</span>
                <span class="value success">{{ getBranchPaidCount(branch.id) }}</span>
              </div>
              <div class="stat-item-inline">
                <span class="label">未交人数</span>
                <span class="value danger">{{ getBranchUnpaidCount(branch.id) }}</span>
              </div>
            </div>
            <div class="amount-display">
              <span class="label">收缴金额：</span>
              <span class="amount">¥{{ getBranchCollectedAmount(branch.id) }} 人民币</span>
            </div>
          </div>
          <div class="card-footer">
            <button class="action-btn view" @click="openBranchDetailModal(branch)">查看详情</button>
            <button v-if="hasPermission('league:edit') && branch.unpaid > 0" class="action-btn pay" @click="openRecordModal(branch)">添加缴费</button>
            <button v-if="hasPermission('league:edit') && branch.unpaid > 0" class="action-btn batch-pay" @click="batchPay(branch)">批量缴费</button>
            <button v-if="hasPermission('league:edit')" class="action-btn edit" @click="openEditBranchModal(branch)">编辑</button>
            <button v-if="hasPermission('league:delete')" class="action-btn delete" @click="deleteBranch(branch)">删除</button>
          </div>
        </div>
      </div>
      
      <div v-if="filteredBranches.length === 0" class="empty-state">
        <p>暂无团支部数据</p>
      </div>
    </div>
    
    <!-- 缴费记录视图 -->
    <div v-if="activeView === 'records'" class="tab-content">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <input type="text" v-model="searchQuery" placeholder="搜索姓名或学号..." class="search-input" />
          <select v-model="selectedBranchId" class="filter-select">
            <option value="">全部团支部</option>
            <option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option>
          </select>
          <select v-model="statusFilter" class="filter-select">
            <option value="">全部状态</option>
            <option value="已缴">已缴</option>
            <option value="未缴">未缴</option>
          </select>
        </div>
        <div class="toolbar-right">
          <button class="btn btn-secondary" @click="downloadFeeTemplate">下载模板</button>
          <label class="btn btn-secondary file-upload-label">
            <input type="file" accept=".xlsx,.xls" style="display: none" @change="handleFeeUpload" />
            导入数据
          </label>
          <button class="btn btn-secondary" @click="exportFeeData">导出数据</button>
          <button v-if="hasPermission('league:edit')" class="btn btn-primary" @click="openRecordModal()">添加缴费</button>
        </div>
      </div>
      
      <!-- 记录列表 -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th>学号</th>
              <th>团支部</th>
              <th>缴费月份</th>
              <th>金额</th>
              <th>状态</th>
              <th>缴费时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in paginatedRecords" :key="record.id">
              <td>{{ record.name }}</td>
              <td>{{ record.studentId }}</td>
              <td><span class="branch-tag">{{ getBranchName(record.branchId) }}</span></td>
              <td>{{ record.month }}</td>
              <td>¥{{ record.amount }}</td>
              <td><span class="status-tag" :class="record.status">{{ record.status }}</span></td>
              <td>{{ record.payDate || '-' }}</td>
              <td>
                <button v-if="hasPermission('league:edit') && record.status === '未缴'" class="action-btn pay" @click="payRecord(record)">缴费</button>
                <span v-else class="paid-text">已缴费</span>
              </td>
            </tr>
          </tbody>
        </table>
        
        <!-- 分页 -->
        <div v-if="filteredRecords.length > pageSize" class="pagination">
          <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">上一页</button>
          <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="page-btn" :disabled="currentPage === totalPages" @click="nextPage">下一页</button>
        </div>
        
        <div v-if="filteredRecords.length === 0" class="empty-state">
          <p>暂无缴费记录</p>
        </div>
      </div>
    </div>
    
    <!-- 团支部模态框 -->
    <div v-if="showBranchModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑团支部' : '添加团支部' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>团支部名称 <span class="required">*</span></label>
            <input type="text" v-model="branchFormData.name" class="form-input" placeholder="例如：计算机学院团支部" />
            <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
          </div>
          <div class="form-group">
            <label>团支部编号 <span class="required">*</span></label>
            <input type="text" v-model="branchFormData.code" class="form-input" placeholder="例如：CST001" />
            <span v-if="formErrors.code" class="form-error">{{ formErrors.code }}</span>
          </div>
          <div class="form-group">
            <label>每月缴费金额（元）<span class="required">*</span></label>
            <input type="number" v-model="branchFormData.amount" class="form-input" min="0" step="0.5" />
            <span v-if="formErrors.amount" class="form-error">{{ formErrors.amount }}</span>
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="branchFormData.description" class="form-textarea" placeholder="团支部简介"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveBranch">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 缴费记录模态框 -->
    <div v-if="showRecordModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>添加缴费记录</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>团支部 <span class="required">*</span></label>
            <select v-model="recordFormData.branchId" class="form-select">
              <option value="">请选择团支部</option>
              <option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option>
            </select>
            <span v-if="formErrors.branchId" class="form-error">{{ formErrors.branchId }}</span>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>姓名 <span class="required">*</span></label>
              <input type="text" v-model="recordFormData.name" class="form-input" placeholder="姓名" />
              <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
            </div>
            <div class="form-group">
              <label>学号 <span class="required">*</span></label>
              <input type="text" v-model="recordFormData.studentId" class="form-input" placeholder="学号" />
              <span v-if="formErrors.studentId" class="form-error">{{ formErrors.studentId }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>缴费月份 <span class="required">*</span></label>
              <input type="month" v-model="recordFormData.month" class="form-input" />
              <span v-if="formErrors.month" class="form-error">{{ formErrors.month }}</span>
            </div>
            <div class="form-group">
              <label>缴费金额（元）</label>
              <input type="number" v-model="recordFormData.amount" class="form-input" min="0" step="0.5" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveRecord">保存并缴费</button>
        </div>
      </div>
    </div>
    
    <!-- 团支部详情模态框 -->
    <div v-if="showBranchDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>团支部详情</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentBranch">
          <div class="detail-section">
            <h3 class="section-title">基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">团支部名称：</span>{{ currentBranch.name }}</div>
              <div class="detail-item"><span class="label">团支部编号：</span>{{ currentBranch.code }}</div>
              <div class="detail-item"><span class="label">每月缴费：</span>¥{{ currentBranch.amount }}</div>
              <div class="detail-item"><span class="label">收缴率：</span><span class="rate-badge">{{ getBranchRate(currentBranch.id) }}</span></div>
              <div class="detail-item full-width" v-if="currentBranch.description"><span class="label">备注：</span>{{ currentBranch.description }}</div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">缴费统计</h3>
            <div class="stats-row">
              <div class="mini-stat">
                <div class="mini-value">{{ getBranchTotalCount(currentBranch.id) }}</div>
                <div class="mini-label">应交人数</div>
              </div>
              <div class="mini-stat success">
                <div class="mini-value">{{ getBranchPaidCount(currentBranch.id) }}</div>
                <div class="mini-label">已交人数</div>
              </div>
              <div class="mini-stat danger">
                <div class="mini-value">{{ getBranchUnpaidCount(currentBranch.id) }}</div>
                <div class="mini-label">未交人数</div>
              </div>
              <div class="mini-stat">
                <div class="mini-value">¥{{ getBranchCollectedAmount(currentBranch.id) }} 人民币</div>
                <div class="mini-label">收缴金额</div>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">缴费记录</h3>
            <div class="mini-table">
              <div v-for="record in records.filter(r => r.branchId === currentBranch.id).slice(0, 5)" :key="record.id" class="mini-row">
                <span>{{ record.name }}</span>
                <span>{{ record.studentId }}</span>
                <span>{{ record.month }}</span>
                <span>¥{{ record.amount }}</span>
                <span class="status-tag" :class="record.status">{{ record.status }}</span>
              </div>
              <div v-if="records.filter(r => r.branchId === currentBranch.id).length === 0" class="empty-mini">
                <p>暂无缴费记录</p>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button class="btn btn-primary" @click="openRecordModal(currentBranch)">添加缴费</button>
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
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 24px;
  color: #1a1a1a;
  font-weight: 600;
  font-family: 'Microsoft YaHei', sans-serif;
}

.tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.tab-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: #ffffff;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid #e8e8e8;
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  border-color: transparent;
}

.tab-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
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

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  width: 250px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
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

.btn-secondary {
  background: #ffffff;
  color: #666;
  border: 1px solid #e8e8e8;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.branch-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 24px;
  transition: all 0.2s ease;
}

.branch-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.branch-info h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.branch-code {
  font-size: 13px;
  color: #999;
}

.rate-badge {
  padding: 6px 12px;
  background: #fff7e6;
  color: #fa8c16;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
}

.rate-badge.high {
  background: #f6ffed;
  color: #52c41a;
}

.card-body {
  margin-bottom: 20px;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-item-inline {
  text-align: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.stat-item-inline .label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.stat-item-inline .value {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.stat-item-inline .value.success {
  color: #52c41a;
}

.stat-item-inline .value.danger {
  color: #ff4d4f;
}

.amount-display {
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
  color: #ffffff;
  text-align: center;
}

.amount-display .label {
  font-size: 14px;
  opacity: 0.9;
}

.amount-display .amount {
  font-size: 24px;
  font-weight: 600;
  margin-left: 8px;
}

.card-footer {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.已缴 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.未缴 {
  background: #fff1f0;
  color: #ff4d4f;
}

.branch-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.action-btn {
  margin: 0 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn.view {
  background: #e6f7ff;
  color: #1890ff;
}

.action-btn.edit {
  background: #fff7e6;
  color: #fa8c16;
}

.action-btn.delete {
  background: #fff1f0;
  color: #f5222d;
}

.action-btn.pay {
  background: #52c41a;
  color: #ffffff;
}

.action-btn.batch-pay {
  background: #722ed1;
  color: #ffffff;
}

.file-upload-label {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}

.file-upload-label:active {
  opacity: 0.9;
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
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.data-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.data-table td {
  font-size: 14px;
  color: #333;
}

.paid-text {
  color: #52c41a;
  font-size: 13px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #ffffff;
  color: #666;
  font-size: 14px;
  cursor: pointer;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
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
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-header h2 {
  font-size: 20px;
  margin: 0;
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
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.required {
  color: #ff4d4f;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  min-height: 80px;
  resize: vertical;
  box-sizing: border-box;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-error {
  display: block;
  font-size: 12px;
  color: #ff4d4f;
  margin-top: 4px;
}

/* 详情样式 */
.detail-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #667eea;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.detail-item {
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 6px;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-item .label {
  color: #999;
  font-weight: 500;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.mini-stat {
  text-align: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.mini-stat.success {
  background: #f6ffed;
}

.mini-stat.danger {
  background: #fff1f0;
}

.mini-value {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.mini-stat.success .mini-value {
  color: #52c41a;
}

.mini-stat.danger .mini-value {
  color: #ff4d4f;
}

.mini-label {
  font-size: 12px;
  color: #666;
}

.mini-table {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.mini-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 80px;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  gap: 12px;
  align-items: center;
}

.mini-row:last-child {
  border-bottom: none;
}

.empty-mini {
  padding: 24px;
  text-align: center;
  color: #999;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .mini-row {
    grid-template-columns: 1fr 1fr;
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
  
  .tabs {
    flex-wrap: wrap;
  }
}
</style>