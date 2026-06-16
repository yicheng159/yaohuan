<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import * as XLSX from 'xlsx';
import { apiFetch } from '../utils/api';
import { hasPermission } from '../utils/permission';
import { getDictionaryNames } from '../utils/dictionary';

const members = ref([]);
const isLoading = ref(false);

const fetchMembers = async () => {
  isLoading.value = true;
  try {
    const response = await apiFetch('/api/members/');
    if (response.ok) {
      const data = await response.json();
      if (data.results && data.results.length > 0) {
        members.value = data.results.map(m => ({
          id: m.id,
          name: m.name,
          department: m.department,
          position: m.position,
          role: m.role,
          grade: m.grade,
          className: m.class_name || '',
          counselorName: m.counselor_name,
          counselorPhone: m.counselor_phone,
          phone: m.phone,
          email: m.email || '',
          avatar: '👤',
          joinDate: m.join_date,
          status: m.status,
          gender: m.gender,
          studentId: m.student_id || ''
        }));
      } else {
        members.value = [];
      }
      filterMembers();
    } else {
      console.error('API请求失败:', response.status);
    }
  } catch (error) {
    console.error('加载成员数据失败:', error);
    showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
  } finally {
    isLoading.value = false;
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchMembers();
  loadDictionaryOptions();
});

// 统计数据
const stats = computed(() => [
  { label: '总人数', value: members.value.length },
  { label: '男生', value: Math.floor(members.value.length * 0.45) },
  { label: '女生', value: Math.ceil(members.value.length * 0.55) },
  { label: '党员', value: Math.floor(members.value.length * 0.12) }
]);

// 部门分布统计
const departmentStats = computed(() => {
  const deptCount = {};
  (departments.value || []).slice(1).forEach(dept => {
    deptCount[dept] = 0;
  });
  
  members.value.forEach(member => {
    if (deptCount[member.department] !== undefined) {
      deptCount[member.department]++;
    }
  });
  
  return (departments.value || []).slice(1).map(dept => ({
    name: dept,
    count: deptCount[dept]
  }));
});

// 分页相关
const currentPage = ref(1);
const pageSize = 10;
const totalPages = computed(() => Math.ceil(filteredMembers.value.length / pageSize));

// 批量选择相关
const selectedMemberIds = ref([]);

// 是否全选
const isAllSelected = computed(() => {
  return paginatedMembers.value.length > 0 && 
         paginatedMembers.value.every(m => selectedMemberIds.value.includes(m.id));
});

// 切换全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    paginatedMembers.value.forEach(m => {
      const index = selectedMemberIds.value.indexOf(m.id);
      if (index !== -1) {
        selectedMemberIds.value.splice(index, 1);
      }
    });
  } else {
    paginatedMembers.value.forEach(m => {
      if (!selectedMemberIds.value.includes(m.id)) {
        selectedMemberIds.value.push(m.id);
      }
    });
  }
};

// 切换单个选择
const toggleSelect = (memberId, event) => {
  event.stopPropagation();
  const index = selectedMemberIds.value.indexOf(memberId);
  if (index === -1) {
    selectedMemberIds.value.push(memberId);
  } else {
    selectedMemberIds.value.splice(index, 1);
  }
};

// 批量删除
const deleteSelected = async () => {
  if (selectedMemberIds.value.length === 0) {
    showErrorMessage('请先选择要删除的成员');
    return;
  }
  
  if (confirm(`确定要删除选中的 ${selectedMemberIds.value.length} 名成员吗？`)) {
    isLoading.value = true;
    let successCount = 0;
    
    try {
      for (const id of selectedMemberIds.value) {
        const response = await apiFetch(`/api/members/${id}/`, {
          method: 'DELETE',
        });
        if (response.ok || response.status === 204) {
          successCount++;
          members.value = members.value.filter(m => m.id !== id);
        }
      }
      
      selectedMemberIds.value = [];
      filterMembers();
      showSuccessMessage(`成功删除 ${successCount} 名成员！`);
    } catch (error) {
      console.error('批量删除失败:', error);
      showErrorMessage('批量删除失败，请重试');
    } finally {
      isLoading.value = false;
    }
  }
};

// 当前页数据
const paginatedMembers = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredMembers.value.slice(start, end);
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
  department: '全部',
  role: '全部'
});

// 部门列表（从数据字典动态加载）
const departments = ref(['全部']);
const statuses = ['全部', '在职', '离职'];
const roles = ref(['全部']);

const loadDictionaryOptions = async () => {
  try {
    const deptNames = await getDictionaryNames('department');
    departments.value = ['全部', ...(Array.isArray(deptNames) ? deptNames : [])];
    const roleNames = await getDictionaryNames('position');
    roles.value = ['全部', ...(Array.isArray(roleNames) ? roleNames : [])];
  } catch (error) {
    console.error('加载数据字典失败:', error);
  }
};

// 搜索
const searchQuery = ref('');

// 过滤成员
const filteredMembers = ref(members.value);

// 模态框控制
const showAddModal = ref(false);
const showEditModal = ref(false);
const showImportModal = ref(false);
const showDetailModal = ref(false);
const showSuccess = ref(false);
const showError = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

// 当前编辑的成员
const currentMember = ref({
  id: null,
  name: '',
  department: '',
  position: '',
  role: '',
  grade: '',
  className: '',
  counselorName: '',
  counselorPhone: '',
  phone: '',
  email: '',
  joinDate: new Date().toISOString().split('T')[0],
  status: '在职',
  gender: '',
  studentId: ''
});

// 详情成员
const detailMember = ref(null);

// 表单验证错误
const formErrors = ref({});

// 导入数据
const importedData = ref([]);
const importPreview = ref([]);
const importErrors = ref([]);

// 当前编辑的成员索引
const editingMemberId = ref(null);

// 过滤成员
const filterMembers = () => {
  filteredMembers.value = members.value.filter(m => {
    const matchStatus = filters.value.status === '全部' || m.status === filters.value.status;
    const matchDept = filters.value.department === '全部' || m.department === filters.value.department;
    const matchRole = filters.value.role === '全部' || m.role === filters.value.role;
    const matchSearch = !searchQuery.value || 
      m.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
      m.id.toString().includes(searchQuery.value) ||
      m.phone.includes(searchQuery.value) ||
      m.email.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      m.department.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (m.studentId && m.studentId.includes(searchQuery.value));
    return matchStatus && matchDept && matchRole && matchSearch;
  });
  currentPage.value = 1; // 重置到第一页
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
const viewDetail = (member) => {
  detailMember.value = member;
  showDetailModal.value = true;
};

// 重置筛选
const resetFilters = () => {
  filters.value = {
    status: '全部',
    department: '全部',
    role: '全部'
  };
  searchQuery.value = '';
  filterMembers();
};

// 验证表单
const validateForm = () => {
  const errors = {};
  
  if (!currentMember.value.name || currentMember.value.name.trim() === '') {
    errors.name = '请输入姓名';
  }
  
  if (!currentMember.value.department) {
    errors.department = '请选择部门';
  }
  
  if (!currentMember.value.position || currentMember.value.position.trim() === '') {
    errors.position = '请输入职位';
  }
  
  if (!currentMember.value.role) {
    errors.role = '请选择角色';
  }
  
  if (!currentMember.value.grade) {
    errors.grade = '请选择年级';
  }
  
  if (!currentMember.value.className || currentMember.value.className.trim() === '') {
    errors.className = '请输入班级';
  }
  
  if (!currentMember.value.counselorName || currentMember.value.counselorName.trim() === '') {
    errors.counselorName = '请输入辅导员姓名';
  }
  
  if (!currentMember.value.counselorPhone) {
    errors.counselorPhone = '请输入辅导员联系方式';
  } else if (!/^1[3-9]\d{9}$/.test(currentMember.value.counselorPhone)) {
    errors.counselorPhone = '请输入有效的手机号码';
  }
  
  if (!currentMember.value.phone) {
    errors.phone = '请输入联系电话';
  } else if (!/^1[3-9]\d{9}$/.test(currentMember.value.phone)) {
    errors.phone = '请输入有效的手机号码';
  }
  
  if (!currentMember.value.email) {
    errors.email = '请输入邮箱';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(currentMember.value.email)) {
    errors.email = '请输入有效的邮箱地址';
  }
  
  if (!currentMember.value.joinDate) {
    errors.joinDate = '请选择加入日期';
  }
  
  if (!currentMember.value.gender) {
    errors.gender = '请选择性别';
  }
  
  if (!currentMember.value.studentId) {
    errors.studentId = '请输入学号';
  } else if (currentMember.value.studentId.length < 10 || currentMember.value.studentId.length > 20) {
    errors.studentId = '学号长度应为10-20个字符';
  } else if (!/^[A-Za-z0-9-_]+$/.test(currentMember.value.studentId)) {
    errors.studentId = '学号只能包含字母、数字、下划线和连字符';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
};

// 打开添加模态框
const openAddModal = () => {
  currentMember.value = {
    id: null,
    name: '',
    department: '',
    position: '',
    role: '',
    grade: '',
    className: '',
    counselorName: '',
    counselorPhone: '',
    phone: '',
    email: '',
    joinDate: new Date().toISOString().split('T')[0],
    status: '在职',
    gender: '',
    studentId: ''
  };
  formErrors.value = {};
  showAddModal.value = true;
};

// 打开编辑模态框
const openEditModal = (member) => {
  currentMember.value = { ...member };
  editingMemberId.value = member.id;
  formErrors.value = {};
  showEditModal.value = true;
};

// 添加成员
const addMember = async () => {
  if (!validateForm()) return;
  
  try {
    // 准备API请求数据
    const apiData = {
      name: currentMember.value.name,
      gender: currentMember.value.gender,
      student_id: currentMember.value.studentId || '',
      department: currentMember.value.department,
      position: currentMember.value.position,
      role: currentMember.value.role,
      grade: currentMember.value.grade,
      class_name: currentMember.value.className || '',
      counselor_name: currentMember.value.counselorName,
      counselor_phone: currentMember.value.counselorPhone || '',
      phone: currentMember.value.phone,
      email: currentMember.value.email || '',
      join_date: currentMember.value.joinDate,
      status: currentMember.value.status
    };
    
    const response = await apiFetch('/api/members/', {
      method: 'POST',
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const newMember = await response.json();
      // 添加到本地数据
      members.value.unshift({
        id: newMember.id,
        name: newMember.name,
        department: newMember.department,
        position: newMember.position,
        role: newMember.role,
        grade: newMember.grade,
        className: newMember.class_name || '',
        counselorName: newMember.counselor_name,
        counselorPhone: newMember.counselor_phone || '',
        phone: newMember.phone,
        email: newMember.email || '',
        avatar: '👤',
        joinDate: newMember.join_date,
        status: newMember.status,
        gender: newMember.gender,
        studentId: newMember.student_id || ''
      });
      
      showSuccessMessage('成员添加成功！');
      showAddModal.value = false;
      filterMembers();
    } else {
      const error = await response.json();
      showErrorMessage('添加失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('添加成员失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }
};

// 编辑成员
const editMember = async () => {
  if (!validateForm()) return;
  
  try {
    // 准备API请求数据
    const apiData = {
      name: currentMember.value.name,
      gender: currentMember.value.gender,
      student_id: currentMember.value.studentId || '',
      department: currentMember.value.department,
      position: currentMember.value.position,
      role: currentMember.value.role,
      grade: currentMember.value.grade,
      class_name: currentMember.value.className || '',
      counselor_name: currentMember.value.counselorName,
      counselor_phone: currentMember.value.counselorPhone || '',
      phone: currentMember.value.phone,
      email: currentMember.value.email || '',
      join_date: currentMember.value.joinDate,
      status: currentMember.value.status
    };
    
    const response = await apiFetch(`/api/members/${editingMemberId.value}/`, {
      method: 'PUT',
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const updatedMember = await response.json();
      // 更新本地数据
      const index = members.value.findIndex(m => m.id === editingMemberId.value);
      if (index !== -1) {
        members.value[index] = {
          id: updatedMember.id,
          name: updatedMember.name,
          department: updatedMember.department,
          position: updatedMember.position,
          role: updatedMember.role,
          grade: updatedMember.grade,
          className: updatedMember.class_name || '',
          counselorName: updatedMember.counselor_name,
          counselorPhone: updatedMember.counselor_phone || '',
          phone: updatedMember.phone,
          email: updatedMember.email || '',
          avatar: '👤',
          joinDate: updatedMember.join_date,
          status: updatedMember.status,
          gender: updatedMember.gender,
          studentId: updatedMember.student_id || ''
        };
      }
      
      showSuccessMessage('成员信息更新成功！');
    } else {
      const error = await response.json();
      showErrorMessage('更新失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('更新成员失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }
  
  showEditModal.value = false;
  filterMembers();
};

// 删除成员
const deleteMember = async (member) => {
  if (confirm(`确定要删除成员「${member.name}」吗？`)) {
    try {
      const response = await apiFetch(`/api/members/${member.id}/`, {
        method: 'DELETE',
      });
      
      if (response.ok || response.status === 204) {
        // 从本地数据中移除
        members.value = members.value.filter(m => m.id !== member.id);
        showSuccessMessage('成员删除成功！');
        filterMembers();
      } else {
        showErrorMessage('删除失败');
      }
    } catch (error) {
      console.error('删除成员失败:', error);
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
        
        if (!row['姓名']) errors.push('姓名不能为空');
        if (!row['部门']) errors.push('部门不能为空');
        if (!row['职位']) errors.push('职位不能为空');
        if (!row['年级']) errors.push('年级不能为空');
        if (!row['班级']) errors.push('班级不能为空');
        if (!row['辅导员姓名']) errors.push('辅导员姓名不能为空');
        if (!row['辅导员联系方式']) errors.push('辅导员联系方式不能为空');
        if (row['辅导员联系方式'] && !/^1[3-9]\d{9}$/.test(row['辅导员联系方式'])) errors.push('辅导员联系方式格式不正确');
        if (!row['联系电话']) errors.push('联系电话不能为空');
        if (row['联系电话'] && !/^1[3-9]\d{9}$/.test(row['联系电话'])) errors.push('联系电话格式不正确');
        if (!row['邮箱']) errors.push('邮箱不能为空');
        if (row['邮箱'] && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(row['邮箱'])) errors.push('邮箱格式不正确');
        if (!row['性别']) errors.push('性别不能为空');
        if (!row['学号']) errors.push('学号不能为空');
        if (row['学号'] && (row['学号'].length < 10 || row['学号'].length > 20)) errors.push('学号长度应为10-20个字符');
        if (row['学号'] && !/^[A-Za-z0-9-_]+$/.test(row['学号'])) errors.push('学号只能包含字母、数字、下划线和连字符');
        
        importPreview.value.push({
          row: index + 1,
          name: row['姓名'] || '',
          department: row['部门'] || '',
          position: row['职位'] || '',
          grade: row['年级'] || '',
          className: row['班级'] || '',
          counselorName: row['辅导员姓名'] || '',
          counselorPhone: row['辅导员联系方式'] || '',
          phone: row['联系电话'] || '',
          email: row['邮箱'] || '',
          joinDate: row['加入日期'] || new Date().toISOString().split('T')[0],
          gender: row['性别'] || '',
          studentId: row['学号'] || '',
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
  
  // 收集有效的导入数据
  const importData = importPreview.value
    .filter(item => item.errors.length === 0)
    .map(item => ({
      name: item.name,
      gender: item.gender,
      studentId: item.studentId,
      department: item.department,
      position: item.position,
      grade: item.grade,
      className: item.className,
      counselorName: item.counselorName,
      counselorPhone: item.counselorPhone,
      phone: item.phone,
      email: item.email,
      joinDate: item.joinDate
    }));
  
  if (importData.length === 0) {
    alert('没有有效数据可以导入');
    return;
  }
  
  try {
    const response = await apiFetch('/api/members/bulk_import/', {
      method: 'POST',
      body: JSON.stringify({ data: importData })
    });
    
    const result = await response.json();
    
    if (result.code === 200) {
      const message = `成功导入 ${result.success_count} 名成员！` + 
        (result.failed_count > 0 ? `\n有 ${result.failed_count} 条数据导入失败：\n${result.errors.map(e => `第${e.row}行: ${e.name}(${e.studentId}) - ${e.error}`).join('\n')}` : '');
      alert(message);
      showImportModal.value = false;
      filterMembers();
    } else {
      alert(result.message || '导入失败');
    }
  } catch (error) {
    console.error('导入失败:', error);
    alert('导入失败，请检查网络连接');
  }
};

// 导出Excel
const exportToExcel = () => {
  try {
    const exportData = filteredMembers.value.map(m => ({
      '姓名': m.name,
      '性别': m.gender,
      '学号': m.studentId,
      '部门': m.department,
      '职位': m.position,
      '年级': m.grade,
      '班级': m.className,
      '辅导员姓名': m.counselorName,
      '辅导员联系方式': m.counselorPhone,
      '联系电话': m.phone,
      '邮箱': m.email,
      '加入日期': m.joinDate,
      '状态': m.status
    }));
    
    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '成员信息');
    
    const fileName = `学生会成员名单_${new Date().toISOString().split('T')[0]}.xlsx`;
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
      '姓名': '张三',
      '性别': '男',
      '学号': '2023001001',
      '部门': '组织部',
      '职位': '部长',
      '年级': '2023级',
      '班级': '计算机2023级1班',
      '辅导员姓名': '李老师',
      '辅导员联系方式': '13812345678',
      '联系电话': '13912345678',
      '邮箱': 'zhangsan@stu.edu.cn',
      '加入日期': '2023-09-01'
    }
  ];
  
  const worksheet = XLSX.utils.json_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '模板');
  
  const fileName = '学生会成员导入模板.xlsx';
  XLSX.writeFile(workbook, fileName);
};
</script>

<template>
  <div class="members-page">
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
      <h1>成员管理</h1>
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
        <select v-model="filters.status" @change="filterMembers" class="filter-select" :class="{ active: filters.status !== '全部' }">
          <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>部门：</label>
        <select v-model="filters.department" @change="filterMembers" class="filter-select" :class="{ active: filters.department !== '全部' }">
          <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>角色：</label>
        <select v-model="filters.role" @change="filterMembers" class="filter-select" :class="{ active: filters.role !== '全部' }">
          <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
        </select>
      </div>
      <div class="filter-group search-group">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索姓名、ID、电话、邮箱..." 
          class="search-input"
          @input="filterMembers"
        />
      </div>
      <button v-if="filters.status !== '全部' || filters.department !== '全部' || filters.role !== '全部' || searchQuery" class="btn btn-text" @click="resetFilters">重置筛选</button>
    </div>
    
    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="result-count">共 {{ filteredMembers.length }} 条结果</span>
        <span v-if="selectedMemberIds.length > 0" class="selected-count">已选择 {{ selectedMemberIds.length }} 条</span>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedMemberIds.length > 0 && hasPermission('member:delete')" class="btn btn-danger" @click="deleteSelected">批量删除</button>
        <button v-if="hasPermission('member:import')" class="btn btn-secondary" @click="downloadTemplate">下载模板</button>
        <label v-if="hasPermission('member:import')" class="btn btn-secondary upload-btn">
          <span>批量导入</span>
          <input type="file" accept=".xlsx,.xls" @change="handleFileUpload" style="display: none;">
        </label>
        <button v-if="hasPermission('member:export')" class="btn btn-secondary" @click="exportToExcel">导出数据</button>
        <button v-if="hasPermission('member:add')" class="btn btn-primary" @click="openAddModal">添加成员</button>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    
    <div class="table-container">
      <div class="table-scroll">
        <table class="members-table">
          <thead>
            <tr>
              <th>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="isAllSelected" @change="toggleSelectAll" />
                </label>
              </th>
              <th>ID</th>
              <th>头像</th>
              <th>姓名</th>
              <th>性别</th>
              <th>学号</th>
              <th>部门</th>
              <th>角色</th>
              <th>职位</th>
              <th>联系方式</th>
              <th>邮箱</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in paginatedMembers" :key="member.id" @click="viewDetail(member)" class="clickable-row" :class="{ selected: selectedMemberIds.includes(member.id) }">
              <td @click.stop>
                <label class="checkbox-label">
                  <input type="checkbox" :checked="selectedMemberIds.includes(member.id)" @change="toggleSelect(member.id, $event)" />
                </label>
              </td>
              <td>{{ member.id }}</td>
              <td><span class="avatar">{{ member.avatar }}</span></td>
              <td>{{ member.name }}</td>
              <td>{{ member.gender }}</td>
              <td>{{ member.studentId }}</td>
              <td><span class="dept-tag">{{ member.department }}</span></td>
              <td><span class="role-tag">{{ member.role }}</span></td>
              <td>{{ member.position }}</td>
              <td>{{ member.phone }}</td>
              <td>{{ member.email }}</td>
              <td><span class="status-tag" :class="member.status">{{ member.status }}</span></td>
              <td @click.stop>
                <button v-if="hasPermission('member:edit')" class="action-btn edit" @click="openEditModal(member)">编辑</button>
                <button v-if="hasPermission('member:delete')" class="action-btn delete" @click="deleteMember(member)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 分页 -->
    <div v-if="totalPages > 0" class="pagination">
      <div class="pagination-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ filteredMembers.length }} 条记录
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
    
    <div class="departments-section">
      <h2 class="section-title">部门分布</h2>
      <div class="departments-grid">
        <div v-for="dept in departmentStats" :key="dept.name" class="dept-card">
          <span class="dept-name">{{ dept.name }}</span>
          <span class="dept-count">{{ dept.count }}人</span>
        </div>
      </div>
    </div>
    
    <!-- 添加成员模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加成员</h3>
          <button class="close-btn" @click="showAddModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>姓名 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.name" 
                class="form-input" 
                :class="{ 'error': formErrors.name }"
              />
              <span v-if="formErrors.name" class="error-text">{{ formErrors.name }}</span>
            </div>
            <div class="form-item">
              <label>性别 <span class="required">*</span></label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="currentMember.gender" value="男" />
                  <span>男</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="currentMember.gender" value="女" />
                  <span>女</span>
                </label>
              </div>
              <span v-if="formErrors.gender" class="error-text">{{ formErrors.gender }}</span>
            </div>
            <div class="form-item">
              <label>学号 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.studentId" 
                class="form-input" 
                :class="{ 'error': formErrors.studentId }"
                placeholder="请输入学号(10-20位)"
                maxlength="20"
              />
              <span v-if="formErrors.studentId" class="error-text">{{ formErrors.studentId }}</span>
            </div>
            <div class="form-item">
              <label>部门 <span class="required">*</span></label>
              <select 
                v-model="currentMember.department" 
                class="form-select" 
                :class="{ 'error': formErrors.department }"
              >
                <option value="">请选择部门</option>
                <option v-for="dept in departments.slice(1)" :key="dept" :value="dept">{{ dept }}</option>
              </select>
              <span v-if="formErrors.department" class="error-text">{{ formErrors.department }}</span>
            </div>
            <div class="form-item">
              <label>职位 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.position" 
                class="form-input" 
                :class="{ 'error': formErrors.position }"
              />
              <span v-if="formErrors.position" class="error-text">{{ formErrors.position }}</span>
            </div>
            <div class="form-item">
              <label>角色 <span class="required">*</span></label>
              <select 
                v-model="currentMember.role" 
                class="form-select" 
                :class="{ 'error': formErrors.role }"
              >
                <option value="">请选择角色</option>
                <option v-for="r in roles.slice(1)" :key="r" :value="r">{{ r }}</option>
              </select>
              <span v-if="formErrors.role" class="error-text">{{ formErrors.role }}</span>
            </div>
            <div class="form-item">
              <label>年级 <span class="required">*</span></label>
              <select 
                v-model="currentMember.grade" 
                class="form-select" 
                :class="{ 'error': formErrors.grade }"
              >
                <option value="">请选择年级</option>
                <option value="2021级">2021级</option>
                <option value="2022级">2022级</option>
                <option value="2023级">2023级</option>
                <option value="2024级">2024级</option>
              </select>
              <span v-if="formErrors.grade" class="error-text">{{ formErrors.grade }}</span>
            </div>
            <div class="form-item">
              <label>班级 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.className" 
                class="form-input" 
                :class="{ 'error': formErrors.className }"
                placeholder="计算机2023级1班"
              />
              <span v-if="formErrors.className" class="error-text">{{ formErrors.className }}</span>
            </div>
            <div class="form-item">
              <label>辅导员姓名 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.counselorName" 
                class="form-input" 
                :class="{ 'error': formErrors.counselorName }"
                placeholder="请输入辅导员姓名"
              />
              <span v-if="formErrors.counselorName" class="error-text">{{ formErrors.counselorName }}</span>
            </div>
            <div class="form-item">
              <label>辅导员联系方式 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.counselorPhone" 
                class="form-input" 
                :class="{ 'error': formErrors.counselorPhone }"
                placeholder="13812345678"
              />
              <span v-if="formErrors.counselorPhone" class="error-text">{{ formErrors.counselorPhone }}</span>
            </div>
            <div class="form-item">
              <label>联系电话 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.phone" 
                class="form-input" 
                :class="{ 'error': formErrors.phone }"
                placeholder="13812345678"
              />
              <span v-if="formErrors.phone" class="error-text">{{ formErrors.phone }}</span>
            </div>
            <div class="form-item">
              <label>邮箱 <span class="required">*</span></label>
              <input 
                type="email" 
                v-model="currentMember.email" 
                class="form-input" 
                :class="{ 'error': formErrors.email }"
                placeholder="example@stu.edu.cn"
              />
              <span v-if="formErrors.email" class="error-text">{{ formErrors.email }}</span>
            </div>
            <div class="form-item">
              <label>状态</label>
              <select v-model="currentMember.status" class="form-select">
                <option value="在职">在职</option>
                <option value="离职">离职</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="addMember">添加</button>
        </div>
      </div>
    </div>
    
    <!-- 编辑成员模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑成员</h3>
          <button class="close-btn" @click="showEditModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>姓名 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.name" 
                class="form-input" 
                :class="{ 'error': formErrors.name }"
              />
              <span v-if="formErrors.name" class="error-text">{{ formErrors.name }}</span>
            </div>
            <div class="form-item">
              <label>性别 <span class="required">*</span></label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="currentMember.gender" value="男" />
                  <span>男</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="currentMember.gender" value="女" />
                  <span>女</span>
                </label>
              </div>
              <span v-if="formErrors.gender" class="error-text">{{ formErrors.gender }}</span>
            </div>
            <div class="form-item">
              <label>学号 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.studentId" 
                class="form-input" 
                :class="{ 'error': formErrors.studentId }"
                placeholder="请输入学号(10-20位)"
                maxlength="20"
              />
              <span v-if="formErrors.studentId" class="error-text">{{ formErrors.studentId }}</span>
            </div>
            <div class="form-item">
              <label>部门 <span class="required">*</span></label>
              <select 
                v-model="currentMember.department" 
                class="form-select" 
                :class="{ 'error': formErrors.department }"
              >
                <option value="">请选择部门</option>
                <option v-for="dept in departments.slice(1)" :key="dept" :value="dept">{{ dept }}</option>
              </select>
              <span v-if="formErrors.department" class="error-text">{{ formErrors.department }}</span>
            </div>
            <div class="form-item">
              <label>职位 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.position" 
                class="form-input" 
                :class="{ 'error': formErrors.position }"
              />
              <span v-if="formErrors.position" class="error-text">{{ formErrors.position }}</span>
            </div>
            <div class="form-item">
              <label>角色 <span class="required">*</span></label>
              <select 
                v-model="currentMember.role" 
                class="form-select" 
                :class="{ 'error': formErrors.role }"
              >
                <option value="">请选择角色</option>
                <option v-for="r in roles.slice(1)" :key="r" :value="r">{{ r }}</option>
              </select>
              <span v-if="formErrors.role" class="error-text">{{ formErrors.role }}</span>
            </div>
            <div class="form-item">
              <label>年级 <span class="required">*</span></label>
              <select 
                v-model="currentMember.grade" 
                class="form-select" 
                :class="{ 'error': formErrors.grade }"
              >
                <option value="">请选择年级</option>
                <option value="2021级">2021级</option>
                <option value="2022级">2022级</option>
                <option value="2023级">2023级</option>
                <option value="2024级">2024级</option>
              </select>
              <span v-if="formErrors.grade" class="error-text">{{ formErrors.grade }}</span>
            </div>
            <div class="form-item">
              <label>班级 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.className" 
                class="form-input" 
                :class="{ 'error': formErrors.className }"
                placeholder="计算机2023级1班"
              />
              <span v-if="formErrors.className" class="error-text">{{ formErrors.className }}</span>
            </div>
            <div class="form-item">
              <label>辅导员姓名 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.counselorName" 
                class="form-input" 
                :class="{ 'error': formErrors.counselorName }"
                placeholder="请输入辅导员姓名"
              />
              <span v-if="formErrors.counselorName" class="error-text">{{ formErrors.counselorName }}</span>
            </div>
            <div class="form-item">
              <label>辅导员联系方式 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.counselorPhone" 
                class="form-input" 
                :class="{ 'error': formErrors.counselorPhone }"
                placeholder="13812345678"
              />
              <span v-if="formErrors.counselorPhone" class="error-text">{{ formErrors.counselorPhone }}</span>
            </div>
            <div class="form-item">
              <label>联系电话 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentMember.phone" 
                class="form-input" 
                :class="{ 'error': formErrors.phone }"
                placeholder="13812345678"
              />
              <span v-if="formErrors.phone" class="error-text">{{ formErrors.phone }}</span>
            </div>
            <div class="form-item">
              <label>邮箱 <span class="required">*</span></label>
              <input 
                type="email" 
                v-model="currentMember.email" 
                class="form-input" 
                :class="{ 'error': formErrors.email }"
                placeholder="example@stu.edu.cn"
              />
              <span v-if="formErrors.email" class="error-text">{{ formErrors.email }}</span>
            </div>
            <div class="form-item">
              <label>状态</label>
              <select v-model="currentMember.status" class="form-select">
                <option value="在职">在职</option>
                <option value="离职">离职</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditModal = false">取消</button>
          <button class="btn btn-primary" @click="editMember">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 批量导入模态框 -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal-content large-modal">
        <div class="modal-header">
          <h3>批量导入成员</h3>
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
                  <th>部门</th>
                  <th>职位</th>
                  <th>年级</th>
                  <th>班级</th>
                  <th>辅导员姓名</th>
                  <th>辅导员联系方式</th>
                  <th>联系电话</th>
                  <th>邮箱</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in importPreview" :key="item.row" :class="{ 'error-row': item.errors.length > 0 }">
                  <td>{{ item.row }}</td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.gender }}</td>
                  <td>{{ item.studentId }}</td>
                  <td>{{ item.department }}</td>
                  <td>{{ item.position }}</td>
                  <td>{{ item.grade }}</td>
                  <td>{{ item.className }}</td>
                  <td>{{ item.counselorName }}</td>
                  <td>{{ item.counselorPhone }}</td>
                  <td>{{ item.phone }}</td>
                  <td>{{ item.email }}</td>
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
    
    <!-- 成员详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-content detail-modal" v-if="detailMember">
        <div class="modal-header">
          <h3>成员详情</h3>
          <button class="close-btn" @click="showDetailModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-header">
            <span class="detail-avatar">{{ detailMember.avatar }}</span>
            <div class="detail-basic">
              <h2 class="detail-name">{{ detailMember.name }}</h2>
              <p class="detail-position">{{ detailMember.department }} · {{ detailMember.position }}</p>
              <span class="status-tag" :class="detailMember.status">{{ detailMember.status }}</span>
            </div>
          </div>
          <div class="detail-info">
            <div class="info-grid">
              <div class="info-item">
                <label>成员ID</label>
                <span>{{ detailMember.id }}</span>
              </div>
              <div class="info-item">
                <label>性别</label>
                <span>{{ detailMember.gender }}</span>
              </div>
              <div class="info-item">
                <label>学号</label>
                <span>{{ detailMember.studentId }}</span>
              </div>
              <div class="info-item">
                <label>角色</label>
                <span class="role-tag">{{ detailMember.role }}</span>
              </div>
              <div class="info-item">
                <label>年级</label>
                <span>{{ detailMember.grade }}</span>
              </div>
              <div class="info-item">
                <label>班级</label>
                <span>{{ detailMember.className }}</span>
              </div>
              <div class="info-item">
                <label>联系电话</label>
                <span>{{ detailMember.phone }}</span>
              </div>
              <div class="info-item">
                <label>邮箱</label>
                <span>{{ detailMember.email }}</span>
              </div>
              <div class="info-item">
                <label>辅导员姓名</label>
                <span>{{ detailMember.counselorName }}</span>
              </div>
              <div class="info-item">
                <label>辅导员电话</label>
                <span>{{ detailMember.counselorPhone }}</span>
              </div>
              <div class="info-item">
                <label>加入日期</label>
                <span>{{ detailMember.joinDate }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal = false">关闭</button>
          <button class="btn btn-primary" @click="openEditModal(detailMember); showDetailModal = false">编辑信息</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.members-page {
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

.department-select {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  background: #ffffff;
  color: #333333;
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

.members-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1200px;
}

.members-table th,
.members-table td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.members-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333333;
  font-size: 14px;
}

.members-table td {
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

.role-tag {
  padding: 4px 12px;
  background: #fff7e6;
  color: #fa8c16;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.detail-modal {
  width: 700px;
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

.detail-avatar {
  font-size: 64px;
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

.detail-position {
  font-size: 16px;
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
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
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

.members-table tbody tr:hover {
  background: #fafafa;
}

.avatar {
  font-size: 28px;
}

.dept-tag {
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

.status-tag.在职 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.离职 {
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

.departments-section {
  margin-top: 32px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 20px;
  font-family: 'Microsoft YaHei', sans-serif;
}

.departments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.dept-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dept-name {
  font-size: 14px;
  font-weight: 500;
  color: #333333;
}

.dept-count {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
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
  width: 900px;
  max-height: 90vh;
  overflow: hidden;
}

.large-modal {
  width: 1100px;
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
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
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

.form-input.error,
.form-select.error {
  border-color: #ff4d4f;
}

.error-text {
  font-size: 12px;
  color: #ff4d4f;
}

.radio-group {
  display: flex;
  gap: 20px;
  padding: 6px 0;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #333333;
}

.radio-item input[type="radio"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}

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

.table-scroll {
  overflow-x: auto;
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
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .form-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .modal-content {
    width: 95%;
  }
  
  .large-modal {
    width: 98%;
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
