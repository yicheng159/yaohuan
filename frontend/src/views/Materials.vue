<script setup>
import { ref, computed, onMounted } from 'vue';
import { hasPermission } from '../utils/permission';

// 物资分类
const categories = ['电子设备', '家具', '户外活动', '宣传用品', '办公用品', '其他'];
const locations = ['仓库A区', '仓库B区', '仓库C区', '办公室', '会议室', '其他'];
const statusOptions = ['正常', '部分损坏', '需要维修', '报废'];

// 用户数据（从后端获取）
const users = ref([]);

// 物资数据（从后端获取）
const materials = ref([]);

// 借用记录（从后端获取）
const borrowRecords = ref([]);

// 操作日志
const operationLogs = ref([]);

// 从后端获取物资列表
const fetchMaterials = async () => {
  try {
    const response = await fetch('/api/materials/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      materials.value = results.map(item => ({
        id: item.id,
        name: item.name,
        model: item.specification,
        category: item.category,
        quantity: item.quantity,
        available: item.quantity - (item.borrowed_quantity || 0),
        unitPrice: item.price,
        entryDate: item.entry_date,
        location: item.storage_location,
        status: item.status,
        description: item.description
      }));
    }
  } catch (error) {
    console.error('获取物资列表失败:', error);
  }
};

// 从后端获取借用记录
const fetchBorrowRecords = async () => {
  try {
    const response = await fetch('/api/material-borrows/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      borrowRecords.value = results.map(record => ({
        id: record.id,
        borrowerId: '',
        borrowerName: record.borrower,
        borrowerDept: '',
        borrowerPhone: record.borrower_phone || '',
        borrowDate: record.borrow_date,
        expectedReturnDate: record.expected_return_date,
        actualReturnDate: record.actual_return_date,
        status: record.status,
        purpose: record.purpose || '',
        notes: record.notes || ''
      }));
    }
  } catch (error) {
    console.error('获取借用记录失败:', error);
  }
};

// 从后端获取成员列表作为借用人的选项
const fetchMembers = async () => {
  try {
    const response = await fetch('/api/members/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      users.value = results.map(member => ({
        id: member.id,
        name: member.name,
        department: member.department || '未知部门',
        phone: member.phone || ''
      }));
    }
  } catch (error) {
    console.error('获取成员列表失败:', error);
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchMaterials();
  fetchBorrowRecords();
  fetchMembers();
});

// 模态框状态
const showAddModal = ref(false);
const showBorrowModal = ref(false);
const showDetailModal = ref(false);
const showEditModal = ref(false);
const showLogModal = ref(false);
const showDeleteModal = ref(false);
const currentMaterial = ref(null);
const formErrors = ref({});
const selectedMaterials = ref([]);

// 添加物资表单
const addForm = ref({
  name: '',
  model: '',
  category: '电子设备',
  quantity: 0,
  unitPrice: 0,
  entryDate: '',
  location: '仓库A区',
  status: '正常',
  description: ''
});

// 借用物资表单
const borrowForm = ref({
  borrowerId: null,
  borrowerName: '',
  borrowerDept: '',
  borrowerPhone: '',
  materials: [{ materialId: null, materialName: '', quantity: 0 }],
  borrowDate: '',
  expectedReturnDate: '',
  purpose: '',
  notes: ''
});

// 编辑物资表单
const editForm = ref({});

// 搜索和筛选
const searchKeyword = ref('');
const filterCategory = ref('');
const filterStatus = ref('');

// 筛选后的物资列表
const filteredMaterials = computed(() => {
  return materials.value.filter(m => {
    const matchKeyword = !searchKeyword.value || 
      m.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      m.model.toLowerCase().includes(searchKeyword.value.toLowerCase());
    const matchCategory = !filterCategory.value || m.category === filterCategory.value;
    const matchStatus = !filterStatus.value || m.status === filterStatus.value;
    return matchKeyword && matchCategory && matchStatus;
  });
});

// 重置筛选
const resetFilters = () => {
  searchKeyword.value = '';
  filterCategory.value = '';
  filterStatus.value = '';
};

// 统计数据
const stats = computed(() => {
  const totalTypes = materials.value.length;
  const totalQuantity = materials.value.reduce((sum, m) => sum + m.quantity, 0);
  const borrowedQuantity = materials.value.reduce((sum, m) => sum + (m.quantity - m.available), 0);
  const normalCount = materials.value.filter(m => m.status === '正常').length;
  const goodRate = totalTypes > 0 ? Math.round((normalCount / totalTypes) * 100) : 0;
  
  return [
    { label: '物资种类', value: totalTypes },
    { label: '库存总量', value: totalQuantity },
    { label: '借出数量', value: borrowedQuantity },
    { label: '完好率', value: goodRate + '%' }
  ];
});

// 物资错误计算属性
const materialErrors = computed(() => {
  if (!formErrors.value) return [];
  return Object.entries(formErrors.value)
    .filter(([key]) => key.startsWith('material_'))
    .map(([key, error]) => ({ key, error }));
});

// 验证添加物资表单
function validateAddForm() {
  const errors = {};
  
  if (!addForm.value.name || addForm.value.name.trim() === '') {
    errors.name = '请输入物资名称';
  }
  
  // 检查重复物资
  const duplicate = materials.value.find(m => 
    m.name === addForm.value.name && m.model === addForm.value.model
  );
  if (duplicate) {
    errors.name = '该物资名称和型号已存在';
  }
  
  if (!addForm.value.model || addForm.value.model.trim() === '') {
    errors.model = '请输入型号规格';
  }
  
  if (addForm.value.quantity <= 0) {
    errors.quantity = '数量必须大于0';
  }
  
  if (addForm.value.unitPrice <= 0) {
    errors.unitPrice = '单价必须大于0';
  }
  
  if (!addForm.value.entryDate) {
    errors.entryDate = '请选择入库日期';
  }
  
  if (!addForm.value.description || addForm.value.description.trim() === '') {
    errors.description = '请输入物资描述';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 验证借用表单
function validateBorrowForm() {
  const errors = {};
  
  if (!borrowForm.value.borrowerName) {
    errors.borrowerName = '请填写借用人员姓名';
  }
  
  if (!borrowForm.value.borrowDate) {
    errors.borrowDate = '请选择借用日期';
  }
  
  if (!borrowForm.value.expectedReturnDate) {
    errors.expectedReturnDate = '请选择预计归还日期';
  } else if (new Date(borrowForm.value.expectedReturnDate) < new Date(borrowForm.value.borrowDate)) {
    errors.expectedReturnDate = '归还日期不能早于借用日期';
  }
  
  // 验证借用物资
  const validMaterials = borrowForm.value.materials.filter(m => m.materialId && m.quantity > 0);
  if (validMaterials.length === 0) {
    errors.materials = '请至少选择一项借用物资';
  }
  
  // 检查库存是否充足
  for (const item of borrowForm.value.materials) {
    if (item.materialId && item.quantity > 0) {
      const material = materials.value.find(m => m.id === item.materialId);
      if (material && item.quantity > material.available) {
        errors[`material_${item.materialId}`] = `${material.name}库存不足，当前可借${material.available}件`;
      }
    }
  }
  
  if (!borrowForm.value.purpose || borrowForm.value.purpose.trim() === '') {
    errors.purpose = '请输入借用用途';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 打开添加物资模态框
function openAddModal() {
  addForm.value = {
    name: '',
    model: '',
    category: '电子设备',
    quantity: 0,
    unitPrice: 0,
    entryDate: new Date().toISOString().split('T')[0],
    location: '仓库A区',
    status: '正常',
    description: ''
  };
  formErrors.value = {};
  showAddModal.value = true;
}

// 获取当前登录用户信息
function getCurrentUser() {
  try {
    const userInfo = localStorage.getItem('user');
    if (userInfo) {
      return JSON.parse(userInfo);
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
  }
  return null;
}

// 打开借用物资模态框
function openBorrowModal(material = null) {
  const currentUser = getCurrentUser();
  
  borrowForm.value = {
    borrowerId: currentUser?.student_id || null,
    borrowerName: currentUser?.member_name || currentUser?.student_id || '',
    borrowerDept: currentUser?.member_department || '',
    borrowerPhone: '',
    materials: [{ materialId: material?.id || null, materialName: material?.name || '', quantity: 1 }],
    borrowDate: new Date().toISOString().split('T')[0],
    expectedReturnDate: '',
    purpose: '',
    notes: ''
  };
  formErrors.value = {};
  showBorrowModal.value = true;
}

// 打开物资详情模态框
function openDetailModal(material) {
  currentMaterial.value = material;
  showDetailModal.value = true;
}

// 打开编辑物资模态框
function openEditModal(material) {
  editForm.value = { ...material };
  formErrors.value = {};
  showEditModal.value = true;
}

// 打开操作日志模态框
function openLogModal() {
  showLogModal.value = true;
}

// 关闭所有模态框
function closeModals() {
  showAddModal.value = false;
  showBorrowModal.value = false;
  showDetailModal.value = false;
  showEditModal.value = false;
  showLogModal.value = false;
  showDeleteModal.value = false;
  currentMaterial.value = null;
  formErrors.value = {};
}

// 删除单个物资
function deleteMaterial(material) {
  currentMaterial.value = material;
  showDeleteModal.value = true;
}

// 确认删除
function confirmDelete() {
  if (currentMaterial.value) {
    const index = materials.value.findIndex(m => m.id === currentMaterial.value.id);
    if (index !== -1) {
      materials.value.splice(index, 1);
    }
    
    // 记录操作日志
    operationLogs.value.unshift({
      id: operationLogs.value.length + 1,
      operation: '删除物资',
      operator: '管理员',
      target: currentMaterial.value.name,
      time: new Date().toLocaleString('zh-CN'),
      details: `删除物资: ${currentMaterial.value.name}`
    });
  }
  closeDeleteModal();
}

// 关闭删除模态框
function closeDeleteModal() {
  showDeleteModal.value = false;
  currentMaterial.value = null;
}

// 切换单个选择
function toggleSelect(materialId) {
  const index = selectedMaterials.value.indexOf(materialId);
  if (index === -1) {
    selectedMaterials.value.push(materialId);
  } else {
    selectedMaterials.value.splice(index, 1);
  }
}

// 全选/取消全选
function toggleSelectAll() {
  if (selectedMaterials.value.length === materials.value.length) {
    selectedMaterials.value = [];
  } else {
    selectedMaterials.value = materials.value.map(m => m.id);
  }
}

// 批量删除
function batchDelete() {
  showDeleteModal.value = true;
}

// 确认批量删除
function confirmBatchDelete() {
  const deletedNames = materials.value
    .filter(m => selectedMaterials.value.includes(m.id))
    .map(m => m.name);
  
  materials.value = materials.value.filter(m => !selectedMaterials.value.includes(m.id));
  
  // 记录操作日志
  operationLogs.value.unshift({
    id: operationLogs.value.length + 1,
    operation: '批量删除物资',
    operator: '管理员',
    target: deletedNames.join(', '),
    time: new Date().toLocaleString('zh-CN'),
    details: `批量删除${selectedMaterials.value.length}件物资`
  });
  
  selectedMaterials.value = [];
  closeDeleteModal();
}

// 添加物资
async function addMaterial() {
  if (!validateAddForm()) {
    return;
  }
  
  const apiData = {
    name: addForm.value.name,
    specification: addForm.value.model,
    category: addForm.value.category,
    quantity: addForm.value.quantity,
    price: addForm.value.unitPrice,
    entry_date: addForm.value.entryDate,
    storage_location: addForm.value.location,
    status: addForm.value.status,
    description: addForm.value.description
  };
  
  try {
    const response = await fetch('/api/materials/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const result = await response.json();
      const newMaterial = {
        id: result.id,
        name: result.name,
        model: result.specification,
        category: result.category,
        quantity: result.quantity,
        available: result.quantity - (result.borrowed_quantity || 0),
        unitPrice: result.price,
        entryDate: result.entry_date,
        location: result.storage_location,
        status: result.status,
        description: result.description
      };
      materials.value.push(newMaterial);
      alert('物资添加成功！');
      closeModals();
    } else {
      alert('添加物资失败');
    }
  } catch (error) {
    console.error('添加物资失败:', error);
    alert('添加物资失败，请检查网络连接');
  }
}

// 添加借用物资项
function addBorrowItem() {
  borrowForm.value.materials.push({ materialId: null, materialName: '', quantity: 1 });
}

// 移除借用物资项
function removeBorrowItem(index) {
  if (borrowForm.value.materials.length > 1) {
    borrowForm.value.materials.splice(index, 1);
  }
}

// 选择物资时更新名称
function onMaterialSelect(index) {
  const materialId = borrowForm.value.materials[index].materialId;
  if (materialId) {
    const material = materials.value.find(m => m.id === materialId);
    if (material) {
      borrowForm.value.materials[index].materialName = material.name;
    }
  }
}

// 选择借用人员时更新信息
function onUserSelect() {
  const userId = borrowForm.value.borrowerId;
  if (userId) {
    const user = users.value.find(u => u.id === userId);
    if (user) {
      borrowForm.value.borrowerName = user.name;
      borrowForm.value.borrowerDept = user.department;
      borrowForm.value.borrowerPhone = user.phone;
    }
  }
}

// 提交借用申请
async function submitBorrow() {
  if (!validateBorrowForm()) {
    return;
  }
  
  const borrowItems = borrowForm.value.materials.filter(m => m.materialId && m.quantity > 0);
  
  const apiData = {
    borrower: borrowForm.value.borrowerName,
    borrower_phone: borrowForm.value.borrowerPhone,
    borrow_date: borrowForm.value.borrowDate,
    expected_return_date: borrowForm.value.expectedReturnDate,
    purpose: borrowForm.value.purpose,
    notes: borrowForm.value.notes
  };
  
  try {
    const response = await fetch('/api/material-borrows/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const result = await response.json();
      
      // 更新物资库存
      for (const item of borrowItems) {
        const material = materials.value.find(m => m.id === item.materialId);
        if (material) {
          material.available -= item.quantity;
        }
      }
      
      // 创建借用记录
      const newRecord = {
        id: result.id,
        borrowerId: borrowForm.value.borrowerId,
        borrowerName: result.borrower,
        borrowerDept: borrowForm.value.borrowerDept || '',
        borrowerPhone: result.borrower_phone || '',
        borrowDate: result.borrow_date,
        expectedReturnDate: result.expected_return_date,
        actualReturnDate: result.actual_return_date,
        status: result.status,
        purpose: result.purpose || '',
        notes: result.notes || ''
      };
      
      borrowRecords.value.unshift(newRecord);
      alert('借用申请提交成功！');
      closeModals();
    } else {
      alert('提交借用申请失败');
    }
  } catch (error) {
    console.error('提交借用申请失败:', error);
    alert('提交借用申请失败，请检查网络连接');
  }
}

// 编辑物资
async function editMaterial() {
  const apiData = {
    name: editForm.value.name,
    specification: editForm.value.model,
    category: editForm.value.category,
    quantity: editForm.value.quantity,
    price: editForm.value.unitPrice,
    entry_date: editForm.value.entryDate,
    storage_location: editForm.value.location,
    status: editForm.value.status,
    description: editForm.value.description
  };
  
  try {
    const response = await fetch(`/api/materials/${editForm.value.id}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(apiData)
    });
    
    if (response.ok) {
      const result = await response.json();
      const index = materials.value.findIndex(m => m.id === editForm.value.id);
      if (index !== -1) {
        materials.value[index] = {
          id: result.id,
          name: result.name,
          model: result.specification,
          category: result.category,
          quantity: result.quantity,
          available: result.quantity - (result.borrowed_quantity || 0),
          unitPrice: result.price,
          entryDate: result.entry_date,
          location: result.storage_location,
          status: result.status,
          description: result.description
        };
      }
      alert('物资编辑成功！');
      closeModals();
    } else {
      alert('编辑物资失败');
    }
  } catch (error) {
    console.error('编辑物资失败:', error);
    alert('编辑物资失败，请检查网络连接');
  }
}

// 归还物资
async function returnMaterial(record) {
  try {
    const response = await fetch(`/api/material-borrows/${record.id}/return_borrow/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (response.ok) {
      const result = await response.json();
      
      // 更新借用记录状态
      record.status = '已归还';
      record.actualReturnDate = result.data?.actual_return_date || new Date().toISOString().split('T')[0];
      
      // 更新物资库存
      fetchMaterials();
      
      alert('物资归还成功！');
    } else {
      alert('归还物资失败');
    }
  } catch (error) {
    console.error('归还物资失败:', error);
    alert('归还物资失败，请检查网络连接');
  }
}
</script>

<template>
  <div class="materials-page">
    <header class="page-header">
      <h1>物资管理</h1>
    </header>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.label" class="stat-item">
        <div class="stat-icon">📦</div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>
    
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-secondary" @click="openLogModal">操作日志</button>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedMaterials.length > 0 && hasPermission('material:delete')" class="btn btn-danger" @click="batchDelete">
          批量删除 ({{ selectedMaterials.length }})
        </button>
        <button v-if="hasPermission('material:add')" class="btn btn-primary" @click="openAddModal">添加物资</button>
        <button v-if="hasPermission('material:edit')" class="btn btn-secondary" @click="openBorrowModal">借用登记</button>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <input 
          type="text" 
          v-model="searchKeyword" 
          placeholder="搜索物资名称或型号..." 
          class="search-input"
        />
      </div>
      <div class="filter-item">
        <select v-model="filterCategory" class="filter-select">
          <option value="">全部分类</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
      <div class="filter-item">
        <select v-model="filterStatus" class="filter-select">
          <option value="">全部状态</option>
          <option value="正常">正常</option>
          <option value="损坏">损坏</option>
          <option value="维修中">维修中</option>
          <option value="已报废">已报废</option>
        </select>
      </div>
      <div class="filter-item">
        <button class="btn btn-secondary" @click="resetFilters">重置</button>
      </div>
    </div>
    
    <!-- 物资列表 -->
    <div class="table-container">
      <table class="materials-table">
        <thead>
          <tr>
            <th>
              <label class="checkbox-label">
                <input type="checkbox" :checked="selectedMaterials.length === materials.length && materials.length > 0" @change="toggleSelectAll" />
              </label>
            </th>
            <th>物资名称</th>
            <th>型号规格</th>
            <th>分类</th>
            <th>总数量</th>
            <th>可借用</th>
            <th>单价</th>
            <th>入库日期</th>
            <th>存放位置</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="material in filteredMaterials" :key="material.id">
            <td>
              <label class="checkbox-label">
                <input type="checkbox" :checked="selectedMaterials.includes(material.id)" @change="toggleSelect(material.id)" />
              </label>
            </td>
            <td>{{ material.name }}</td>
            <td>{{ material.model }}</td>
            <td><span class="category-tag">{{ material.category }}</span></td>
            <td>{{ material.quantity }}</td>
            <td><span class="available-tag">{{ material.available }}</span></td>
            <td>¥{{ material.unitPrice }}</td>
            <td>{{ material.entryDate }}</td>
            <td>{{ material.location }}</td>
            <td><span class="status-tag" :class="material.status">{{ material.status }}</span></td>
            <td>
              <button class="action-btn view" @click="openDetailModal(material)">查看</button>
              <button v-if="hasPermission('material:edit')" class="action-btn edit" @click="openEditModal(material)">编辑</button>
              <button v-if="hasPermission('material:edit')" class="action-btn borrow" @click="openBorrowModal(material)">借用</button>
              <button v-if="hasPermission('material:delete')" class="action-btn delete" @click="deleteMaterial(material)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 借用记录 -->
    <div class="borrow-records-section">
      <h2 class="section-title">借用记录</h2>
      <div class="borrow-records-grid">
        <div v-for="record in borrowRecords" :key="record.id" class="borrow-record-card">
          <div class="record-header">
            <span class="record-id">#{{ record.id }}</span>
            <span class="record-status" :class="record.status">{{ record.status }}</span>
          </div>
          <div class="record-body">
            <div class="record-info">
              <p><span class="label">借用人：</span>{{ record.borrowerName }} ({{ record.borrowerDept }})</p>
              <p><span class="label">借用日期：</span>{{ record.borrowDate }}</p>
              <p><span class="label">预计归还：</span>{{ record.expectedReturnDate }}</p>
              <p v-if="record.actualReturnDate"><span class="label">实际归还：</span>{{ record.actualReturnDate }}</p>
            </div>
            <div class="borrowed-materials">
              <p class="label">借用物资：</p>
              <div class="material-list">
                <span v-for="item in record.materials" :key="item.materialId" class="material-item">
                  {{ item.materialName }} ({{ item.quantity }}件)
                </span>
              </div>
            </div>
            <div class="record-purpose">
              <p><span class="label">用途：</span>{{ record.purpose }}</p>
            </div>
          </div>
          <div class="record-footer">
            <button v-if="record.status === '借用中'" class="btn btn-return" @click="returnMaterial(record)">归还</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 添加物资模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>添加物资</h2>
          <button class="close-btn" @click="closeModals">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">物资名称 <span class="required">*</span></label>
            <input type="text" v-model="addForm.name" class="form-input" placeholder="请输入物资名称" />
            <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
          </div>
          
          <div class="form-group">
            <label class="form-label">型号规格 <span class="required">*</span></label>
            <input type="text" v-model="addForm.model" class="form-input" placeholder="请输入型号规格" />
            <span v-if="formErrors.model" class="form-error">{{ formErrors.model }}</span>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">分类 <span class="required">*</span></label>
              <select v-model="addForm.category" class="form-select">
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">存放位置 <span class="required">*</span></label>
              <select v-model="addForm.location" class="form-select">
                <option v-for="loc in locations" :key="loc" :value="loc">{{ loc }}</option>
              </select>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">数量 <span class="required">*</span></label>
              <input type="number" v-model.number="addForm.quantity" class="form-input" min="1" />
              <span v-if="formErrors.quantity" class="form-error">{{ formErrors.quantity }}</span>
            </div>
            
            <div class="form-group">
              <label class="form-label">单价(元) <span class="required">*</span></label>
              <input type="number" v-model.number="addForm.unitPrice" class="form-input" min="0" step="0.01" />
              <span v-if="formErrors.unitPrice" class="form-error">{{ formErrors.unitPrice }}</span>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">入库日期 <span class="required">*</span></label>
              <input type="date" v-model="addForm.entryDate" class="form-input" />
              <span v-if="formErrors.entryDate" class="form-error">{{ formErrors.entryDate }}</span>
            </div>
            
            <div class="form-group">
              <label class="form-label">状态</label>
              <select v-model="addForm.status" class="form-select">
                <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
              </select>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">物资描述 <span class="required">*</span></label>
            <textarea v-model="addForm.description" class="form-textarea" placeholder="请输入物资描述" rows="3"></textarea>
            <span v-if="formErrors.description" class="form-error">{{ formErrors.description }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModals">取消</button>
          <button class="btn btn-primary" @click="addMaterial">添加</button>
        </div>
      </div>
    </div>
    
    <!-- 借用物资模态框 -->
    <div v-if="showBorrowModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-content borrow-modal" @click.stop>
        <div class="modal-header">
          <h2>借用登记</h2>
          <button class="close-btn" @click="closeModals">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">借用人员 <span class="required">*</span></label>
            <select v-model="borrowForm.borrowerId" class="form-select" @change="onUserSelect">
              <option value="">请选择借用人员</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ user.name }} ({{ user.department }})
              </option>
            </select>
            <span v-if="formErrors.borrowerId" class="form-error">{{ formErrors.borrowerId }}</span>
          </div>
          
          <div class="borrower-info" v-if="borrowForm.borrowerId">
            <div class="info-item">
              <span class="label">姓名：</span>{{ borrowForm.borrowerName }}
            </div>
            <div class="info-item">
              <span class="label">部门：</span>{{ borrowForm.borrowerDept }}
            </div>
            <div class="info-item">
              <span class="label">电话：</span>{{ borrowForm.borrowerPhone }}
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">借用物资 <span class="required">*</span></label>
            <div class="borrow-items">
              <div v-for="(item, index) in borrowForm.materials" :key="index" class="borrow-item">
                <select v-model="item.materialId" class="form-select" @change="onMaterialSelect(index)">
                  <option value="">请选择物资</option>
                  <option v-for="material in materials" :key="material.id" :value="material.id">
                    {{ material.name }} (库存: {{ material.available }}件)
                  </option>
                </select>
                <input type="number" v-model.number="item.quantity" class="form-input quantity-input" min="1" placeholder="数量" />
                <button v-if="borrowForm.materials.length > 1" class="remove-btn" @click="removeBorrowItem(index)">删除</button>
              </div>
            </div>
            <button class="btn btn-add-item" @click="addBorrowItem">+ 添加物资</button>
            <span v-if="formErrors && formErrors.materials" class="form-error">{{ formErrors.materials }}</span>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">借用日期 <span class="required">*</span></label>
              <input type="date" v-model="borrowForm.borrowDate" class="form-input" />
              <span v-if="formErrors.borrowDate" class="form-error">{{ formErrors.borrowDate }}</span>
            </div>
            
            <div class="form-group">
              <label class="form-label">预计归还日期 <span class="required">*</span></label>
              <input type="date" v-model="borrowForm.expectedReturnDate" class="form-input" />
              <span v-if="formErrors.expectedReturnDate" class="form-error">{{ formErrors.expectedReturnDate }}</span>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">借用用途 <span class="required">*</span></label>
            <input type="text" v-model="borrowForm.purpose" class="form-input" placeholder="请输入借用用途" />
            <span v-if="formErrors.purpose" class="form-error">{{ formErrors.purpose }}</span>
          </div>
          
          <div class="form-group">
            <label class="form-label">备注</label>
            <textarea v-model="borrowForm.notes" class="form-textarea" placeholder="请输入备注信息" rows="2"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModals">取消</button>
          <button class="btn btn-primary" @click="submitBorrow">提交</button>
        </div>
      </div>
    </div>
    
    <!-- 物资详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-content detail-modal" @click.stop>
        <div class="modal-header">
          <h2>物资详情</h2>
          <button class="close-btn" @click="closeModals">&times;</button>
        </div>
        <div class="modal-body" v-if="currentMaterial">
          <div class="detail-header">
            <div class="detail-icon">📦</div>
            <div class="detail-title-section">
              <h3 class="detail-title">{{ currentMaterial.name }}</h3>
              <div class="detail-tags">
                <span class="detail-category">{{ currentMaterial.category }}</span>
                <span class="detail-status" :class="currentMaterial.status">{{ currentMaterial.status }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <h4 class="section-title">基本信息</h4>
            <div class="detail-info-grid">
              <div class="detail-info-item">
                <div class="info-label">型号规格</div>
                <div class="info-value">{{ currentMaterial.model }}</div>
              </div>
              <div class="detail-info-item">
                <div class="info-label">总数量</div>
                <div class="info-value">{{ currentMaterial.quantity }}件</div>
              </div>
              <div class="detail-info-item">
                <div class="info-label">可借用</div>
                <div class="info-value">{{ currentMaterial.available }}件</div>
              </div>
              <div class="detail-info-item">
                <div class="info-label">单价</div>
                <div class="info-value">¥{{ currentMaterial.unitPrice }}</div>
              </div>
              <div class="detail-info-item">
                <div class="info-label">入库日期</div>
                <div class="info-value">{{ currentMaterial.entryDate }}</div>
              </div>
              <div class="detail-info-item">
                <div class="info-label">存放位置</div>
                <div class="info-value">{{ currentMaterial.location }}</div>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <h4 class="section-title">物资描述</h4>
            <p class="detail-description">{{ currentMaterial.description }}</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModals">关闭</button>
          <button class="btn btn-primary" @click="openEditModal(currentMaterial); closeModals()">编辑</button>
        </div>
      </div>
    </div>
    
    <!-- 编辑物资模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>编辑物资</h2>
          <button class="close-btn" @click="closeModals">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">物资名称</label>
            <input type="text" v-model="editForm.name" class="form-input" />
          </div>
          
          <div class="form-group">
            <label class="form-label">型号规格</label>
            <input type="text" v-model="editForm.model" class="form-input" />
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">分类</label>
              <select v-model="editForm.category" class="form-select">
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">存放位置</label>
              <select v-model="editForm.location" class="form-select">
                <option v-for="loc in locations" :key="loc" :value="loc">{{ loc }}</option>
              </select>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">总数量</label>
              <input type="number" v-model.number="editForm.quantity" class="form-input" min="0" />
            </div>
            
            <div class="form-group">
              <label class="form-label">可借用数量</label>
              <input type="number" v-model.number="editForm.available" class="form-input" min="0" />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">单价(元)</label>
              <input type="number" v-model.number="editForm.unitPrice" class="form-input" min="0" step="0.01" />
            </div>
            
            <div class="form-group">
              <label class="form-label">状态</label>
              <select v-model="editForm.status" class="form-select">
                <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
              </select>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">物资描述</label>
            <textarea v-model="editForm.description" class="form-textarea" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModals">取消</button>
          <button class="btn btn-primary" @click="editMaterial">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 操作日志模态框 -->
    <div v-if="showLogModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-content log-modal" @click.stop>
        <div class="modal-header">
          <h2>操作日志</h2>
          <button class="close-btn" @click="closeModals">&times;</button>
        </div>
        <div class="modal-body">
          <div class="log-list">
            <div v-for="log in operationLogs" :key="log.id" class="log-item">
              <div class="log-header">
                <span class="log-operation" :class="log.operation">{{ log.operation }}</span>
                <span class="log-time">{{ log.time }}</span>
              </div>
              <div class="log-body">
                <p><span class="label">操作人：</span>{{ log.operator }}</p>
                <p><span class="label">目标：</span>{{ log.target }}</p>
                <p><span class="label">详情：</span>{{ log.details }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModals">关闭</button>
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
          <p v-if="selectedMaterials.length > 0">
            确定要删除选中的 {{ selectedMaterials.length }} 个物资吗？此操作不可撤销。
          </p>
          <p v-else-if="currentMaterial">
            确定要删除物资「{{ currentMaterial.name }}」吗？此操作不可撤销。
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeDeleteModal">取消</button>
          <button class="btn btn-danger" @click="selectedMaterials.length > 0 ? confirmBatchDelete() : confirmDelete()">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.materials-page {
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
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.2s ease;
}

.stat-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 28px;
  opacity: 0.8;
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
  margin-bottom: 24px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-weight: 500;
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

.table-container {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 32px;
}

.materials-table {
  width: 100%;
  border-collapse: collapse;
}

.materials-table th,
.materials-table td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.materials-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333333;
  font-size: 14px;
}

.materials-table td {
  font-size: 14px;
  color: #333333;
}

.materials-table tbody tr:hover {
  background: #fafafa;
}

.category-tag {
  padding: 4px 12px;
  background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
  color: #5b21b6;
  border-radius: 4px;
  font-size: 12px;
}

.available-tag {
  padding: 4px 12px;
  background: #f6ffed;
  color: #52c41a;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.正常 {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.部分损坏 {
  background: #fff7e6;
  color: #fa8c16;
}

.status-tag.需要维修 {
  background: #fff1f0;
  color: #f5222d;
}

.status-tag.报废 {
  background: #f5f5f5;
  color: #8c8c8c;
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

.action-btn.view {
  background: #e6f7ff;
  color: #1890ff;
}

.action-btn.edit {
  background: #fff7e6;
  color: #fa8c16;
}

.action-btn.borrow {
  background: #f6ffed;
  color: #52c41a;
}

.action-btn.delete {
  background: #fff1f0;
  color: #f5222d;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
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

.borrow-records-section {
  margin-top: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 20px;
}

.borrow-records-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.borrow-record-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

.borrow-record-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.record-id {
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.record-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.record-status.借用中 {
  background: #e6f7ff;
  color: #1890ff;
}

.record-status.已归还 {
  background: #f6ffed;
  color: #52c41a;
}

.record-body {
  margin-bottom: 16px;
}

.record-info p,
.borrowed-materials p,
.record-purpose p {
  margin: 8px 0;
  font-size: 13px;
  color: #666;
}

.label {
  color: #8c8c8c;
  font-weight: 500;
}

.material-list {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.material-item {
  padding: 4px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
  color: #333;
}

.record-footer {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.btn-return {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
  padding: 8px 16px;
}

.btn-return:hover {
  background: #d9f7be;
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

.borrow-modal {
  max-width: 700px;
}

.detail-modal {
  max-width: 700px;
}

.log-modal {
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

.borrower-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  margin-bottom: 20px;
}

.info-item {
  font-size: 13px;
}

.borrow-items {
  margin-bottom: 12px;
}

.borrow-item {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  align-items: center;
}

.borrow-item .form-select {
  flex: 1;
}

.quantity-input {
  width: 100px;
}

.remove-btn {
  padding: 8px 12px;
  background: #fff1f0;
  color: #f5222d;
  border: 1px solid #ffa39e;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.remove-btn:hover {
  background: #ffccc7;
}

.btn-add-item {
  background: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
  padding: 8px 16px;
  font-size: 13px;
}

.btn-add-item:hover {
  background: #bae7ff;
}

/* 详情模态框样式 */
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

.detail-category {
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

.detail-status.正常 {
  background: #f6ffed;
  color: #52c41a;
}

.detail-status.部分损坏 {
  background: #fff7e6;
  color: #fa8c16;
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

.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.detail-info-item {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.detail-info-item .info-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.detail-info-item .info-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.detail-description {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin: 0;
}

/* 操作日志样式 */
.log-list {
  max-height: 500px;
  overflow-y: auto;
}

.log-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.log-operation {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.log-operation.添加物资 {
  background: #f6ffed;
  color: #52c41a;
}

.log-operation.借用物资 {
  background: #e6f7ff;
  color: #1890ff;
}

.log-operation.归还物资 {
  background: #fff7e6;
  color: #fa8c16;
}

.log-operation.编辑物资 {
  background: #f0f9ff;
  color: #0284c7;
}

.log-time {
  font-size: 12px;
  color: #8c8c8c;
}

.log-body p {
  margin: 4px 0;
  font-size: 13px;
  color: #666;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .detail-info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .materials-page {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .borrower-info {
    grid-template-columns: 1fr;
  }
  
  .borrow-item {
    flex-direction: column;
  }
  
  .quantity-input {
    width: 100%;
  }
  
  .detail-info-grid {
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
}
</style>