<script setup>
import { ref, computed, onMounted } from 'vue';
import * as XLSX from 'xlsx';
import { hasPermission } from '../../utils/permission';
import { getDictionaryNames } from '../../utils/dictionary';

// Excel表头映射
const excelHeaders = [
  '学院', '年级', '组织全称', '所属辅导员', '姓名', '性别', 
  '学号', '出生年月', '民族', '身份证号码', '手机号码', 
  '团内职务', '政治面貌', '团员发展编号', '入团年月', 
  '户籍地', '转接状态', '转接原因', '转接地址', '备注'
];

// Excel数据字段映射
const fieldMapping = {
  '学院': 'college',
  '年级': 'grade',
  '组织全称': 'organization',
  '所属辅导员': 'counselor',
  '姓名': 'name',
  '性别': 'gender',
  '学号': 'studentId',
  '出生年月': 'birthDate',
  '民族': 'nationality',
  '身份证号码': 'idCard',
  '手机号码': 'phone',
  '团内职务': 'position',
  '政治面貌': 'politicalStatus',
  '团员发展编号': 'memberCode',
  '入团年月': 'joinDate',
  '户籍地': 'residence',
  '转接状态': 'transferStatus',
  '转接原因': 'transferReason',
  '转接地址': 'transferAddress',
  '备注': 'remark'
};

// 学院列表（从数据字典动态加载）
const colleges = ref([]);

// 年级列表
const grades = ['2021级', '2022级', '2023级', '2024级', '2025级'];

// 政治面貌选项
const politicalStatusOptions = ['共青团员', '中共党员', '中共预备党员', '群众', '其他'];

// 团内职务选项（从数据字典动态加载）
const positions = ref([]);

// 民族列表（从数据字典动态加载）
const nationalities = ref([]);

const loadDictionaryOptions = async () => {
  colleges.value = await getDictionaryNames('college');
  positions.value = await getDictionaryNames('position');
  nationalities.value = await getDictionaryNames('ethnicity');
};

// 转接状态选项
const transferStatusOptions = ['未转接', '转接中', '已完成', '已撤销'];

// 转接原因选项
const transferReasons = ['升学', '毕业', '工作调动', '居住地变更', '其他'];

// 辅导员列表
const counselors = [
  { id: 1, name: '王老师', phone: '13800138001' },
  { id: 2, name: '李老师', phone: '13800138002' },
  { id: 3, name: '张老师', phone: '13800138003' },
  { id: 4, name: '刘老师', phone: '13800138004' },
  { id: 5, name: '陈老师', phone: '13800138005' }
];

// 团员数据（从后端获取）
const members = ref([]);

// 从后端获取团员列表
const fetchMembers = async () => {
  try {
    const response = await fetch('/api/league-members/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      members.value = results.map(item => ({
        id: item.id,
        college: item.college || '',
        grade: item.grade || '',
        organization: item.organization || '',
        counselor: item.counselor || '',
        counselorPhone: item.counselor_phone || '',
        name: item.name,
        gender: item.gender || '',
        studentId: item.student_id || '',
        birthDate: item.birth_date || '',
        nationality: item.ethnicity || '',
        idCard: item.id_card || '',
        phone: item.phone || '',
        position: item.position || '',
        politicalStatus: item.political_status || '',
        memberCode: item.development_number || '',
        joinDate: item.join_date || '',
        residence: item.hometown || '',
        transferReason: item.transfer_reason || '',
        transferStatus: item.transfer_status || '未转接',
        transferAddress: item.transfer_address || '',
        remark: item.notes || ''
      }));
    }
  } catch (error) {
    console.error('获取团员列表失败:', error);
  }
};

// 模态框状态
const showModal = ref(false);
const showDetailModal = ref(false);

// 页面加载时获取数据
onMounted(() => {
  fetchMembers();
  loadDictionaryOptions();
});

const showDeleteModal = ref(false);
const isEdit = ref(false);
const currentMember = ref(null);
const formErrors = ref({});
const selectedMembers = ref([]);

// 导入相关变量
const showImportModal = ref(false);
const importPreview = ref([]);
const importErrors = ref([]);
const importedData = ref([]);

// 表单数据
const formData = ref({
  college: '',
  grade: '',
  organization: '',
  counselor: '',
  counselorPhone: '',
  name: '',
  gender: '男',
  studentId: '',
  birthDate: '',
  nationality: '汉族',
  idCard: '',
  phone: '',
  position: '普通团员',
  politicalStatus: '共青团员',
  memberCode: '',
  joinDate: '',
  residence: '',
  transferReason: '',
  transferStatus: '未转接',
  transferAddress: '',
  remark: ''
});

// 搜索和筛选
const searchQuery = ref('');
const filters = ref({
  college: '全部',
  grade: '全部',
  politicalStatus: '全部'
});

// 统计数据
const stats = computed(() => {
  const total = members.value.length;
  const registered = members.value.filter(m => m.transferStatus === '未转接').length;
  const inTransfer = members.value.filter(m => m.transferStatus === '转接中').length;
  const completed = members.value.filter(m => m.transferStatus === '已完成').length;
  
  return [
    { label: '团员总数', value: total },
    { label: '在册团员', value: registered },
    { label: '转接中', value: inTransfer },
    { label: '已转接', value: completed }
  ];
});

// 筛选后的团员列表
const filteredMembers = computed(() => {
  return members.value.filter(m => {
    const matchSearch = !searchQuery.value || 
      m.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      m.studentId.includes(searchQuery.value) ||
      m.phone.includes(searchQuery.value);
    
    const matchCollege = filters.value.college === '全部' || m.college === filters.value.college;
    const matchGrade = filters.value.grade === '全部' || m.grade === filters.value.grade;
    const matchStatus = filters.value.politicalStatus === '全部' || m.politicalStatus === filters.value.politicalStatus;
    
    return matchSearch && matchCollege && matchGrade && matchStatus;
  });
});

// 验证表单
function validateForm() {
  const errors = {};
  
  if (!formData.value.college) errors.college = '请选择学院';
  if (!formData.value.grade) errors.grade = '请选择年级';
  if (!formData.value.organization) errors.organization = '请输入组织全称';
  if (!formData.value.counselor) errors.counselor = '请选择辅导员';
  if (!formData.value.name) errors.name = '请输入姓名';
  if (!formData.value.studentId) errors.studentId = '请输入学号';
  if (!formData.value.birthDate) errors.birthDate = '请选择出生年月';
  if (!formData.value.idCard) errors.idCard = '请输入身份证号码';
  if (!formData.value.phone) errors.phone = '请输入手机号码';
  if (!formData.value.memberCode) errors.memberCode = '请输入团员发展编号';
  if (!formData.value.joinDate) errors.joinDate = '请选择入团年月';
  
  // 身份证验证
  if (formData.value.idCard && !/^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/.test(formData.value.idCard)) {
    errors.idCard = '身份证号码格式不正确';
  }
  
  // 手机号验证
  if (formData.value.phone && !/^1[3-9]\d{9}$/.test(formData.value.phone)) {
    errors.phone = '手机号码格式不正确';
  }
  
  // 学号验证
  if (formData.value.studentId && !/^[\d]{8,12}$/.test(formData.value.studentId)) {
    errors.studentId = '学号格式不正确（8-12位数字）';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 打开创建模态框
function openCreateModal() {
  isEdit.value = false;
  currentMember.value = null;
  formData.value = {
    college: '',
    grade: '',
    organization: '',
    counselor: '',
    counselorPhone: '',
    name: '',
    gender: '男',
    studentId: '',
    birthDate: '',
    nationality: '汉族',
    idCard: '',
    phone: '',
    position: '普通团员',
    politicalStatus: '共青团员',
    memberCode: '',
    joinDate: '',
    residence: '',
    transferReason: '',
    transferStatus: '未转接',
    transferAddress: '',
    remark: ''
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

// 打开删除确认模态框
function openDeleteModal(member) {
  currentMember.value = member;
  showDeleteModal.value = true;
}

// 关闭模态框
function closeModal() {
  showModal.value = false;
  showDetailModal.value = false;
  showDeleteModal.value = false;
  currentMember.value = null;
  formErrors.value = {};
}

// 保存团员信息
function saveMember() {
  if (!validateForm()) return;
  
  if (isEdit.value) {
    const index = members.value.findIndex(m => m.id === currentMember.value.id);
    if (index !== -1) {
      members.value[index] = { ...formData.value };
    }
  } else {
    const newMember = {
      id: members.value.length + 1,
      ...formData.value
    };
    members.value.unshift(newMember);
  }
  
  closeModal();
}

// 删除团员
function deleteMember() {
  if (currentMember.value) {
    const index = members.value.findIndex(m => m.id === currentMember.value.id);
    if (index !== -1) {
      members.value.splice(index, 1);
    }
  }
  closeModal();
}

// 选择辅导员
function selectCounselor() {
  const counselor = counselors.find(c => c.name === formData.value.counselor);
  if (counselor) {
    formData.value.counselorPhone = counselor.phone;
  }
}

// 切换选择
function toggleSelect(id) {
  const index = selectedMembers.value.indexOf(id);
  if (index === -1) {
    selectedMembers.value.push(id);
  } else {
    selectedMembers.value.splice(index, 1);
  }
}

// 全选
function toggleSelectAll() {
  if (selectedMembers.value.length === filteredMembers.value.length) {
    selectedMembers.value = [];
  } else {
    selectedMembers.value = filteredMembers.value.map(m => m.id);
  }
}

// 批量删除
function batchDelete() {
  members.value = members.value.filter(m => !selectedMembers.value.includes(m.id));
  selectedMembers.value = [];
}

// 下载导入模板
function downloadTemplate() {
  // 创建模板数据（只有表头和示例行）
  const templateData = [
    excelHeaders,
    ['计算机学院', '2024级', '计算机学院团委', '王老师', '李小明', '男', 
     '2024001001', '2006-01-15', '汉族', '110101200601151234', 
     '13912345678', '普通团员', '共青团员', 'TY2024001', 
     '2024-09-01', '北京市朝阳区', '未转接', '', '', '示例数据']
  ];
  
  // 创建工作簿
  const worksheet = XLSX.utils.aoa_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '团员信息');
  
  // 设置列宽
  worksheet['!cols'] = [
    { wch: 12 }, { wch: 10 }, { wch: 20 }, { wch: 12 }, { wch: 10 }, { wch: 6 },
    { wch: 12 }, { wch: 12 }, { wch: 8 }, { wch: 20 }, { wch: 13 }, { wch: 12 },
    { wch: 12 }, { wch: 14 }, { wch: 12 }, { wch: 20 }, { wch: 10 }, { wch: 10 },
    { wch: 20 }, { wch: 15 }
  ];
  
  // 下载文件
  XLSX.writeFile(workbook, '团员信息导入模板.xlsx');
}

// 导出团员数据
function exportData() {
  // 将数据转换为Excel格式
  const exportData = filteredMembers.value.map(member => ({
    '学院': member.college,
    '年级': member.grade,
    '组织全称': member.organization,
    '所属辅导员': member.counselor,
    '姓名': member.name,
    '性别': member.gender,
    '学号': member.studentId,
    '出生年月': member.birthDate,
    '民族': member.nationality,
    '身份证号码': member.idCard,
    '手机号码': member.phone,
    '团内职务': member.position,
    '政治面貌': member.politicalStatus,
    '团员发展编号': member.memberCode,
    '入团年月': member.joinDate,
    '户籍地': member.residence,
    '转接状态': member.transferStatus,
    '转接原因': member.transferReason,
    '转接地址': member.transferAddress,
    '备注': member.remark
  }));
  
  // 创建工作簿
  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '团员信息');
  
  // 设置列宽
  worksheet['!cols'] = [
    { wch: 12 }, { wch: 10 }, { wch: 20 }, { wch: 12 }, { wch: 10 }, { wch: 6 },
    { wch: 12 }, { wch: 12 }, { wch: 8 }, { wch: 20 }, { wch: 13 }, { wch: 12 },
    { wch: 12 }, { wch: 14 }, { wch: 12 }, { wch: 20 }, { wch: 10 }, { wch: 10 },
    { wch: 20 }, { wch: 15 }
  ];
  
  // 下载文件
  const fileName = `团员信息_${new Date().toISOString().split('T')[0]}.xlsx`;
  XLSX.writeFile(workbook, fileName);
}

// 导入Excel文件
async function handleFileUpload(event) {
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
      
      // 验证表头
      const headers = jsonData[0];
      if (!validateHeaders(headers)) {
        alert('Excel表头格式不正确，请使用下载的模板');
        event.target.value = '';
        return;
      }
      
      // 解析数据（从第二行开始）
      let successCount = 0;
      let errorCount = 0;
      const newMembers = [];
      
      for (let i = 1; i < jsonData.length; i++) {
        const rowData = jsonData[i];
        if (rowData.length === 0 || !rowData[4]) continue; // 跳过空行或姓名为空的行
        
        try {
          const member = parseRowData(headers, rowData);
          if (member) {
            member.id = members.value.length + newMembers.length + 1;
            newMembers.push(member);
            successCount++;
          } else {
            errorCount++;
          }
        } catch (error) {
          console.error('解析第', i + 1, '行失败:', error);
          errorCount++;
        }
      }
      
      // 调用后端API保存数据
      if (newMembers.length > 0) {
        try {
          const importData = newMembers.map(member => ({
            name: member.name,
            gender: member.gender,
            studentId: member.studentId,
            birthDate: member.birthDate,
            nationality: member.nationality || '汉族',
            idCard: member.idCard,
            phone: member.phone,
            college: member.college,
            grade: member.grade,
            organization: member.organization,
            counselor: member.counselor,
            position: member.position || '普通团员',
            politicalStatus: member.politicalStatus || '共青团员',
            memberCode: member.memberCode,
            joinDate: member.joinDate,
            residence: member.residence || '',
            transferStatus: member.transferStatus || '未转接',
            transferReason: member.transferReason || '',
            transferAddress: member.transferAddress || '',
            remark: member.remark || ''
          }));
          
          const response = await fetch('/api/league-members/bulk_import/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ data: importData })
          });
          
          const result = await response.json();
          
          if (result.code === 200) {
            const message = `成功导入 ${result.success_count} 名团员！` + 
              (result.failed_count > 0 ? `\n有 ${result.failed_count} 条数据导入失败：\n${result.errors.map(e => `第${e.row}行: ${e.name}(${e.studentId}) - ${e.error}`).join('\n')}` : '');
            alert(message);
            fetchMembers();
          } else {
            alert(result.message || '导入失败');
          }
        } catch (error) {
          console.error('导入失败:', error);
          alert('导入失败，请检查网络连接');
        }
      } else {
        alert(`没有有效数据可以导入。成功：${successCount}条，失败：${errorCount}条`);
      }
      
    } catch (error) {
      console.error('解析Excel文件失败:', error);
      alert('解析Excel文件失败，请检查文件格式');
    }
    
    event.target.value = '';
  };
  
  reader.readAsArrayBuffer(file);
}

// 验证表头
function validateHeaders(headers) {
  if (!headers || headers.length < excelHeaders.length) return false;
  return excelHeaders.every((header, index) => headers[index] === header);
}

// 解析单行数据
function parseRowData(headers, rowData) {
  const member = {
    counselorPhone: '',
    position: '普通团员',
    politicalStatus: '共青团员',
    transferStatus: '未转接',
    transferReason: '',
    transferAddress: '',
    remark: ''
  };
  
  headers.forEach((header, index) => {
    const fieldName = fieldMapping[header];
    if (fieldName && rowData[index] !== undefined && rowData[index] !== null) {
      member[fieldName] = String(rowData[index]).trim();
    }
  });
  
  // 必需字段验证
  if (!member.college || !member.grade || !member.organization || 
      !member.counselor || !member.name || !member.studentId || 
      !member.birthDate || !member.idCard || !member.phone || 
      !member.memberCode || !member.joinDate) {
    return null;
  }
  
  // 根据辅导员查找电话号码
  const counselor = counselors.find(c => c.name === member.counselor);
  if (counselor) {
    member.counselorPhone = counselor.phone;
  }
  
  return member;
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>团员管理</h1>
    </header>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.label" class="stat-item">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>
    
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <input type="text" v-model="searchQuery" placeholder="搜索姓名、学号、手机号..." class="search-input" />
        </div>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedMembers.length > 0 && hasPermission('league:delete')" class="btn btn-danger" @click="batchDelete">
          批量删除 ({{ selectedMembers.length }})
        </button>
        <button v-if="hasPermission('league:edit')" class="btn btn-secondary" @click="downloadTemplate">下载模板</button>
        <label v-if="hasPermission('league:edit')" class="btn btn-secondary file-upload-label">
          <input type="file" accept=".xlsx,.xls" style="display: none" @change="handleFileUpload" />
          导入数据
        </label>
        <button v-if="hasPermission('league:edit')" class="btn btn-secondary" @click="exportData">导出数据</button>
        <button v-if="hasPermission('league:add')" class="btn btn-primary" @click="openCreateModal">新增团员</button>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>学院：</label>
        <select v-model="filters.college">
          <option value="全部">全部</option>
          <option v-for="college in colleges" :key="college" :value="college">{{ college }}</option>
        </select>
      </div>
      <div class="filter-item">
        <label>年级：</label>
        <select v-model="filters.grade">
          <option value="全部">全部</option>
          <option v-for="grade in grades" :key="grade" :value="grade">{{ grade }}</option>
        </select>
      </div>
      <div class="filter-item">
        <label>政治面貌：</label>
        <select v-model="filters.politicalStatus">
          <option value="全部">全部</option>
          <option v-for="status in politicalStatusOptions" :key="status" :value="status">{{ status }}</option>
        </select>
      </div>
    </div>
    
    <!-- 团员列表 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>
              <input type="checkbox" :checked="selectedMembers.length === filteredMembers.length && filteredMembers.length > 0" @change="toggleSelectAll" />
            </th>
            <th>姓名</th>
            <th>学院</th>
            <th>年级</th>
            <th>学号</th>
            <th>政治面貌</th>
            <th>团内职务</th>
            <th>入团时间</th>
            <th>转接状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in filteredMembers" :key="member.id">
            <td>
              <input type="checkbox" :checked="selectedMembers.includes(member.id)" @change="toggleSelect(member.id)" />
            </td>
            <td>{{ member.name }}</td>
            <td><span class="college-tag">{{ member.college }}</span></td>
            <td>{{ member.grade }}</td>
            <td>{{ member.studentId }}</td>
            <td><span class="status-tag">{{ member.politicalStatus }}</span></td>
            <td>{{ member.position }}</td>
            <td>{{ member.joinDate }}</td>
            <td><span class="transfer-tag" :class="member.transferStatus">{{ member.transferStatus }}</span></td>
            <td>
              <button class="action-btn view" @click="openDetailModal(member)">查看</button>
              <button v-if="hasPermission('league:edit')" class="action-btn edit" @click="openEditModal(member)">编辑</button>
              <button v-if="hasPermission('league:delete')" class="action-btn delete" @click="openDeleteModal(member)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="filteredMembers.length === 0" class="empty-state">
        <p>暂无团员数据</p>
      </div>
    </div>
    
    <!-- 新增/编辑模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑团员' : '新增团员' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-section">
            <h3 class="section-title">基本信息</h3>
            <div class="form-row">
              <div class="form-group">
                <label>学院 <span class="required">*</span></label>
                <select v-model="formData.college" class="form-select">
                  <option value="">请选择学院</option>
                  <option v-for="college in colleges" :key="college" :value="college">{{ college }}</option>
                </select>
                <span v-if="formErrors.college" class="form-error">{{ formErrors.college }}</span>
              </div>
              <div class="form-group">
                <label>年级 <span class="required">*</span></label>
                <select v-model="formData.grade" class="form-select">
                  <option value="">请选择年级</option>
                  <option v-for="grade in grades" :key="grade" :value="grade">{{ grade }}</option>
                </select>
                <span v-if="formErrors.grade" class="form-error">{{ formErrors.grade }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>组织全称 <span class="required">*</span></label>
                <input type="text" v-model="formData.organization" class="form-input" placeholder="请输入组织全称" />
                <span v-if="formErrors.organization" class="form-error">{{ formErrors.organization }}</span>
              </div>
              <div class="form-group">
                <label>所属辅导员 <span class="required">*</span></label>
                <select v-model="formData.counselor" class="form-select" @change="selectCounselor">
                  <option value="">请选择辅导员</option>
                  <option v-for="counselor in counselors" :key="counselor.id" :value="counselor.name">{{ counselor.name }}</option>
                </select>
                <span v-if="formErrors.counselor" class="form-error">{{ formErrors.counselor }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>辅导员联系方式</label>
                <input type="text" v-model="formData.counselorPhone" class="form-input" readonly />
              </div>
            </div>
          </div>
          
          <div class="form-section">
            <h3 class="section-title">个人信息</h3>
            <div class="form-row">
              <div class="form-group">
                <label>姓名 <span class="required">*</span></label>
                <input type="text" v-model="formData.name" class="form-input" placeholder="请输入姓名" />
                <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
              </div>
              <div class="form-group">
                <label>性别</label>
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
                <label>学号 <span class="required">*</span></label>
                <input type="text" v-model="formData.studentId" class="form-input" placeholder="请输入学号" />
                <span v-if="formErrors.studentId" class="form-error">{{ formErrors.studentId }}</span>
              </div>
              <div class="form-group">
                <label>出生年月 <span class="required">*</span></label>
                <input type="date" v-model="formData.birthDate" class="form-input" />
                <span v-if="formErrors.birthDate" class="form-error">{{ formErrors.birthDate }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>民族</label>
                <select v-model="formData.nationality" class="form-select">
                  <option v-for="nation in nationalities" :key="nation" :value="nation">{{ nation }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>身份证号码 <span class="required">*</span></label>
                <input type="text" v-model="formData.idCard" class="form-input" placeholder="请输入身份证号码" />
                <span v-if="formErrors.idCard" class="form-error">{{ formErrors.idCard }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>手机号码 <span class="required">*</span></label>
                <input type="text" v-model="formData.phone" class="form-input" placeholder="请输入手机号码" />
                <span v-if="formErrors.phone" class="form-error">{{ formErrors.phone }}</span>
              </div>
            </div>
          </div>
          
          <div class="form-section">
            <h3 class="section-title">团务信息</h3>
            <div class="form-row">
              <div class="form-group">
                <label>团内职务</label>
                <select v-model="formData.position" class="form-select">
                  <option v-for="pos in positions" :key="pos" :value="pos">{{ pos }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>政治面貌</label>
                <select v-model="formData.politicalStatus" class="form-select">
                  <option v-for="status in politicalStatusOptions" :key="status" :value="status">{{ status }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>团员发展编号 <span class="required">*</span></label>
                <input type="text" v-model="formData.memberCode" class="form-input" placeholder="请输入团员发展编号" />
                <span v-if="formErrors.memberCode" class="form-error">{{ formErrors.memberCode }}</span>
              </div>
              <div class="form-group">
                <label>入团年月 <span class="required">*</span></label>
                <input type="date" v-model="formData.joinDate" class="form-input" />
                <span v-if="formErrors.joinDate" class="form-error">{{ formErrors.joinDate }}</span>
              </div>
            </div>
          </div>
          
          <div class="form-section">
            <h3 class="section-title">团组织关系转接</h3>
            <div class="form-row">
              <div class="form-group">
                <label>户籍地</label>
                <input type="text" v-model="formData.residence" class="form-input" placeholder="请输入户籍地" />
              </div>
              <div class="form-group">
                <label>转接状态</label>
                <select v-model="formData.transferStatus" class="form-select">
                  <option v-for="status in transferStatusOptions" :key="status" :value="status">{{ status }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>转接原因</label>
                <select v-model="formData.transferReason" class="form-select">
                  <option value="">请选择转接原因</option>
                  <option v-for="reason in transferReasons" :key="reason" :value="reason">{{ reason }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>转接地址</label>
                <input type="text" v-model="formData.transferAddress" class="form-input" placeholder="请输入转接地址" />
              </div>
            </div>
            <div class="form-group">
              <label>备注</label>
              <textarea v-model="formData.remark" class="form-textarea" placeholder="请输入备注信息"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveMember">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>团员详情</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentMember">
          <div class="detail-section">
            <h3 class="section-title">基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">学院：</span>{{ currentMember.college }}</div>
              <div class="detail-item"><span class="label">年级：</span>{{ currentMember.grade }}</div>
              <div class="detail-item"><span class="label">组织全称：</span>{{ currentMember.organization }}</div>
              <div class="detail-item"><span class="label">所属辅导员：</span>{{ currentMember.counselor }}</div>
              <div class="detail-item"><span class="label">辅导员联系方式：</span>{{ currentMember.counselorPhone }}</div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">个人信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">姓名：</span>{{ currentMember.name }}</div>
              <div class="detail-item"><span class="label">性别：</span>{{ currentMember.gender }}</div>
              <div class="detail-item"><span class="label">学号：</span>{{ currentMember.studentId }}</div>
              <div class="detail-item"><span class="label">出生年月：</span>{{ currentMember.birthDate }}</div>
              <div class="detail-item"><span class="label">民族：</span>{{ currentMember.nationality }}</div>
              <div class="detail-item"><span class="label">身份证号码：</span>{{ currentMember.idCard }}</div>
              <div class="detail-item"><span class="label">手机号码：</span>{{ currentMember.phone }}</div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">团务信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">团内职务：</span>{{ currentMember.position }}</div>
              <div class="detail-item"><span class="label">政治面貌：</span>{{ currentMember.politicalStatus }}</div>
              <div class="detail-item"><span class="label">团员发展编号：</span>{{ currentMember.memberCode }}</div>
              <div class="detail-item"><span class="label">入团年月：</span>{{ currentMember.joinDate }}</div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">团组织关系转接</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">户籍地：</span>{{ currentMember.residence }}</div>
              <div class="detail-item"><span class="label">转接状态：</span><span class="transfer-tag" :class="currentMember.transferStatus">{{ currentMember.transferStatus }}</span></div>
              <div class="detail-item"><span class="label">转接原因：</span>{{ currentMember.transferReason || '-' }}</div>
              <div class="detail-item"><span class="label">转接地址：</span>{{ currentMember.transferAddress || '-' }}</div>
              <div class="detail-item full-width"><span class="label">备注：</span>{{ currentMember.remark || '-' }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button class="btn btn-primary" @click="openEditModal(currentMember); closeModal()">编辑</button>
        </div>
      </div>
    </div>
    
    <!-- 删除确认模态框 -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <h2>确认删除</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="delete-icon">⚠️</div>
          <p>确定要删除团员「{{ currentMember?.name }}」吗？此操作不可撤销。</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-danger" @click="deleteMember">确认删除</button>
        </div>
      </div>
    </div>
    
    <!-- 批量导入预览模态框 -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal-content large-modal">
        <div class="modal-header">
          <h3>批量导入团员</h3>
          <button class="close-btn" @click="showImportModal = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="importErrors.length > 0" class="error-summary">
            <strong>⚠️ 发现 {{ importErrors.length }} 条数据错误：</strong>
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
                  <th>姓名</th>
                  <th>性别</th>
                  <th>学号</th>
                  <th>学院</th>
                  <th>年级</th>
                  <th>团内职务</th>
                  <th>政治面貌</th>
                  <th>转接状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in importPreview" :key="item.row" :class="{ 'error-row': item.errors.length > 0 }">
                  <td>{{ item.row }}</td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.gender }}</td>
                  <td>{{ item.studentId }}</td>
                  <td>{{ item.college }}</td>
                  <td>{{ item.grade }}</td>
                  <td>{{ item.position }}</td>
                  <td>{{ item.politicalStatus }}</td>
                  <td>{{ item.transferStatus }}</td>
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
  margin-bottom: 16px;
  gap: 16px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  position: relative;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  width: 250px;
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
  background: #ff4d4f;
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

.filter-bar {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 24px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  color: #666;
}

.filter-item select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
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

.college-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag {
  padding: 4px 12px;
  background: #f6ffed;
  color: #52c41a;
  border-radius: 4px;
  font-size: 12px;
}

.transfer-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.transfer-tag.未转接 {
  background: #f6ffed;
  color: #52c41a;
}

.transfer-tag.转接中 {
  background: #fff7e6;
  color: #fa8c16;
}

.transfer-tag.已完成 {
  background: #e6f7ff;
  color: #1890ff;
}

.transfer-tag.已撤销 {
  background: #f5f5f5;
  color: #8c8c8c;
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

.delete-modal {
  max-width: 400px;
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
.form-section {
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
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
  gap: 6px;
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
  padding: 8px 12px;
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

.delete-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 16px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-bar {
    flex-wrap: wrap;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
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
}
</style>