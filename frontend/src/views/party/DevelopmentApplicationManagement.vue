<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import * as XLSX from 'xlsx';
import { hasPermission } from '../../utils/permission';
import { getDictionaryNames } from '../../utils/dictionary';

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 申请数据
const applications = ref([]);

// 加载状态
const isLoading = ref(false);

// 从API加载申请数据
const fetchApplications = async () => {
  isLoading.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/development-applications/`);
    if (response.ok) {
      const data = await response.json();
      if (data.results && data.results.length > 0) {
        applications.value = data.results.map(item => ({
          id: item.id,
          name: item.name,
          gender: item.gender,
          ethnicity: item.ethnicity,
          birthDate: item.birth_date,
          education: item.education,
          organization: item.organization,
          phone: item.phone,
          studentId: item.student_id || '',
          grade: item.grade || '',
          department: item.department || '',
          currentStage: item.current_stage,
          approvalStatus: item.application_status,
          applicationDate: item.application_date,
          notes: item.notes || ''
        }));
      } else if (Array.isArray(data) && data.length > 0) {
        applications.value = data.map(item => ({
          id: item.id,
          name: item.name,
          gender: item.gender,
          ethnicity: item.ethnicity,
          birthDate: item.birth_date,
          education: item.education,
          organization: item.organization,
          phone: item.phone,
          studentId: item.student_id || '',
          grade: item.grade || '',
          department: item.department || '',
          currentStage: item.current_stage,
          approvalStatus: item.application_status,
          applicationDate: item.application_date,
          notes: item.notes || ''
        }));
      } else {
        applications.value = [];
      }
      filterApplications();
    } else {
      console.error('API请求失败:', response.status);
      showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
    }
  } catch (error) {
    console.error('加载申请数据失败:', error);
    showErrorMessage('无法连接到服务器，请检查后端服务是否运行');
  } finally {
    isLoading.value = false;
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchApplications();
  loadDictionaryOptions();
});

// 统计数据
const stats = computed(() => {
  const total = applications.value.length;
  const pending = applications.value.filter(a => a.approvalStatus === '待审批').length;
  const approved = applications.value.filter(a => a.approvalStatus === '已通过').length;
  const rejected = applications.value.filter(a => a.approvalStatus === '已拒绝').length;

  return [
    { label: '申请总数', value: total, icon: '📋' },
    { label: '待审批', value: pending, icon: '⏳' },
    { label: '已通过', value: approved, icon: '✓' },
    { label: '已拒绝', value: rejected, icon: '✕' }
  ];
});

// 分页相关
const currentPage = ref(1);
const pageSize = 10;
const totalPages = computed(() => Math.ceil(filteredApplications.value.length / pageSize));

// 批量选择相关
const selectedIds = ref([]);

// 是否全选
const isAllSelected = computed(() => {
  return paginatedApplications.value.length > 0 &&
    paginatedApplications.value.every(a => selectedIds.value.includes(a.id));
});

// 切换全选
const toggleSelectAll = () => {
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
};

// 切换单个选择
const toggleSelect = (appId, event) => {
  event.stopPropagation();
  const index = selectedIds.value.indexOf(appId);
  if (index === -1) {
    selectedIds.value.push(appId);
  } else {
    selectedIds.value.splice(index, 1);
  }
};

// 批量删除
const deleteSelected = async () => {
  if (selectedIds.value.length === 0) {
    showErrorMessage('请先选择要删除的申请');
    return;
  }

  if (confirm(`确定要删除选中的 ${selectedIds.value.length} 条申请吗？`)) {
    isLoading.value = true;
    let successCount = 0;

    try {
      for (const id of selectedIds.value) {
        const response = await fetch(`${API_BASE_URL}/development-applications/${id}/`, {
          method: 'DELETE',
        });
        if (response.ok || response.status === 204) {
          successCount++;
          applications.value = applications.value.filter(a => a.id !== id);
        }
      }

      selectedIds.value = [];
      filterApplications();
      showSuccessMessage(`成功删除 ${successCount} 条申请！`);
    } catch (error) {
      console.error('批量删除失败:', error);
      showErrorMessage('批量删除失败，请重试');
    } finally {
      isLoading.value = false;
    }
  }
};

// 批量审批
const batchApprove = async () => {
  if (selectedIds.value.length === 0) {
    showErrorMessage('请先选择要审批的申请');
    return;
  }

  const pendingIds = selectedIds.value.filter(id => {
    const app = applications.value.find(a => a.id === id);
    return app && app.approvalStatus === '待审批';
  });

  if (pendingIds.length === 0) {
    showErrorMessage('选中的申请中没有待审批状态的申请');
    return;
  }

  if (confirm(`确定要通过选中的 ${pendingIds.length} 条待审批申请吗？`)) {
    isLoading.value = true;
    let successCount = 0;

    try {
      for (const id of pendingIds) {
        const response = await fetch(`${API_BASE_URL}/development-applications/${id}/advance_stage/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({})
        });
        if (response.ok) {
          successCount++;
          const data = await response.json();
          const index = applications.value.findIndex(a => a.id === id);
          if (index !== -1) {
            applications.value[index].currentStage = data.current_stage;
            applications.value[index].approvalStatus = '待审批';
          }
        }
      }

      selectedIds.value = [];
      filterApplications();
      showSuccessMessage(`成功通过 ${successCount} 条申请！已进入下一阶段`);
    } catch (error) {
      console.error('批量审批失败:', error);
      showErrorMessage('批量审批失败，请重试');
    } finally {
      isLoading.value = false;
    }
  }
};

// 当前页数据
const paginatedApplications = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredApplications.value.slice(start, end);
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
  currentStage: '全部',
  approvalStatus: '全部'
});

// 当前阶段列表
const stages = ['全部', '入党申请', '积极分子', '发展对象', '预备党员', '正式党员'];

// 审批状态列表
const approvalStatuses = ['全部', '待审批', '已通过', '已拒绝', '已完成'];

// 搜索
const searchQuery = ref('');

// 过滤后的申请
const filteredApplications = ref([]);

// 模态框控制
const showAddModal = ref(false);
const showEditModal = ref(false);
const showDetailModal = ref(false);
const showApprovalModal = ref(false);
const showSuccess = ref(false);
const showError = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

// 当前编辑的申请
const currentApplication = ref({
  id: null,
  name: '',
  gender: '',
  ethnicity: '汉族',
  birthDate: '',
  education: '本科',
  organization: '',
  phone: '',
  studentId: '',
  grade: '',
  department: '',
  currentStage: '入党申请',
  approvalStatus: '待审批',
  applicationDate: new Date().toISOString().split('T')[0],
  notes: ''
});

// 详情申请
const detailApplication = ref(null);

// 审批申请
const approvalApplication = ref(null);
const approvalReason = ref('');

// 表单验证错误
const formErrors = ref({});

// 当前编辑的申请ID
const editingId = ref(null);

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

// 年级列表
const grades = ['2021级', '2022级', '2023级', '2024级', '2025级'];

// 过滤申请
const filterApplications = () => {
  filteredApplications.value = applications.value.filter(a => {
    const matchStage = filters.value.currentStage === '全部' || a.currentStage === filters.value.currentStage;
    const matchStatus = filters.value.approvalStatus === '全部' || a.approvalStatus === filters.value.approvalStatus;
    const matchSearch = !searchQuery.value ||
      a.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      a.id.toString().includes(searchQuery.value) ||
      a.phone.includes(searchQuery.value) ||
      (a.studentId && a.studentId.includes(searchQuery.value)) ||
      (a.department && a.department.toLowerCase().includes(searchQuery.value.toLowerCase()));
    return matchStage && matchStatus && matchSearch;
  });
  currentPage.value = 1;
  scrollToTop();
};

// 获取阶段索引
const getStageIndex = (stage) => {
  return stages.slice(1).indexOf(stage);
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
const viewDetail = (application) => {
  detailApplication.value = application;
  showDetailModal.value = true;
};

// 重置筛选
const resetFilters = () => {
  filters.value = {
    currentStage: '全部',
    approvalStatus: '全部'
  };
  searchQuery.value = '';
  filterApplications();
};

// 验证表单
const validateForm = () => {
  const errors = {};

  if (!currentApplication.value.name || currentApplication.value.name.trim() === '') {
    errors.name = '请输入姓名';
  }

  if (!currentApplication.value.gender) {
    errors.gender = '请选择性别';
  }

  if (!currentApplication.value.ethnicity) {
    errors.ethnicity = '请选择民族';
  }

  if (!currentApplication.value.birthDate) {
    errors.birthDate = '请选择出生日期';
  }

  if (!currentApplication.value.education) {
    errors.education = '请选择学历';
  }

  if (!currentApplication.value.organization) {
    errors.organization = '请选择所属党组织';
  }

  if (!currentApplication.value.phone) {
    errors.phone = '请输入联系电话';
  } else if (!/^1[3-9]\d{9}$/.test(currentApplication.value.phone)) {
    errors.phone = '请输入有效的手机号码';
  }

  if (!currentApplication.value.currentStage) {
    errors.currentStage = '请选择当前阶段';
  }

  if (!currentApplication.value.applicationDate) {
    errors.applicationDate = '请选择申请日期';
  }

  formErrors.value = errors;
  return Object.keys(errors).length === 0;
};

// 打开添加模态框
const openAddModal = () => {
  currentApplication.value = {
    id: null,
    name: '',
    gender: '',
    ethnicity: '汉族',
    birthDate: '',
    education: '本科',
    organization: '',
    phone: '',
    studentId: '',
    grade: '',
    department: '',
    currentStage: '入党申请',
    approvalStatus: '待审批',
    applicationDate: new Date().toISOString().split('T')[0],
    notes: ''
  };
  formErrors.value = {};
  showAddModal.value = true;
};

// 打开编辑模态框
const openEditModal = (application) => {
  currentApplication.value = { ...application };
  editingId.value = application.id;
  formErrors.value = {};
  showEditModal.value = true;
};

// 打开审批模态框
const openApprovalModal = (application, action) => {
  approvalApplication.value = { ...application, action };
  approvalReason.value = '';
  showApprovalModal.value = true;
};

// 添加申请
const addApplication = async () => {
  if (!validateForm()) return;

  try {
    const apiData = {
      name: currentApplication.value.name,
      gender: currentApplication.value.gender,
      ethnicity: currentApplication.value.ethnicity,
      birth_date: currentApplication.value.birthDate,
      education: currentApplication.value.education,
      organization: currentApplication.value.organization,
      phone: currentApplication.value.phone,
      student_id: currentApplication.value.studentId || '',
      grade: currentApplication.value.grade || '',
      department: currentApplication.value.department || '',
      current_stage: currentApplication.value.currentStage,
      approval_status: currentApplication.value.approvalStatus,
      application_date: currentApplication.value.applicationDate,
      notes: currentApplication.value.notes || ''
    };

    const response = await fetch(`${API_BASE_URL}/development-applications/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(apiData)
    });

    if (response.ok) {
      const newItem = await response.json();
      applications.value.unshift({
        id: newItem.id,
        name: newItem.name,
        gender: newItem.gender,
        ethnicity: newItem.ethnicity,
        birthDate: newItem.birth_date,
        education: newItem.education,
        organization: newItem.organization,
        phone: newItem.phone,
        studentId: newItem.student_id || '',
        grade: newItem.grade || '',
        department: newItem.department || '',
        currentStage: newItem.current_stage,
        approvalStatus: newItem.approval_status,
        applicationDate: newItem.application_date,
        notes: newItem.notes || ''
      });

      showSuccessMessage('申请添加成功！');
      showAddModal.value = false;
      filterApplications();
    } else {
      const error = await response.json();
      showErrorMessage('添加失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('添加申请失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }
};

// 编辑申请
const editApplication = async () => {
  if (!validateForm()) return;

  try {
    const apiData = {
      name: currentApplication.value.name,
      gender: currentApplication.value.gender,
      ethnicity: currentApplication.value.ethnicity,
      birth_date: currentApplication.value.birthDate,
      education: currentApplication.value.education,
      organization: currentApplication.value.organization,
      phone: currentApplication.value.phone,
      student_id: currentApplication.value.studentId || '',
      grade: currentApplication.value.grade || '',
      department: currentApplication.value.department || '',
      current_stage: currentApplication.value.currentStage,
      approval_status: currentApplication.value.approvalStatus,
      application_date: currentApplication.value.applicationDate,
      notes: currentApplication.value.notes || ''
    };

    const response = await fetch(`${API_BASE_URL}/development-applications/${editingId.value}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(apiData)
    });

    if (response.ok) {
      const updatedItem = await response.json();
      const index = applications.value.findIndex(a => a.id === editingId.value);
      if (index !== -1) {
        applications.value[index] = {
          id: updatedItem.id,
          name: updatedItem.name,
          gender: updatedItem.gender,
          ethnicity: updatedItem.ethnicity,
          birthDate: updatedItem.birth_date,
          education: updatedItem.education,
          organization: updatedItem.organization,
          phone: updatedItem.phone,
          studentId: updatedItem.student_id || '',
          grade: updatedItem.grade || '',
          department: updatedItem.department || '',
          currentStage: updatedItem.current_stage,
          approvalStatus: updatedItem.approval_status,
          applicationDate: updatedItem.application_date,
          notes: updatedItem.notes || ''
        };
      }

      showSuccessMessage('申请信息更新成功！');
    } else {
      const error = await response.json();
      showErrorMessage('更新失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('更新申请失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  }

  showEditModal.value = false;
  filterApplications();
};

// 审批申请
const processApproval = async () => {
  if (!approvalApplication.value) return;

  isLoading.value = true;
  try {
    const action = approvalApplication.value.action;
    const endpoint = action === 'approve' ? 'approve' : 'reject';
    const response = await fetch(`${API_BASE_URL}/development-applications/${approvalApplication.value.id}/${endpoint}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        reason: approvalReason.value || ''
      })
    });

    if (response.ok) {
      const data = await response.json();
      const index = applications.value.findIndex(a => a.id === approvalApplication.value.id);
      if (index !== -1) {
        if (action === 'approve') {
          applications.value[index].approvalStatus = '已通过';
        } else {
          applications.value[index].approvalStatus = '已拒绝';
        }
        if (approvalReason.value) {
          applications.value[index].notes = approvalReason.value;
        }
      }

      if (action === 'approve') {
        await advanceStage(approvalApplication.value.id);
        showSuccessMessage('审批已通过！申请已进入下一阶段');
      } else {
        showSuccessMessage('审批已拒绝！');
      }
      showApprovalModal.value = false;
      filterApplications();
    } else {
      const error = await response.json();
      showErrorMessage('审批失败：' + JSON.stringify(error));
    }
  } catch (error) {
    console.error('审批失败:', error);
    showErrorMessage('网络错误，请稍后重试');
  } finally {
    isLoading.value = false;
  }
};

// 推进到下一阶段
const advanceStage = async (id) => {
  try {
    const response = await fetch(`${API_BASE_URL}/development-applications/${id}/advance_stage/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    });

    if (response.ok) {
      const data = await response.json();
      const index = applications.value.findIndex(a => a.id === id);
      if (index !== -1) {
        applications.value[index].currentStage = data.current_stage;
        applications.value[index].approvalStatus = '待审批';
      }
    }
  } catch (error) {
    console.error('推进阶段失败:', error);
  }
};

// 删除申请
const deleteApplication = async (application) => {
  if (confirm(`确定要删除申请「${application.name}」吗？`)) {
    try {
      const response = await fetch(`${API_BASE_URL}/development-applications/${application.id}/`, {
        method: 'DELETE',
      });

      if (response.ok || response.status === 204) {
        applications.value = applications.value.filter(a => a.id !== application.id);
        showSuccessMessage('申请删除成功！');
        filterApplications();
      } else {
        showErrorMessage('删除失败');
      }
    } catch (error) {
      console.error('删除申请失败:', error);
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

// 导出Excel
const exportToExcel = () => {
  try {
    const exportData = filteredApplications.value.map(a => ({
      '姓名': a.name,
      '性别': a.gender,
      '民族': a.ethnicity,
      '出生日期': a.birthDate,
      '学历': a.education,
      '所属党组织': a.organization,
      '联系电话': a.phone,
      '学号': a.studentId || '-',
      '年级': a.grade || '-',
      '学院': a.department || '-',
      '当前阶段': a.currentStage,
      '审批状态': a.approvalStatus,
      '申请日期': a.applicationDate,
      '备注': a.notes || '-'
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '党员发展申请');

    worksheet['!cols'] = [
      { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 },
      { wch: 18 }, { wch: 13 }, { wch: 12 }, { wch: 10 }, { wch: 15 },
      { wch: 12 }, { wch: 10 }, { wch: 12 }, { wch: 20 }
    ];

    const fileName = `党员发展申请数据_${new Date().toISOString().split('T')[0]}.xlsx`;
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
      '民族': '汉族',
      '出生日期': '2002-05-15',
      '学历': '本科',
      '所属党组织': '计算机学院党支部',
      '联系电话': '13912345678',
      '学号': '2021001001',
      '年级': '2021级',
      '学院': '计算机学院',
      '当前阶段': '入党申请',
      '审批状态': '待审批',
      '申请日期': '2024-09-01'
    }
  ];

  const worksheet = XLSX.utils.json_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '模板');

  worksheet['!cols'] = [
    { wch: 10 }, { wch: 6 }, { wch: 8 }, { wch: 12 }, { wch: 8 },
    { wch: 18 }, { wch: 13 }, { wch: 12 }, { wch: 10 }, { wch: 15 },
    { wch: 12 }, { wch: 10 }, { wch: 12 }
  ];

  const fileName = '党员发展申请导入模板.xlsx';
  XLSX.writeFile(workbook, fileName);
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
  reader.onload = async (e) => {
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

      let successCount = 0;
      let errorCount = 0;

      for (const row of jsonData) {
        try {
          const apiData = {
            name: row['姓名'] || '',
            gender: row['性别'] || '',
            ethnicity: row['民族'] || '汉族',
            birth_date: row['出生日期'] || '',
            education: row['学历'] || '本科',
            organization: row['所属党组织'] || '',
            phone: row['联系电话'] || '',
            student_id: row['学号'] || '',
            grade: row['年级'] || '',
            department: row['学院'] || '',
            current_stage: row['当前阶段'] || '入党申请',
            approval_status: row['审批状态'] || '待审批',
            application_date: row['申请日期'] || new Date().toISOString().split('T')[0],
            notes: ''
          };

          // 必填字段验证
          if (!apiData.name || !apiData.gender || !apiData.organization || !apiData.phone) {
            errorCount++;
            continue;
          }

          // 手机号验证
          if (!/^1[3-9]\d{9}$/.test(apiData.phone)) {
            errorCount++;
            continue;
          }

          const response = await fetch(`${API_BASE_URL}/development-applications/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiData)
          });

          if (response.ok) {
            successCount++;
          } else {
            errorCount++;
          }
        } catch (error) {
          errorCount++;
        }
      }

      if (successCount > 0) {
        await fetchApplications();
      }

      showSuccessMessage(`导入完成！成功：${successCount}条，失败：${errorCount}条`);
    } catch (error) {
      showErrorMessage('解析Excel文件失败，请检查文件格式');
      console.error(error);
    }
  };
  reader.readAsArrayBuffer(file);
  event.target.value = '';
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
      <h1>党员发展申请管理</h1>
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
      <div class="filter-group">
        <label>当前阶段：</label>
        <select v-model="filters.currentStage" @change="filterApplications" class="filter-select" :class="{ active: filters.currentStage !== '全部' }">
          <option v-for="stage in stages" :key="stage" :value="stage">{{ stage }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>审批状态：</label>
        <select v-model="filters.approvalStatus" @change="filterApplications" class="filter-select" :class="{ active: filters.approvalStatus !== '全部' }">
          <option v-for="status in approvalStatuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </div>
      <div class="filter-group search-group">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索姓名、学号、电话..."
          class="search-input"
          @input="filterApplications"
        />
      </div>
      <button v-if="filters.currentStage !== '全部' || filters.approvalStatus !== '全部' || searchQuery" class="btn btn-text" @click="resetFilters">重置筛选</button>
    </div>

    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="result-count">共 {{ filteredApplications.length }} 条结果</span>
        <span v-if="selectedIds.length > 0" class="selected-count">已选择 {{ selectedIds.length }} 条</span>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedIds.length > 0 && hasPermission('party:delete')" class="btn btn-danger" @click="deleteSelected">批量删除</button>
        <button v-if="selectedIds.length > 0 && hasPermission('party:edit')" class="btn btn-success" @click="batchApprove">批量通过</button>
        <button v-if="hasPermission('party:edit')" class="btn btn-secondary" @click="downloadTemplate">下载模板</button>
        <label v-if="hasPermission('party:edit')" class="btn btn-secondary upload-btn">
          <span>批量导入</span>
          <input type="file" accept=".xlsx,.xls" @change="handleFileUpload" style="display: none;">
        </label>
        <button v-if="hasPermission('party:edit')" class="btn btn-secondary" @click="exportToExcel">导出数据</button>
        <button v-if="hasPermission('party:add')" class="btn btn-primary" @click="openAddModal">新增申请</button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

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
              <th>姓名</th>
              <th>性别</th>
              <th>民族</th>
              <th>学历</th>
              <th>所属党组织</th>
              <th>联系电话</th>
              <th>学号</th>
              <th>年级</th>
              <th>学院</th>
              <th>当前阶段</th>
              <th>审批状态</th>
              <th>申请日期</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="app in paginatedApplications" :key="app.id" @click="viewDetail(app)" class="clickable-row" :class="{ selected: selectedIds.includes(app.id) }">
              <td @click.stop>
                <label class="checkbox-label">
                  <input type="checkbox" :checked="selectedIds.includes(app.id)" @change="toggleSelect(app.id, $event)" />
                </label>
              </td>
              <td>{{ app.id }}</td>
              <td>{{ app.name }}</td>
              <td><span class="gender-tag">{{ app.gender }}</span></td>
              <td>{{ app.ethnicity }}</td>
              <td>{{ app.education }}</td>
              <td><span class="org-tag">{{ app.organization }}</span></td>
              <td>{{ app.phone }}</td>
              <td>{{ app.studentId || '-' }}</td>
              <td>{{ app.grade || '-' }}</td>
              <td>{{ app.department || '-' }}</td>
              <td><span class="stage-tag" :class="app.currentStage">{{ app.currentStage }}</span></td>
              <td><span class="status-tag" :class="app.approvalStatus">{{ app.approvalStatus }}</span></td>
              <td>{{ app.applicationDate }}</td>
              <td @click.stop>
                <button v-if="app.approvalStatus === '待审批' && hasPermission('party:edit')" class="action-btn approve" @click="openApprovalModal(app, 'approve')">通过</button>
                <button v-if="app.approvalStatus === '待审批' && hasPermission('party:edit')" class="action-btn reject" @click="openApprovalModal(app, 'reject')">拒绝</button>
                <button v-if="hasPermission('party:edit')" class="action-btn edit" @click="openEditModal(app)">编辑</button>
                <button v-if="hasPermission('party:delete')" class="action-btn delete" @click="deleteApplication(app)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 0" class="pagination">
      <div class="pagination-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ filteredApplications.length }} 条记录
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

    <!-- 新增申请模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content large-modal">
        <div class="modal-header">
          <h3>新增党员发展申请</h3>
          <button class="close-btn" @click="showAddModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>姓名 <span class="required">*</span></label>
              <input type="text" v-model="currentApplication.name" class="form-input" :class="{ 'error': formErrors.name }" />
              <span v-if="formErrors.name" class="error-text">{{ formErrors.name }}</span>
            </div>
            <div class="form-item">
              <label>性别 <span class="required">*</span></label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="currentApplication.gender" value="男" />
                  <span>男</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="currentApplication.gender" value="女" />
                  <span>女</span>
                </label>
              </div>
              <span v-if="formErrors.gender" class="error-text">{{ formErrors.gender }}</span>
            </div>
            <div class="form-item">
              <label>民族 <span class="required">*</span></label>
              <select v-model="currentApplication.ethnicity" class="form-select" :class="{ 'error': formErrors.ethnicity }">
                <option v-for="eth in ethnicities" :key="eth" :value="eth">{{ eth }}</option>
              </select>
              <span v-if="formErrors.ethnicity" class="error-text">{{ formErrors.ethnicity }}</span>
            </div>
            <div class="form-item">
              <label>出生日期 <span class="required">*</span></label>
              <input type="date" v-model="currentApplication.birthDate" class="form-input" :class="{ 'error': formErrors.birthDate }" />
              <span v-if="formErrors.birthDate" class="error-text">{{ formErrors.birthDate }}</span>
            </div>
            <div class="form-item">
              <label>学历 <span class="required">*</span></label>
              <select v-model="currentApplication.education" class="form-select" :class="{ 'error': formErrors.education }">
                <option v-for="edu in educations" :key="edu" :value="edu">{{ edu }}</option>
              </select>
              <span v-if="formErrors.education" class="error-text">{{ formErrors.education }}</span>
            </div>
            <div class="form-item">
              <label>所属党组织 <span class="required">*</span></label>
              <select v-model="currentApplication.organization" class="form-select" :class="{ 'error': formErrors.organization }">
                <option value="">请选择党组织</option>
                <option v-for="org in organizations" :key="org" :value="org">{{ org }}</option>
              </select>
              <span v-if="formErrors.organization" class="error-text">{{ formErrors.organization }}</span>
            </div>
            <div class="form-item">
              <label>联系电话 <span class="required">*</span></label>
              <input type="text" v-model="currentApplication.phone" class="form-input" :class="{ 'error': formErrors.phone }" placeholder="13812345678" />
              <span v-if="formErrors.phone" class="error-text">{{ formErrors.phone }}</span>
            </div>
            <div class="form-item">
              <label>学号</label>
              <input type="text" v-model="currentApplication.studentId" class="form-input" placeholder="学号" />
            </div>
            <div class="form-item">
              <label>年级</label>
              <select v-model="currentApplication.grade" class="form-select">
                <option value="">请选择年级</option>
                <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
            <div class="form-item">
              <label>学院</label>
              <input type="text" v-model="currentApplication.department" class="form-input" placeholder="学院" />
            </div>
            <div class="form-item">
              <label>当前阶段 <span class="required">*</span></label>
              <select v-model="currentApplication.currentStage" class="form-select" :class="{ 'error': formErrors.currentStage }">
                <option v-for="stage in stages.slice(1)" :key="stage" :value="stage">{{ stage }}</option>
              </select>
              <span v-if="formErrors.currentStage" class="error-text">{{ formErrors.currentStage }}</span>
            </div>
            <div class="form-item">
              <label>申请日期 <span class="required">*</span></label>
              <input type="date" v-model="currentApplication.applicationDate" class="form-input" :class="{ 'error': formErrors.applicationDate }" />
              <span v-if="formErrors.applicationDate" class="error-text">{{ formErrors.applicationDate }}</span>
            </div>
            <div class="form-item full-width">
              <label>备注</label>
              <textarea v-model="currentApplication.notes" class="form-textarea" placeholder="备注信息"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="addApplication">添加</button>
        </div>
      </div>
    </div>

    <!-- 编辑申请模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content large-modal">
        <div class="modal-header">
          <h3>编辑党员发展申请</h3>
          <button class="close-btn" @click="showEditModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>姓名 <span class="required">*</span></label>
              <input type="text" v-model="currentApplication.name" class="form-input" :class="{ 'error': formErrors.name }" />
              <span v-if="formErrors.name" class="error-text">{{ formErrors.name }}</span>
            </div>
            <div class="form-item">
              <label>性别 <span class="required">*</span></label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="currentApplication.gender" value="男" />
                  <span>男</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="currentApplication.gender" value="女" />
                  <span>女</span>
                </label>
              </div>
              <span v-if="formErrors.gender" class="error-text">{{ formErrors.gender }}</span>
            </div>
            <div class="form-item">
              <label>民族 <span class="required">*</span></label>
              <select v-model="currentApplication.ethnicity" class="form-select" :class="{ 'error': formErrors.ethnicity }">
                <option v-for="eth in ethnicities" :key="eth" :value="eth">{{ eth }}</option>
              </select>
              <span v-if="formErrors.ethnicity" class="error-text">{{ formErrors.ethnicity }}</span>
            </div>
            <div class="form-item">
              <label>出生日期 <span class="required">*</span></label>
              <input type="date" v-model="currentApplication.birthDate" class="form-input" :class="{ 'error': formErrors.birthDate }" />
              <span v-if="formErrors.birthDate" class="error-text">{{ formErrors.birthDate }}</span>
            </div>
            <div class="form-item">
              <label>学历 <span class="required">*</span></label>
              <select v-model="currentApplication.education" class="form-select" :class="{ 'error': formErrors.education }">
                <option v-for="edu in educations" :key="edu" :value="edu">{{ edu }}</option>
              </select>
              <span v-if="formErrors.education" class="error-text">{{ formErrors.education }}</span>
            </div>
            <div class="form-item">
              <label>所属党组织 <span class="required">*</span></label>
              <select v-model="currentApplication.organization" class="form-select" :class="{ 'error': formErrors.organization }">
                <option value="">请选择党组织</option>
                <option v-for="org in organizations" :key="org" :value="org">{{ org }}</option>
              </select>
              <span v-if="formErrors.organization" class="error-text">{{ formErrors.organization }}</span>
            </div>
            <div class="form-item">
              <label>联系电话 <span class="required">*</span></label>
              <input type="text" v-model="currentApplication.phone" class="form-input" :class="{ 'error': formErrors.phone }" placeholder="13812345678" />
              <span v-if="formErrors.phone" class="error-text">{{ formErrors.phone }}</span>
            </div>
            <div class="form-item">
              <label>学号</label>
              <input type="text" v-model="currentApplication.studentId" class="form-input" placeholder="学号" />
            </div>
            <div class="form-item">
              <label>年级</label>
              <select v-model="currentApplication.grade" class="form-select">
                <option value="">请选择年级</option>
                <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
            <div class="form-item">
              <label>学院</label>
              <input type="text" v-model="currentApplication.department" class="form-input" placeholder="学院" />
            </div>
            <div class="form-item">
              <label>当前阶段 <span class="required">*</span></label>
              <select v-model="currentApplication.currentStage" class="form-select" :class="{ 'error': formErrors.currentStage }">
                <option v-for="stage in stages.slice(1)" :key="stage" :value="stage">{{ stage }}</option>
              </select>
              <span v-if="formErrors.currentStage" class="error-text">{{ formErrors.currentStage }}</span>
            </div>
            <div class="form-item">
              <label>审批状态</label>
              <select v-model="currentApplication.approvalStatus" class="form-select">
                <option v-for="status in approvalStatuses.slice(1)" :key="status" :value="status">{{ status }}</option>
              </select>
            </div>
            <div class="form-item">
              <label>申请日期 <span class="required">*</span></label>
              <input type="date" v-model="currentApplication.applicationDate" class="form-input" :class="{ 'error': formErrors.applicationDate }" />
              <span v-if="formErrors.applicationDate" class="error-text">{{ formErrors.applicationDate }}</span>
            </div>
            <div class="form-item full-width">
              <label>备注</label>
              <textarea v-model="currentApplication.notes" class="form-textarea" placeholder="备注信息"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditModal = false">取消</button>
          <button class="btn btn-primary" @click="editApplication">保存</button>
        </div>
      </div>
    </div>

    <!-- 详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-content detail-modal" v-if="detailApplication">
        <div class="modal-header">
          <h3>申请详情</h3>
          <button class="close-btn" @click="showDetailModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="progress-bar-container">
            <div class="progress-step" v-for="(stage, index) in stages.slice(1)" :key="stage">
              <div class="step-circle" :class="{ active: getStageIndex(detailApplication.currentStage) >= index, current: detailApplication.currentStage === stage }">
                {{ index + 1 }}
              </div>
              <div class="step-label">{{ stage }}</div>
              <div v-if="index < stages.slice(1).length - 1" class="step-line" :class="{ active: getStageIndex(detailApplication.currentStage) > index }"></div>
            </div>
          </div>
          <div class="detail-header">
            <div class="detail-avatar">👤</div>
            <div class="detail-basic">
              <h2 class="detail-name">{{ detailApplication.name }}</h2>
              <p class="detail-position">{{ detailApplication.organization }} · {{ detailApplication.currentStage }}</p>
              <span class="status-tag" :class="detailApplication.approvalStatus">{{ detailApplication.approvalStatus }}</span>
            </div>
          </div>
          <div class="detail-info">
            <div class="info-grid">
              <div class="info-item">
                <label>申请ID</label>
                <span>{{ detailApplication.id }}</span>
              </div>
              <div class="info-item">
                <label>性别</label>
                <span>{{ detailApplication.gender }}</span>
              </div>
              <div class="info-item">
                <label>民族</label>
                <span>{{ detailApplication.ethnicity }}</span>
              </div>
              <div class="info-item">
                <label>出生日期</label>
                <span>{{ detailApplication.birthDate }}</span>
              </div>
              <div class="info-item">
                <label>学历</label>
                <span>{{ detailApplication.education }}</span>
              </div>
              <div class="info-item">
                <label>所属党组织</label>
                <span>{{ detailApplication.organization }}</span>
              </div>
              <div class="info-item">
                <label>联系电话</label>
                <span>{{ detailApplication.phone }}</span>
              </div>
              <div class="info-item">
                <label>学号</label>
                <span>{{ detailApplication.studentId || '-' }}</span>
              </div>
              <div class="info-item">
                <label>年级</label>
                <span>{{ detailApplication.grade || '-' }}</span>
              </div>
              <div class="info-item">
                <label>学院</label>
                <span>{{ detailApplication.department || '-' }}</span>
              </div>
              <div class="info-item">
                <label>当前阶段</label>
                <span class="stage-tag" :class="detailApplication.currentStage">{{ detailApplication.currentStage }}</span>
              </div>
              <div class="info-item">
                <label>审批状态</label>
                <span class="status-tag" :class="detailApplication.approvalStatus">{{ detailApplication.approvalStatus }}</span>
              </div>
              <div class="info-item">
                <label>申请日期</label>
                <span>{{ detailApplication.applicationDate }}</span>
              </div>
              <div class="info-item full-width">
                <label>备注</label>
                <span>{{ detailApplication.notes || '无' }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal = false">关闭</button>
          <button v-if="detailApplication.approvalStatus === '待审批' && hasPermission('party:edit')" class="btn btn-success" @click="openApprovalModal(detailApplication, 'approve'); showDetailModal = false">通过</button>
          <button v-if="detailApplication.approvalStatus === '待审批' && hasPermission('party:edit')" class="btn btn-danger" @click="openApprovalModal(detailApplication, 'reject'); showDetailModal = false">拒绝</button>
          <button v-if="hasPermission('party:edit')" class="btn btn-primary" @click="openEditModal(detailApplication); showDetailModal = false">编辑信息</button>
        </div>
      </div>
    </div>

    <!-- 审批模态框 -->
    <div v-if="showApprovalModal" class="modal-overlay" @click.self="showApprovalModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ approvalApplication?.action === 'approve' ? '通过申请' : '拒绝申请' }}</h3>
          <button class="close-btn" @click="showApprovalModal = false">×</button>
        </div>
        <div class="modal-body" v-if="approvalApplication">
          <div class="approval-info">
            <p><strong>申请人：</strong>{{ approvalApplication.name }}</p>
            <p><strong>当前阶段：</strong>{{ approvalApplication.currentStage }}</p>
            <p><strong>所属组织：</strong>{{ approvalApplication.organization }}</p>
          </div>
          <div class="form-group">
            <label>审批说明（可选）</label>
            <textarea v-model="approvalReason" class="form-textarea" placeholder="请输入审批说明或理由..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showApprovalModal = false">取消</button>
          <button class="btn btn-primary" :class="{ 'btn-success': approvalApplication?.action === 'approve', 'btn-danger': approvalApplication?.action === 'reject' }" @click="processApproval">确认</button>
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

.result-count {
  font-size: 14px;
  color: #666666;
}

.selected-count {
  font-size: 14px;
  color: #1890ff;
  font-weight: 500;
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
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.btn-secondary {
  background: #ffffff;
  color: #666;
  border: 1px solid #e8e8e8;
}

.btn-secondary:hover {
  background: #f5f5f5;
}

.btn-success {
  background: #52c41a;
  color: #ffffff;
}

.btn-success:hover {
  background: #73d13d;
}

.btn-danger {
  background: #ff4d4f;
  color: #ffffff;
}

.btn-danger:hover {
  background: #ff7875;
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

.upload-btn {
  position: relative;
  overflow: hidden;
  cursor: pointer;
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

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1400px;
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

.stage-tag.入党申请 {
  background: #fff7e6;
  color: #fa8c16;
}

.stage-tag.积极分子 {
  background: #e6f7ff;
  color: #1890ff;
}

.stage-tag.发展对象 {
  background: #f9f0ff;
  color: #722ed1;
}

.stage-tag.预备党员 {
  background: #fff1f0;
  color: #f5222d;
}

.stage-tag.正式党员 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.待审批 {
  background: #fff7e6;
  color: #fa8c16;
}

.status-tag.已通过 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.已拒绝 {
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

.action-btn.approve {
  background: #f6ffed;
  color: #52c41a;
}

.action-btn.approve:hover {
  background: #d9f7be;
}

.action-btn.reject {
  background: #fff1f0;
  color: #ff4d4f;
}

.action-btn.reject:hover {
  background: #ffccc7;
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
  width: 600px;
  max-height: 90vh;
  overflow: hidden;
}

.large-modal {
  width: 900px;
}

.detail-modal {
  width: 700px;
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

.form-textarea {
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  min-height: 80px;
  resize: vertical;
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

.approval-info {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.approval-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #333333;
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

@media (max-width: 1024px) {
  .stats-grid {
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

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .progress-bar-container {
    flex-wrap: wrap;
  }

  .progress-step {
    flex: 1;
    min-width: 45%;
  }

  .step-line {
    display: none;
  }
}

.progress-bar-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 24px;
  position: relative;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.step-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #d9d9d9;
  color: #999999;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  z-index: 1;
}

.step-circle.active {
  background: #52c41a;
  color: #ffffff;
}

.step-circle.current {
  background: #1890ff;
  transform: scale(1.1);
  box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.2);
}

.step-label {
  font-size: 12px;
  color: #999999;
  text-align: center;
  white-space: nowrap;
  transition: color 0.3s ease;
}

.step-circle.active + .step-label {
  color: #333333;
  font-weight: 500;
}

.step-circle.current + .step-label {
  color: #1890ff;
  font-weight: 600;
}

.step-line {
  position: absolute;
  top: 20px;
  left: 50%;
  width: calc(100% - 20px);
  height: 3px;
  background: #d9d9d9;
  z-index: 0;
  margin-left: 10px;
}

.step-line.active {
  background: #52c41a;
}

.progress-step:last-child .step-line {
  display: none;
}
</style>