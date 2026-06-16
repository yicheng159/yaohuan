<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { hasPermission } from '../../utils/permission';

// API配置
const API_BASE_URL = '/api/qingma-courses/';

// 课程数据
const courses = ref([]);
const loading = ref(false);
const error = ref(null);

// 模态框状态
const showModal = ref(false);
const showDetailModal = ref(false);
const showDeleteModal = ref(false);
const isEdit = ref(false);
const currentCourse = ref(null);
const formErrors = ref({});
const selectedCourses = ref([]);

// 表单数据
const formData = ref({
  name: '',
  qingma_class: '',
  teacher: '',
  course_type: '理论课',
  hours: 0,
  credits: 0,
  course_time: '',
  location: '',
  status: '未开始',
  description: ''
});

// 搜索和筛选
const searchQuery = ref('');
const filters = ref({
  qingma_class: '全部',
  course_type: '全部',
  status: '全部'
});

// 分页
const currentPage = ref(1);
const pageSize = ref(10);

// 青马班列表（从API获取或预设）
const qingmaClasses = ref([
  { id: 1, name: '第28期青马班' },
  { id: 2, name: '第27期青马班' },
  { id: 3, name: '第29期青马班' }
]);

// 课程类型选项
const courseTypes = ['理论课', '实践课', '研讨课', '专题讲座'];

// 课程状态选项
const courseStatuses = ['未开始', '进行中', '已结束'];

// 统计数据
const stats = computed(() => {
  const total = courses.value.length;
  const notStarted = courses.value.filter(c => c.status === '未开始').length;
  const inProgress = courses.value.filter(c => c.status === '进行中').length;
  const ended = courses.value.filter(c => c.status === '已结束').length;
  
  return [
    { label: '课程总数', value: total, icon: '📚' },
    { label: '未开始', value: notStarted, icon: '⏳' },
    { label: '进行中', value: inProgress, icon: '🎯' },
    { label: '已结束', value: ended, icon: '✅' }
  ];
});

// 筛选后的课程列表
const filteredCourses = computed(() => {
  return courses.value.filter(c => {
    const matchSearch = !searchQuery.value || 
      c.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      c.teacher.includes(searchQuery.value) ||
      c.location.includes(searchQuery.value);
    
    const matchClass = filters.value.qingma_class === '全部' || c.qingma_class === filters.value.qingma_class;
    const matchType = filters.value.course_type === '全部' || c.course_type === filters.value.course_type;
    const matchStatus = filters.value.status === '全部' || c.status === filters.value.status;
    
    return matchSearch && matchClass && matchType && matchStatus;
  });
});

// 分页后的课程列表
const paginatedCourses = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredCourses.value.slice(start, end);
});

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredCourses.value.length / pageSize.value);
});

// 获取青马班名称
function getQingmaClassName(classId) {
  const cls = qingmaClasses.value.find(c => c.id === classId);
  return cls ? cls.name : '';
}

// 从API获取课程数据
async function fetchCourses() {
  loading.value = true;
  error.value = null;
  
  try {
    const response = await axios.get(API_BASE_URL);
    const results = response.data.results || response.data;
    courses.value = results.map(item => ({
      ...item,
      qingma_class: getQingmaClassName(item.qingma_class),
      course_time: item.course_time ? formatDateTime(item.course_time) : ''
    }));
  } catch (err) {
    error.value = '获取课程数据失败：' + (err.response?.data?.message || err.message);
    console.error('获取课程数据失败:', err);
  } finally {
    loading.value = false;
  }
}

// 格式化日期时间
function formatDateTime(dateTimeStr) {
  if (!dateTimeStr) return '';
  const date = new Date(dateTimeStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 创建课程
async function createCourse() {
  loading.value = true;
  error.value = null;
  
  try {
    const postData = {
      ...formData.value,
      qingma_class: getClassIdByName(formData.value.qingma_class)
    };
    const response = await axios.post(API_BASE_URL, postData);
    const newCourse = {
      ...response.data,
      qingma_class: formData.value.qingma_class,
      course_time: formatDateTime(response.data.course_time)
    };
    courses.value.unshift(newCourse);
    showModal.value = false;
    resetForm();
  } catch (err) {
    error.value = '创建课程失败：' + (err.response?.data?.message || err.message);
    console.error('创建课程失败:', err);
  } finally {
    loading.value = false;
  }
}

// 根据班级名称获取班级ID
function getClassIdByName(className) {
  const cls = qingmaClasses.value.find(c => c.name === className);
  return cls ? cls.id : null;
}

// 更新课程
async function updateCourse() {
  if (!currentCourse.value) return;
  
  loading.value = true;
  error.value = null;
  
  try {
    const putData = {
      ...formData.value,
      qingma_class: getClassIdByName(formData.value.qingma_class)
    };
    const response = await axios.put(`${API_BASE_URL}${currentCourse.value.id}/`, putData);
    const index = courses.value.findIndex(c => c.id === currentCourse.value.id);
    if (index !== -1) {
      courses.value[index] = {
        ...response.data,
        qingma_class: formData.value.qingma_class,
        course_time: formatDateTime(response.data.course_time)
      };
    }
    showModal.value = false;
    resetForm();
  } catch (err) {
    error.value = '更新课程失败：' + (err.response?.data?.message || err.message);
    console.error('更新课程失败:', err);
  } finally {
    loading.value = false;
  }
}

// 删除课程
async function deleteCourseApi() {
  if (!currentCourse.value) return;
  
  loading.value = true;
  error.value = null;
  
  try {
    await axios.delete(`${API_BASE_URL}${currentCourse.value.id}/`);
    const index = courses.value.findIndex(c => c.id === currentCourse.value.id);
    if (index !== -1) {
      courses.value.splice(index, 1);
    }
    showDeleteModal.value = false;
    currentCourse.value = null;
  } catch (err) {
    error.value = '删除课程失败：' + (err.response?.data?.message || err.message);
    console.error('删除课程失败:', err);
  } finally {
    loading.value = false;
  }
}

// 批量删除课程
async function batchDeleteCourses() {
  if (selectedCourses.value.length === 0) return;
  
  loading.value = true;
  error.value = null;
  
  try {
    // 批量删除请求
    const deletePromises = selectedCourses.value.map(id => 
      axios.delete(`${API_BASE_URL}${id}/`)
    );
    
    await Promise.all(deletePromises);
    
    // 从本地数据中移除
    courses.value = courses.value.filter(c => !selectedCourses.value.includes(c.id));
    selectedCourses.value = [];
  } catch (err) {
    error.value = '批量删除失败：' + (err.response?.data?.message || err.message);
    console.error('批量删除失败:', err);
  } finally {
    loading.value = false;
  }
}

// 验证表单
function validateForm() {
  const errors = {};
  
  if (!formData.value.name) errors.name = '请输入课程名称';
  if (!formData.value.qingma_class) errors.qingma_class = '请选择青马班';
  if (!formData.value.teacher) errors.teacher = '请输入授课教师';
  if (!formData.value.course_type) errors.course_type = '请选择课程类型';
  if (!formData.value.hours || formData.value.hours < 1) errors.hours = '学时必须大于0';
  if (!formData.value.credits || formData.value.credits < 0.5) errors.credits = '学分必须大于0.5';
  if (!formData.value.course_time) errors.course_time = '请输入上课时间';
  if (!formData.value.location) errors.location = '请输入上课地点';
  if (!formData.value.status) errors.status = '请选择状态';
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 重置表单
function resetForm() {
  formData.value = {
    name: '',
    qingma_class: '',
    teacher: '',
    course_type: '理论课',
    hours: 0,
    credits: 0,
    course_time: '',
    location: '',
    status: '未开始',
    description: ''
  };
  formErrors.value = {};
  currentCourse.value = null;
}

// 打开创建模态框
function openCreateModal() {
  isEdit.value = false;
  resetForm();
  showModal.value = true;
}

// 打开编辑模态框
function openEditModal(course) {
  isEdit.value = true;
  currentCourse.value = course;
  formData.value = { ...course };
  formErrors.value = {};
  showModal.value = true;
}

// 打开详情模态框
function openDetailModal(course) {
  currentCourse.value = course;
  showDetailModal.value = true;
}

// 打开删除确认模态框
function openDeleteModal(course) {
  currentCourse.value = course;
  showDeleteModal.value = true;
}

// 关闭模态框
function closeModal() {
  showModal.value = false;
  showDetailModal.value = false;
  showDeleteModal.value = false;
  resetForm();
}

// 保存课程
async function saveCourse() {
  if (!validateForm()) return;
  
  if (isEdit.value) {
    await updateCourse();
  } else {
    await createCourse();
  }
}

// 删除课程
async function deleteCourse() {
  await deleteCourseApi();
}

// 切换选择
function toggleSelect(id) {
  const index = selectedCourses.value.indexOf(id);
  if (index === -1) {
    selectedCourses.value.push(id);
  } else {
    selectedCourses.value.splice(index, 1);
  }
}

// 全选
function toggleSelectAll() {
  if (selectedCourses.value.length === paginatedCourses.value.length) {
    selectedCourses.value = [];
  } else {
    selectedCourses.value = paginatedCourses.value.map(c => c.id);
  }
}

// 分页操作
function prevPage() {
  if (currentPage.value > 1) currentPage.value--;
}

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++;
}

function goToPage(page) {
  currentPage.value = page;
}

// 页面加载时获取数据
onMounted(() => {
  fetchCourses();
});
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>青马班课程管理</h1>
    </header>
    
    <!-- 错误提示 -->
    <div v-if="error" class="error-alert">
      <p>{{ error }}</p>
      <button class="btn btn-secondary" @click="error = null">关闭</button>
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
    
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <input type="text" v-model="searchQuery" placeholder="搜索课程名称、教师、地点..." class="search-input" />
        </div>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedCourses.length > 0 && hasPermission('league:delete')" class="btn btn-danger" @click="batchDeleteCourses">
          批量删除 ({{ selectedCourses.length }})
        </button>
        <button v-if="hasPermission('league:add')" class="btn btn-primary" @click="openCreateModal">新增课程</button>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>青马班：</label>
        <select v-model="filters.qingma_class">
          <option value="全部">全部</option>
          <option v-for="cls in qingmaClasses" :key="cls.id" :value="cls.name">{{ cls.name }}</option>
        </select>
      </div>
      <div class="filter-item">
        <label>课程类型：</label>
        <select v-model="filters.course_type">
          <option value="全部">全部</option>
          <option v-for="type in courseTypes" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>
      <div class="filter-item">
        <label>状态：</label>
        <select v-model="filters.status">
          <option value="全部">全部</option>
          <option v-for="status in courseStatuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading && courses.length === 0" class="loading-state">
      <p>正在加载课程数据...</p>
    </div>
    
    <!-- 课程列表 -->
    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>
              <input type="checkbox" :checked="selectedCourses.length === paginatedCourses.length && paginatedCourses.length > 0" @change="toggleSelectAll" />
            </th>
            <th>课程名称</th>
            <th>青马班</th>
            <th>授课教师</th>
            <th>课程类型</th>
            <th>学时</th>
            <th>学分</th>
            <th>上课时间</th>
            <th>上课地点</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="course in paginatedCourses" :key="course.id">
            <td>
              <input type="checkbox" :checked="selectedCourses.includes(course.id)" @change="toggleSelect(course.id)" />
            </td>
            <td>{{ course.name }}</td>
            <td><span class="class-tag">{{ course.qingma_class }}</span></td>
            <td>{{ course.teacher }}</td>
            <td><span class="type-tag">{{ course.course_type }}</span></td>
            <td>{{ course.hours }}学时</td>
            <td>{{ course.credits }}学分</td>
            <td>{{ course.course_time }}</td>
            <td>{{ course.location }}</td>
            <td><span class="status-tag" :class="course.status">{{ course.status }}</span></td>
            <td>
              <button class="action-btn view" @click="openDetailModal(course)">查看</button>
              <button v-if="hasPermission('league:edit')" class="action-btn edit" @click="openEditModal(course)">编辑</button>
              <button v-if="hasPermission('league:delete')" class="action-btn delete" @click="openDeleteModal(course)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- 分页 -->
      <div v-if="filteredCourses.length > pageSize" class="pagination">
        <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">上一页</button>
        <div class="page-numbers">
          <button v-for="page in totalPages" :key="page" class="page-num-btn" :class="{ active: currentPage === page }" @click="goToPage(page)">{{ page }}</button>
        </div>
        <button class="page-btn" :disabled="currentPage === totalPages" @click="nextPage">下一页</button>
        <span class="page-info">共 {{ filteredCourses.length }} 条</span>
      </div>
      
      <div v-if="filteredCourses.length === 0" class="empty-state">
        <p>暂无课程数据</p>
      </div>
    </div>
    
    <!-- 新增/编辑模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑课程' : '新增课程' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-section">
            <h3 class="section-title">基本信息</h3>
            <div class="form-row">
              <div class="form-group">
                <label>课程名称 <span class="required">*</span></label>
                <input type="text" v-model="formData.name" class="form-input" placeholder="请输入课程名称" />
                <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
              </div>
              <div class="form-group">
                <label>青马班 <span class="required">*</span></label>
                <select v-model="formData.qingma_class" class="form-select">
                  <option value="">请选择青马班</option>
                  <option v-for="cls in qingmaClasses" :key="cls.id" :value="cls.name">{{ cls.name }}</option>
                </select>
                <span v-if="formErrors.qingma_class" class="form-error">{{ formErrors.qingma_class }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>授课教师 <span class="required">*</span></label>
                <input type="text" v-model="formData.teacher" class="form-input" placeholder="请输入授课教师" />
                <span v-if="formErrors.teacher" class="form-error">{{ formErrors.teacher }}</span>
              </div>
              <div class="form-group">
                <label>课程类型 <span class="required">*</span></label>
                <select v-model="formData.course_type" class="form-select">
                  <option v-for="type in courseTypes" :key="type" :value="type">{{ type }}</option>
                </select>
                <span v-if="formErrors.course_type" class="form-error">{{ formErrors.course_type }}</span>
              </div>
            </div>
          </div>
          
          <div class="form-section">
            <h3 class="section-title">课程信息</h3>
            <div class="form-row">
              <div class="form-group">
                <label>学时 <span class="required">*</span></label>
                <input type="number" v-model="formData.hours" class="form-input" min="1" placeholder="请输入学时" />
                <span v-if="formErrors.hours" class="form-error">{{ formErrors.hours }}</span>
              </div>
              <div class="form-group">
                <label>学分 <span class="required">*</span></label>
                <input type="number" v-model="formData.credits" class="form-input" min="0.5" step="0.5" placeholder="请输入学分" />
                <span v-if="formErrors.credits" class="form-error">{{ formErrors.credits }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>上课时间 <span class="required">*</span></label>
                <input type="datetime-local" v-model="formData.course_time" class="form-input" />
                <span v-if="formErrors.course_time" class="form-error">{{ formErrors.course_time }}</span>
              </div>
              <div class="form-group">
                <label>上课地点 <span class="required">*</span></label>
                <input type="text" v-model="formData.location" class="form-input" placeholder="请输入上课地点" />
                <span v-if="formErrors.location" class="form-error">{{ formErrors.location }}</span>
              </div>
            </div>
            <div class="form-group">
              <label>状态 <span class="required">*</span></label>
              <select v-model="formData.status" class="form-select">
                <option v-for="status in courseStatuses" :key="status" :value="status">{{ status }}</option>
              </select>
              <span v-if="formErrors.status" class="form-error">{{ formErrors.status }}</span>
            </div>
          </div>
          
          <div class="form-section">
            <h3 class="section-title">课程描述</h3>
            <div class="form-group">
              <label>课程描述</label>
              <textarea v-model="formData.description" class="form-textarea" placeholder="请输入课程描述"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveCourse" :disabled="loading">
            {{ loading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>课程详情</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentCourse">
          <div class="detail-section">
            <h3 class="section-title">基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">课程名称：</span>{{ currentCourse.name }}</div>
              <div class="detail-item"><span class="label">青马班：</span><span class="class-tag">{{ currentCourse.qingma_class }}</span></div>
              <div class="detail-item"><span class="label">授课教师：</span>{{ currentCourse.teacher }}</div>
              <div class="detail-item"><span class="label">课程类型：</span><span class="type-tag">{{ currentCourse.course_type }}</span></div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">课程信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">学时：</span>{{ currentCourse.hours }}学时</div>
              <div class="detail-item"><span class="label">学分：</span>{{ currentCourse.credits }}学分</div>
              <div class="detail-item"><span class="label">上课时间：</span>{{ currentCourse.course_time }}</div>
              <div class="detail-item"><span class="label">上课地点：</span>{{ currentCourse.location }}</div>
              <div class="detail-item"><span class="label">状态：</span><span class="status-tag" :class="currentCourse.status">{{ currentCourse.status }}</span></div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">课程描述</h3>
            <div class="detail-item full-width">
              <span class="label">描述：</span>{{ currentCourse.description || '暂无描述' }}
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button class="btn btn-primary" @click="openEditModal(currentCourse); closeModal()">编辑</button>
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
          <p>确定要删除课程「{{ currentCourse?.name }}」吗？此操作不可撤销。</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-danger" @click="deleteCourse" :disabled="loading">
            {{ loading ? '删除中...' : '确认删除' }}
          </button>
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

.error-alert {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-alert p {
  color: #ff4d4f;
  font-size: 14px;
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
  width: 300px;
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.loading-state {
  padding: 48px;
  text-align: center;
  color: #999;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
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

.class-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.type-tag {
  padding: 4px 12px;
  background: #fff0f6;
  color: #eb2f96;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.未开始 {
  background: #fff7e6;
  color: #fa8c16;
}

.status-tag.进行中 {
  background: #e6f7ff;
  color: #1890ff;
}

.status-tag.已结束 {
  background: #f5f5f5;
  color: #666666;
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
  gap: 12px;
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

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-num-btn {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #ffffff;
  color: #666;
  font-size: 14px;
  cursor: pointer;
}

.page-num-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  border-color: transparent;
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
  min-height: 100px;
  resize: vertical;
  box-sizing: border-box;
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
  
  .pagination {
    flex-wrap: wrap;
  }
}
</style>