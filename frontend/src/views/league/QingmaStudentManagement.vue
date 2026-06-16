<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import * as XLSX from 'xlsx';
import { hasPermission } from '../../utils/permission';

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 学员数据 - 初始为空,从API加载
const students = ref([]);

// 加载状态
const isLoading = ref(false);

// 从API加载学员数据
const fetchStudents = async () => {
  isLoading.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/qingma-students/`);
    if (response.ok) {
      const data = await response.json();
      if (data.results && data.results.length > 0) {
        students.value = data.results.map(s => ({
          id: s.id,
          name: s.name,
          gender: s.gender,
          studentId: s.student_id || '',
          qingmaClass: s.qingma_class || '',
          className: s.class_name || '',
          grade: s.grade || '',
          phone: s.phone || '',
          email: s.email || '',
          counselorName: s.counselor_name || '',
          counselorPhone: s.counselor_phone || '',
          status: s.status || '在读',
          avatar: '👤'
        }));
      } else if (Array.isArray(data) && data.length > 0) {
        students.value = data.map(s => ({
          id: s.id,
          name: s.name,
          gender: s.gender,
          studentId: s.student_id || '',
          qingmaClass: s.qingma_class || '',
          className: s.class_name || '',
          grade: s.grade || '',
          phone: s.phone || '',
          email: s.email || '',
          counselorName: s.counselor_name || '',
          counselorPhone: s.counselor_phone || '',
          status: s.status || '在读',
          avatar: '👤'
        }));
      } else {
        students.value = [];
      }
      filterStudents();
    } else {
      console.error('API请求失败:', response.status);
      showErrorMessage('无法连接到服务器,请检查后端服务是否运行');
    }
  } catch (error) {
    console.error('加载学员数据失败:', error);
    showErrorMessage('无法连接到服务器,请检查后端服务是否运行');
  } finally {
    isLoading.value = false;
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchStudents();
});

// 统计数据
const stats = computed(() => [
  { label: '学员总数', value: students.value.length },
  { label: '在读', value: students.value.filter(s => s.status === '在读').length },
  { label: '已结业', value: students.value.filter(s => s.status === '已结业').length },
  { label: '休学', value: students.value.filter(s => s.status === '休学').length }
]);

// 分页相关
const currentPage = ref(1);
const pageSize = 10;
const totalPages = computed(() => Math.ceil(filteredStudents.value.length / pageSize));

// 批量选择相关
const selectedStudentIds = ref([]);

// 是否全选
const isAllSelected = computed(() => {
  return paginatedStudents.value.length > 0 && 
         paginatedStudents.value.every(s => selectedStudentIds.value.includes(s.id));
});

// 切换全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    paginatedStudents.value.forEach(s => {
      const index = selectedStudentIds.value.indexOf(s.id);
      if (index !== -1) {
        selectedStudentIds.value.splice(index, 1);
      }
    });
  } else {
    paginatedStudents.value.forEach(s => {
      if (!selectedStudentIds.value.includes(s.id)) {
        selectedStudentIds.value.push(s.id);
      }
    });
  }
};

// 切换单个选择
const toggleSelect = (studentId, event) => {
  event.stopPropagation();
  const index = selectedStudentIds.value.indexOf(studentId);
  if (index === -1) {
    selectedStudentIds.value.push(studentId);
  } else {
    selectedStudentIds.value.splice(index, 1);
  }
};

// 批量删除
const deleteSelected = async () => {
  if (selectedStudentIds.value.length === 0) {
    showErrorMessage('请先选择要删除的学员');
    return;
  }
  
  if (confirm(`确定要删除选中的 ${selectedStudentIds.value.length} 名学员吗?`)) {
    isLoading.value = true;
    let successCount = 0;
    
    try {
      for (const id of selectedStudentIds.value) {
        const response = await fetch(`${API_BASE_URL}/qingma-students/${id}/`, {
          method: 'DELETE',
        });
        if (response.ok || response.status === 204) {
          successCount++;
          students.value = students.value.filter(s => s.id !== id);
        }
      }
      
      selectedStudentIds.value = [];
      filterStudents();
      showSuccessMessage(`成功删除 ${successCount} 名学员!`);
    } catch (error) {
      console.error('批量删除失败:', error);
      showErrorMessage('批量删除失败,请重试');
    } finally {
      isLoading.value = false;
    }
  }
};

// 当前页数据
const paginatedStudents = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredStudents.value.slice(start, end);
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
  qingmaClass: '全部',
  status: '全部'
});

// 青马班列表
const qingmaClasses = ['全部', '第28期青马班', '第27期青马班', '第29期青马班'];
const statuses = ['全部', '在读', '已结业', '休学'];

// 搜索
const searchQuery = ref('');

// 过滤学员
const filteredStudents = ref(students.value);

// 模态框控制
const showAddModal = ref(false);
const showEditModal = ref(false);
const showImportModal = ref(false);
const showDetailModal = ref(false);
const showSuccess = ref(false);
const showError = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

// 当前编辑的学员
const currentStudent = ref({
  id: null,
  name: '',
  gender: '',
  studentId: '',
  qingmaClass: '',
  className: '',
  grade: '',
  phone: '',
  email: '',
  counselorName: '',
  counselorPhone: '',
  status: '在读'
});

// 详情学员
const detailStudent = ref(null);

// 表单验证错误
const formErrors = ref({});

// 导入数据
const importedData = ref([]);
const importPreview = ref([]);
const importErrors = ref([]);

// 当前编辑的学员索引
const editingStudentId = ref(null);

// 过滤学员
const filterStudents = () => {
  filteredStudents.value = students.value.filter(s => {
    const matchQingmaClass = filters.value.qingmaClass === '全部' || s.qingmaClass === filters.value.qingmaClass;
    const matchStatus = filters.value.status === '全部' || s.status === filters.value.status;
    const matchSearch = !searchQuery.value || 
      s.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
      s.id.toString().includes(searchQuery.value) ||
      s.phone.includes(searchQuery.value) ||
      s.email.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (s.studentId && s.studentId.includes(searchQuery.value));
    return matchQingmaClass && matchStatus && matchSearch;
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
const viewDetail = (student) => {
  detailStudent.value = student;
  showDetailModal.value = true;
};

// 重置筛选
const resetFilters = () => {
  filters.value = {
    qingmaClass: '全部',
    status: '全部'
  };
  searchQuery.value = '';
  filterStudents();
};

// 验证表单
const validateForm = () => {
  const errors = {};
  
  if (!currentStudent.value.name || currentStudent.value.name.trim() === '') {
    errors.name = '请输入姓名';
  }
  
  if (!currentStudent.value.gender) {
    errors.gender = '请选择性别';
  }
  
  if (!currentStudent.value.studentId) {
    errors.studentId = '请输入学号';
  } else if (currentStudent.value.studentId.length < 10 || currentStudent.value.studentId.length > 20) {
    errors.studentId = '学号长度应为10-20个字符';
  }
  
  if (!currentStudent.value.qingmaClass) {
    errors.qingmaClass = '请选择青马班';
  }
  
  if (!currentStudent.value.className) {
    errors.className = '请输入班级';
  }
  
  if (!currentStudent.value.grade) {
    errors.grade = '请选择年级';
  }
  
  if (!currentStudent.value.phone) {
    errors.phone = '请输入联系方式';
  } else if (!/^1[3-9]\d{9}$/.test(currentStudent.value.phone)) {
    errors.phone = '请输入有效的手机号码';
  }
  
  if (!currentStudent.value.email) {
    errors.email = '请输入邮箱';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(currentStudent.value.email)) {
    errors.email = '请输入有效的邮箱地址';
  }
  
  if (!currentStudent.value.counselorName) {
    errors.counselorName = '请输入辅导员姓名';
  }
  
  if (!currentStudent.value.counselorPhone) {
    errors.counselorPhone = '请输入辅导员联系方式';
  } else if (!/^1[3-9]\d{9}$/.test(currentStudent.value.counselorPhone)) {
    errors.counselorPhone = '请输入有效的手机号码';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
};

// 打开添加模态框
const openAddModal = () => {
  currentStudent.value = {
    id: null,
    name: '',
    gender: '',
    studentId: '',
    qingmaClass: '',
    className: '',
    grade: '',
    phone: '',
    email: '',
    counselorName: '',
    counselorPhone: '',
    status: '在读'
  };
  formErrors.value = {};
  showAddModal.value = true;
};

// 打开编辑模态框
const openEditModal = (student) => {
  currentStudent.value = { ...student };
  editingStudentId.value = student.id;
  formErrors.value = {};
  showEditModal.value = true;
};

// 添加学员
const addStudent = async () => {
  if (!validateForm()) return;
  
  try {
    const apiData = {
      name: currentStudent.value.name,
      gender: currentStudent.value.gender,
      student_id: currentStudent.value.studentId,
      qingma_class: currentStudent.value.qingmaClass,
      class_name: currentStudent.value.className,
      grade: currentStudent.value.grade,
      phone: currentStudent.value.phone,
      email: currentStudent.value.email,
      counselor_name: currentStudent.value.counselorName,
      counselor_phone: currentStudent.value.counselorPhone,
      status: currentStudent.value.status
    };
    
    const response = await fetch(`${API_BASE_URL}/qingma-students/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const newStudent = await response.json();
      students.value.unshift({
        id: newStudent.id,
        name: newStudent.name,
        gender: newStudent.gender,
        studentId: newStudent.student_id || '',
        qingmaClass: newStudent.qingma_class || '',
        className: newStudent.class_name || '',
        grade: newStudent.grade || '',
        phone: newStudent.phone || '',
        email: newStudent.email || '',
        counselorName: newStudent.counselor_name || '',
        counselorPhone: newStudent.counselor_phone || '',
        status: newStudent.status || '在读',
        avatar: '👤'
      });
      
      showSuccessMessage('学员添加成功!');
      showAddModal.value = false;
      filterStudents();
    } else {
      const error = await response.json();
      showErrorMessage('添加失败:' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('添加学员失败:', error);
    showErrorMessage('网络错误,请稍后重试');
  }
};

// 编辑学员
const editStudent = async () => {
  if (!validateForm()) return;
  
  try {
    const apiData = {
      name: currentStudent.value.name,
      gender: currentStudent.value.gender,
      student_id: currentStudent.value.studentId,
      qingma_class: currentStudent.value.qingmaClass,
      class_name: currentStudent.value.className,
      grade: currentStudent.value.grade,
      phone: currentStudent.value.phone,
      email: currentStudent.value.email,
      counselor_name: currentStudent.value.counselorName,
      counselor_phone: currentStudent.value.counselorPhone,
      status: currentStudent.value.status
    };
    
    const response = await fetch(`${API_BASE_URL}/qingma-students/${editingStudentId.value}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const updatedStudent = await response.json();
      const index = students.value.findIndex(s => s.id === editingStudentId.value);
      if (index !== -1) {
        students.value[index] = {
          id: updatedStudent.id,
          name: updatedStudent.name,
          gender: updatedStudent.gender,
          studentId: updatedStudent.student_id || '',
          qingmaClass: updatedStudent.qingma_class || '',
          className: updatedStudent.class_name || '',
          grade: updatedStudent.grade || '',
          phone: updatedStudent.phone || '',
          email: updatedStudent.email || '',
          counselorName: updatedStudent.counselor_name || '',
          counselorPhone: updatedStudent.counselor_phone || '',
          status: updatedStudent.status || '在读',
          avatar: '👤'
        };
      }
      
      showSuccessMessage('学员信息更新成功!');
    } else {
      const error = await response.json();
      showErrorMessage('更新失败:' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('更新学员失败:', error);
    showErrorMessage('网络错误,请稍后重试');
  }
  
  showEditModal.value = false;
  filterStudents();
};

// 删除学员
const deleteStudent = async (student) => {
  if (confirm(`确定要删除学员「${student.name}」吗?`)) {
    try {
      const response = await fetch(`${API_BASE_URL}/qingma-students/${student.id}/`, {
        method: 'DELETE',
      });
      
      if (response.ok || response.status === 204) {
        students.value = students.value.filter(s => s.id !== student.id);
        showSuccessMessage('学员删除成功!');
        filterStudents();
      } else {
        showErrorMessage('删除失败');
      }
    } catch (error) {
      console.error('删除学员失败:', error);
      showErrorMessage('网络错误,请稍后重试');
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
    showErrorMessage('请上传Excel文件(.xlsx或.xls格式)');
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
      
      importErrors.value = [];
      importPreview.value = [];
      
      jsonData.forEach((row, index) => {
        const errors = [];
        
        if (!row['姓名']) errors.push('姓名不能为空');
        if (!row['性别']) errors.push('性别不能为空');
        if (!row['学号']) errors.push('学号不能为空');
        if (!row['青马班']) errors.push('青马班不能为空');
        if (!row['班级']) errors.push('班级不能为空');
        if (!row['年级']) errors.push('年级不能为空');
        if (!row['联系方式']) errors.push('联系方式不能为空');
        if (row['联系方式'] && !/^1[3-9]\d{9}$/.test(row['联系方式'])) errors.push('联系方式格式不正确');
        if (!row['邮箱']) errors.push('邮箱不能为空');
        if (row['邮箱'] && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(row['邮箱'])) errors.push('邮箱格式不正确');
        if (!row['辅导员姓名']) errors.push('辅导员姓名不能为空');
        if (!row['辅导员联系方式']) errors.push('辅导员联系方式不能为空');
        if (row['辅导员联系方式'] && !/^1[3-9]\d{9}$/.test(row['辅导员联系方式'])) errors.push('辅导员联系方式格式不正确');
        
        importPreview.value.push({
          row: index + 1,
          name: row['姓名'] || '',
          gender: row['性别'] || '',
          studentId: row['学号'] || '',
          qingmaClass: row['青马班'] || '',
          className: row['班级'] || '',
          grade: row['年级'] || '',
          phone: row['联系方式'] || '',
          email: row['邮箱'] || '',
          counselorName: row['辅导员姓名'] || '',
          counselorPhone: row['辅导员联系方式'] || '',
          status: row['状态'] || '在读',
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
      showErrorMessage('解析Excel文件失败,请检查文件格式');
      console.error(error);
    }
  };
  reader.readAsArrayBuffer(file);
};

// 确认导入
const confirmImport = async () => {
  if (importErrors.value.length > 0) {
    if (!confirm(`发现 ${importErrors.value.length} 条数据存在错误,是否继续导入有效数据?`)) {
      return;
    }
  }
  
  let successCount = 0;
  
  try {
    for (const item of importPreview.value) {
      if (item.errors.length === 0) {
        const apiData = {
          name: item.name,
          gender: item.gender,
          student_id: item.studentId,
          qingma_class: item.qingmaClass,
          class_name: item.className,
          grade: item.grade,
          phone: item.phone,
          email: item.email,
          counselor_name: item.counselorName,
          counselor_phone: item.counselorPhone,
          status: item.status
        };
        
        const response = await fetch(`${API_BASE_URL}/qingma-students/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(apiData)
        });
        
        if (response.ok) {
          const newStudent = await response.json();
          students.value.unshift({
            id: newStudent.id,
            name: newStudent.name,
            gender: newStudent.gender,
            studentId: newStudent.student_id || '',
            qingmaClass: newStudent.qingma_class || '',
            className: newStudent.class_name || '',
            grade: newStudent.grade || '',
            phone: newStudent.phone || '',
            email: newStudent.email || '',
            counselorName: newStudent.counselor_name || '',
            counselorPhone: newStudent.counselor_phone || '',
            status: newStudent.status || '在读',
            avatar: '👤'
          });
          successCount++;
        }
      }
    }
    
    showSuccessMessage(`成功导入 ${successCount} 名学员!`);
    showImportModal.value = false;
    filterStudents();
  } catch (error) {
    console.error('导入失败:', error);
    showErrorMessage('导入失败,请重试');
  }
};

// 导出Excel
const exportToExcel = () => {
  try {
    const exportData = filteredStudents.value.map(s => ({
      '姓名': s.name,
      '性别': s.gender,
      '学号': s.studentId,
      '青马班': s.qingmaClass,
      '班级': s.className,
      '年级': s.grade,
      '联系方式': s.phone,
      '邮箱': s.email,
      '辅导员姓名': s.counselorName,
      '辅导员联系方式': s.counselorPhone,
      '状态': s.status
    }));
    
    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '学员信息');
    
    const fileName = `青马班学员名单_${new Date().toISOString().split('T')[0]}.xlsx`;
    XLSX.writeFile(workbook, fileName);
    
    showSuccessMessage('数据导出成功!');
  } catch (error) {
    showErrorMessage('导出失败,请重试');
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
      '青马班': '第28期青马班',
      '班级': '计算机2023级1班',
      '年级': '2023级',
      '联系方式': '13912345678',
      '邮箱': 'zhangsan@edu.cn',
      '辅导员姓名': '王老师',
      '辅导员联系方式': '13800138001',
      '状态': '在读'
    }
  ];
  
  const worksheet = XLSX.utils.json_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '模板');
  
  const fileName = '青马班学员导入模板.xlsx';
  XLSX.writeFile(workbook, fileName);
};
</script>

<template>
  <div class="students-page">
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
      <h1>青马班学员管理</h1>
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
        <label>青马班:</label>
        <select v-model="filters.qingmaClass" @change="filterStudents" class="filter-select" :class="{ active: filters.qingmaClass !== '全部' }">
          <option v-for="c in qingmaClasses" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>状态:</label>
        <select v-model="filters.status" @change="filterStudents" class="filter-select" :class="{ active: filters.status !== '全部' }">
          <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div class="filter-group search-group">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索姓名、ID、电话、邮箱..." 
          class="search-input"
          @input="filterStudents"
        />
      </div>
      <button v-if="filters.qingmaClass !== '全部' || filters.status !== '全部' || searchQuery" class="btn btn-text" @click="resetFilters">重置筛选</button>
    </div>
    
    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="result-count">共 {{ filteredStudents.length }} 条结果</span>
        <span v-if="selectedStudentIds.length > 0" class="selected-count">已选择 {{ selectedStudentIds.length }} 条</span>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedStudentIds.length > 0 && hasPermission('league:delete')" class="btn btn-danger" @click="deleteSelected">批量删除</button>
        <button v-if="hasPermission('league:edit')" class="btn btn-secondary" @click="downloadTemplate">下载模板</button>
        <label v-if="hasPermission('league:edit')" class="btn btn-secondary upload-btn">
          <span>批量导入</span>
          <input type="file" accept=".xlsx,.xls" @change="handleFileUpload" style="display: none;">
        </label>
        <button v-if="hasPermission('league:edit')" class="btn btn-secondary" @click="exportToExcel">导出数据</button>
        <button v-if="hasPermission('league:add')" class="btn btn-primary" @click="openAddModal">添加学员</button>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    
    <div class="table-container">
      <div class="table-scroll">
        <table class="students-table">
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
              <th>青马班</th>
              <th>班级</th>
              <th>年级</th>
              <th>联系方式</th>
              <th>邮箱</th>
              <th>辅导员</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in paginatedStudents" :key="student.id" @click="viewDetail(student)" class="clickable-row" :class="{ selected: selectedStudentIds.includes(student.id) }">
              <td @click.stop>
                <label class="checkbox-label">
                  <input type="checkbox" :checked="selectedStudentIds.includes(student.id)" @change="toggleSelect(student.id, $event)" />
                </label>
              </td>
              <td>{{ student.id }}</td>
              <td><span class="avatar">{{ student.avatar }}</span></td>
              <td>{{ student.name }}</td>
              <td>{{ student.gender }}</td>
              <td>{{ student.studentId }}</td>
              <td><span class="qingma-tag">{{ student.qingmaClass }}</span></td>
              <td>{{ student.className }}</td>
              <td>{{ student.grade }}</td>
              <td>{{ student.phone }}</td>
              <td>{{ student.email }}</td>
              <td>{{ student.counselorName }}</td>
              <td><span class="status-tag" :class="student.status">{{ student.status }}</span></td>
              <td @click.stop>
                <button v-if="hasPermission('league:edit')" class="action-btn edit" @click="openEditModal(student)">编辑</button>
                <button v-if="hasPermission('league:delete')" class="action-btn delete" @click="deleteStudent(student)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 分页 -->
    <div v-if="totalPages > 0" class="pagination">
      <div class="pagination-info">
        第 {{ currentPage }} / {{ totalPages }} 页,共 {{ filteredStudents.length }} 条记录
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
    
    <!-- 添加学员模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加学员</h3>
          <button class="close-btn" @click="showAddModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>姓名 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.name" 
                class="form-input" 
                :class="{ 'error': formErrors.name }"
              />
              <span v-if="formErrors.name" class="error-text">{{ formErrors.name }}</span>
            </div>
            <div class="form-item">
              <label>性别 <span class="required">*</span></label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="currentStudent.gender" value="男" />
                  <span>男</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="currentStudent.gender" value="女" />
                  <span>女</span>
                </label>
              </div>
              <span v-if="formErrors.gender" class="error-text">{{ formErrors.gender }}</span>
            </div>
            <div class="form-item">
              <label>学号 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.studentId" 
                class="form-input" 
                :class="{ 'error': formErrors.studentId }"
                placeholder="请输入学号(10-20位)"
                maxlength="20"
              />
              <span v-if="formErrors.studentId" class="error-text">{{ formErrors.studentId }}</span>
            </div>
            <div class="form-item">
              <label>青马班 <span class="required">*</span></label>
              <select 
                v-model="currentStudent.qingmaClass" 
                class="form-select" 
                :class="{ 'error': formErrors.qingmaClass }"
              >
                <option value="">请选择青马班</option>
                <option v-for="c in qingmaClasses.slice(1)" :key="c" :value="c">{{ c }}</option>
              </select>
              <span v-if="formErrors.qingmaClass" class="error-text">{{ formErrors.qingmaClass }}</span>
            </div>
            <div class="form-item">
              <label>班级 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.className" 
                class="form-input" 
                :class="{ 'error': formErrors.className }"
                placeholder="计算机2023级1班"
              />
              <span v-if="formErrors.className" class="error-text">{{ formErrors.className }}</span>
            </div>
            <div class="form-item">
              <label>年级 <span class="required">*</span></label>
              <select 
                v-model="currentStudent.grade" 
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
              <label>联系方式 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.phone" 
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
                v-model="currentStudent.email" 
                class="form-input" 
                :class="{ 'error': formErrors.email }"
                placeholder="example@edu.cn"
              />
              <span v-if="formErrors.email" class="error-text">{{ formErrors.email }}</span>
            </div>
            <div class="form-item">
              <label>辅导员姓名 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.counselorName" 
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
                v-model="currentStudent.counselorPhone" 
                class="form-input" 
                :class="{ 'error': formErrors.counselorPhone }"
                placeholder="13812345678"
              />
              <span v-if="formErrors.counselorPhone" class="error-text">{{ formErrors.counselorPhone }}</span>
            </div>
            <div class="form-item">
              <label>状态</label>
              <select v-model="currentStudent.status" class="form-select">
                <option value="在读">在读</option>
                <option value="已结业">已结业</option>
                <option value="休学">休学</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="addStudent">添加</button>
        </div>
      </div>
    </div>
    
    <!-- 编辑学员模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑学员</h3>
          <button class="close-btn" @click="showEditModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>姓名 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.name" 
                class="form-input" 
                :class="{ 'error': formErrors.name }"
              />
              <span v-if="formErrors.name" class="error-text">{{ formErrors.name }}</span>
            </div>
            <div class="form-item">
              <label>性别 <span class="required">*</span></label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="currentStudent.gender" value="男" />
                  <span>男</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="currentStudent.gender" value="女" />
                  <span>女</span>
                </label>
              </div>
              <span v-if="formErrors.gender" class="error-text">{{ formErrors.gender }}</span>
            </div>
            <div class="form-item">
              <label>学号 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.studentId" 
                class="form-input" 
                :class="{ 'error': formErrors.studentId }"
                placeholder="请输入学号(10-20位)"
                maxlength="20"
              />
              <span v-if="formErrors.studentId" class="error-text">{{ formErrors.studentId }}</span>
            </div>
            <div class="form-item">
              <label>青马班 <span class="required">*</span></label>
              <select 
                v-model="currentStudent.qingmaClass" 
                class="form-select" 
                :class="{ 'error': formErrors.qingmaClass }"
              >
                <option value="">请选择青马班</option>
                <option v-for="c in qingmaClasses.slice(1)" :key="c" :value="c">{{ c }}</option>
              </select>
              <span v-if="formErrors.qingmaClass" class="error-text">{{ formErrors.qingmaClass }}</span>
            </div>
            <div class="form-item">
              <label>班级 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.className" 
                class="form-input" 
                :class="{ 'error': formErrors.className }"
                placeholder="计算机2023级1班"
              />
              <span v-if="formErrors.className" class="error-text">{{ formErrors.className }}</span>
            </div>
            <div class="form-item">
              <label>年级 <span class="required">*</span></label>
              <select 
                v-model="currentStudent.grade" 
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
              <label>联系方式 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.phone" 
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
                v-model="currentStudent.email" 
                class="form-input" 
                :class="{ 'error': formErrors.email }"
                placeholder="example@edu.cn"
              />
              <span v-if="formErrors.email" class="error-text">{{ formErrors.email }}</span>
            </div>
            <div class="form-item">
              <label>辅导员姓名 <span class="required">*</span></label>
              <input 
                type="text" 
                v-model="currentStudent.counselorName" 
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
                v-model="currentStudent.counselorPhone" 
                class="form-input" 
                :class="{ 'error': formErrors.counselorPhone }"
                placeholder="13812345678"
              />
              <span v-if="formErrors.counselorPhone" class="error-text">{{ formErrors.counselorPhone }}</span>
            </div>
            <div class="form-item">
              <label>状态</label>
              <select v-model="currentStudent.status" class="form-select">
                <option value="在读">在读</option>
                <option value="已结业">已结业</option>
                <option value="休学">休学</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditModal = false">取消</button>
          <button class="btn btn-primary" @click="editStudent">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 批量导入模态框 -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal-content large-modal">
        <div class="modal-header">
          <h3>批量导入学员</h3>
          <button class="close-btn" @click="showImportModal = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="importErrors.length > 0" class="error-summary">
            <strong>⚠️ 发现 {{ importErrors.length }} 条数据错误:</strong>
            <ul>
              <li v-for="err in importErrors" :key="err.row">
                第 {{ err.row }} 行:{{ err.errors.join(';') }}
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
                  <th>青马班</th>
                  <th>班级</th>
                  <th>年级</th>
                  <th>联系方式</th>
                  <th>邮箱</th>
                  <th>辅导员姓名</th>
                  <th>辅导员联系方式</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in importPreview" :key="item.row" :class="{ 'error-row': item.errors.length > 0 }">
                  <td>{{ item.row }}</td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.gender }}</td>
                  <td>{{ item.studentId }}</td>
                  <td>{{ item.qingmaClass }}</td>
                  <td>{{ item.className }}</td>
                  <td>{{ item.grade }}</td>
                  <td>{{ item.phone }}</td>
                  <td>{{ item.email }}</td>
                  <td>{{ item.counselorName }}</td>
                  <td>{{ item.counselorPhone }}</td>
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
    
    <!-- 学员详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-content detail-modal" v-if="detailStudent">
        <div class="modal-header">
          <h3>学员详情</h3>
          <button class="close-btn" @click="showDetailModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-header">
            <span class="detail-avatar">{{ detailStudent.avatar }}</span>
            <div class="detail-basic">
              <h2 class="detail-name">{{ detailStudent.name }}</h2>
              <p class="detail-position">{{ detailStudent.qingmaClass }} · {{ detailStudent.className }}</p>
              <span class="status-tag" :class="detailStudent.status">{{ detailStudent.status }}</span>
            </div>
          </div>
          <div class="detail-info">
            <div class="info-grid">
              <div class="info-item">
                <label>学员ID</label>
                <span>{{ detailStudent.id }}</span>
              </div>
              <div class="info-item">
                <label>性别</label>
                <span>{{ detailStudent.gender }}</span>
              </div>
              <div class="info-item">
                <label>学号</label>
                <span>{{ detailStudent.studentId }}</span>
              </div>
              <div class="info-item">
                <label>青马班</label>
                <span class="qingma-tag">{{ detailStudent.qingmaClass }}</span>
              </div>
              <div class="info-item">
                <label>年级</label>
                <span>{{ detailStudent.grade }}</span>
              </div>
              <div class="info-item">
                <label>班级</label>
                <span>{{ detailStudent.className }}</span>
              </div>
              <div class="info-item">
                <label>联系方式</label>
                <span>{{ detailStudent.phone }}</span>
              </div>
              <div class="info-item">
                <label>邮箱</label>
                <span>{{ detailStudent.email }}</span>
              </div>
              <div class="info-item">
                <label>辅导员姓名</label>
                <span>{{ detailStudent.counselorName }}</span>
              </div>
              <div class="info-item">
                <label>辅导员电话</label>
                <span>{{ detailStudent.counselorPhone }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal = false">关闭</button>
          <button class="btn btn-primary" @click="openEditModal(detailStudent); showDetailModal = false">编辑信息</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.students-page {
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

.students-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1400px;
}

.students-table th,
.students-table td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.students-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333333;
  font-size: 14px;
}

.students-table td {
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

.qingma-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
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

.students-table tbody tr:hover {
  background: #fafafa;
}

.avatar {
  font-size: 28px;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.在读 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.已结业 {
  background: #e6f7ff;
  color: #1890ff;
}

.status-tag.休学 {
  background: #fff7e6;
  color: #fa8c16;
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
  
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>