<script setup>
import { ref, computed, onMounted } from 'vue';
import * as XLSX from 'xlsx';
import { hasPermission } from '../../utils/permission';

// Excel表头映射
const excelHeaders = [
  '姓名', '青马班编号', '班级', '学号', '性别', '联系方式', '辅导员姓名', '辅导员联系方式'
];

// Excel数据字段映射
const fieldMapping = {
  '姓名': 'name',
  '青马班编号': 'classCode',
  '班级': 'department',
  '学号': 'studentId',
  '性别': 'gender',
  '联系方式': 'phone',
  '辅导员姓名': 'counselorName',
  '辅导员联系方式': 'counselorPhone'
};

// 青马班数据（从后端获取）
const classes = ref([]);

// 学员数据（从后端获取）
const students = ref([]);

// 课程数据（从后端获取）
const courses = ref([]);

// 从后端获取青马班列表
const fetchClasses = async () => {
  try {
    const response = await fetch('/api/qingma-classes/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      classes.value = results.map(item => ({
        id: item.id,
        classCode: item.code,
        name: item.name,
        session: item.session,
        teacher: item.headmaster,
        teacherPhone: item.headmaster_phone,
        startDate: item.start_date,
        endDate: item.end_date,
        maxStudents: item.max_students,
        currentStudents: item.current_students,
        status: item.status,
        description: item.description
      }));
    }
  } catch (error) {
    console.error('获取青马班列表失败:', error);
  }
};

// 从后端获取学员列表
const fetchStudents = async () => {
  try {
    const response = await fetch('/api/qingma-students/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      students.value = results.map(item => ({
        id: item.id,
        name: item.name,
        studentId: item.student_id,
        classId: item.qingma_class,
        session: item.session,
        grade: item.grade,
        department: item.department,
        gender: item.gender,
        phone: item.phone,
        email: item.email,
        counselorName: item.counselor_name,
        counselorPhone: item.counselor_phone,
        status: item.status
      }));
    }
  } catch (error) {
    console.error('获取学员列表失败:', error);
  }
};

// 从后端获取课程列表
const fetchCourses = async () => {
  try {
    const response = await fetch('/api/qingma-courses/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const results = data.results || data;
      courses.value = results.map(item => ({
        id: item.id,
        classId: item.qingma_class,
        name: item.name,
        teacher: item.teacher,
        type: item.course_type,
        hours: item.hours,
        credits: item.credits,
        time: item.course_time ? item.course_time.replace('Z', '').slice(0, 16) : '',
        location: item.location,
        status: item.status
      }));
    }
  } catch (error) {
    console.error('获取课程列表失败:', error);
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchClasses();
  fetchStudents();
  fetchCourses();
});

// 模态框状态
const showClassModal = ref(false);
const showStudentModal = ref(false);
const showCourseModal = ref(false);
const showClassDetailModal = ref(false);
const showCourseScheduleModal = ref(false);
const isEdit = ref(false);
const currentClass = ref(null);
const currentStudent = ref(null);
const currentCourse = ref(null);
const formErrors = ref({});
const activeTab = ref('classes');

// 班级表单数据
const classFormData = ref({
  classCode: '',
  name: '',
  session: '',
  teacher: '',
  teacherPhone: '',
  startDate: '',
  endDate: '',
  maxStudents: 50,
  description: ''
});

// 学员表单数据
const studentFormData = ref({
  name: '',
  studentId: '',
  classId: '',
  session: '',
  grade: '',
  department: '',
  gender: '男',
  phone: '',
  email: '',
  counselorName: '',
  counselorPhone: '',
  status: '在读'
});

// 课程表单数据
const courseFormData = ref({
  classId: '',
  name: '',
  teacher: '',
  type: '理论课',
  hours: 0,
  credits: 0,
  time: '',
  location: '',
  status: '进行中'
});

// 搜索和筛选
const classSearchQuery = ref('');
const studentSearchQuery = ref('');
const courseSearchQuery = ref('');
const selectedClassId = ref('');

// 分页
const studentPageSize = 8;
const studentCurrentPage = ref(1);

// 学院列表
const departments = ['计算机学院', '商学院', '文学院', '工学院', '理学院', '医学院', '艺术学院', '体育学院'];

// 年级列表
const grades = ['2021级', '2022级', '2023级', '2024级', '2025级'];

// 课程类型
const courseTypes = ['理论课', '实践课', '研讨课', '专题讲座'];

// 统计数据
const classStats = computed(() => {
  const total = classes.value.length;
  const active = classes.value.filter(c => c.status === '进行中').length;
  const preparing = classes.value.filter(c => c.status === '筹备中').length;
  const completed = classes.value.filter(c => c.status === '已结业').length;
  
  return [
    { label: '班级总数', value: total },
    { label: '进行中', value: active },
    { label: '筹备中', value: preparing },
    { label: '已结业', value: completed }
  ];
});

// 筛选后的班级
const filteredClasses = computed(() => {
  return classes.value.filter(c => {
    return !classSearchQuery.value || 
      c.name.toLowerCase().includes(classSearchQuery.value.toLowerCase()) ||
      c.session.includes(classSearchQuery.value);
  });
});

// 筛选后的学员
const filteredStudents = computed(() => {
  return students.value.filter(s => {
    const matchClass = !selectedClassId.value || s.classId === selectedClassId.value;
    const matchSearch = !studentSearchQuery.value || 
      s.name.toLowerCase().includes(studentSearchQuery.value.toLowerCase()) ||
      s.studentId.includes(studentSearchQuery.value) ||
      s.department.includes(studentSearchQuery.value);
    return matchClass && matchSearch;
  });
});

// 分页后的学员
const paginatedStudents = computed(() => {
  const start = (studentCurrentPage.value - 1) * studentPageSize;
  const end = start + studentPageSize;
  return filteredStudents.value.slice(start, end);
});

// 学员总页数
const studentTotalPages = computed(() => {
  return Math.ceil(filteredStudents.value.length / studentPageSize);
});

// 筛选后的课程
const filteredCourses = computed(() => {
  return courses.value.filter(c => {
    const matchClass = !selectedClassId.value || c.classId === selectedClassId.value;
    const matchSearch = !courseSearchQuery.value || 
      c.name.toLowerCase().includes(courseSearchQuery.value.toLowerCase()) ||
      c.teacher.includes(courseSearchQuery.value);
    return matchClass && matchSearch;
  });
});

// 获取班级名称
function getClassName(classId) {
  const cls = classes.value.find(c => c.id === classId);
  return cls ? cls.name : '';
}

// 验证班级表单
function validateClassForm() {
  const errors = {};
  
  if (!classFormData.value.classCode) errors.classCode = '请输入班级编号';
  if (!classFormData.value.name) errors.name = '请输入班级名称';
  if (!classFormData.value.session) errors.session = '请输入届数';
  if (!classFormData.value.teacher) errors.teacher = '请输入班主任姓名';
  if (!classFormData.value.teacherPhone) errors.teacherPhone = '请输入班主任联系方式';
  if (!classFormData.value.startDate) errors.startDate = '请选择开始时间';
  if (!classFormData.value.endDate) errors.endDate = '请选择结束时间';
  if (!classFormData.value.maxStudents || classFormData.value.maxStudents < 1) errors.maxStudents = '人数上限必须大于0';
  
  if (classFormData.value.teacherPhone && !/^1[3-9]\d{9}$/.test(classFormData.value.teacherPhone)) {
    errors.teacherPhone = '手机号码格式不正确';
  }
  
  if (classFormData.value.startDate && classFormData.value.endDate && classFormData.value.startDate > classFormData.value.endDate) {
    errors.endDate = '结束时间不能早于开始时间';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 验证学员表单
function validateStudentForm() {
  const errors = {};
  
  if (!studentFormData.value.name) errors.name = '请输入姓名';
  if (!studentFormData.value.studentId) errors.studentId = '请输入学号';
  if (!studentFormData.value.session) errors.session = '请选择青马班期数';
  if (!studentFormData.value.department) errors.department = '请输入班级';
  if (!studentFormData.value.gender) errors.gender = '请选择性别';
  if (!studentFormData.value.phone) errors.phone = '请输入联系方式';
  if (!studentFormData.value.counselorName) errors.counselorName = '请输入辅导员姓名';
  if (!studentFormData.value.counselorPhone) errors.counselorPhone = '请输入辅导员联系方式';
  
  if (studentFormData.value.phone && !/^1[3-9]\d{9}$/.test(studentFormData.value.phone)) {
    errors.phone = '联系方式格式不正确';
  }
  
  if (studentFormData.value.counselorPhone && !/^1[3-9]\d{9}$/.test(studentFormData.value.counselorPhone)) {
    errors.counselorPhone = '辅导员联系方式格式不正确';
  }
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 根据青马班期数更新班级ID
function updateClassIdFromSession() {
  const cls = classes.value.find(c => c.session === studentFormData.value.session);
  if (cls) {
    studentFormData.value.classId = cls.id;
  }
}

// 验证课程表单
function validateCourseForm() {
  const errors = {};
  
  if (!courseFormData.value.classId) errors.classId = '请选择班级';
  if (!courseFormData.value.name) errors.name = '请输入课程名称';
  if (!courseFormData.value.teacher) errors.teacher = '请输入授课教师';
  if (!courseFormData.value.hours || courseFormData.value.hours < 1) errors.hours = '学时必须大于0';
  if (!courseFormData.value.credits || courseFormData.value.credits < 0.5) errors.credits = '学分必须大于0.5';
  if (!courseFormData.value.time) errors.time = '请输入上课时间';
  if (!courseFormData.value.location) errors.location = '请输入上课地点';
  
  formErrors.value = errors;
  return Object.keys(errors).length === 0;
}

// 打开创建班级模态框
function openCreateClassModal() {
  isEdit.value = false;
  currentClass.value = null;
  classFormData.value = {
    classCode: '',
    name: '',
    session: '',
    teacher: '',
    teacherPhone: '',
    startDate: '',
    endDate: '',
    maxStudents: 50,
    description: ''
  };
  formErrors.value = {};
  showClassModal.value = true;
}

// 打开编辑班级模态框
function openEditClassModal(cls) {
  isEdit.value = true;
  currentClass.value = cls;
  classFormData.value = { ...cls };
  formErrors.value = {};
  showClassModal.value = true;
}

// 打开班级详情模态框
function openClassDetailModal(cls) {
  currentClass.value = cls;
  showClassDetailModal.value = true;
}

// 保存班级
async function saveClass() {
  if (!validateClassForm()) return;
  
  const apiData = {
    name: classFormData.value.name,
    code: classFormData.value.classCode,
    session: classFormData.value.session,
    headmaster: classFormData.value.teacher,
    headmaster_phone: classFormData.value.teacherPhone,
    start_date: classFormData.value.startDate,
    end_date: classFormData.value.endDate,
    max_students: classFormData.value.maxStudents,
    description: classFormData.value.description,
    status: '筹备中',
    current_students: 0
  };
  
  try {
    let response;
    if (isEdit.value) {
      response = await fetch(`/api/qingma-classes/${currentClass.value.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(apiData)
      });
    } else {
      response = await fetch('/api/qingma-classes/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(apiData)
      });
    }
    
    if (response.ok) {
      const result = await response.json();
      if (isEdit.value) {
        const index = classes.value.findIndex(c => c.id === currentClass.value.id);
        if (index !== -1) {
          classes.value[index] = {
            id: result.id,
            classCode: result.code,
            name: result.name,
            session: result.session,
            teacher: result.headmaster,
            teacherPhone: result.headmaster_phone,
            startDate: result.start_date,
            endDate: result.end_date,
            maxStudents: result.max_students,
            currentStudents: result.current_students,
            status: result.status,
            description: result.description
          };
        }
        alert('青马班更新成功！');
      } else {
        classes.value.unshift({
          id: result.id,
          classCode: result.code,
          name: result.name,
          session: result.session,
          teacher: result.headmaster,
          teacherPhone: result.headmaster_phone,
          startDate: result.start_date,
          endDate: result.end_date,
          maxStudents: result.max_students,
          currentStudents: result.current_students,
          status: result.status,
          description: result.description
        });
        alert('青马班添加成功！');
      }
      showClassModal.value = false;
    } else {
      const error = await response.json();
      alert('保存失败: ' + (error.message || JSON.stringify(error)));
    }
  } catch (error) {
    console.error('保存青马班失败:', error);
    alert('保存失败，请检查网络连接');
  }
}

// 打开创建学员模态框
function openCreateStudentModal() {
  isEdit.value = false;
  currentStudent.value = null;
  studentFormData.value = {
    name: '',
    studentId: '',
    classId: selectedClassId.value || '',
    session: '',
    grade: '2023级',
    department: '',
    gender: '男',
    phone: '',
    email: '',
    counselorName: '',
    counselorPhone: '',
    status: '在读'
  };
  formErrors.value = {};
  showStudentModal.value = true;
}

// 打开编辑学员模态框
function openEditStudentModal(student) {
  isEdit.value = true;
  currentStudent.value = student;
  studentFormData.value = { ...student };
  formErrors.value = {};
  showStudentModal.value = true;
}

// 保存学员
async function saveStudent() {
  if (!validateStudentForm()) return;
  
  const apiData = {
    name: studentFormData.value.name,
    gender: studentFormData.value.gender,
    student_id: studentFormData.value.studentId,
    qingma_class: studentFormData.value.classId,
    department: studentFormData.value.department,
    grade: studentFormData.value.grade,
    phone: studentFormData.value.phone,
    email: studentFormData.value.email,
    counselor_name: studentFormData.value.counselorName,
    counselor_phone: studentFormData.value.counselorPhone,
    status: '在读'
  };
  
  try {
    let response;
    if (isEdit.value) {
      response = await fetch(`/api/qingma-students/${currentStudent.value.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(apiData)
      });
    } else {
      response = await fetch('/api/qingma-students/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(apiData)
      });
    }
    
    if (response.ok) {
      const result = await response.json();
      if (isEdit.value) {
        const index = students.value.findIndex(s => s.id === currentStudent.value.id);
        if (index !== -1) {
          students.value[index] = {
            id: result.id,
            name: result.name,
            studentId: result.student_id,
            classId: result.qingma_class,
            session: result.session || '',
            grade: result.grade,
            department: result.department,
            gender: result.gender,
            phone: result.phone,
            email: result.email,
            counselorName: result.counselor_name,
            counselorPhone: result.counselor_phone,
            status: result.status
          };
        }
        alert('学员更新成功！');
      } else {
        students.value.unshift({
          id: result.id,
          name: result.name,
          studentId: result.student_id,
          classId: result.qingma_class,
          session: result.session || '',
          grade: result.grade,
          department: result.department,
          gender: result.gender,
          phone: result.phone,
          email: result.email,
          counselorName: result.counselor_name,
          counselorPhone: result.counselor_phone,
          status: result.status
        });
        alert('学员添加成功！');
        // 刷新班级数据以更新人数
        fetchClasses();
      }
      showStudentModal.value = false;
    } else {
      const error = await response.json();
      alert('保存失败: ' + (error.message || JSON.stringify(error)));
    }
  } catch (error) {
    console.error('保存学员失败:', error);
    alert('保存失败，请检查网络连接');
  }
}

// 打开创建课程模态框
function openCreateCourseModal() {
  isEdit.value = false;
  currentCourse.value = null;
  courseFormData.value = {
    classId: selectedClassId.value || '',
    name: '',
    teacher: '',
    type: '理论课',
    hours: 0,
    credits: 0,
    time: new Date().toISOString().slice(0, 16),
    location: '',
    status: '进行中'
  };
  formErrors.value = {};
  showCourseModal.value = true;
}

// 打开编辑课程模态框
function openEditCourseModal(course) {
  isEdit.value = true;
  currentCourse.value = course;
  courseFormData.value = { ...course };
  formErrors.value = {};
  showCourseModal.value = true;
}

// 保存课程
async function saveCourse() {
  if (!validateCourseForm()) return;
  
  const apiData = {
    name: courseFormData.value.name,
    qingma_class: courseFormData.value.classId,
    teacher: courseFormData.value.teacher,
    course_type: courseFormData.value.type,
    hours: courseFormData.value.hours,
    credits: courseFormData.value.credits,
    course_time: courseFormData.value.time,
    location: courseFormData.value.location,
    status: '未开始',
    description: courseFormData.value.description || ''
  };
  
  try {
    let response;
    if (isEdit.value) {
      response = await fetch(`/api/qingma-courses/${currentCourse.value.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(apiData)
      });
    } else {
      response = await fetch('/api/qingma-courses/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(apiData)
      });
    }
    
    if (response.ok) {
      const result = await response.json();
      if (isEdit.value) {
        const index = courses.value.findIndex(c => c.id === currentCourse.value.id);
        if (index !== -1) {
          courses.value[index] = {
            id: result.id,
            classId: result.qingma_class,
            name: result.name,
            teacher: result.teacher,
            type: result.course_type,
            hours: result.hours,
            credits: result.credits,
            time: result.course_time,
            location: result.location,
            status: result.status
          };
        }
        alert('课程更新成功！');
      } else {
        courses.value.unshift({
          id: result.id,
          classId: result.qingma_class,
          name: result.name,
          teacher: result.teacher,
          type: result.course_type,
          hours: result.hours,
          credits: result.credits,
          time: result.course_time,
          location: result.location,
          status: result.status
        });
        alert('课程添加成功！');
      }
      showCourseModal.value = false;
    } else {
      const error = await response.json();
      alert('保存失败: ' + (error.message || JSON.stringify(error)));
    }
  } catch (error) {
    console.error('保存课程失败:', error);
    alert('保存失败，请检查网络连接');
  }
}

// 删除班级
function deleteClass(cls) {
  if (confirm(`确定要删除班级「${cls.name}」吗？`)) {
    const index = classes.value.findIndex(c => c.id === cls.id);
    if (index !== -1) {
      classes.value.splice(index, 1);
      // 删除相关学员和课程
      students.value = students.value.filter(s => s.classId !== cls.id);
      courses.value = courses.value.filter(c => c.classId !== cls.id);
    }
  }
}

// 删除学员
async function deleteStudent(student) {
  if (confirm(`确定要删除学员「${student.name}」吗？`)) {
    try {
      const response = await fetch(`/api/qingma-students/${student.id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const index = students.value.findIndex(s => s.id === student.id);
        if (index !== -1) {
          students.value.splice(index, 1);
          const cls = classes.value.find(c => c.id === student.classId);
          if (cls) cls.currentStudents--;
        }
        alert('学员删除成功！');
      } else {
        const error = await response.json();
        alert('删除失败: ' + (error.message || JSON.stringify(error)));
      }
    } catch (error) {
      console.error('删除学员失败:', error);
      alert('删除失败，请检查网络连接');
    }
  }
}

// 删除课程
function deleteCourse(course) {
  if (confirm(`确定要删除课程「${course.name}」吗？`)) {
    const index = courses.value.findIndex(c => c.id === course.id);
    if (index !== -1) {
      courses.value.splice(index, 1);
    }
  }
}

// 打开课程表视图
function openCourseSchedule(cls) {
  currentClass.value = cls;
  showCourseScheduleModal.value = true;
}

// 关闭模态框
function closeModal() {
  showClassModal.value = false;
  showStudentModal.value = false;
  showCourseModal.value = false;
  showClassDetailModal.value = false;
  showCourseScheduleModal.value = false;
  formErrors.value = {};
}

// 学员分页
function prevStudentPage() {
  if (studentCurrentPage.value > 1) studentCurrentPage.value--;
}

function nextStudentPage() {
  if (studentCurrentPage.value < studentTotalPages.value) studentCurrentPage.value++;
}

// 下载导入模板
function downloadStudentTemplate() {
  const templateData = [
    excelHeaders,
    ['张三', 'QM028', '计算机2022级1班', '2022001001', '男', '13912345678', '王老师', '13800138001']
  ];
  
  const worksheet = XLSX.utils.aoa_to_sheet(templateData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '学员信息');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 12 }, { wch: 18 }, { wch: 12 }, { wch: 6 }, { wch: 13 }, { wch: 12 }, { wch: 13 }
  ];
  
  XLSX.writeFile(workbook, '青马班学员导入模板.xlsx');
}

// 导出学员数据
function exportStudents() {
  const exportData = filteredStudents.value.map(student => {
    const cls = classes.value.find(c => c.id === student.classId);
    return {
      '姓名': student.name,
      '青马班编号': cls ? cls.classCode : '',
      '青马班期数': student.session,
      '班级': student.department,
      '学号': student.studentId,
      '性别': student.gender,
      '联系方式': student.phone,
      '邮箱': student.email || '-',
      '辅导员姓名': student.counselorName,
      '辅导员联系方式': student.counselorPhone,
      '状态': student.status,
      '年级': student.grade
    };
  });
  
  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '学员信息');
  
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 12 }, { wch: 12 }, { wch: 18 }, { wch: 12 }, { wch: 6 }, { wch: 13 }, { wch: 18 }, { wch: 12 }, { wch: 13 }, { wch: 8 }, { wch: 10 }
  ];
  
  const fileName = `青马班学员数据_${new Date().toISOString().split('T')[0]}.xlsx`;
  XLSX.writeFile(workbook, fileName);
}

// 导入学员数据
async function handleStudentUpload(event) {
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
      if (!validateStudentHeaders(headers)) {
        alert('Excel表头格式不正确，请使用下载的模板');
        event.target.value = '';
        return;
      }
      
      const newStudents = [];
      const errors = [];
      
      for (let i = 1; i < jsonData.length; i++) {
        const rowData = jsonData[i];
        if (rowData.length === 0 || !rowData[0]) continue;
        
        try {
          const student = parseStudentRowData(headers, rowData, i + 1);
          if (student) {
            newStudents.push(student);
          } else {
            errors.push(`第${i + 1}行：必填字段缺失或格式错误`);
          }
        } catch (error) {
          errors.push(`第${i + 1}行：${error.message}`);
        }
      }
      
      if (newStudents.length > 0) {
        try {
          const response = await fetch('/api/qingma-students/bulk_import/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ data: newStudents })
          });
          
          if (response.ok) {
            const result = await response.json();
            fetchStudents();
            fetchClasses();
            
            const allErrors = [...errors, ...(result.errors || []).map(e => `第${e.row}行：${e.error}`)];
            if (allErrors.length > 0) {
              alert(`导入完成！成功：${result.success_count}条，失败：${result.failed_count + errors.length}条\n\n失败详情：\n${allErrors.join('\n')}`);
            } else {
              alert(`导入完成！成功：${result.success_count}条，失败：${result.failed_count}条`);
            }
          } else {
            const error = await response.json();
            alert('导入失败: ' + (error.message || JSON.stringify(error)));
          }
        } catch (error) {
          console.error('导入学员失败:', error);
          alert('导入失败，请检查网络连接');
        }
      } else if (errors.length > 0) {
        alert(`导入失败！所有数据均未通过验证\n\n失败详情：\n${errors.join('\n')}`);
      }
      
    } catch (error) {
      console.error('解析Excel文件失败:', error);
      alert('解析Excel文件失败，请检查文件格式');
    }
    
    event.target.value = '';
  };
  
  reader.readAsArrayBuffer(file);
}

// 验证学员表头
function validateStudentHeaders(headers) {
  if (!headers || headers.length < excelHeaders.length) return false;
  return excelHeaders.every((header, index) => headers[index] === header);
}

// 解析学员行数据
function parseStudentRowData(headers, rowData, rowNum) {
  const student = {
    grade: '2023级',
    email: '',
    status: '在读'
  };
  
  headers.forEach((header, index) => {
    const fieldName = fieldMapping[header];
    if (fieldName && rowData[index] !== undefined && rowData[index] !== null) {
      student[fieldName] = String(rowData[index]).trim();
    }
  });
  
  // 必填字段验证
  if (!student.name || !student.classCode || !student.department || 
      !student.studentId || !student.gender || !student.phone || 
      !student.counselorName || !student.counselorPhone) {
    return null;
  }
  
  // 手机号验证
  if (!/^1[3-9]\d{9}$/.test(student.phone)) {
    throw new Error('联系方式格式不正确');
  }
  
  // 辅导员联系方式验证
  if (!/^1[3-9]\d{9}$/.test(student.counselorPhone)) {
    throw new Error('辅导员联系方式格式不正确');
  }
  
  // 性别验证
  if (student.gender !== '男' && student.gender !== '女') {
    throw new Error('性别必须为"男"或"女"');
  }
  
  // 根据青马班编号查找班级ID
  const cls = classes.value.find(c => c.classCode === student.classCode);
  if (!cls) {
    throw new Error(`青马班编号不存在：${student.classCode}`);
  }
  
  student.classId = cls.id;
  student.session = cls.session; // 自动填充青马班期数
  delete student.classCode; // 删除临时字段
  
  return student;
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <h1>青马班管理</h1>
    </header>
    
    <!-- 标签切换 -->
    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'classes' }" @click="activeTab = 'classes'">班级管理</button>
      <button class="tab-btn" :class="{ active: activeTab === 'students' }" @click="activeTab = 'students'">学员管理</button>
      <button class="tab-btn" :class="{ active: activeTab === 'courses' }" @click="activeTab = 'courses'">课程安排</button>
    </div>
    
    <!-- 班级管理 -->
    <div v-if="activeTab === 'classes'" class="tab-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div v-for="stat in classStats" :key="stat.label" class="stat-item">
          <div class="stat-icon">📚</div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
      
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <input type="text" v-model="classSearchQuery" placeholder="搜索班级名称或届数..." class="search-input" />
        </div>
        <div class="toolbar-right">
          <button class="btn btn-primary" @click="openCreateClassModal">添加班级</button>
        </div>
      </div>
      
      <!-- 班级列表 -->
      <div class="cards-grid">
        <div v-for="cls in filteredClasses" :key="cls.id" class="class-card">
          <div class="card-header">
            <h3>{{ cls.name }}</h3>
            <span class="status-tag" :class="cls.status">{{ cls.status }}</span>
          </div>
          <div class="card-body">
            <div class="info-item">
              <span class="label">编号：</span>{{ cls.classCode }}
            </div>
            <div class="info-item">
              <span class="label">届数：</span>{{ cls.session }}
            </div>
            <div class="info-item">
              <span class="label">班主任：</span>{{ cls.teacher }}
            </div>
            <div class="info-item">
              <span class="label">联系方式：</span>{{ cls.teacherPhone }}
            </div>
            <div class="info-item">
              <span class="label">时间：</span>{{ cls.startDate }} ~ {{ cls.endDate }}
            </div>
            <div class="info-item">
              <span class="label">人数：</span>{{ cls.currentStudents }}/{{ cls.maxStudents }}
            </div>
          </div>
          <div class="card-footer">
            <button class="action-btn view" @click="openClassDetailModal(cls)">查看详情</button>
            <button v-if="hasPermission('league:edit')" class="action-btn edit" @click="openEditClassModal(cls)">编辑</button>
            <button class="action-btn schedule" @click="openCourseSchedule(cls)">课程表</button>
            <button v-if="hasPermission('league:delete')" class="action-btn delete" @click="deleteClass(cls)">删除</button>
          </div>
        </div>
      </div>
      
      <div v-if="filteredClasses.length === 0" class="empty-state">
        <p>暂无班级数据</p>
      </div>
    </div>
    
    <!-- 学员管理 -->
    <div v-if="activeTab === 'students'" class="tab-content">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <input type="text" v-model="studentSearchQuery" placeholder="搜索姓名、学号、班级..." class="search-input" />
          <select v-model="selectedClassId" class="filter-select">
            <option value="">全部班级</option>
            <option v-for="cls in classes" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
          </select>
        </div>
        <div class="toolbar-right">
          <button class="btn btn-secondary" @click="downloadStudentTemplate">下载模板</button>
          <label class="btn btn-secondary file-upload-label">
            <input type="file" accept=".xlsx,.xls" style="display: none" @change="handleStudentUpload" />
            导入数据
          </label>
          <button class="btn btn-secondary" @click="exportStudents">导出数据</button>
          <button class="btn btn-primary" @click="openCreateStudentModal">添加学员</button>
        </div>
      </div>
      
      <!-- 学员列表 -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th>青马班期数</th>
              <th>学号</th>
              <th>性别</th>
              <th>班级</th>
              <th>联系方式</th>
              <th>辅导员姓名</th>
              <th>辅导员联系方式</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in paginatedStudents" :key="student.id">
              <td>{{ student.name }}</td>
              <td><span class="session-tag">{{ student.session }}</span></td>
              <td>{{ student.studentId }}</td>
              <td><span class="gender-tag">{{ student.gender }}</span></td>
              <td><span class="dept-tag">{{ student.department }}</span></td>
              <td>{{ student.phone }}</td>
              <td>{{ student.counselorName }}</td>
              <td>{{ student.counselorPhone }}</td>
              <td><span class="status-tag" :class="student.status">{{ student.status }}</span></td>
              <td>
                <button v-if="hasPermission('league:edit')" class="action-btn edit" @click="openEditStudentModal(student)">编辑</button>
                <button v-if="hasPermission('league:delete')" class="action-btn delete" @click="deleteStudent(student)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <!-- 分页 -->
        <div v-if="filteredStudents.length > studentPageSize" class="pagination">
          <button class="page-btn" :disabled="studentCurrentPage === 1" @click="prevStudentPage">上一页</button>
          <span class="page-info">第 {{ studentCurrentPage }} / {{ studentTotalPages }} 页</span>
          <button class="page-btn" :disabled="studentCurrentPage === studentTotalPages" @click="nextStudentPage">下一页</button>
        </div>
        
        <div v-if="filteredStudents.length === 0" class="empty-state">
          <p>暂无学员数据</p>
        </div>
      </div>
    </div>
    
    <!-- 课程安排 -->
    <div v-if="activeTab === 'courses'" class="tab-content">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <input type="text" v-model="courseSearchQuery" placeholder="搜索课程名称或教师..." class="search-input" />
          <select v-model="selectedClassId" class="filter-select">
            <option value="">全部班级</option>
            <option v-for="cls in classes" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
          </select>
        </div>
        <div class="toolbar-right">
          <button class="btn btn-primary" @click="openCreateCourseModal">添加课程</button>
        </div>
      </div>
      
      <!-- 课程列表 -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>课程名称</th>
              <th>班级</th>
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
            <tr v-for="course in filteredCourses" :key="course.id">
              <td>{{ course.name }}</td>
              <td><span class="class-tag">{{ getClassName(course.classId) }}</span></td>
              <td>{{ course.teacher }}</td>
              <td><span class="type-tag">{{ course.type }}</span></td>
              <td>{{ course.hours }}学时</td>
              <td>{{ course.credits }}学分</td>
              <td>{{ course.time }}</td>
              <td>{{ course.location }}</td>
              <td><span class="status-tag" :class="course.status">{{ course.status }}</span></td>
              <td>
                <button v-if="hasPermission('league:edit')" class="action-btn edit" @click="openEditCourseModal(course)">编辑</button>
                <button v-if="hasPermission('league:delete')" class="action-btn delete" @click="deleteCourse(course)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <div v-if="filteredCourses.length === 0" class="empty-state">
          <p>暂无课程数据</p>
        </div>
      </div>
    </div>
    
    <!-- 班级模态框 -->
    <div v-if="showClassModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑班级' : '添加班级' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>班级编号 <span class="required">*</span></label>
            <input type="text" v-model="classFormData.classCode" class="form-input" placeholder="例如：QM001" />
            <span v-if="formErrors.classCode" class="form-error">{{ formErrors.classCode }}</span>
          </div>
          <div class="form-group">
            <label>班级名称 <span class="required">*</span></label>
            <input type="text" v-model="classFormData.name" class="form-input" placeholder="例如：第28期青马班" />
            <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>届数 <span class="required">*</span></label>
              <input type="text" v-model="classFormData.session" class="form-input" placeholder="例如：第28期" />
              <span v-if="formErrors.session" class="form-error">{{ formErrors.session }}</span>
            </div>
            <div class="form-group">
              <label>人数上限 <span class="required">*</span></label>
              <input type="number" v-model="classFormData.maxStudents" class="form-input" min="1" />
              <span v-if="formErrors.maxStudents" class="form-error">{{ formErrors.maxStudents }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>班主任 <span class="required">*</span></label>
              <input type="text" v-model="classFormData.teacher" class="form-input" placeholder="班主任姓名" />
              <span v-if="formErrors.teacher" class="form-error">{{ formErrors.teacher }}</span>
            </div>
            <div class="form-group">
              <label>联系方式 <span class="required">*</span></label>
              <input type="text" v-model="classFormData.teacherPhone" class="form-input" placeholder="手机号码" />
              <span v-if="formErrors.teacherPhone" class="form-error">{{ formErrors.teacherPhone }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>开始时间 <span class="required">*</span></label>
              <input type="date" v-model="classFormData.startDate" class="form-input" />
              <span v-if="formErrors.startDate" class="form-error">{{ formErrors.startDate }}</span>
            </div>
            <div class="form-group">
              <label>结束时间 <span class="required">*</span></label>
              <input type="date" v-model="classFormData.endDate" class="form-input" />
              <span v-if="formErrors.endDate" class="form-error">{{ formErrors.endDate }}</span>
            </div>
          </div>
          <div class="form-group">
            <label>班级描述</label>
            <textarea v-model="classFormData.description" class="form-textarea" placeholder="班级简介"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveClass">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 学员模态框 -->
    <div v-if="showStudentModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑学员' : '添加学员' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>姓名 <span class="required">*</span></label>
              <input type="text" v-model="studentFormData.name" class="form-input" placeholder="学员姓名" />
              <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
            </div>
            <div class="form-group">
              <label>学号 <span class="required">*</span></label>
              <input type="text" v-model="studentFormData.studentId" class="form-input" placeholder="学员学号" />
              <span v-if="formErrors.studentId" class="form-error">{{ formErrors.studentId }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>青马班期数 <span class="required">*</span></label>
              <select v-model="studentFormData.session" class="form-select" @change="updateClassIdFromSession">
                <option value="">请选择青马班期数</option>
                <option v-for="cls in classes" :key="cls.id" :value="cls.session">{{ cls.session }}</option>
              </select>
              <span v-if="formErrors.session" class="form-error">{{ formErrors.session }}</span>
            </div>
            <div class="form-group">
              <label>性别 <span class="required">*</span></label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="studentFormData.gender" value="男" /> 男
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="studentFormData.gender" value="女" /> 女
                </label>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>班级 <span class="required">*</span></label>
              <input type="text" v-model="studentFormData.department" class="form-input" placeholder="所属班级" />
              <span v-if="formErrors.department" class="form-error">{{ formErrors.department }}</span>
            </div>
            <div class="form-group">
              <label>联系方式 <span class="required">*</span></label>
              <input type="text" v-model="studentFormData.phone" class="form-input" placeholder="手机号码" />
              <span v-if="formErrors.phone" class="form-error">{{ formErrors.phone }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>辅导员姓名 <span class="required">*</span></label>
              <input type="text" v-model="studentFormData.counselorName" class="form-input" placeholder="辅导员姓名" />
              <span v-if="formErrors.counselorName" class="form-error">{{ formErrors.counselorName }}</span>
            </div>
            <div class="form-group">
              <label>辅导员联系方式 <span class="required">*</span></label>
              <input type="text" v-model="studentFormData.counselorPhone" class="form-input" placeholder="辅导员联系方式" />
              <span v-if="formErrors.counselorPhone" class="form-error">{{ formErrors.counselorPhone }}</span>
            </div>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="studentFormData.status" class="form-select">
              <option value="在读">在读</option>
              <option value="已结业">已结业</option>
              <option value="休学">休学</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveStudent">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 课程模态框 -->
    <div v-if="showCourseModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ isEdit ? '编辑课程' : '添加课程' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>所属班级 <span class="required">*</span></label>
            <select v-model="courseFormData.classId" class="form-select">
              <option value="">请选择班级</option>
              <option v-for="cls in classes" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
            </select>
            <span v-if="formErrors.classId" class="form-error">{{ formErrors.classId }}</span>
          </div>
          <div class="form-group">
            <label>课程名称 <span class="required">*</span></label>
            <input type="text" v-model="courseFormData.name" class="form-input" placeholder="课程名称" />
            <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>授课教师 <span class="required">*</span></label>
              <input type="text" v-model="courseFormData.teacher" class="form-input" placeholder="授课教师" />
              <span v-if="formErrors.teacher" class="form-error">{{ formErrors.teacher }}</span>
            </div>
            <div class="form-group">
              <label>课程类型</label>
              <select v-model="courseFormData.type" class="form-select">
                <option v-for="type in courseTypes" :key="type" :value="type">{{ type }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>学时 <span class="required">*</span></label>
              <input type="number" v-model="courseFormData.hours" class="form-input" min="1" />
              <span v-if="formErrors.hours" class="form-error">{{ formErrors.hours }}</span>
            </div>
            <div class="form-group">
              <label>学分 <span class="required">*</span></label>
              <input type="number" v-model="courseFormData.credits" class="form-input" min="0.5" step="0.5" />
              <span v-if="formErrors.credits" class="form-error">{{ formErrors.credits }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>上课时间 <span class="required">*</span></label>
              <input type="datetime-local" v-model="courseFormData.time" class="form-input" />
              <span v-if="formErrors.time" class="form-error">{{ formErrors.time }}</span>
            </div>
            <div class="form-group">
              <label>上课地点 <span class="required">*</span></label>
              <input type="text" v-model="courseFormData.location" class="form-input" placeholder="上课地点" />
              <span v-if="formErrors.location" class="form-error">{{ formErrors.location }}</span>
            </div>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="courseFormData.status" class="form-select">
              <option value="进行中">进行中</option>
              <option value="已结束">已结束</option>
              <option value="未开始">未开始</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveCourse">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 班级详情模态框 -->
    <div v-if="showClassDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>班级详情</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentClass">
          <div class="detail-section">
            <h3 class="section-title">基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">班级编号：</span>{{ currentClass.classCode }}</div>
              <div class="detail-item"><span class="label">班级名称：</span>{{ currentClass.name }}</div>
              <div class="detail-item"><span class="label">届数：</span>{{ currentClass.session }}</div>
              <div class="detail-item"><span class="label">班主任：</span>{{ currentClass.teacher }}</div>
              <div class="detail-item"><span class="label">联系方式：</span>{{ currentClass.teacherPhone }}</div>
              <div class="detail-item"><span class="label">开始时间：</span>{{ currentClass.startDate }}</div>
              <div class="detail-item"><span class="label">结束时间：</span>{{ currentClass.endDate }}</div>
              <div class="detail-item"><span class="label">当前人数：</span>{{ currentClass.currentStudents }}/{{ currentClass.maxStudents }}</div>
              <div class="detail-item"><span class="label">状态：</span><span class="status-tag" :class="currentClass.status">{{ currentClass.status }}</span></div>
              <div class="detail-item full-width"><span class="label">描述：</span>{{ currentClass.description }}</div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">学员列表</h3>
            <div class="mini-table">
              <div v-for="student in students.filter(s => s.classId === currentClass.id)" :key="student.id" class="mini-row">
                <span>{{ student.name }}</span>
                <span>{{ student.studentId }}</span>
                <span>{{ student.department }}</span>
                <span class="status-tag" :class="student.status">{{ student.status }}</span>
              </div>
              <div v-if="students.filter(s => s.classId === currentClass.id).length === 0" class="empty-mini">
                <p>暂无学员</p>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3 class="section-title">课程安排</h3>
            <div class="mini-table">
              <div v-for="course in courses.filter(c => c.classId === currentClass.id)" :key="course.id" class="mini-row">
                <span>{{ course.name }}</span>
                <span>{{ course.teacher }}</span>
                <span>{{ course.time }}</span>
                <span class="status-tag" :class="course.status">{{ course.status }}</span>
              </div>
              <div v-if="courses.filter(c => c.classId === currentClass.id).length === 0" class="empty-mini">
                <p>暂无课程</p>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button class="btn btn-primary" @click="openEditClassModal(currentClass); closeModal()">编辑</button>
        </div>
      </div>
    </div>
    
    <!-- 课程表视图模态框 -->
    <div v-if="showCourseScheduleModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ currentClass?.name }} 课程表</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body" v-if="currentClass">
          <div class="schedule-grid">
            <div class="schedule-header">
              <div class="time-col">时间</div>
              <div class="day-col">周一</div>
              <div class="day-col">周二</div>
              <div class="day-col">周三</div>
              <div class="day-col">周四</div>
              <div class="day-col">周五</div>
            </div>
            <div class="schedule-row">
              <div class="time-col">08:00-10:00</div>
              <div v-for="day in ['周一', '周二', '周三', '周四', '周五']" :key="day" class="day-col">
                <div v-for="course in courses.filter(c => c.classId === currentClass.id && c.time.includes(day) && c.time.includes('08:00'))" :key="course.id" class="course-block">
                  <div class="course-name">{{ course.name }}</div>
                  <div class="course-info">{{ course.teacher }} | {{ course.location }}</div>
                </div>
              </div>
            </div>
            <div class="schedule-row">
              <div class="time-col">10:00-12:00</div>
              <div v-for="day in ['周一', '周二', '周三', '周四', '周五']" :key="day" class="day-col">
                <div v-for="course in courses.filter(c => c.classId === currentClass.id && c.time.includes(day) && c.time.includes('10:00'))" :key="course.id" class="course-block">
                  <div class="course-name">{{ course.name }}</div>
                  <div class="course-info">{{ course.teacher }} | {{ course.location }}</div>
                </div>
              </div>
            </div>
            <div class="schedule-row">
              <div class="time-col">14:00-16:00</div>
              <div v-for="day in ['周一', '周二', '周三', '周四', '周五']" :key="day" class="day-col">
                <div v-for="course in courses.filter(c => c.classId === currentClass.id && c.time.includes(day) && c.time.includes('14:00'))" :key="course.id" class="course-block">
                  <div class="course-name">{{ course.name }}</div>
                  <div class="course-info">{{ course.teacher }} | {{ course.location }}</div>
                </div>
              </div>
            </div>
            <div class="schedule-row">
              <div class="time-col">16:00-18:00</div>
              <div v-for="day in ['周一', '周二', '周三', '周四', '周五']" :key="day" class="day-col">
                <div v-for="course in courses.filter(c => c.classId === currentClass.id && c.time.includes(day) && c.time.includes('16:00'))" :key="course.id" class="course-block">
                  <div class="course-name">{{ course.name }}</div>
                  <div class="course-info">{{ course.teacher }} | {{ course.location }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
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

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.class-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 24px;
  transition: all 0.2s ease;
}

.class-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.card-body {
  margin-bottom: 16px;
}

.info-item {
  font-size: 14px;
  color: #666;
  margin: 8px 0;
}

.info-item .label {
  color: #999;
  font-weight: 500;
}

.card-footer {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.进行中,
.status-tag.在读 {
  background: #e6f7ff;
  color: #1890ff;
}

.status-tag.筹备中,
.status-tag.未开始 {
  background: #fff7e6;
  color: #fa8c16;
}

.status-tag.已结业,
.status-tag.已结束 {
  background: #f5f5f5;
  color: #666666;
}

.class-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.session-tag {
  padding: 4px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.gender-tag {
  padding: 4px 12px;
  background: #f6ffed;
  color: #52c41a;
  border-radius: 4px;
  font-size: 12px;
}

.dept-tag {
  padding: 4px 12px;
  background: #f6ffed;
  color: #52c41a;
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

.action-btn.schedule {
  background: #f6ffed;
  color: #52c41a;
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

/* 详情样式 */
.detail-section {
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

.mini-table {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.mini-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  gap: 12px;
}

.mini-row:last-child {
  border-bottom: none;
}

.empty-mini {
  padding: 24px;
  text-align: center;
  color: #999;
}

/* 课程表样式 */
.schedule-grid {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.schedule-header,
.schedule-row {
  display: grid;
  grid-template-columns: 100px repeat(5, 1fr);
}

.time-col,
.day-col {
  padding: 12px;
  border-right: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  text-align: center;
}

.schedule-header .time-col,
.schedule-header .day-col {
  background: #fafafa;
  font-weight: 600;
  color: #333;
}

.course-block {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  padding: 8px;
  border-radius: 6px;
  margin: 4px;
}

.course-name {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
}

.course-info {
  font-size: 11px;
  opacity: 0.9;
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
  
  .mini-row {
    grid-template-columns: 1fr 1fr;
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
  
  .schedule-grid {
    font-size: 12px;
  }
}
</style>