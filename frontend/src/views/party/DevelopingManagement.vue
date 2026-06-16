<script setup>
import { ref, computed, onMounted } from 'vue';
import * as XLSX from 'xlsx';
import axios from 'axios';
import { hasPermission } from '../../utils/permission';
import { getDictionaryNames } from '../../utils/dictionary';

// API配置
const API_URL = '/api/developing-members/';

// Excel表头映射
const excelHeaders = [
  '姓名', '性别', '民族', '出生日期', '学历', '确定时间', '所属党组织', '联系电话', '培养人', '状态'
];

// Excel数据字段映射
const fieldMapping = {
  '姓名': 'name',
  '性别': 'gender',
  '民族': 'ethnicity',
  '出生日期': 'birthDate',
  '学历': 'education',
  '确定时间': 'confirmDate',
  '所属党组织': 'organization',
  '联系电话': 'phone',
  '培养人': 'mentor',
  '状态': 'status'
};

// 发展对象数据
const members = ref([]);
const loading = ref(false);

// 批量选择相关
const selectedIds = ref([]);

// 是否全选
const isAllSelected = computed(() => {
  return paginatedMembers.value.length > 0 &&
    paginatedMembers.value.every(m => selectedIds.value.includes(m.id));
});

// 切换全选
function toggleSelectAll() {
  if (isAllSelected.value) {
    paginatedMembers.value.forEach(m => {
      const index = selectedIds.value.indexOf(m.id);
      if (index !== -1) {
        selectedIds.value.splice(index, 1);
      }
    });
  } else {
    paginatedMembers.value.forEach(m => {
      if (!selectedIds.value.includes(m.id)) {
        selectedIds.value.push(m.id);
      }
    });
  }
}

// 切换单个选择
function toggleSelect(memberId, event) {
  event.stopPropagation();
  const index = selectedIds.value.indexOf(memberId);
  if (index === -1) {
    selectedIds.value.push(memberId);
  } else {
    selectedIds.value.splice(index, 1);
  }
}

// 批量删除
async function deleteSelected() {
  if (selectedIds.value.length === 0) {
    alert('请先选择要删除的发展对象');
    return;
  }

  if (confirm(`确定要删除选中的 ${selectedIds.value.length} 条发展对象吗？`)) {
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
          members.value = members.value.filter(m => m.id !== id);
        }
      }

      selectedIds.value = [];
      alert(`成功删除 ${successCount} 条发展对象！`);
    } catch (error) {
      console.error('批量删除失败:', error);
      alert('批量删除失败，请重试');
    } finally {
      loading.value = false;
    }
  }
}

// 从API获取发展对象数据
async function fetchMembers() {
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
    members.value = data.map(item => ({
      id: item.id,
      name: item.name,
      gender: item.gender,
      ethnicity: item.ethnicity,
      birthDate: formatDate(item.birth_date),
      education: item.education,
      confirmDate: formatDate(item.determined_date),
      organization: item.organization,
      phone: item.phone,
      mentor: item.cultivator || '',
      status: item.status,
      studentId: item.student_id || '',
      grade: item.grade || '',
      department: item.department || '',
      email: item.email || '',
      address: item.address || '',
      notes: item.notes || '',
      inspectionRecords: item.inspection_records || []
    }));
  } catch (error) {
    console.error('获取发展对象数据失败:', error);
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
  fetchMembers();
  loadDictionaryOptions();
});

// 统计数据
const stats = computed(() => {
  const total = members.value.length;
  const inspecting = members.value.filter(m => m.status === '考察中').length;
  const converted = members.value.filter(m => m.status === '已转预备党员').length;
  const thisMonth = members.value.filter(m => {
    const confirmDate = new Date(m.confirmDate);
    const now = new Date();
    return confirmDate.getMonth() === now.getMonth() && confirmDate.getFullYear() === now.getFullYear();
  }).length;
  
  return [
    { label: '发展对象总数', value: total, icon: '👥' },
    { label: '考察中', value: inspecting, icon: '📋' },
    { label: '已转预备党员', value: converted, icon: '✓' },
    { label: '本月新增', value: thisMonth, icon: '📈' }
  ];
});

// 模态框状态
const showModal = ref(false);
const showDetailModal = ref(false);
const showInspectionModal = ref(false);
const isEdit = ref(false);
const currentMember = ref(null);
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
  confirmDate: '',
  organization: '',
  phone: '',
  mentor: '',
  status: '考察中',
  studentId: '',
  grade: '',
  department: '',
  email: '',
  address: '',
  notes: '',
  inspectionRecords: []
});

// 考察记录表单
const inspectionFormData = ref({
  date: '',
  content: '',
  inspector: '',
  conclusion: '合格'
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
const statuses = ['考察中', '已转预备党员'];

// 考察结论列表
const conclusions = ['合格', '基本合格', '不合格'];

// 筛选后的发展对象
const filteredMembers = computed(() => {
  return members.value.filter(m => {
    const matchSearch = !searchQuery.value || 
      m.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      m.studentId.includes(searchQuery.value) ||
      m.phone.includes(searchQuery.value);
    const matchOrg = !organizationFilter.value || m.organization === organizationFilter.value;
    const matchStatus = !statusFilter.value || m.status === statusFilter.value;
    const matchGender = !genderFilter.value || m.gender === genderFilter.value;
    return matchSearch && matchOrg && matchStatus && matchGender;
  });
});

// 分页后的发展对象
const paginatedMembers = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredMembers.value.slice(start, end);
});

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredMembers.value.length / pageSize);
});

// 验证表单
function validateForm() {
  const errors = {};
  
  if (!formData.value.name) errors.name = '请输入姓名';
  if (!formData.value.gender) errors.gender = '请选择性别';
  if (!formData.value.ethnicity) errors.ethnicity = '请选择民族';
  if (!formData.value.birthDate) errors.birthDate = '请选择出生日期';
  if (!formData.value.education) errors.education = '请选择学历';
  if (!formData.value.confirmDate) errors.confirmDate = '请选择确定时间';
  if (!formData.value.organization) errors.organization = '请选择所属党组织';
  if (!formData.value.phone) errors.phone = '请输入联系电话';
  if (!formData.value.mentor) errors.mentor = '请输入培养人';
  
  if (formData.value.phone && !/^1[3-9]\d{9}$/.test(formData.value.phone)) {
    errors.phone = '联系电话格式不正确';
  }
  
  if (formData.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    errors.email = '邮箱格式不正确';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 验证考察记录表单
function validateInspectionForm() {
  const errors = {};
  
  if (!inspectionFormData.value.date) errors.date = '请选择考察时间';
  if (!inspectionFormData.value.content) errors.content = '请输入考察内容';
  if (!inspectionFormData.value.inspector) errors.inspector = '请输入考察人';
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 打开创建模态框
function openCreateModal() {
  isEdit.value = false;
  currentMember.value = null;
  formData.value = {
    name: '',
    gender: '男',
    ethnicity: '汉族',
    birthDate: '',
    education: '本科',
    confirmDate: '',
    organization: '',
    phone: '',
    mentor: '',
    status: '考察中',
    studentId: '',
    grade: '',
    department: '',
    email: '',
    address: '',
    notes: '',
    inspectionRecords: []
  };
  formErrors.value = {};
  showModal.value = true;
}

// 打开编辑模态框
function openEditModal(member) {
  isEdit.value = true;
  currentMember.value = member;
  formData.value = { ...member, inspectionRecords: [...(member.inspectionRecords || [])] };
  formErrors.value = {};
  showModal.value = true;
}

// 打开详情模态框
function openDetailModal(member) {
  currentMember.value = member;
  showDetailModal.value = true;
}

// 打开考察记录模态框
function openInspectionModal(member) {
  currentMember.value = member;
  inspectionFormData.value = {
    date: '',
    content: '',
    inspector: '',
    conclusion: '合格'
  };
  formErrors.value = {};
  showInspectionModal.value = true;
}

// 保存发展对象
async function saveMember() {
  if (!validateForm()) return;
  
  const token = localStorage.getItem('token');
  if (!token) {
    alert('未登录或token已过期');
    return;
  }
  
  // 转换日期格式为API需要的格式
  const apiData = {
    name: formData.value.name,
    gender: formData.value.gender,
    ethnicity: formData.value.ethnicity,
    birth_date: formData.value.birthDate,
    education: formData.value.education,
    determined_date: formData.value.confirmDate,
    organization: formData.value.organization,
    phone: formData.value.phone,
    cultivator: formData.value.mentor,
    status: formData.value.status,
    student_id: formData.value.studentId || '',
    grade: formData.value.grade || '',
    department: formData.value.department || '',
    email: formData.value.email || '',
    address: formData.value.address || '',
    notes: formData.value.notes || ''
  };
  
  try {
    let response;
    if (isEdit.value) {
      // 编辑 - PUT请求
      response = await axios.put(`${API_URL}${currentMember.value.id}/`, apiData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } else {
      // 新增 - POST请求
      response = await axios.post(API_URL, apiData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    }
    
    if (response.status === 200 || response.status === 201) {
      showModal.value = false;
      fetchMembers(); // 刷新数据
      alert(isEdit.value ? '修改成功！' : '添加成功！');
    }
  } catch (error) {
    console.error('保存失败:', error);
    alert('保存失败：' + (error.response?.data?.detail || error.message));
  }
}

// 删除发展对象
async function deleteMember(member) {
  if (!confirm(`确定要删除发展对象「${member.name}」吗？`)) return;
  
  const token = localStorage.getItem('token');
  if (!token) {
    alert('未登录或token已过期');
    return;
  }
  
  try {
    const response = await axios.delete(`${API_URL}${member.id}/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.status === 204 || response.status === 200) {
      fetchMembers(); // 刷新数据
      alert('删除成功！');
    }
  } catch (error) {
    console.error('删除失败:', error);
    alert('删除失败：' + (error.response?.data?.detail || error.message));
  }
}

// 添加考察记录
async function addInspectionRecord() {
  if (!validateInspectionForm()) return;
  
  const token = localStorage.getItem('token');
  if (!token) {
    alert('未登录或token已过期');
    return;
  }
  
  const apiData = {
    developing_member: currentMember.value.id,
    inspection_date: inspectionFormData.value.date,
    content: inspectionFormData.value.content,
    inspector: inspectionFormData.value.inspector,
    conclusion: inspectionFormData.value.conclusion
  };
  
  try {
    const response = await axios.post('/api/inspection-records/', apiData, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.status === 201) {
      showInspectionModal.value = false;
      fetchMembers(); // 刷新数据
      alert('考察记录添加成功！');
    }
  } catch (error) {
    console.error('添加考察记录失败:', error);
    alert('添加失败：' + (error.response?.data?.detail || error.message));
  }
}

// 删除考察记录
async function deleteInspectionRecord(member, recordId) {
  if (!confirm('确定要删除这条考察记录吗？')) return;
  
  const token = localStorage.getItem('token');
  if (!token) {
    alert('未登录或token已过期');
    return;
  }
  
  try {
    const response = await axios.delete(`/api/inspection-records/${recordId}/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.status === 204 || response.status === 200) {
      fetchMembers(); // 刷新数据
      alert('删除成功！');
    }
  } catch (error) {
    console.error('删除考察记录失败:', error);
    alert('删除失败：' + (error.response?.data?.detail || error.message));
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
  showInspectionModal.value = false;
  formErrors.value = {};
}

// Excel功能
function downloadTemplate() {
  const templateData = [
    excelHeaders,
    ['张明', '男', '汉族', '2001-05-15', '本科', '2024-03-01', '计算机学院党支部', '13912345678', '王老师', '考察中']
  ];
  
  const worksheet = XLSX.utils.aoa_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '发展对象信息');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 12 }, { wch: 18 }, { wch: 13 }, { wch: 15 }, { wch: 12 }
  ];
  
  XLSX.writeFile(workbook, '发展对象信息导入模板.xlsx');
}

function exportData() {
  const exportData = filteredMembers.value.map(member => ({
    '姓名': member.name,
    '性别': member.gender,
    '民族': member.ethnicity,
    '出生日期': member.birthDate,
    '学历': member.education,
    '确定时间': member.confirmDate,
    '所属党组织': member.organization,
    '联系电话': member.phone,
    '培养人': member.mentor,
    '状态': member.status,
    '学号': member.studentId || '-',
    '年级': member.grade || '-',
    '学院': member.department || '-',
    '邮箱': member.email || '-',
    '地址': member.address || '-',
    '备注': member.notes || '-',
    '考察记录数': member.inspectionRecords?.length || 0
  }));
  
  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '发展对象信息');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 12 }, { wch: 18 }, { wch: 13 }, { wch: 15 }, { wch: 12 }, { wch: 12 }, { wch: 10 }, { wch: 15 }, { wch: 18 }, { wch: 20 }, { wch: 20 }, { wch: 12 }
  ];
  
  const fileName = `发展对象信息数据_${new Date().toISOString().split('T')[0]}.xlsx`;
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
      const newMembers = [];
      const errors = [];
      
      for (let i = 1; i < jsonData.length; i++) {
        const rowData = jsonData[i];
        if (rowData.length === 0 || !rowData[0]) continue;
        
        try {
          const member = {
            id: members.value.length + newMembers.length + 1,
            studentId: '',
            grade: '',
            department: '',
            email: '',
            address: '',
            notes: '',
            inspectionRecords: []
          };
          
          headers.forEach((header, index) => {
            const fieldName = fieldMapping[header];
            if (fieldName && rowData[index] !== undefined && rowData[index] !== null) {
              member[fieldName] = String(rowData[index]).trim();
            }
          });
          
          // 必填字段验证
          if (!member.name || !member.gender || !member.confirmDate || !member.organization || !member.phone) {
            errorCount++;
            errors.push(`第${i + 1}行：必填字段缺失`);
            continue;
          }
          
          // 手机号验证
          if (!/^1[3-9]\d{9}$/.test(member.phone)) {
            errorCount++;
            errors.push(`第${i + 1}行：联系电话格式不正确`);
            continue;
          }
          
          newMembers.push(member);
          successCount++;
        } catch (error) {
          errorCount++;
          errors.push(`第${i + 1}行：${error.message}`);
        }
      }
      
      newMembers.forEach(member => members.value.unshift(member));
      
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
      <h1>发展对象管理</h1>
    </header>
    
    <!-- 标签切换 -->
    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">发展对象列表</button>
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
    
    <!-- 发展对象列表 -->
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
          <button v-if="hasPermission('party:add')" class="btn btn-primary" @click="openCreateModal">新增发展对象</button>
        </div>
      </div>
      
      <!-- 发展对象列表表格 -->
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
              <th>确定时间</th>
              <th>所属党组织</th>
              <th>培养人</th>
              <th>联系电话</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in paginatedMembers" :key="member.id">
              <td @click.stop>
                <input type="checkbox" :checked="selectedIds.includes(member.id)" @change="toggleSelect(member.id, $event)" />
              </td>
              <td>{{ member.name }}</td>
              <td><span class="gender-tag">{{ member.gender }}</span></td>
              <td>{{ member.ethnicity }}</td>
              <td>{{ member.education }}</td>
              <td>{{ member.confirmDate }}</td>
              <td><span class="org-tag">{{ member.organization }}</span></td>
              <td>{{ member.mentor }}</td>
              <td>{{ member.phone }}</td>
              <td><span class="status-tag" :class="member.status === '考察中' ? 'inspecting' : 'converted'">{{ member.status }}</span></td>
              <td>
                <button class="action-btn view" @click="openDetailModal(member)">查看</button>
                <button v-if="hasPermission('party:edit')" class="action-btn edit" @click="openEditModal(member)">编辑</button>
                <button v-if="hasPermission('party:delete')" class="action-btn delete" @click="deleteMember(member)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <!-- 分页 -->
        <div v-if="filteredMembers.length > pageSize" class="pagination">
          <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">上一页</button>
          <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="page-btn" :disabled="currentPage === totalPages" @click="nextPage">下一页</button>
        </div>
        
        <div v-if="filteredMembers.length === 0" class="empty-state">
          <p>暂无发展对象数据</p>
        </div>
      </div>
    </div>
    
    <!-- 统计分析 -->
    <div v-if="activeTab === 'stats'" class="tab-content">
      <div class="stats-section">
        <h3 class="section-title">发展对象构成分析</h3>
        <div class="stats-row">
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.gender === '男').length }}</div>
            <div class="mini-label">男性</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.gender === '女').length }}</div>
            <div class="mini-label">女性</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.status === '考察中').length }}</div>
            <div class="mini-label">考察中</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.status === '已转预备党员').length }}</div>
            <div class="mini-label">已转预备党员</div>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <h3 class="section-title">学历分布</h3>
        <div class="stats-row">
          <div class="mini-stat" v-for="edu in educations" :key="edu">
            <div class="mini-value">{{ members.filter(m => m.education === edu).length }}</div>
            <div class="mini-label">{{ edu }}</div>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <h3 class="section-title">组织分布</h3>
        <div class="stats-row">
          <div class="mini-stat" v-for="org in organizations.slice(0, 4)" :key="org">
            <div class="mini-value">{{ members.filter(m => m.organization === org).length }}</div>
            <div class="mini-label">{{ org.replace('党支部', '') }}</div>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <h3 class="section-title">考察记录统计</h3>
        <div class="stats-row">
          <div class="mini-stat">
            <div class="mini-value">{{ members.reduce((sum, m) => sum + (m.inspectionRecords?.length || 0), 0) }}</div>
            <div class="mini-label">总考察记录</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => !m.inspectionRecords || m.inspectionRecords.length === 0).length }}</div>
            <div class="mini-label">无考察记录</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.inspectionRecords && m.inspectionRecords.length >= 2).length }}</div>
            <div class="mini-label">考察记录≥2次</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.inspectionRecords && m.inspectionRecords.length >= 4).length }}</div>
            <div class="mini-label">考察记录≥4次</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 发展对象信息模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑发展对象信息' : '新增发展对象信息' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>姓名 <span class="required">*</span></label>
              <input type="text" v-model="formData.name" class="form-input" placeholder="发展对象姓名" />
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
              <label>确定时间 <span class="required">*</span></label>
              <input type="date" v-model="formData.confirmDate" class="form-input" />
              <span v-if="formErrors.confirmDate" class="form-error">{{ formErrors.confirmDate }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>所属党组织 <span class="required">*</span></label>
              <select v-model="formData.organization" class="form-select">
                <option v-for="org in organizations" :key="org" :value="org">{{ org }}</option>
              </select>
              <span v-if="formErrors.organization" class="form-error">{{ formErrors.organization }}</span>
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model="formData.status" class="form-select">
                <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
              </select>
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
              <input type="text" v-model="formData.mentor" class="form-input" placeholder="培养人姓名（多人用顿号分隔）" />
              <span v-if="formErrors.mentor" class="form-error">{{ formErrors.mentor }}</span>
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
          <div class="form-row">
            <div class="form-group">
              <label>邮箱</label>
              <input type="text" v-model="formData.email" class="form-input" placeholder="邮箱地址" />
              <span v-if="formErrors.email" class="form-error">{{ formErrors.email }}</span>
            </div>
            <div class="form-group">
              <label>地址</label>
              <input type="text" v-model="formData.address" class="form-input" placeholder="地址" />
            </div>
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="formData.notes" class="form-textarea" placeholder="备注信息"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveMember">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 发展对象详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>发展对象详细信息</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentMember">
          <div class="detail-section">
            <h3 class="section-title">基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">姓名：</span>{{ currentMember.name }}</div>
              <div class="detail-item"><span class="label">性别：</span>{{ currentMember.gender }}</div>
              <div class="detail-item"><span class="label">民族：</span>{{ currentMember.ethnicity }}</div>
              <div class="detail-item"><span class="label">出生日期：</span>{{ currentMember.birthDate }}</div>
              <div class="detail-item"><span class="label">学历：</span>{{ currentMember.education }}</div>
              <div class="detail-item"><span class="label">状态：</span><span class="status-tag" :class="currentMember.status === '考察中' ? 'inspecting' : 'converted'">{{ currentMember.status }}</span></div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">党务信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">确定时间：</span>{{ currentMember.confirmDate }}</div>
              <div class="detail-item"><span class="label">所属党组织：</span>{{ currentMember.organization }}</div>
              <div class="detail-item"><span class="label">培养人：</span>{{ currentMember.mentor }}</div>
              <div class="detail-item"><span class="label">学号：</span>{{ currentMember.studentId || '-' }}</div>
              <div class="detail-item"><span class="label">年级：</span>{{ currentMember.grade || '-' }}</div>
              <div class="detail-item"><span class="label">学院：</span>{{ currentMember.department || '-' }}</div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">联系方式</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">联系电话：</span>{{ currentMember.phone }}</div>
              <div class="detail-item"><span class="label">邮箱：</span>{{ currentMember.email || '-' }}</div>
              <div class="detail-item"><span class="label">地址：</span>{{ currentMember.address || '-' }}</div>
            </div>
          </div>
          
          <div class="detail-section">
            <div class="section-header">
              <h3 class="section-title">考察记录</h3>
              <button class="btn btn-primary btn-sm" @click="openInspectionModal(currentMember)">添加考察记录</button>
            </div>
            <div v-if="currentMember.inspectionRecords && currentMember.inspectionRecords.length > 0" class="inspection-list">
              <div v-for="record in currentMember.inspectionRecords" :key="record.id" class="inspection-item">
                <div class="inspection-header">
                  <span class="inspection-date">{{ record.date }}</span>
                  <span class="inspection-conclusion" :class="record.conclusion">{{ record.conclusion }}</span>
                  <button v-if="hasPermission('party:edit')" class="delete-record-btn" @click="deleteInspectionRecord(currentMember, record.id)">删除</button>
                </div>
                <div class="inspection-content">{{ record.content }}</div>
                <div class="inspection-footer">考察人：{{ record.inspector }}</div>
              </div>
            </div>
            <div v-else class="empty-inspection">
              <p>暂无考察记录</p>
            </div>
          </div>
          
          <div v-if="currentMember.notes" class="detail-section">
            <h3 class="section-title">备注</h3>
            <div class="detail-notes">{{ currentMember.notes }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button v-if="hasPermission('party:edit')" class="btn btn-primary" @click="openEditModal(currentMember); closeModal()">编辑</button>
        </div>
      </div>
    </div>
    
    <!-- 添加考察记录模态框 -->
    <div v-if="showInspectionModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>添加考察记录</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>考察时间 <span class="required">*</span></label>
            <input type="date" v-model="inspectionFormData.date" class="form-input" />
            <span v-if="formErrors.date" class="form-error">{{ formErrors.date }}</span>
          </div>
          <div class="form-group">
            <label>考察内容 <span class="required">*</span></label>
            <textarea v-model="inspectionFormData.content" class="form-textarea" placeholder="请输入考察内容"></textarea>
            <span v-if="formErrors.content" class="form-error">{{ formErrors.content }}</span>
          </div>
          <div class="form-group">
            <label>考察人 <span class="required">*</span></label>
            <input type="text" v-model="inspectionFormData.inspector" class="form-input" placeholder="考察人姓名" />
            <span v-if="formErrors.inspector" class="form-error">{{ formErrors.inspector }}</span>
          </div>
          <div class="form-group">
            <label>考察结论</label>
            <select v-model="inspectionFormData.conclusion" class="form-select">
              <option v-for="conclusion in conclusions" :key="conclusion" :value="conclusion">{{ conclusion }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="addInspectionRecord">保存</button>
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

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
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

.status-tag.inspecting {
  background: #e6f7ff;
  color: #1890ff;
}

.status-tag.converted {
  background: #f6ffed;
  color: #52c41a;
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
  border-bottom: none;
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

.detail-notes {
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 6px;
  color: #333;
}

/* 考察记录样式 */
.inspection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.inspection-item {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.inspection-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.inspection-date {
  font-weight: 600;
  color: #333;
}

.inspection-conclusion {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.inspection-conclusion.合格 {
  background: #f6ffed;
  color: #52c41a;
}

.inspection-conclusion.基本合格 {
  background: #fff7e6;
  color: #fa8c16;
}

.inspection-conclusion.不合格 {
  background: #fff1f0;
  color: #f5222d;
}

.delete-record-btn {
  margin-left: auto;
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: #fff1f0;
  color: #f5222d;
  font-size: 12px;
  cursor: pointer;
}

.inspection-content {
  color: #333;
  margin-bottom: 8px;
  line-height: 1.6;
}

.inspection-footer {
  font-size: 12px;
  color: #999;
}

.empty-inspection {
  padding: 24px;
  text-align: center;
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