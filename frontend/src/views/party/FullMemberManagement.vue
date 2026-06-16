<script setup>
import { ref, computed, onMounted } from 'vue';
import * as XLSX from 'xlsx';
import axios from 'axios';
import { hasPermission } from '../../utils/permission';
import { getDictionaryNames } from '../../utils/dictionary';

// API配置
const API_URL = '/api/development-applications/';

// 审批阶段定义
const stages = [
  { key: 'application', label: '入党申请', color: '#1890ff' },
  { key: 'activist', label: '积极分子', color: '#52c41a' },
  { key: 'candidate', label: '发展对象', color: '#fa8c16' },
  { key: 'probationary', label: '预备党员', color: '#722ed1' },
  { key: 'full', label: '正式党员', color: '#f5222d' }
];

// 审批状态定义
const approvalStatuses = [
  { key: 'pending', label: '待审批', color: '#faad14' },
  { key: 'approved', label: '已通过', color: '#52c41a' },
  { key: 'rejected', label: '已拒绝', color: '#f5222d' }
];

// Excel表头映射
const excelHeaders = [
  '姓名', '性别', '民族', '出生日期', '学历', '联系电话', '所属党组织',
  '申请日期', '当前阶段', '审批状态', '备注'
];

// Excel数据字段映射
const fieldMapping = {
  '姓名': 'name',
  '性别': 'gender',
  '民族': 'ethnicity',
  '出生日期': 'birthDate',
  '学历': 'education',
  '联系电话': 'phone',
  '所属党组织': 'organization',
  '申请日期': 'applicationDate',
  '当前阶段': 'currentStage',
  '审批状态': 'approvalStatus',
  '备注': 'notes'
};

// 申请数据
const applications = ref([]);
const loading = ref(false);

// 批量选择相关
const selectedIds = ref([]);

// 是否全选
const isAllSelected = computed(() => {
  return paginatedApplications.value.length > 0 &&
    paginatedApplications.value.every(a => selectedIds.value.includes(a.id));
});

// 切换全选
function toggleSelectAll() {
  if (isAllSelected.value) {
    paginatedApplications.value.forEach(a => {
      const index = selectedIds.value.indexOf(a.id);
      if (index !== -1) {
        selectedIds.value.splice(index, 1);
      }
    });
  } else {
    paginatedApplications.value.forEach(a => {
      if (!selectedIds.value.includes(a.id)) {
        selectedIds.value.push(a.id);
      }
    });
  }
}

// 切换单个选择
function toggleSelect(applicationId, event) {
  event.stopPropagation();
  const index = selectedIds.value.indexOf(applicationId);
  if (index === -1) {
    selectedIds.value.push(applicationId);
  } else {
    selectedIds.value.splice(index, 1);
  }
}

// 批量删除
async function deleteSelected() {
  if (selectedIds.value.length === 0) {
    alert('请先选择要删除的申请');
    return;
  }

  if (confirm(`确定要删除选中的 ${selectedIds.value.length} 条申请吗？`)) {
    const token = localStorage.getItem('token');
    loading.value = true;
    let successCount = 0;

    try {
      for (const id of selectedIds.value) {
        const response = await axios.delete(`${API_URL}${id}/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.status === 204 || response.status === 200) {
          successCount++;
          applications.value = applications.value.filter(a => a.id !== id);
        }
      }

      selectedIds.value = [];
      alert(`成功删除 ${successCount} 条申请！`);
    } catch (error) {
      console.error('批量删除失败:', error);
      alert('批量删除失败，请重试');
    } finally {
      loading.value = false;
    }
  }
}

// 从API获取党员发展申请数据
async function fetchApplications() {
  loading.value = true;
  const token = localStorage.getItem('token');
  
  if (!token) {
    console.error('未登录或token已过期');
    loading.value = false;
    return;
  }
  
  try {
    const response = await axios.get(API_URL, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = response.data.results || response.data;
    applications.value = data.map(item => ({
      id: item.id,
      name: item.name,
      gender: item.gender,
      ethnicity: item.ethnicity,
      birthDate: formatDate(item.birth_date),
      education: item.education,
      phone: item.phone,
      organization: item.organization,
      applicationDate: formatDate(item.application_date),
      currentStage: item.current_stage,
      approvalStatus: item.application_status,
      notes: item.notes || '',
      studentId: item.student_id || '',
      grade: item.grade || '',
      department: item.department || '',
      email: item.email || '',
      history: item.approval_records || []
    }));
  } catch (error) {
    console.error('获取党员发展申请数据失败:', error);
  } finally {
    loading.value = false;
  }
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  return date.toISOString().split('T')[0];
}

// 页面加载时获取数据
onMounted(() => {
  fetchApplications();
  loadDictionaryOptions();
});

// 统计数据
const stats = computed(() => {
  const total = applications.value.length;
  const pending = applications.value.filter(a => a.approvalStatus === 'pending').length;
  const approved = applications.value.filter(a => a.approvalStatus === 'approved').length;
  const rejected = applications.value.filter(a => a.approvalStatus === 'rejected').length;
  
  return [
    { label: '申请总数', value: total, icon: '📋' },
    { label: '待审批', value: pending, icon: '⏳' },
    { label: '已通过', value: approved, icon: '✅' },
    { label: '已拒绝', value: rejected, icon: '❌' }
  ];
});

// 模态框状态
const showModal = ref(false);
const showDetailModal = ref(false);
const showApprovalModal = ref(false);
const currentApplication = ref(null);
const formErrors = ref({});
const activeTab = ref('list');

// 筛选状态
const searchQuery = ref('');
const organizationFilter = ref('');
const stageFilter = ref('');
const statusFilter = ref('');

// 分页
const pageSize = 10;
const currentPage = ref(1);

// 审批表单
const approvalForm = ref({
  status: 'approved',
  opinion: ''
});

// 组织列表
const organizations = [
  '计算机学院党支部', '商学院党支部', '文学院党支部', '工学院党支部',
  '理学院党支部', '医学院党支部', '艺术学院党支部', '体育学院党支部'
];

// 民族列表
const ethnicities = [
  '汉族', '回族', '藏族', '维吾尔族', '苗族', '彝族', '壮族', '布依族',
  '朝鲜族', '满族', '侗族', '瑶族', '白族', '土家族', '哈尼族', '其他'
];

// 学历列表
const educations = ref([]);

const loadDictionaryOptions = async () => {
  educations.value = await getDictionaryNames('education');
};

// 筛选后的申请
const filteredApplications = computed(() => {
  return applications.value.filter(a => {
    const matchSearch = !searchQuery.value || 
      a.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      a.studentId.includes(searchQuery.value) ||
      a.phone.includes(searchQuery.value);
    const matchOrg = !organizationFilter.value || a.organization === organizationFilter.value;
    const matchStage = !stageFilter.value || a.currentStage === stageFilter.value;
    const matchStatus = !statusFilter.value || a.approvalStatus === statusFilter.value;
    return matchSearch && matchOrg && matchStage && matchStatus;
  });
});

// 分页后的申请
const paginatedApplications = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredApplications.value.slice(start, end);
});

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredApplications.value.length / pageSize);
});

// 获取阶段标签
function getStageLabel(stageKey) {
  const stage = stages.find(s => s.key === stageKey);
  return stage ? stage.label : stageKey;
}

// 获取阶段颜色
function getStageColor(stageKey) {
  const stage = stages.find(s => s.key === stageKey);
  return stage ? stage.color : '#999';
}

// 获取状态标签
function getStatusLabel(statusKey) {
  const status = approvalStatuses.find(s => s.key === statusKey);
  return status ? status.label : statusKey;
}

// 获取状态颜色
function getStatusColor(statusKey) {
  const status = approvalStatuses.find(s => s.key === statusKey);
  return status ? status.color : '#999';
}

// 打开详情模态框
function openDetailModal(application) {
  currentApplication.value = application;
  showDetailModal.value = true;
}

// 打开审批模态框
function openApprovalModal(application) {
  currentApplication.value = application;
  approvalForm.value = {
    status: 'approved',
    opinion: ''
  };
  formErrors.value = {};
  showApprovalModal.value = true;
}

// 验证审批表单
function validateApprovalForm() {
  const errors = {};
  
  if (!approvalForm.value.opinion) {
    errors.opinion = '请填写审批意见';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 提交审批
async function submitApproval() {
  if (!validateApprovalForm()) return;
  
  const token = localStorage.getItem('token');
  if (!token) {
    alert('未登录或token已过期');
    return;
  }
  
  const app = currentApplication.value;
  
  try {
    // 先创建审批历史记录
    const historyData = {
      application: app.id,
      stage: app.currentStage,
      status: approvalForm.value.status === 'approved' ? '已通过' : '已拒绝',
      opinion: approvalForm.value.opinion
    };
    
    await axios.post('/api/approval-records/', historyData, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    // 调用审批接口
    const approveEndpoint = approvalForm.value.status === 'approved' ? 'approve' : 'reject';
    const response = await axios.post(`${API_URL}${app.id}/${approveEndpoint}/`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.status === 200) {
      showApprovalModal.value = false;
      fetchApplications(); // 刷新数据
      alert('审批成功！');
    }
  } catch (error) {
    console.error('审批失败:', error);
    alert('审批失败：' + (error.response?.data?.detail || error.message));
  }
}

// 关闭模态框
function closeModal() {
  showModal.value = false;
  showDetailModal.value = false;
  showApprovalModal.value = false;
  formErrors.value = {};
}

// 分页操作
function prevPage() {
  if (currentPage.value > 1) currentPage.value--;
}

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++;
}

// 获取流程进度百分比
function getProgressPercent(application) {
  const stageIndex = stages.findIndex(s => s.key === application.currentStage);
  return ((stageIndex + 1) / stages.length) * 100;
}

// Excel功能
function downloadTemplate() {
  const templateData = [
    excelHeaders,
    ['张三', '男', '汉族', '2000-05-15', '本科', '13912345678', '计算机学院党支部', '2024-01-01', 'application', 'pending', '']
  ];
  
  const worksheet = XLSX.utils.aoa_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '党员发展流程');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 13 }, { wch: 18 }, { wch: 12 }, { wch: 10 }, { wch: 10 }, { wch: 20 }
  ];
  
  XLSX.writeFile(workbook, '党员发展流程导入模板.xlsx');
}

function exportData() {
  const exportData = filteredApplications.value.map(app => ({
    '姓名': app.name,
    '性别': app.gender,
    '民族': app.ethnicity,
    '出生日期': app.birthDate,
    '学历': app.education,
    '联系电话': app.phone,
    '所属党组织': app.organization,
    '申请日期': app.applicationDate,
    '当前阶段': getStageLabel(app.currentStage),
    '审批状态': getStatusLabel(app.approvalStatus),
    '学号': app.studentId || '-',
    '年级': app.grade || '-',
    '学院': app.department || '-',
    '邮箱': app.email || '-',
    '入党介绍人': app.introducer || '-',
    '备注': app.notes || '-'
  }));
  
  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '党员发展流程');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 13 }, { wch: 18 }, { wch: 12 }, { wch: 10 }, { wch: 10 }, { wch: 12 }, { wch: 10 }, { wch: 15 }, { wch: 18 }, { wch: 10 }, { wch: 20 }
  ];
  
  const fileName = `党员发展流程数据_${new Date().toISOString().split('T')[0]}.xlsx`;
  XLSX.writeFile(workbook, fileName);
}

function handleUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
    alert('请上传Excel文件（.xlsx或.xls格式）');
    event.target.value = '';
    return;
  }
  
  const reader = new FileReader();
  reader.onload = (e) => {
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
      if (!headers || headers.length < excelHeaders.length) {
        alert('Excel表头格式不正确，请使用下载的模板');
        event.target.value = '';
        return;
      }
      
      let successCount = 0;
      let errorCount = 0;
      const newApplications = [];
      const errors = [];
      
      for (let i = 1; i < jsonData.length; i++) {
        const rowData = jsonData[i];
        if (rowData.length === 0 || !rowData[0]) continue;
        
        try {
          const application = {
            id: applications.value.length + newApplications.length + 1,
            studentId: '',
            grade: '',
            department: '',
            email: '',
            introducer: '',
            notes: '',
            history: []
          };
          
          headers.forEach((header, index) => {
            const fieldName = fieldMapping[header];
            if (fieldName && rowData[index] !== undefined && rowData[index] !== null) {
              application[fieldName] = String(rowData[index]).trim();
            }
          });
          
          // 必填字段验证
          if (!application.name || !application.phone || !application.organization || !application.applicationDate) {
            errorCount++;
            errors.push(`第${i + 1}行：必填字段缺失`);
            continue;
          }
          
          // 手机号验证
          if (!/^1[3-9]\d{9}$/.test(application.phone)) {
            errorCount++;
            errors.push(`第${i + 1}行：联系电话格式不正确`);
            continue;
          }
          
          // 设置默认值
          if (!application.currentStage) application.currentStage = 'application';
          if (!application.approvalStatus) application.approvalStatus = 'pending';
          if (!application.gender) application.gender = '男';
          if (!application.ethnicity) application.ethnicity = '汉族';
          if (!application.education) application.education = '本科';
          
          newApplications.push(application);
          successCount++;
        } catch (error) {
          errorCount++;
          errors.push(`第${i + 1}行：${error.message}`);
        }
      }
      
      newApplications.forEach(app => applications.value.unshift(app));
      
      if (errors.length > 0) {
        alert(`导入完成！成功：${successCount}条，失败：${errorCount}条\n\n失败详情：\n${errors.slice(0, 10).join('\n')}`);
      } else {
        alert(`导入完成！成功：${successCount}条，失败：${errorCount}条`);
      }
      
    } catch (error) {
      console.error('解析Excel文件失败:', error);
      alert('解析Excel文件失败，请检查文件格式');
    }
    
    event.target.value = '';
  };
  
  reader.readAsArrayBuffer(file);
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>党员发展流程管理</h1>
    </header>
    
    <!-- 标签切换 -->
    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">申请列表</button>
      <button class="tab-btn" :class="{ active: activeTab === 'stats' }" @click="activeTab = 'stats'">统计分析</button>
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
    
    <!-- 申请列表 -->
    <div v-if="activeTab === 'list'" class="tab-content">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <span v-if="selectedIds.length > 0" class="selected-count">已选择 {{ selectedIds.length }} 条</span>
          <input type="text" v-model="searchQuery" placeholder="搜索姓名、学号或电话..." class="search-input" />
          <select v-model="organizationFilter" class="filter-select">
            <option value="">全部组织</option>
            <option v-for="org in organizations" :key="org" :value="org">{{ org }}</option>
          </select>
          <select v-model="stageFilter" class="filter-select">
            <option value="">全部阶段</option>
            <option v-for="stage in stages" :key="stage.key" :value="stage.key">{{ stage.label }}</option>
          </select>
          <select v-model="statusFilter" class="filter-select">
            <option value="">全部状态</option>
            <option v-for="status in approvalStatuses" :key="status.key" :value="status.key">{{ status.label }}</option>
          </select>
        </div>
        <div class="toolbar-right">
          <button v-if="selectedIds.length > 0 && hasPermission('party:delete')" class="btn btn-danger" @click="deleteSelected">批量删除</button>
          <button v-if="hasPermission('party:edit')" class="btn btn-secondary" @click="downloadTemplate">下载模板</button>
          <label v-if="hasPermission('party:edit')" class="btn btn-secondary file-upload-label">
            <input type="file" accept=".xlsx,.xls" style="display: none" @change="handleUpload" />
            导入数据
          </label>
          <button v-if="hasPermission('party:edit')" class="btn btn-secondary" @click="exportData">导出数据</button>
        </div>
      </div>
      
      <!-- 申请列表表格 -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>
                <input type="checkbox" v-model="isAllSelected" @change="toggleSelectAll" />
              </th>
              <th>姓名</th>
              <th>性别</th>
              <th>学历</th>
              <th>所属党组织</th>
              <th>申请日期</th>
              <th>当前阶段</th>
              <th>审批状态</th>
              <th>流程进度</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="app in paginatedApplications" :key="app.id">
              <td @click.stop>
                <input type="checkbox" :checked="selectedIds.includes(app.id)" @change="toggleSelect(app.id, $event)" />
              </td>
              <td>{{ app.name }}</td>
              <td><span class="gender-tag">{{ app.gender }}</span></td>
              <td>{{ app.education }}</td>
              <td><span class="org-tag">{{ app.organization }}</span></td>
              <td>{{ app.applicationDate }}</td>
              <td>
                <span class="stage-tag" :style="{ background: getStageColor(app.currentStage) + '20', color: getStageColor(app.currentStage) }">
                  {{ getStageLabel(app.currentStage) }}
                </span>
              </td>
              <td>
                <span class="status-tag" :style="{ background: getStatusColor(app.approvalStatus) + '20', color: getStatusColor(app.approvalStatus) }">
                  {{ getStatusLabel(app.approvalStatus) }}
                </span>
              </td>
              <td>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: getProgressPercent(app) + '%' }"></div>
                </div>
                <span class="progress-text">{{ Math.round(getProgressPercent(app)) }}%</span>
              </td>
              <td>
                <button class="action-btn view" @click="openDetailModal(app)">详情</button>
                <button v-if="app.approvalStatus === 'pending'" class="action-btn approve" @click="openApprovalModal(app)">审批</button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <!-- 分页 -->
        <div v-if="filteredApplications.length > pageSize" class="pagination">
          <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">上一页</button>
          <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="page-btn" :disabled="currentPage === totalPages" @click="nextPage">下一页</button>
        </div>
        
        <div v-if="filteredApplications.length === 0" class="empty-state">
          <p>暂无申请数据</p>
        </div>
      </div>
    </div>
    
    <!-- 统计分析 -->
    <div v-if="activeTab === 'stats'" class="tab-content">
      <div class="stats-section">
        <h3 class="section-title">阶段分布</h3>
        <div class="stats-row">
          <div class="mini-stat" v-for="stage in stages" :key="stage.key">
            <div class="mini-value">{{ applications.filter(a => a.currentStage === stage.key).length }}</div>
            <div class="mini-label">{{ stage.label }}</div>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <h3 class="section-title">审批状态分布</h3>
        <div class="stats-row">
          <div class="mini-stat" v-for="status in approvalStatuses" :key="status.key">
            <div class="mini-value">{{ applications.filter(a => a.approvalStatus === status.key).length }}</div>
            <div class="mini-label">{{ status.label }}</div>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <h3 class="section-title">组织分布</h3>
        <div class="stats-row">
          <div class="mini-stat" v-for="org in organizations.slice(0, 4)" :key="org">
            <div class="mini-value">{{ applications.filter(a => a.organization === org).length }}</div>
            <div class="mini-label">{{ org.replace('党支部', '') }}</div>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <h3 class="section-title">性别分布</h3>
        <div class="stats-row">
          <div class="mini-stat">
            <div class="mini-value">{{ applications.filter(a => a.gender === '男').length }}</div>
            <div class="mini-label">男性</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ applications.filter(a => a.gender === '女').length }}</div>
            <div class="mini-label">女性</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>申请详情</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentApplication">
          <!-- 流程进度 -->
          <div class="flow-progress">
            <div class="flow-steps">
              <div v-for="(stage, index) in stages" :key="stage.key" class="flow-step" :class="{ active: stages.findIndex(s => s.key === currentApplication.currentStage) >= index, current: currentApplication.currentStage === stage.key }">
                <div class="step-circle" :style="{ background: stages.findIndex(s => s.key === currentApplication.currentStage) >= index ? getStageColor(stage.key) : '#e8e8e8' }">
                  {{ index + 1 }}
                </div>
                <div class="step-label">{{ stage.label }}</div>
                <div v-if="index < stages.length - 1" class="step-line" :class="{ active: stages.findIndex(s => s.key === currentApplication.currentStage) > index }"></div>
              </div>
            </div>
          </div>
          
          <!-- 基本信息 -->
          <div class="detail-section">
            <h3 class="section-title">基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">姓名：</span>{{ currentApplication.name }}</div>
              <div class="detail-item"><span class="label">性别：</span>{{ currentApplication.gender }}</div>
              <div class="detail-item"><span class="label">民族：</span>{{ currentApplication.ethnicity }}</div>
              <div class="detail-item"><span class="label">出生日期：</span>{{ currentApplication.birthDate }}</div>
              <div class="detail-item"><span class="label">学历：</span>{{ currentApplication.education }}</div>
              <div class="detail-item"><span class="label">联系电话：</span>{{ currentApplication.phone }}</div>
              <div class="detail-item"><span class="label">所属党组织：</span>{{ currentApplication.organization }}</div>
              <div class="detail-item"><span class="label">申请日期：</span>{{ currentApplication.applicationDate }}</div>
            </div>
          </div>
          
          <!-- 学籍信息 -->
          <div class="detail-section">
            <h3 class="section-title">学籍信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">学号：</span>{{ currentApplication.studentId || '-' }}</div>
              <div class="detail-item"><span class="label">年级：</span>{{ currentApplication.grade || '-' }}</div>
              <div class="detail-item"><span class="label">学院：</span>{{ currentApplication.department || '-' }}</div>
              <div class="detail-item"><span class="label">邮箱：</span>{{ currentApplication.email || '-' }}</div>
              <div class="detail-item"><span class="label">入党介绍人：</span>{{ currentApplication.introducer || '-' }}</div>
              <div class="detail-item"><span class="label">备注：</span>{{ currentApplication.notes || '-' }}</div>
            </div>
          </div>
          
          <!-- 审批历史 -->
          <div class="detail-section">
            <h3 class="section-title">审批历史</h3>
            <div v-if="currentApplication.history && currentApplication.history.length > 0" class="history-timeline">
              <div v-for="(record, index) in currentApplication.history" :key="index" class="history-item">
                <div class="history-marker">
                  <div class="marker-dot" :style="{ background: record.status === 'approved' ? '#52c41a' : '#f5222d' }"></div>
                  <div v-if="index < currentApplication.history.length - 1" class="marker-line"></div>
                </div>
                <div class="history-content">
                  <div class="history-header">
                    <span class="stage-name">{{ getStageLabel(record.stage) }}</span>
                    <span class="status-badge" :style="{ background: record.status === 'approved' ? '#f6ffed' : '#fff1f0', color: record.status === 'approved' ? '#52c41a' : '#f5222d' }">
                      {{ record.status === 'approved' ? '已通过' : '已拒绝' }}
                    </span>
                  </div>
                  <div class="history-info">
                    <div><span class="info-label">审批人：</span>{{ record.approver }}</div>
                    <div><span class="info-label">审批时间：</span>{{ record.approveTime }}</div>
                  </div>
                  <div class="history-opinion">
                    <span class="info-label">审批意见：</span>{{ record.opinion }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-history">
              <p>暂无审批记录</p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button v-if="currentApplication && currentApplication.approvalStatus === 'pending'" class="btn btn-primary" @click="closeModal(); openApprovalModal(currentApplication)">审批</button>
        </div>
      </div>
    </div>
    
    <!-- 审批模态框 -->
    <div v-if="showApprovalModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>审批操作</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentApplication">
          <div class="approval-info">
            <div class="info-row">
              <span class="info-label">申请人：</span>
              <span class="info-value">{{ currentApplication.name }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">当前阶段：</span>
              <span class="stage-tag" :style="{ background: getStageColor(currentApplication.currentStage) + '20', color: getStageColor(currentApplication.currentStage) }">
                {{ getStageLabel(currentApplication.currentStage) }}
              </span>
            </div>
          </div>
          
          <div class="form-group">
            <label>审批结果 <span class="required">*</span></label>
            <div class="radio-group">
              <label class="radio-item">
                <input type="radio" v-model="approvalForm.status" value="approved" />
                <span class="radio-label approved">同意</span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="approvalForm.status" value="rejected" />
                <span class="radio-label rejected">拒绝</span>
              </label>
            </div>
          </div>
          
          <div class="form-group">
            <label>审批意见 <span class="required">*</span></label>
            <textarea v-model="approvalForm.opinion" class="form-textarea" placeholder="请填写审批意见..." rows="4"></textarea>
            <span v-if="formErrors.opinion" class="form-error">{{ formErrors.opinion }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="submitApproval">提交审批</button>
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
  flex-wrap: wrap;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
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

.btn-danger {
  background: #fff1f0;
  color: #f5222d;
  border: 1px solid #ffa39e;
}

.btn-danger:hover {
  background: #ff4d4f;
  color: #ffffff;
  border-color: #ff4d4f;
}

.selected-count {
  color: #1890ff;
  font-weight: 500;
  padding: 4px 12px;
  background: #e6f7ff;
  border-radius: 4px;
  margin-right: 12px;
}

.file-upload-label {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
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

.data-table th input[type="checkbox"],
.data-table td input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
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

.gender-tag {
  padding: 4px 12px;
  background: #f6ffed;
  color: #52c41a;
  border-radius: 4px;
  font-size: 12px;
}

.org-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.stage-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.progress-bar {
  width: 100px;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
  display: inline-block;
  vertical-align: middle;
  margin-right: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #666;
  vertical-align: middle;
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

.action-btn.approve {
  background: #f6ffed;
  color: #52c41a;
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

/* 统计分析样式 */
.stats-section {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #667eea;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.mini-stat {
  text-align: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.mini-value {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.mini-label {
  font-size: 12px;
  color: #666;
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

/* 流程进度样式 */
.flow-progress {
  margin-bottom: 24px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.flow-steps {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.step-label {
  font-size: 12px;
  color: #666;
  text-align: center;
}

.step-line {
  position: absolute;
  top: 18px;
  left: calc(50% + 20px);
  width: calc(100% - 40px);
  height: 2px;
  background: #e8e8e8;
}

.step-line.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.flow-step.current .step-label {
  color: #667eea;
  font-weight: 600;
}

/* 详情样式 */
.detail-section {
  margin-bottom: 24px;
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

.detail-item .label {
  color: #999;
  font-weight: 500;
}

/* 审批历史样式 */
.history-timeline {
  padding-left: 8px;
}

.history-item {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.history-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.marker-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.marker-line {
  width: 2px;
  flex: 1;
  background: #e8e8e8;
  margin-top: 4px;
}

.history-content {
  flex: 1;
  padding-bottom: 16px;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.stage-name {
  font-weight: 600;
  color: #333;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.history-info {
  display: flex;
  gap: 24px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
}

.info-label {
  color: #999;
}

.history-opinion {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
}

.empty-history {
  padding: 24px;
  text-align: center;
  color: #999;
}

/* 审批表单样式 */
.approval-info {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-value {
  font-weight: 500;
}

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

.form-error {
  display: block;
  font-size: 12px;
  color: #ff4d4f;
  margin-top: 4px;
}

.radio-group {
  display: flex;
  gap: 24px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio-item input[type="radio"] {
  cursor: pointer;
}

.radio-label {
  font-size: 14px;
}

.radio-label.approved {
  color: #52c41a;
}

.radio-label.rejected {
  color: #f5222d;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .flow-steps {
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .flow-step {
    flex: 0 0 calc(33.33% - 12px);
  }
  
  .step-line {
    display: none;
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
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .flow-step {
    flex: 0 0 calc(50% - 8px);
  }
  
  .history-info {
    flex-direction: column;
    gap: 4px;
  }
}
</style>