<script setup>
import { ref, computed, onMounted } from 'vue';
import { hasPermission } from '../utils/permission';
import { getDictionaryNames } from '../utils/dictionary';

const activityTypes = ['全部', '文体类', '学术类', '公益类', '交流类', '其他'];
const statusOptions = ['全部', '筹备中', '进行中', '已结束'];
const participantRanges = ['全部', '0-50人', '51-100人', '101-200人', '200人以上'];
const departments = ref(['全部']);
const userDepartments = ref([]);
const sortByOptions = ['开始时间', '结束时间', '参与人数'];
const sortOrderOptions = ['正序', '倒序'];
const timeDimensionOptions = ['月份', '周'];

const loadDictionaryOptions = async () => {
  departments.value = ['全部', ...(await getDictionaryNames('department'))];
  userDepartments.value = await getDictionaryNames('department');
};

// 活动数据（从后端获取）
const activities = ref([]);

// 负责人数据（从成员管理获取）
const users = ref([]);

// 从后端获取活动列表
const fetchActivities = async () => {
  try {
    const response = await fetch('/api/activities/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      // API返回的是分页数据，需要从results中获取列表
      const results = data.results || data;
      activities.value = results.map(activity => ({
        id: activity.id,
        name: activity.name,
        type: activity.type,
        date: activity.start_time,
        endDate: activity.end_time,
        location: activity.location,
        organizer: activity.organizer,
        leader: activity.leader,
        status: activity.status,
        participants: activity.participants_count,
        description: activity.description
      }));
    }
  } catch (error) {
    console.error('获取活动列表失败:', error);
  }
};

// 获取成员列表作为负责人选项
const fetchMembers = async () => {
  try {
    const response = await fetch('/api/members/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      // API返回的是分页数据，需要从results中获取列表
      const results = data.results || data;
      users.value = results.map(member => ({
        id: member.id,
        name: member.name,
        department: member.department || '未知部门',
        avatar: '👤'
      }));
    }
  } catch (error) {
    console.error('获取成员列表失败:', error);
  }
};

// 表单状态
const showModal = ref(false);
const showDetailModal = ref(false);
const showDeleteModal = ref(false);
const isEdit = ref(false);
const currentActivityId = ref(null);
const currentActivity = ref(null);
const formErrors = ref({});
const selectedActivities = ref([]);
const formData = ref({
  name: '',
  description: '',
  type: '文体类',
  organizer: '',
  organizerId: null,
  date: '',
  endDate: '',
  location: '',
  participants: 0,
  status: '未开始'
});

// 验证表单
function validateForm() {
  const errors = {};
  
  if (!formData.value.name || formData.value.name.trim() === '') {
    errors.name = '请输入活动名称';
  } else if (formData.value.name.length > 100) {
    errors.name = '活动名称不能超过100字符';
  }
  
  if (!formData.value.description || formData.value.description.trim() === '') {
    errors.description = '请输入活动简介';
  }
  
  if (!formData.value.organizer) {
    errors.organizer = '请选择主办部门';
  }
  
  if (!formData.value.organizerId) {
    errors.organizerId = '请选择负责人';
  }
  
  if (!formData.value.date) {
    errors.date = '请选择开始时间';
  }
  
  if (!formData.value.endDate) {
    errors.endDate = '请选择结束时间';
  } else if (formData.value.date && new Date(formData.value.endDate) < new Date(formData.value.date)) {
    errors.endDate = '结束时间不能早于开始时间';
  }
  
  if (!formData.value.location || formData.value.location.trim() === '') {
    errors.location = '请输入活动地点';
  }
  
  if (formData.value.participants < 0) {
    errors.participants = '参与人数不能为负数';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 打开创建活动模态框
function openCreateModal() {
  isEdit.value = false;
  currentActivityId.value = null;
  formData.value = {
    name: '',
    description: '',
    type: '文体类',
    organizer: '',
    organizerId: null,
    date: '',
    endDate: '',
    location: '',
    participants: 0,
    status: '未开始'
  };
  formErrors.value = {};
  showModal.value = true;
}

// 打开编辑活动模态框
function openEditModal(activity) {
  isEdit.value = true;
  currentActivityId.value = activity.id;
  formData.value = {
    name: activity.name,
    description: activity.description,
    type: activity.type,
    organizer: activity.organizer,
    organizerId: users.value.find(u => u.name === '张三')?.id || 1,
    date: activity.date,
    endDate: activity.endDate,
    location: activity.location,
    participants: activity.participants,
    status: activity.status
  };
  formErrors.value = {};
  showModal.value = true;
}

// 关闭模态框
function closeModal() {
  showModal.value = false;
}

// 打开详情模态框
function openDetailModal(activity) {
  currentActivity.value = activity;
  showDetailModal.value = true;
}

// 关闭详情模态框
function closeDetailModal() {
  showDetailModal.value = false;
  currentActivity.value = null;
}

// 保存活动
async function saveActivity() {
  if (!validateForm()) {
    return;
  }
  
  const apiData = {
    name: formData.value.name,
    description: formData.value.description,
    type: formData.value.type,
    organizer: formData.value.organizer,
    leader: formData.value.organizerId ? users.value.find(u => u.id === formData.value.organizerId)?.name || '' : '',
    start_time: formData.value.date,
    end_time: formData.value.endDate,
    location: formData.value.location,
    participants_count: formData.value.participants,
    status: formData.value.status
  };
  
  try {
    if (isEdit.value) {
      // 编辑模式
      const response = await fetch(`/api/activities/${currentActivityId.value}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(apiData)
      });
      
      if (response.ok) {
        const updatedActivity = await response.json();
        const index = activities.value.findIndex(a => a.id === currentActivityId.value);
        if (index !== -1) {
          activities.value[index] = {
            ...activities.value[index],
            ...updatedActivity
          };
        }
        alert('活动更新成功！');
      } else {
        alert('更新活动失败');
      }
    } else {
      // 创建模式
      const response = await fetch('/api/activities/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(apiData)
      });
      
      if (response.ok) {
        const newActivity = await response.json();
        activities.value.unshift({
          id: newActivity.id,
          name: newActivity.name,
          type: newActivity.type,
          date: newActivity.date,
          endDate: newActivity.end_date,
          location: newActivity.location,
          organizer: newActivity.organizer,
          status: newActivity.status,
          participants: newActivity.participants,
          description: newActivity.description
        });
        alert('活动创建成功！');
      } else {
        alert('创建活动失败');
      }
    }
    
    showModal.value = false;
  } catch (error) {
    console.error('保存活动失败:', error);
    alert('保存活动失败，请检查网络连接');
  }
}

// 删除单个活动
function deleteActivity(activity) {
  currentActivity.value = activity;
  showDeleteModal.value = true;
}

// 确认删除
function confirmDelete() {
  if (currentActivity.value) {
    const index = activities.value.findIndex(a => a.id === currentActivity.value.id);
    if (index !== -1) {
      activities.value.splice(index, 1);
    }
  }
  closeDeleteModal();
}

// 关闭删除模态框
function closeDeleteModal() {
  showDeleteModal.value = false;
  currentActivity.value = null;
}

// 切换单个选择
function toggleSelect(activityId) {
  const index = selectedActivities.value.indexOf(activityId);
  if (index === -1) {
    selectedActivities.value.push(activityId);
  } else {
    selectedActivities.value.splice(index, 1);
  }
}

// 全选/取消全选
function toggleSelectAll() {
  if (selectedActivities.value.length === paginatedActivities.value.length) {
    selectedActivities.value = [];
  } else {
    selectedActivities.value = paginatedActivities.value.map(a => a.id);
  }
}

// 批量删除
function batchDelete() {
  showDeleteModal.value = true;
}

// 确认批量删除
function confirmBatchDelete() {
  activities.value = activities.value.filter(a => !selectedActivities.value.includes(a.id));
  selectedActivities.value = [];
  closeDeleteModal();
}

// 搜索和筛选状态
const searchQuery = ref('');
const filters = ref({
  type: '全部',
  status: '全部',
  participants: '全部',
  department: '全部'
});

// 排序状态
const sortConfig = ref({
  sortBy: '开始时间',
  sortOrder: '倒序',
  timeDimension: '月份'
});

// 分页相关
const currentPage = ref(1);
const pageSize = 8;
const isLoading = ref(false);

// 统计数据
const stats = computed(() => {
  const now = new Date();
  const currentMonth = now.getMonth() + 1;
  const currentYear = now.getFullYear();
  
  const thisMonthActivities = activities.value.filter(a => {
    const date = new Date(a.date);
    return date.getMonth() + 1 === currentMonth && date.getFullYear() === currentYear;
  });
  
  const ongoing = activities.value.filter(a => a.status === '进行中').length;
  const ended = activities.value.filter(a => a.status === '已结束').length;
  const totalParticipants = activities.value.reduce((sum, a) => sum + a.participants, 0);
  
  return [
    { label: '本月活动', value: thisMonthActivities.length },
    { label: '进行中', value: ongoing },
    { label: '已结束', value: ended },
    { label: '总参与人次', value: totalParticipants }
  ];
});

// 获取活动的月份
function getMonth(dateStr) {
  return new Date(dateStr).getMonth() + 1;
}

// 获取活动的周数
function getWeek(dateStr) {
  const date = new Date(dateStr);
  const startOfYear = new Date(date.getFullYear(), 0, 1);
  const week = Math.ceil((((date - startOfYear) / 86400000) + startOfYear.getDay() + 1) / 7);
  return week;
}

// 文本高亮函数
function highlightText(text, query) {
  if (!query) return text;
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<mark class="highlight">$1</mark>');
}

// 根据参与人数范围筛选
function matchParticipantsRange(participants, range) {
  switch(range) {
    case '0-50人': return participants <= 50;
    case '51-100人': return participants > 50 && participants <= 100;
    case '101-200人': return participants > 100 && participants <= 200;
    case '200人以上': return participants > 200;
    default: return true;
  }
}

// 过滤活动
const filteredActivities = computed(() => {
  let result = activities.value.filter(activity => {
    // 搜索匹配
    const matchSearch = !searchQuery.value || 
      activity.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      activity.description.toLowerCase().includes(searchQuery.value.toLowerCase());
    
    // 类型匹配
    const matchType = filters.value.type === '全部' || activity.type === filters.value.type;
    
    // 状态匹配
    const matchStatus = filters.value.status === '全部' || activity.status === filters.value.status;
    
    // 参与人数匹配
    const matchParticipants = matchParticipantsRange(activity.participants, filters.value.participants);
    
    // 部门匹配
    const matchDepartment = filters.value.department === '全部' || activity.organizer === filters.value.department;
    
    return matchSearch && matchType && matchStatus && matchParticipants && matchDepartment;
  });
  
  // 排序
  result = [...result].sort((a, b) => {
    let dateA, dateB;
    
    if (sortConfig.value.sortBy === '开始时间') {
      dateA = new Date(a.date);
      dateB = new Date(b.date);
    } else if (sortConfig.value.sortBy === '结束时间') {
      dateA = new Date(a.endDate);
      dateB = new Date(b.endDate);
    } else if (sortConfig.value.sortBy === '参与人数') {
      return sortConfig.value.sortOrder === '倒序' 
        ? b.participants - a.participants 
        : a.participants - b.participants;
    }
    
    return sortConfig.value.sortOrder === '倒序' 
      ? dateB - dateA 
      : dateA - dateB;
  });
  
  return result;
});

// 分页活动
const paginatedActivities = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredActivities.value.slice(start, end);
});

const totalPages = computed(() => Math.ceil(filteredActivities.value.length / pageSize));

// 重置筛选
function resetFilters() {
  searchQuery.value = '';
  filters.value = {
    type: '全部',
    status: '全部',
    participants: '全部',
    department: '全部'
  };
  sortConfig.value = {
    sortBy: '开始时间',
    sortOrder: '倒序',
    timeDimension: '月份'
  };
  currentPage.value = 1;
}

// 页码跳转
function goToPage(page) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
  }
}

// 页面加载
onMounted(() => {
  isLoading.value = true;
  fetchActivities();
  fetchMembers();
  loadDictionaryOptions();
  setTimeout(() => {
    isLoading.value = false;
  }, 500);
});
</script>

<template>
  <div class="activities-page">
    <header class="page-header">
      <h1>活动管理</h1>
    </header>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.label" class="stat-item">
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">{{ stat.label }}</div>
      </div>
    </div>
    
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="M21 21l-4.35-4.35"></path>
          </svg>
          <input type="text" v-model="searchQuery" placeholder="搜索活动名称或描述..." class="search-input" />
        </div>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedActivities.length > 0 && hasPermission('activity:delete')" class="btn btn-danger" @click="batchDelete">
          批量删除 ({{ selectedActivities.length }})
        </button>
        <button class="btn btn-secondary" @click="resetFilters">重置</button>
        <button v-if="hasPermission('activity:add')" class="btn btn-primary" @click="openCreateModal">创建活动</button>
      </div>
    </div>
    
    <!-- 筛选和排序 -->
    <div class="filter-sort-bar">
      <div class="filters">
        <div class="filter-item">
          <label>活动类型：</label>
          <select v-model="filters.type">
            <option v-for="type in activityTypes" :key="type" :value="type">{{ type }}</option>
          </select>
        </div>
        <div class="filter-item">
          <label>活动状态：</label>
          <select v-model="filters.status">
            <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
          </select>
        </div>
        <div class="filter-item">
          <label>参与人数：</label>
          <select v-model="filters.participants">
            <option v-for="range in participantRanges" :key="range" :value="range">{{ range }}</option>
          </select>
        </div>
        <div class="filter-item">
          <label>组织部门：</label>
          <select v-model="filters.department">
            <option v-for="dept in departments" :key="dept" :value="dept">{{ dept }}</option>
          </select>
        </div>
      </div>
      <div class="sort-controls">
        <div class="sort-item">
          <label>排序方式：</label>
          <select v-model="sortConfig.sortBy">
            <option v-for="option in sortByOptions" :key="option" :value="option">{{ option }}</option>
          </select>
        </div>
        <div class="sort-item" v-if="sortConfig.sortBy !== '参与人数'">
          <label>时间维度：</label>
          <select v-model="sortConfig.timeDimension">
            <option v-for="option in timeDimensionOptions" :key="option" :value="option">{{ option }}</option>
          </select>
        </div>
        <div class="sort-item">
          <label>排序：</label>
          <select v-model="sortConfig.sortOrder">
            <option v-for="option in sortOrderOptions" :key="option" :value="option">{{ option }}</option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="filteredActivities.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>暂无活动数据</h3>
      <p>请尝试调整筛选条件或创建新活动</p>
    </div>
    
    <!-- 活动列表 -->
    <div v-else class="activities-grid">
      <div class="select-all-box">
        <label class="checkbox-label">
          <input type="checkbox" :checked="selectedActivities.length === paginatedActivities.length && paginatedActivities.length > 0" @change="toggleSelectAll" />
          <span>全选</span>
        </label>
      </div>
      <div v-for="activity in paginatedActivities" :key="activity.id" class="activity-card">
        <label class="card-checkbox">
          <input type="checkbox" :checked="selectedActivities.includes(activity.id)" @change="toggleSelect(activity.id)" />
        </label>
        <div class="card-header">
          <span class="activity-icon">📅</span>
          <div class="card-header-right">
            <span class="activity-type">{{ activity.type }}</span>
            <span class="activity-status" :class="activity.status">
              {{ activity.status }}
            </span>
          </div>
        </div>
        <h3 class="activity-name" v-html="highlightText(activity.name, searchQuery)"></h3>
        <p class="activity-desc" v-html="highlightText(activity.description, searchQuery)"></p>
        <div class="activity-info">
          <p><span class="info-label">时间：</span>{{ activity.date }} ~ {{ activity.endDate }}</p>
          <p><span class="info-label">地点：</span>{{ activity.location }}</p>
          <p><span class="info-label">人数：</span>{{ activity.participants }}人</p>
        </div>
        <div class="card-footer">
          <span class="organizer">组织部门: {{ activity.organizer }}</span>
          <div class="actions">
            <button class="detail-btn" @click="openDetailModal(activity)">查看详情</button>
            <button v-if="hasPermission('activity:edit')" class="edit-btn" @click="openEditModal(activity)">编辑</button>
            <button v-if="hasPermission('activity:delete')" class="delete-btn" @click="deleteActivity(activity)">删除</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button class="page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
        上一页
      </button>
      <div class="page-numbers">
        <button
          v-for="page in totalPages"
          :key="page"
          class="page-number"
          :class="{ active: currentPage === page }"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
      </div>
      <button class="page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
        下一页
      </button>
    </div>
    
    <!-- 活动创建/编辑模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑活动' : '创建活动' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">活动名称 <span class="required">*</span></label>
            <input 
              type="text" 
              v-model="formData.name" 
              class="form-input" 
              placeholder="请输入活动名称" 
              maxlength="100"
            />
            <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
          </div>
          
          <div class="form-group">
            <label class="form-label">活动简介 <span class="required">*</span></label>
            <textarea 
              v-model="formData.description" 
              class="form-textarea" 
              placeholder="请输入活动简介"
              rows="4"
            ></textarea>
            <span v-if="formErrors.description" class="form-error">{{ formErrors.description }}</span>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">活动类型 <span class="required">*</span></label>
              <select v-model="formData.type" class="form-select">
                <option v-for="type in activityTypes.filter(t => t !== '全部')" :key="type" :value="type">{{ type }}</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">主办部门 <span class="required">*</span></label>
              <select v-model="formData.organizer" class="form-select">
                <option value="">请选择部门</option>
                <option v-for="dept in userDepartments" :key="dept" :value="dept">{{ dept }}</option>
              </select>
              <span v-if="formErrors.organizer" class="form-error">{{ formErrors.organizer }}</span>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">负责人 <span class="required">*</span></label>
            <select v-model="formData.organizerId" class="form-select">
              <option value="">请选择负责人</option>
              <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }} ({{ user.department }})</option>
            </select>
            <span v-if="formErrors.organizerId" class="form-error">{{ formErrors.organizerId }}</span>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">开始时间 <span class="required">*</span></label>
              <input 
                type="datetime-local" 
                v-model="formData.date" 
                class="form-input"
              />
              <span v-if="formErrors.date" class="form-error">{{ formErrors.date }}</span>
            </div>
            
            <div class="form-group">
              <label class="form-label">结束时间 <span class="required">*</span></label>
              <input 
                type="datetime-local" 
                v-model="formData.endDate" 
                class="form-input"
              />
              <span v-if="formErrors.endDate" class="form-error">{{ formErrors.endDate }}</span>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">活动地点 <span class="required">*</span></label>
            <input 
              type="text" 
              v-model="formData.location" 
              class="form-input" 
              placeholder="请输入活动地点"
            />
            <span v-if="formErrors.location" class="form-error">{{ formErrors.location }}</span>
          </div>
          
          <div class="form-group">
            <label class="form-label">预计参与人数</label>
            <input 
              type="number" 
              v-model.number="formData.participants" 
              class="form-input" 
              placeholder="请输入预计参与人数"
              min="0"
            />
            <span v-if="formErrors.participants" class="form-error">{{ formErrors.participants }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveActivity">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 活动详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeDetailModal">
      <div class="modal-content detail-modal" @click.stop>
        <div class="modal-header">
          <h2>活动详情</h2>
          <button class="close-btn" @click="closeDetailModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentActivity">
          <div class="detail-header">
            <div class="detail-icon">📅</div>
            <div class="detail-title-section">
              <h3 class="detail-title">{{ currentActivity.name }}</h3>
              <div class="detail-tags">
                <span class="detail-type">{{ currentActivity.type }}</span>
                <span class="detail-status" :class="currentActivity.status">{{ currentActivity.status }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <h4 class="section-title">活动简介</h4>
            <p class="detail-description">{{ currentActivity.description }}</p>
          </div>
          
          <div class="detail-info-grid">
            <div class="detail-info-item">
              <div class="info-icon">🏢</div>
              <div class="info-content">
                <div class="info-label">主办部门</div>
                <div class="info-value">{{ currentActivity.organizer }}</div>
              </div>
            </div>
            
            <div class="detail-info-item">
              <div class="info-icon">📍</div>
              <div class="info-content">
                <div class="info-label">活动地点</div>
                <div class="info-value">{{ currentActivity.location }}</div>
              </div>
            </div>
            
            <div class="detail-info-item">
              <div class="info-icon">👥</div>
              <div class="info-content">
                <div class="info-label">参与人数</div>
                <div class="info-value">{{ currentActivity.participants }}人</div>
              </div>
            </div>
            
            <div class="detail-info-item">
              <div class="info-icon">⏰</div>
              <div class="info-content">
                <div class="info-label">活动时间</div>
                <div class="info-value">{{ currentActivity.date }} ~ {{ currentActivity.endDate }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeDetailModal">关闭</button>
          <button v-if="hasPermission('activity:edit')" class="btn btn-primary" @click="openEditModal(currentActivity); closeDetailModal()">编辑</button>
        </div>
      </div>
    </div>
    
    <!-- 删除确认模态框 -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <h2>确认删除</h2>
          <button class="close-btn" @click="closeDeleteModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="delete-icon">⚠️</div>
          <p v-if="selectedActivities.length > 0">
            确定要删除选中的 {{ selectedActivities.length }} 个活动吗？此操作不可撤销。
          </p>
          <p v-else-if="currentActivity">
            确定要删除活动「{{ currentActivity.name }}」吗？此操作不可撤销。
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeDeleteModal">取消</button>
          <button class="btn btn-danger" @click="selectedActivities.length > 0 ? confirmBatchDelete() : confirmDelete()">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.activities-page {
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
  margin-bottom: 32px;
}

.stat-item {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: all 0.2s ease;
}

.stat-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666666;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #999;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
}

.search-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
  background: #ffffff;
  color: #666666;
  border: 1px solid #e8e8e8;
}

.btn-secondary:hover {
  background: #f5f5f5;
}

.filter-sort-bar {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.filters,
.sort-controls {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-item,
.sort-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label,
.sort-item label {
  font-size: 14px;
  color: #666666;
  white-space: nowrap;
}

.filter-item select,
.sort-item select {
  padding: 8px 12px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
  background: #ffffff;
  transition: all 0.2s ease;
}

.filter-item select:focus,
.sort-item select:focus {
  border-color: #667eea;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-container p {
  margin-top: 16px;
  color: #666666;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 600;
}

.empty-state p {
  font-size: 14px;
  color: #999;
}

.activities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.activity-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s ease;
}

.activity-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transform: translateY(-4px);
  border-color: #667eea;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.activity-icon {
  font-size: 28px;
}

.card-header-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.activity-type {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
  color: #5b21b6;
}

.activity-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.activity-status.进行中 {
  background: #e6f7ff;
  color: #1890ff;
}

.activity-status.已结束 {
  background: #f5f5f5;
  color: #666666;
}

.activity-status.筹备中 {
  background: #fff7e6;
  color: #fa8c16;
}

.activity-name {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 10px;
  line-height: 1.4;
}

.activity-desc {
  font-size: 14px;
  color: #666666;
  margin-bottom: 16px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.highlight {
  background: #fef08a;
  padding: 0 2px;
  border-radius: 2px;
}

.activity-info {
  margin-bottom: 16px;
}

.activity-info p {
  font-size: 13px;
  color: #8c8c8c;
  margin: 6px 0;
}

.info-label {
  color: #595959;
  font-weight: 500;
}

.card-footer {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.organizer {
  font-size: 13px;
  color: #8c8c8c;
}

.actions {
  display: flex;
  gap: 8px;
}

.detail-btn,
.edit-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.detail-btn {
  background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
  color: #5b21b6;
}

.detail-btn:hover {
  opacity: 0.8;
}

.edit-btn {
  background: #fff7e6;
  color: #fa8c16;
}

.edit-btn:hover {
  opacity: 0.8;
}

.delete-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fff1f0;
  color: #f5222d;
}

.delete-btn:hover {
  opacity: 0.8;
}

.select-all-box {
  grid-column: 1 / -1;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 16px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.card-checkbox {
  position: absolute;
  top: 16px;
  left: 16px;
}

.card-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.btn-danger {
  background: #ff4d4f;
  color: #ffffff;
}

.btn-danger:hover {
  background: #ff7875;
}

.delete-modal {
  max-width: 400px;
}

.delete-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 16px;
}

.delete-modal .modal-body p {
  text-align: center;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: #ffffff;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 8px;
}

.page-number {
  width: 36px;
  height: 36px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: #ffffff;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-number:hover {
  border-color: #667eea;
  color: #667eea;
}

.page-number.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  border-color: transparent;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-sort-bar {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .activities-page {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .stat-item {
    padding: 16px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .activities-grid {
    grid-template-columns: 1fr;
  }
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
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
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
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  line-height: 1;
  transition: color 0.2s ease;
}

.close-btn:hover {
  color: #666;
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e8e8e8;
}

/* 表单样式 */
.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-label {
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
.form-select,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  resize: vertical;
  line-height: 1.6;
}

.form-error {
  display: block;
  font-size: 12px;
  color: #ff4d4f;
  margin-top: 4px;
}

/* 详情模态框样式 */
.detail-modal {
  max-width: 700px;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-icon {
  font-size: 48px;
  line-height: 1;
}

.detail-title-section {
  flex: 1;
}

.detail-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.detail-tags {
  display: flex;
  gap: 8px;
  align-items: center;
}

.detail-type {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
  color: #5b21b6;
}

.detail-status {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.detail-status.进行中 {
  background: #e6f7ff;
  color: #1890ff;
}

.detail-status.已结束 {
  background: #f5f5f5;
  color: #666666;
}

.detail-status.筹备中 {
  background: #fff7e6;
  color: #fa8c16;
}

.detail-status.未开始 {
  background: #f0f9ff;
  color: #0284c7;
}

.detail-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.detail-description {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin: 0;
}

.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.info-icon {
  font-size: 24px;
  line-height: 1;
}

.info-content {
  flex: 1;
}

.info-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.info-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    max-width: 100%;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 16px;
  }
  
  .detail-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .detail-title-section {
    width: 100%;
  }
  
  .detail-tags {
    justify-content: center;
  }
  
  .detail-info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
