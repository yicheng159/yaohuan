<script setup>
import { ref, computed, onMounted } from 'vue';
import * as XLSX from 'xlsx';
import axios from 'axios';
import { hasPermission } from '../../utils/permission';
import { getDictionaryNames } from '../../utils/dictionary';

// API配置
const API_URL = '/api/activists/';

// Excel表头映射
const excelHeaders = [
  '姓名', '性别', '民族', '出生日期', '学历', '申请时间', '培养时间',
  '所属班级', '联系电话', '培养人', '状态'
];

// Excel数据字段映射
const fieldMapping = {
  '姓名': 'name',
  '性别': 'gender',
  '民族': 'ethnicity',
  '出生日期': 'birthDate',
  '学历': 'education',
  '申请时间': 'applyDate',
  '培养时间': 'cultivateDate',
  '所属班级': 'organization',
  '联系电话': 'phone',
  '培养人': 'cultivator',
  '状态': 'status'
};

// 积极分子数据
const activists = ref([]);
const loading = ref(false);

// 批量选择相关
const selectedIds = ref([]);

// 是否全选
const isAllSelected = computed(() => {
  return paginatedActivists.value.length > 0 &&
    paginatedActivists.value.every(a => selectedIds.value.includes(a.id));
});

// 切换全选
function toggleSelectAll() {
  if (isAllSelected.value) {
    paginatedActivists.value.forEach(a => {
      const index = selectedIds.value.indexOf(a.id);
      if (index !== -1) {
        selectedIds.value.splice(index, 1);
      }
    });
  } else {
    paginatedActivists.value.forEach(a => {
      if (!selectedIds.value.includes(a.id)) {
        selectedIds.value.push(a.id);
      }
    });
  }
}

// 切换单个选择
function toggleSelect(activistId, event) {
  event.stopPropagation();
  const index = selectedIds.value.indexOf(activistId);
  if (index === -1) {
    selectedIds.value.push(activistId);
  } else {
    selectedIds.value.splice(index, 1);
  }
}

// 批量删除
async function deleteSelected() {
  if (selectedIds.value.length === 0) {
    alert('请先选择要删除的积极分子');
    return;
  }

  if (confirm(`确定要删除选中的 ${selectedIds.value.length} 条积极分子吗？`)) {
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
          activists.value = activists.value.filter(a => a.id !== id);
        }
      }

      selectedIds.value = [];
      alert(`成功删除 ${successCount} 条积极分子！`);
    } catch (error) {
      console.error('批量删除失败:', error);
      alert('批量删除失败，请重试');
    } finally {
      loading.value = false;
    }
  }
}

// 获取积极分子数据
async function fetchActivists() {
  loading.value = true;
  const token = localStorage.getItem('token');
  
  if (!token) {
    console.error('未登录或token已过期');
    alert('请先登录');
    loading.value = false;
    return;
  }
  
  try {
    const response = await axios.get(API_URL, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = response.data.results || response.data;
    activists.value = data.map(item => ({
      id: item.id,
      name: item.name,
      gender: item.gender,
      ethnicity: item.ethnicity,
      birthDate: formatDate(item.birth_date),
      education: item.education,
      applyDate: formatDate(item.application_date),
      cultivateDate: formatDate(item.cultivation_date),
      organization: item.organization,
      phone: item.phone,
      cultivator: item.cultivator,
      status: item.status,
      studentId: item.student_id || '',
      grade: item.grade || '',
      department: item.department || '',
      email: item.email || '',
      address: item.address || '',
      notes: item.notes || '',
      trainingRecords: []
    }));
  } catch (error) {
    console.error('获取积极分子数据失败:', error);
    if (error.response && error.response.status === 401) {
      alert('登录已过期，请重新登录');
    } else if (error.response && error.response.status === 403) {
      alert('无权限访问，请重新登录');
    } else {
      alert('获取积极分子数据失败');
    }
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

// 统计数据
const stats = computed(() => {
  const total = activists.value.length;
  const cultivating = activists.value.filter(a => a.status === '培养中').length;
  const transferred = activists.value.filter(a => a.status === '已转发展对象').length;
  const currentMonth = new Date().toISOString().slice(0, 7);
  const thisMonthNew = activists.value.filter(a => a.applyDate && a.applyDate.startsWith(currentMonth)).length;

  return [
    { label: '积极分子总数', value: total, icon: '👥' },
    { label: '培养中', value: cultivating, icon: '📚' },
    { label: '已转发展对象', value: transferred, icon: '✓' },
    { label: '本月新增', value: thisMonthNew, icon: '📈' }
  ];
});

// 模态框状态
const showModal = ref(false);
const showDetailModal = ref(false);
const showTrainingModal = ref(false);
const isEdit = ref(false);
const currentActivist = ref(null);
const formErrors = ref({});
const activeTab = ref('list');

// 筛选状态
const searchQuery = ref('');
const organizationFilter = ref('');
const statusFilter = ref('');
const genderFilter = ref('');

// 分页
const pageSize = 10;
const currentPage = ref(1);

// 表单数据
const formData = ref({
  name: '',
  gender: '男',
  ethnicity: '汉族',
  birthDate: '',
  education: '本科',
  applyDate: '',
  cultivateDate: '',
  organization: '',
  phone: '',
  cultivator: '',
  status: '培养中',
  studentId: '',
  grade: '',
  department: '',
  email: '',
  address: '',
  notes: '',
  trainingRecords: []
});

// 培养记录表单
const trainingFormData = ref({
  activity: '',
  date: '',
  content: '',
  evaluation: ''
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

// 状态列表
const statuses = ['培养中', '已转发展对象', '已取消'];

// 筛选后的积极分子
const filteredActivists = computed(() => {
  return activists.value.filter(a => {
    const matchSearch = !searchQuery.value ||
      a.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (a.studentId && a.studentId.includes(searchQuery.value)) ||
      a.phone.includes(searchQuery.value);
    const matchOrg = !organizationFilter.value || a.organization === organizationFilter.value;
    const matchStatus = !statusFilter.value || a.status === statusFilter.value;
    const matchGender = !genderFilter.value || a.gender === genderFilter.value;
    return matchSearch && matchOrg && matchStatus && matchGender;
  });
});

// 分页后的积极分子
const paginatedActivists = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredActivists.value.slice(start, end);
});

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredActivists.value.length / pageSize);
});

// 验证表单
function validateForm() {
  const errors = {};

  if (!formData.value.name) errors.name = '请输入姓名';
  if (!formData.value.gender) errors.gender = '请选择性别';
  if (!formData.value.ethnicity) errors.ethnicity = '请选择民族';
  if (!formData.value.birthDate) errors.birthDate = '请选择出生日期';
  if (!formData.value.education) errors.education = '请选择学历';
  if (!formData.value.applyDate) errors.applyDate = '请选择申请时间';
  if (!formData.value.cultivateDate) errors.cultivateDate = '请选择培养时间';
  if (!formData.value.organization) errors.organization = '请选择所属班级';
  if (!formData.value.phone) errors.phone = '请输入联系电话';
  if (!formData.value.cultivator) errors.cultivator = '请输入培养人';

  if (formData.value.phone && !/^1[3-9]\d{9}$/.test(formData.value.phone)) {
    errors.phone = '联系电话格式不正确';
  }

  if (formData.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    errors.email = '邮箱格式不正确';
  }

  if (formData.value.cultivateDate && formData.value.applyDate && formData.value.cultivateDate < formData.value.applyDate) {
    errors.cultivateDate = '培养时间不能早于申请时间';
  }

  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 验证培养记录表单
function validateTrainingForm() {
  const errors = {};
  if (!trainingFormData.value.activity) errors.activity = '请输入培养活动';
  if (!trainingFormData.value.date) errors.date = '请选择培养时间';
  if (!trainingFormData.value.content) errors.content = '请输入培养内容';
  if (!trainingFormData.value.evaluation) errors.evaluation = '请输入培养人评价';

  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 打开创建模态框
function openCreateModal() {
  isEdit.value = false;
  currentActivist.value = null;
  formData.value = {
    name: '',
    gender: '男',
    ethnicity: '汉族',
    birthDate: '',
    education: '本科',
    applyDate: '',
    cultivateDate: '',
    organization: '',
    phone: '',
    cultivator: '',
    status: '培养中',
    studentId: '',
    grade: '',
    department: '',
    email: '',
    address: '',
    notes: '',
    trainingRecords: []
  };
  formErrors.value = {};
  showModal.value = true;
}

// 打开编辑模态框
function openEditModal(activist) {
  isEdit.value = true;
  currentActivist.value = activist;
  formData.value = { ...activist, trainingRecords: [...(activist.trainingRecords || [])] };
  formErrors.value = {};
  showModal.value = true;
}

// 打开详情模态框
function openDetailModal(activist) {
  currentActivist.value = activist;
  showDetailModal.value = true;
}

// 打开培养记录模态框
function openTrainingModal(activist) {
  currentActivist.value = activist;
  trainingFormData.value = {
    activity: '',
    date: '',
    content: '',
    evaluation: ''
  };
  formErrors.value = {};
  showTrainingModal.value = true;
}

// 保存积极分子
async function saveActivist() {
  if (!validateForm()) return;

  const token = localStorage.getItem('token');
  const data = {
    name: formData.value.name,
    gender: formData.value.gender,
    ethnicity: formData.value.ethnicity,
    birth_date: formData.value.birthDate,
    education: formData.value.education,
    application_date: formData.value.applyDate,
    cultivation_date: formData.value.cultivateDate,
    organization: formData.value.organization,
    phone: formData.value.phone,
    cultivator: formData.value.cultivator,
    status: formData.value.status,
    student_id: formData.value.studentId,
    grade: formData.value.grade,
    department: formData.value.department,
    email: formData.value.email,
    address: formData.value.address,
    notes: formData.value.notes
  };

  try {
    if (isEdit.value) {
      await axios.put(`${API_URL}${currentActivist.value.id}/`, data, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } else {
      await axios.post(API_URL, data, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    }
    await fetchActivists();
    showModal.value = false;
  } catch (error) {
    console.error('保存积极分子失败:', error);
    alert('保存积极分子失败');
  }
}

// 删除积极分子
async function deleteActivist(activist) {
  if (confirm(`确定要删除入党积极分子「${activist.name}」吗？`)) {
    const token = localStorage.getItem('token');
    try {
      await axios.delete(`${API_URL}${activist.id}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      await fetchActivists();
    } catch (error) {
      console.error('删除积极分子失败:', error);
      alert('删除积极分子失败');
    }
  }
}

// 添加培养记录
function addTrainingRecord() {
  if (!validateTrainingForm()) return;

  const newRecord = {
    id: (currentActivist.value.trainingRecords?.length || 0) + 1,
    ...trainingFormData.value
  };

  if (!currentActivist.value.trainingRecords) {
    currentActivist.value.trainingRecords = [];
  }
  currentActivist.value.trainingRecords.push(newRecord);

  // 同步更新到主数据
  const index = activists.value.findIndex(a => a.id === currentActivist.value.id);
  if (index !== -1) {
    activists.value[index].trainingRecords = [...currentActivist.value.trainingRecords];
  }

  showTrainingModal.value = false;
}

// 删除培养记录
function deleteTrainingRecord(record) {
  if (confirm(`确定要删除该培养记录吗？`)) {
    const index = currentActivist.value.trainingRecords.findIndex(r => r.id === record.id);
    if (index !== -1) {
      currentActivist.value.trainingRecords.splice(index, 1);

      // 同步更新到主数据
      const activistIndex = activists.value.findIndex(a => a.id === currentActivist.value.id);
      if (activistIndex !== -1) {
        activists.value[activistIndex].trainingRecords = [...currentActivist.value.trainingRecords];
      }
    }
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
  showModal.value = false;
  showDetailModal.value = false;
  showTrainingModal.value = false;
  formErrors.value = {};
}

// Excel功能
function downloadTemplate() {
  const templateData = [
    excelHeaders,
    ['张三', '男', '汉族', '2002-05-15', '本科', '2024-09-01', '2024-10-01', '计算机学院党支部', '13912345678', '王老师', '培养中']
  ];

  const worksheet = XLSX.utils.aoa_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '入党积极分子');

  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 12 }, { wch: 12 }, { wch: 18 }, { wch: 13 }, { wch: 10 }, { wch: 12 }
  ];

  XLSX.writeFile(workbook, '入党积极分子导入模板.xlsx');
}

function exportData() {
  const exportData = filteredActivists.value.map(activist => ({
    '姓名': activist.name,
    '性别': activist.gender,
    '民族': activist.ethnicity,
    '出生日期': activist.birthDate,
    '学历': activist.education,
    '申请时间': activist.applyDate,
    '培养时间': activist.cultivateDate,
    '所属班级': activist.organization,
    '联系电话': activist.phone,
    '培养人': activist.cultivator,
    '状态': activist.status,
    '学号': activist.studentId || '-',
    '年级': activist.grade || '-',
    '学院': activist.department || '-',
    '邮箱': activist.email || '-',
    '地址': activist.address || '-',
    '备注': activist.notes || '-'
  }));

  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '入党积极分子');

  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 12 }, { wch: 12 }, { wch: 18 }, { wch: 13 }, { wch: 10 }, { wch: 12 }, { wch: 12 }, { wch: 10 }, { wch: 15 }, { wch: 18 }, { wch: 20 }, { wch: 20 }
  ];

  const fileName = `入党积极分子数据_${new Date().toISOString().split('T')[0]}.xlsx`;
  XLSX.writeFile(workbook, fileName);
}

async function handleUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
    alert('请上传Excel文件（.xlsx或.xls格式）');
    event.target.value = '';
    return;
  }

  const reader = new FileReader();
  reader.onload = async (e) => {
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
      const newActivists = [];
      const errors = [];

      for (let i = 1; i < jsonData.length; i++) {
        const rowData = jsonData[i];
        if (rowData.length === 0 || !rowData[0]) continue;

        try {
          const activist = {
            studentId: '',
            grade: '',
            department: '',
            email: '',
            address: '',
            notes: ''
          };

          headers.forEach((header, index) => {
            const fieldName = fieldMapping[header];
            if (fieldName && rowData[index] !== undefined && rowData[index] !== null) {
              activist[fieldName] = String(rowData[index]).trim();
            }
          });

          // 必填字段验证
          if (!activist.name || !activist.gender || !activist.applyDate || !activist.organization || !activist.phone) {
            errorCount++;
            errors.push(`第${i + 1}行：必填字段缺失`);
            continue;
          }

          // 手机号验证
          if (!/^1[3-9]\d{9}$/.test(activist.phone)) {
            errorCount++;
            errors.push(`第${i + 1}行：联系电话格式不正确`);
            continue;
          }

          newActivists.push(activist);
          successCount++;
        } catch (error) {
          errorCount++;
          errors.push(`第${i + 1}行：${error.message}`);
        }
      }

      // 批量保存到后端
      if (newActivists.length > 0) {
        const token = localStorage.getItem('token');
        const savePromises = newActivists.map(activist => {
          const data = {
            name: activist.name,
            gender: activist.gender,
            ethnicity: activist.ethnicity || '汉族',
            birth_date: activist.birthDate || '2000-01-01',
            education: activist.education || '本科',
            application_date: activist.applyDate,
            cultivation_date: activist.cultivateDate || activist.applyDate,
            organization: activist.organization,
            phone: activist.phone,
            cultivator: activist.cultivator || '',
            status: activist.status || '培养中',
            student_id: activist.studentId || '',
            grade: activist.grade || '',
            department: activist.department || '',
            email: activist.email || '',
            address: activist.address || '',
            notes: activist.notes || ''
          };
          return axios.post(API_URL, data, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
        });

        try {
          await Promise.all(savePromises);
          await fetchActivists();
        } catch (saveError) {
          console.error('保存数据失败:', saveError);
          errorCount += savePromises.length;
          successCount -= savePromises.length;
        }
      }

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

// 页面加载时获取数据
onMounted(() => {
  fetchActivists();
  loadDictionaryOptions();
});
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>入党积极分子管理</h1>
    </header>

    <!-- 标签切换 -->
    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">积极分子列表</button>
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

    <!-- 积极分子列表 -->
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
          <select v-model="statusFilter" class="filter-select">
            <option value="">全部状态</option>
            <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
          </select>
          <select v-model="genderFilter" class="filter-select">
            <option value="">全部性别</option>
            <option value="男">男</option>
            <option value="女">女</option>
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
          <button v-if="hasPermission('party:add')" class="btn btn-primary" @click="openCreateModal">新增积极分子</button>
        </div>
      </div>

      <!-- 积极分子列表表格 -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>
                <input type="checkbox" v-model="isAllSelected" @change="toggleSelectAll" />
              </th>
              <th>姓名</th>
              <th>性别</th>
              <th>民族</th>
              <th>学历</th>
              <th>申请时间</th>
              <th>培养时间</th>
              <th>所属班级</th>
              <th>培养人</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="activist in paginatedActivists" :key="activist.id">
              <td @click.stop>
                <input type="checkbox" :checked="selectedIds.includes(activist.id)" @change="toggleSelect(activist.id, $event)" />
              </td>
              <td>{{ activist.name }}</td>
              <td><span class="gender-tag">{{ activist.gender }}</span></td>
              <td>{{ activist.ethnicity }}</td>
              <td>{{ activist.education }}</td>
              <td>{{ activist.applyDate }}</td>
              <td>{{ activist.cultivateDate }}</td>
              <td><span class="org-tag">{{ activist.organization }}</span></td>
              <td>{{ activist.cultivator }}</td>
              <td><span class="status-tag" :class="activist.status.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '')">{{ activist.status }}</span></td>
              <td>
                <button class="action-btn view" @click="openDetailModal(activist)">查看</button>
                <button v-if="hasPermission('party:edit')" class="action-btn edit" @click="openEditModal(activist)">编辑</button>
                <button v-if="hasPermission('party:delete')" class="action-btn delete" @click="deleteActivist(activist)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 分页 -->
        <div v-if="filteredActivists.length > pageSize" class="pagination">
          <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">上一页</button>
          <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="page-btn" :disabled="currentPage === totalPages" @click="nextPage">下一页</button>
        </div>

        <div v-if="filteredActivists.length === 0" class="empty-state">
          <p>暂无入党积极分子数据</p>
        </div>
      </div>
    </div>

    <!-- 统计分析 -->
    <div v-if="activeTab === 'stats'" class="tab-content">
      <div class="stats-section">
        <h3 class="section-title">人员构成分析</h3>
        <div class="stats-row">
          <div class="mini-stat">
            <div class="mini-value">{{ activists.filter(a => a.gender === '男').length }}</div>
            <div class="mini-label">男性</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ activists.filter(a => a.gender === '女').length }}</div>
            <div class="mini-label">女性</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ activists.filter(a => a.status === '培养中').length }}</div>
            <div class="mini-label">培养中</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ activists.filter(a => a.status === '已转发展对象').length }}</div>
            <div class="mini-label">已转发展对象</div>
          </div>
        </div>
      </div>

      <div class="stats-section">
        <h3 class="section-title">学历分布</h3>
        <div class="stats-row">
          <div class="mini-stat" v-for="edu in educations" :key="edu">
            <div class="mini-value">{{ activists.filter(a => a.education === edu).length }}</div>
            <div class="mini-label">{{ edu }}</div>
          </div>
        </div>
      </div>

      <div class="stats-section">
        <h3 class="section-title">组织分布</h3>
        <div class="stats-row">
          <div class="mini-stat" v-for="org in organizations.slice(0, 4)" :key="org">
            <div class="mini-value">{{ activists.filter(a => a.organization === org).length }}</div>
            <div class="mini-label">{{ org.replace('党支部', '') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 积极分子信息模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑入党积极分子信息' : '新增入党积极分子信息' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>姓名 <span class="required">*</span></label>
              <input type="text" v-model="formData.name" class="form-input" placeholder="姓名" />
              <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
            </div>
            <div class="form-group">
              <label>性别 <span class="required">*</span></label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="formData.gender" value="男" /> 男
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="formData.gender" value="女" /> 女
                </label>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>民族 <span class="required">*</span></label>
              <select v-model="formData.ethnicity" class="form-select">
                <option v-for="eth in ethnicities" :key="eth" :value="eth">{{ eth }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>出生日期 <span class="required">*</span></label>
              <input type="date" v-model="formData.birthDate" class="form-input" />
              <span v-if="formErrors.birthDate" class="form-error">{{ formErrors.birthDate }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>学历 <span class="required">*</span></label>
              <select v-model="formData.education" class="form-select">
                <option v-for="edu in educations" :key="edu" :value="edu">{{ edu }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>所属班级 <span class="required">*</span></label>
              <input type="text" v-model="formData.organization" class="form-input" placeholder="请输入所属班级" />
              <span v-if="formErrors.organization" class="form-error">{{ formErrors.organization }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>申请时间 <span class="required">*</span></label>
              <input type="date" v-model="formData.applyDate" class="form-input" />
              <span v-if="formErrors.applyDate" class="form-error">{{ formErrors.applyDate }}</span>
            </div>
            <div class="form-group">
              <label>培养时间 <span class="required">*</span></label>
              <input type="date" v-model="formData.cultivateDate" class="form-input" />
              <span v-if="formErrors.cultivateDate" class="form-error">{{ formErrors.cultivateDate }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>联系电话 <span class="required">*</span></label>
              <input type="text" v-model="formData.phone" class="form-input" placeholder="手机号码" />
              <span v-if="formErrors.phone" class="form-error">{{ formErrors.phone }}</span>
            </div>
            <div class="form-group">
              <label>培养人 <span class="required">*</span></label>
              <input type="text" v-model="formData.cultivator" class="form-input" placeholder="培养人姓名" />
              <span v-if="formErrors.cultivator" class="form-error">{{ formErrors.cultivator }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>状态</label>
              <select v-model="formData.status" class="form-select">
                <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <input type="text" v-model="formData.email" class="form-input" placeholder="邮箱地址" />
              <span v-if="formErrors.email" class="form-error">{{ formErrors.email }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>学号</label>
              <input type="text" v-model="formData.studentId" class="form-input" placeholder="学号" />
            </div>
            <div class="form-group">
              <label>年级</label>
              <input type="text" v-model="formData.grade" class="form-input" placeholder="年级" />
            </div>
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="formData.notes" class="form-textarea" placeholder="备注信息"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveActivist">保存</button>
        </div>
      </div>
    </div>

    <!-- 积极分子详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal detail-modal" @click.stop>
        <div class="modal-header">
          <h2>入党积极分子详细信息</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentActivist">
          <div class="detail-section">
            <h3 class="section-title">基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">姓名：</span>{{ currentActivist.name }}</div>
              <div class="detail-item"><span class="label">性别：</span>{{ currentActivist.gender }}</div>
              <div class="detail-item"><span class="label">民族：</span>{{ currentActivist.ethnicity }}</div>
              <div class="detail-item"><span class="label">出生日期：</span>{{ currentActivist.birthDate }}</div>
              <div class="detail-item"><span class="label">学历：</span>{{ currentActivist.education }}</div>
              <div class="detail-item"><span class="label">状态：</span><span class="status-tag" :class="currentActivist.status.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '')">{{ currentActivist.status }}</span></div>
            </div>
          </div>

          <div class="detail-section">
            <h3 class="section-title">培养信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">申请时间：</span>{{ currentActivist.applyDate }}</div>
              <div class="detail-item"><span class="label">培养时间：</span>{{ currentActivist.cultivateDate }}</div>
              <div class="detail-item"><span class="label">所属班级：</span>{{ currentActivist.organization }}</div>
              <div class="detail-item"><span class="label">培养人：</span>{{ currentActivist.cultivator }}</div>
            </div>
          </div>

          <div class="detail-section">
            <h3 class="section-title">联系方式</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">联系电话：</span>{{ currentActivist.phone }}</div>
              <div class="detail-item"><span class="label">邮箱：</span>{{ currentActivist.email || '-' }}</div>
              <div class="detail-item"><span class="label">地址：</span>{{ currentActivist.address || '-' }}</div>
            </div>
          </div>

          <!-- 培养过程记录 -->
          <div class="detail-section">
            <div class="section-header">
              <h3 class="section-title">培养过程记录</h3>
              <button class="btn btn-primary btn-sm" @click="openTrainingModal(currentActivist)">添加记录</button>
            </div>
            <div v-if="currentActivist.trainingRecords && currentActivist.trainingRecords.length > 0" class="training-records">
              <div v-for="record in currentActivist.trainingRecords" :key="record.id" class="training-record-item">
                <div class="record-header">
                  <span class="record-activity">{{ record.activity }}</span>
                  <span class="record-date">{{ record.date }}</span>
                  <button v-if="hasPermission('party:edit')" class="action-btn delete" @click="deleteTrainingRecord(record)">删除</button>
                </div>
                <div class="record-content">
                  <p><strong>培养内容：</strong>{{ record.content }}</p>
                  <p><strong>培养人评价：</strong>{{ record.evaluation }}</p>
                </div>
              </div>
            </div>
            <div v-else class="empty-records">
              <p>暂无培养记录</p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button v-if="hasPermission('party:edit')" class="btn btn-primary" @click="openEditModal(currentActivist); closeModal()">编辑</button>
        </div>
      </div>
    </div>

    <!-- 添加培养记录模态框 -->
    <div v-if="showTrainingModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>添加培养记录</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>培养活动 <span class="required">*</span></label>
            <input type="text" v-model="trainingFormData.activity" class="form-input" placeholder="如：入党积极分子培训班、社会实践活动等" />
            <span v-if="formErrors.activity" class="form-error">{{ formErrors.activity }}</span>
          </div>
          <div class="form-group">
            <label>培养时间 <span class="required">*</span></label>
            <input type="date" v-model="trainingFormData.date" class="form-input" />
            <span v-if="formErrors.date" class="form-error">{{ formErrors.date }}</span>
          </div>
          <div class="form-group">
            <label>培养内容 <span class="required">*</span></label>
            <textarea v-model="trainingFormData.content" class="form-textarea" placeholder="详细描述培养活动内容"></textarea>
            <span v-if="formErrors.content" class="form-error">{{ formErrors.content }}</span>
          </div>
          <div class="form-group">
            <label>培养人评价 <span class="required">*</span></label>
            <textarea v-model="trainingFormData.evaluation" class="form-textarea" placeholder="培养人对该活动的评价"></textarea>
            <span v-if="formErrors.evaluation" class="form-error">{{ formErrors.evaluation }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="addTrainingRecord">保存</button>
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

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
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

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.培养中 {
  background: #e6f7ff;
  color: #1890ff;
}

.status-tag.已转发展对象 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.已取消 {
  background: #f5f5f5;
  color: #666;
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #667eea;
}

.section-header .section-title {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
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
  max-width: 800px;
}

.detail-modal {
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

.radio-group {
  display: flex;
  gap: 16px;
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

/* 培养记录样式 */
.training-records {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.training-record-item {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  border-left: 3px solid #667eea;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.record-activity {
  font-weight: 600;
  color: #333;
  font-size: 15px;
}

.record-date {
  color: #666;
  font-size: 13px;
}

.record-content {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.record-content p {
  margin: 8px 0;
}

.empty-records {
  text-align: center;
  padding: 32px;
  color: #999;
  background: #f9fafb;
  border-radius: 8px;
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

  .toolbar-left,
  .toolbar-right {
    flex-wrap: wrap;
  }
}
</style>