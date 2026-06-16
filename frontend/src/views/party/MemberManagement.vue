<script setup>
import { ref, computed, onMounted } from 'vue';
import * as XLSX from 'xlsx';
import axios from 'axios';
import { hasPermission } from '../../utils/permission';
import { getDictionaryNames } from '../../utils/dictionary';

// API配置
const API_URL = '/api/party-members/';

// Excel表头映射
const excelHeaders = [
  '姓名', '性别', '民族', '出生日期', '学历', '入党时间', '转正时间', 
  '所属党组织', '联系电话', '入党介绍人', '党员状态'
];

// Excel数据字段映射
const fieldMapping = {
  '姓名': 'name',
  '性别': 'gender',
  '民族': 'ethnicity',
  '出生日期': 'birthDate',
  '学历': 'education',
  '入党时间': 'joinDate',
  '转正时间': 'regularDate',
  '所属党组织': 'organization',
  '联系电话': 'phone',
  '入党介绍人': 'introducer',
  '党员状态': 'status'
};

// 党员数据
const members = ref([]);
const loading = ref(false);

// 统计数据
const stats = computed(() => {
  const total = members.value.length;
  const regular = members.value.filter(m => m.regularDate).length;
  const probationary = members.value.filter(m => !m.regularDate).length;
  const active = members.value.filter(m => m.status === '正常').length;
  
  return [
    { label: '党员总数', value: total, icon: '👥' },
    { label: '正式党员', value: regular, icon: '✓' },
    { label: '预备党员', value: probationary, icon: '⏳' },
    { label: '正常状态', value: active, icon: '✅' }
  ];
});

// 模态框状态
const showModal = ref(false);
const showDetailModal = ref(false);
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
  joinDate: '',
  regularDate: '',
  organization: '',
  phone: '',
  introducer: '',
  status: '正常',
  studentId: '',
  grade: '',
  department: '',
  email: '',
  address: '',
  notes: ''
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
const statuses = ['正常', '暂停', '转出'];

// 筛选后的党员
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

// 分页后的党员
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
  if (!formData.value.joinDate) errors.joinDate = '请选择入党时间';
  if (!formData.value.organization) errors.organization = '请选择所属党组织';
  if (!formData.value.phone) errors.phone = '请输入联系电话';
  if (!formData.value.introducer) errors.introducer = '请输入入党介绍人';
  
  if (formData.value.phone && !/^1[3-9]\d{9}$/.test(formData.value.phone)) {
    errors.phone = '联系电话格式不正确';
  }
  
  if (formData.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    errors.email = '邮箱格式不正确';
  }
  
  if (formData.value.regularDate && formData.value.joinDate && formData.value.regularDate < formData.value.joinDate) {
    errors.regularDate = '转正时间不能早于入党时间';
  }
  
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
    joinDate: '',
    regularDate: '',
    organization: '',
    phone: '',
    introducer: '',
    status: '正常',
    studentId: '',
    grade: '',
    department: '',
    email: '',
    address: '',
    notes: ''
  };
  formErrors.value = {};
  showModal.value = true;
}

// 打开编辑模态框
function openEditModal(member) {
  isEdit.value = true;
  currentMember.value = member;
  formData.value = { ...member };
  formErrors.value = {};
  showModal.value = true;
}

// 打开详情模态框
function openDetailModal(member) {
  currentMember.value = member;
  showDetailModal.value = true;
}

// 获取党员数据
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
    // 后端返回分页数据，需要从 results 中获取
    const data = response.data.results || response.data;
    members.value = data.map(item => ({
      id: item.id,
      name: item.name,
      gender: item.gender,
      ethnicity: item.ethnicity,
      birthDate: formatDate(item.birth_date),
      education: item.education,
      joinDate: formatDate(item.join_date),
      regularDate: formatDate(item.regular_date),
      organization: item.organization,
      phone: item.phone,
      introducer: item.introducer,
      status: item.status,
      studentId: item.student_id || '',
      grade: item.grade || '',
      department: item.department || '',
      email: item.email || '',
      address: item.address || '',
      notes: item.notes || ''
    }));
  } catch (error) {
    console.error('获取党员数据失败:', error);
  } finally {
    loading.value = false;
  }
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  return date.toISOString().split('T')[0];
}

// 保存党员
async function saveMember() {
  if (!validateForm()) return;
  
  const token = localStorage.getItem('token');
  const data = {
    name: formData.value.name,
    gender: formData.value.gender,
    ethnicity: formData.value.ethnicity,
    birth_date: formData.value.birthDate,
    education: formData.value.education,
    join_date: formData.value.joinDate,
    regular_date: formData.value.regularDate || null,
    organization: formData.value.organization,
    phone: formData.value.phone,
    introducer: formData.value.introducer,
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
      await axios.put(`${API_URL}${currentMember.value.id}/`, data, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } else {
      await axios.post(API_URL, data, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    }
    await fetchMembers();
    showModal.value = false;
  } catch (error) {
    console.error('保存党员失败:', error);
    alert('保存党员失败');
  }
}

// 删除党员
async function deleteMember(member) {
  if (confirm(`确定要删除党员「${member.name}」吗？`)) {
    const token = localStorage.getItem('token');
    try {
      await axios.delete(`${API_URL}${member.id}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      await fetchMembers();
    } catch (error) {
      console.error('删除党员失败:', error);
      alert('删除党员失败');
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
  formErrors.value = {};
}

// Excel功能
function downloadTemplate() {
  const templateData = [
    excelHeaders,
    ['张三', '男', '汉族', '1990-05-15', '本科', '2023-07-01', '2024-07-01', '计算机学院党支部', '13912345678', '王老师', '正常']
  ];
  
  const worksheet = XLSX.utils.aoa_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '党员信息');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 12 }, { wch: 12 }, { wch: 18 }, { wch: 13 }, { wch: 10 }, { wch: 8 }
  ];
  
  XLSX.writeFile(workbook, '党员信息导入模板.xlsx');
}

function exportData() {
  const exportData = filteredMembers.value.map(member => ({
    '姓名': member.name,
    '性别': member.gender,
    '民族': member.ethnicity,
    '出生日期': member.birthDate,
    '学历': member.education,
    '入党时间': member.joinDate,
    '转正时间': member.regularDate || '预备党员',
    '所属党组织': member.organization,
    '联系电话': member.phone,
    '入党介绍人': member.introducer,
    '党员状态': member.status,
    '学号': member.studentId || '-',
    '年级': member.grade || '-',
    '学院': member.department || '-',
    '邮箱': member.email || '-',
    '地址': member.address || '-',
    '备注': member.notes || '-'
  }));
  
  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '党员信息');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 12 }, { wch: 12 }, { wch: 18 }, { wch: 13 }, { wch: 10 }, { wch: 8 }, { wch: 12 }, { wch: 10 }, { wch: 15 }, { wch: 18 }, { wch: 20 }, { wch: 20 }
  ];
  
  const fileName = `党员信息数据_${new Date().toISOString().split('T')[0]}.xlsx`;
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
            notes: ''
          };
          
          headers.forEach((header, index) => {
            const fieldName = fieldMapping[header];
            if (fieldName && rowData[index] !== undefined && rowData[index] !== null) {
              member[fieldName] = String(rowData[index]).trim();
            }
          });
          
          // 必填字段验证
          if (!member.name || !member.gender || !member.joinDate || !member.organization || !member.phone) {
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
      
      // 批量保存到后端
      if (newMembers.length > 0) {
        const token = localStorage.getItem('token');
        const savePromises = newMembers.map(member => {
          const data = {
            name: member.name,
            gender: member.gender,
            ethnicity: member.ethnicity || '汉族',
            birth_date: member.birthDate || '1990-01-01',
            education: member.education || '本科',
            join_date: member.joinDate,
            regular_date: member.regularDate || null,
            organization: member.organization,
            phone: member.phone,
            introducer: member.introducer || '',
            status: member.status || '正常',
            student_id: member.studentId || '',
            grade: member.grade || '',
            department: member.department || '',
            email: member.email || '',
            address: member.address || '',
            notes: member.notes || ''
          };
          return axios.post(API_URL, data, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
        });
        
        try {
          await Promise.all(savePromises);
          await fetchMembers();
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
  fetchMembers();
  loadDictionaryOptions();
});
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>党员信息管理</h1>
    </header>
    
    <!-- 标签切换 -->
    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">党员列表</button>
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
    
    <!-- 党员列表 -->
    <div v-if="activeTab === 'list'" class="tab-content">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
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
          <button v-if="hasPermission('party:edit')" class="btn btn-secondary" @click="downloadTemplate">下载模板</button>
          <label v-if="hasPermission('party:edit')" class="btn btn-secondary file-upload-label">
            <input type="file" accept=".xlsx,.xls" style="display: none" @change="handleUpload" />
            导入数据
          </label>
          <button v-if="hasPermission('party:edit')" class="btn btn-secondary" @click="exportData">导出数据</button>
          <button v-if="hasPermission('party:add')" class="btn btn-primary" @click="openCreateModal">新增党员</button>
        </div>
      </div>
      
      <!-- 党员列表表格 -->
      <div class="table-container">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <span>正在加载党员数据...</span>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th>性别</th>
              <th>民族</th>
              <th>学历</th>
              <th>入党时间</th>
              <th>转正时间</th>
              <th>所属党组织</th>
              <th>联系电话</th>
              <th>党员状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in paginatedMembers" :key="member.id">
              <td>{{ member.name }}</td>
              <td><span class="gender-tag">{{ member.gender }}</span></td>
              <td>{{ member.ethnicity }}</td>
              <td>{{ member.education }}</td>
              <td>{{ member.joinDate }}</td>
              <td>{{ member.regularDate || '预备党员' }}</td>
              <td><span class="org-tag">{{ member.organization }}</span></td>
              <td>{{ member.phone }}</td>
              <td><span class="status-tag" :class="member.status">{{ member.status }}</span></td>
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
          <p>暂无党员数据</p>
        </div>
      </div>
    </div>
    
    <!-- 统计分析 -->
    <div v-if="activeTab === 'stats'" class="tab-content">
      <div class="stats-section">
        <h3 class="section-title">党员构成分析</h3>
        <div class="stats-row">
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.gender === '男').length }}</div>
            <div class="mini-label">男性党员</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.gender === '女').length }}</div>
            <div class="mini-label">女性党员</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => m.regularDate).length }}</div>
            <div class="mini-label">正式党员</div>
          </div>
          <div class="mini-stat">
            <div class="mini-value">{{ members.filter(m => !m.regularDate).length }}</div>
            <div class="mini-label">预备党员</div>
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
    </div>
    
    <!-- 党员信息模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑党员信息' : '新增党员信息' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>姓名 <span class="required">*</span></label>
              <input type="text" v-model="formData.name" class="form-input" placeholder="党员姓名" />
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
              <label>所属党组织 <span class="required">*</span></label>
              <select v-model="formData.organization" class="form-select">
                <option v-for="org in organizations" :key="org" :value="org">{{ org }}</option>
              </select>
              <span v-if="formErrors.organization" class="form-error">{{ formErrors.organization }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>入党时间 <span class="required">*</span></label>
              <input type="date" v-model="formData.joinDate" class="form-input" />
              <span v-if="formErrors.joinDate" class="form-error">{{ formErrors.joinDate }}</span>
            </div>
            <div class="form-group">
              <label>转正时间</label>
              <input type="date" v-model="formData.regularDate" class="form-input" />
              <span v-if="formErrors.regularDate" class="form-error">{{ formErrors.regularDate }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>联系电话 <span class="required">*</span></label>
              <input type="text" v-model="formData.phone" class="form-input" placeholder="手机号码" />
              <span v-if="formErrors.phone" class="form-error">{{ formErrors.phone }}</span>
            </div>
            <div class="form-group">
              <label>入党介绍人 <span class="required">*</span></label>
              <input type="text" v-model="formData.introducer" class="form-input" placeholder="入党介绍人姓名" />
              <span v-if="formErrors.introducer" class="form-error">{{ formErrors.introducer }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>党员状态</label>
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
          <button class="btn btn-primary" @click="saveMember">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 党员详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>党员详细信息</h2>
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
              <div class="detail-item"><span class="label">党员状态：</span><span class="status-tag" :class="currentMember.status">{{ currentMember.status }}</span></div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">党务信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">入党时间：</span>{{ currentMember.joinDate }}</div>
              <div class="detail-item"><span class="label">转正时间：</span>{{ currentMember.regularDate || '预备党员' }}</div>
              <div class="detail-item"><span class="label">所属党组织：</span>{{ currentMember.organization }}</div>
              <div class="detail-item"><span class="label">入党介绍人：</span>{{ currentMember.introducer }}</div>
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
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button v-if="hasPermission('party:edit')" class="btn btn-primary" @click="openEditModal(currentMember); closeModal()">编辑</button>
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

.status-tag.正常 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.暂停 {
  background: #fff7e6;
  color: #fa8c16;
}

.status-tag.转出 {
  background: #e6f7ff;
  color: #1890ff;
}

.status-tag.去世 {
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
}
</style>