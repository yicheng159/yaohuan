from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

# ============================================================
# 权限管理模块
# ============================================================
import json

class Role(models.Model):
    """角色模型"""
    name = models.CharField('角色名称', max_length=50, unique=True)
    description = models.TextField('角色描述', blank=True)
    permissions = models.TextField('权限列表', default='[]')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def get_permissions(self):
        try:
            return json.loads(self.permissions)
        except:
            return []

    def set_permissions(self, permissions):
        self.permissions = json.dumps(permissions)

    class Meta:
        db_table = 'roles'
        verbose_name = '角色'
        verbose_name_plural = '角色管理'

    def __str__(self):
        return self.name


class PermissionLog(models.Model):
    """权限不足操作日志"""
    user = models.ForeignKey('UserAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='permission_logs')
    student_id = models.CharField('学号', max_length=20, blank=True)
    role = models.CharField('角色', max_length=50, blank=True)
    required_permission = models.CharField('需要的权限', max_length=100)
    method = models.CharField('请求方法', max_length=10)
    path = models.CharField('请求路径', max_length=500)
    ip = models.GenericIPAddressField('IP地址', null=True, blank=True)
    created_at = models.DateTimeField('尝试时间', auto_now_add=True)

    class Meta:
        db_table = 'permission_logs'
        verbose_name = '权限日志'
        verbose_name_plural = '权限日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student_id} - {self.required_permission} - {self.created_at}'


class PermissionChangeLog(models.Model):
    """权限变更日志"""
    OPERATION_TYPES = [
        ('create_role', '创建角色'),
        ('edit_role', '编辑角色'),
        ('delete_role', '删除角色'),
        ('assign_role', '分配角色'),
        ('remove_role', '移除角色'),
        ('change_permissions', '修改权限'),
        ('create_user', '创建用户'),
        ('edit_user', '编辑用户'),
        ('delete_user', '删除用户'),
    ]

    operator = models.ForeignKey('UserAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='permission_change_logs', verbose_name='操作人')
    operator_student_id = models.CharField('操作人学号', max_length=20, blank=True)
    operator_name = models.CharField('操作人姓名', max_length=50, blank=True)
    operation_type = models.CharField('操作类型', max_length=50, choices=OPERATION_TYPES)
    target_type = models.CharField('目标类型', max_length=50, blank=True, help_text='角色/用户')
    target_id = models.IntegerField('目标ID', null=True, blank=True)
    target_name = models.CharField('目标名称', max_length=100, blank=True)
    change_detail = models.TextField('变更详情', blank=True, help_text='JSON格式的详细变更内容')
    before_value = models.TextField('变更前值', blank=True, help_text='变更前的数据')
    after_value = models.TextField('变更后值', blank=True, help_text='变更后的数据')
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    class Meta:
        db_table = 'permission_change_logs'
        verbose_name = '权限变更日志'
        verbose_name_plural = '权限变更日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.operator_name} - {self.operation_type} - {self.created_at}'


class DataDictionary(models.Model):
    """数据字典模型 - 用于管理学历、学院、部门等可配置选项"""
    CATEGORY_CHOICES = [
        ('education', '学历'),
        ('college', '学院'),
        ('department', '部门'),
        ('position', '职务'),
        ('ethnicity', '民族'),
        ('party_status', '党员状态'),
        ('league_status', '团员状态'),
        ('activity_type', '活动类型'),
        ('material_category', '物资分类'),
        ('custom', '自定义'),
    ]

    category = models.CharField('分类', max_length=50, choices=CATEGORY_CHOICES)
    code = models.CharField('编码', max_length=50, unique=True)
    name = models.CharField('名称', max_length=100)
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    description = models.CharField('描述', max_length=200, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'data_dictionaries'
        verbose_name = '数据字典'
        verbose_name_plural = '数据字典'
        ordering = ['category', 'sort_order', 'name']

    def __str__(self):
        return f'{self.get_category_display()} - {self.name}'


class UserAccount(models.Model):
    """用户账户模型"""
    member = models.OneToOneField('Member', on_delete=models.CASCADE, related_name='account', null=True, blank=True)
    student_id = models.CharField('学号', max_length=20, unique=True)
    password = models.CharField('密码', max_length=255)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_active = models.BooleanField('是否启用', default=True)
    last_login = models.DateTimeField('最后登录时间', null=True, blank=True)
    login_count = models.IntegerField('登录次数', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'user_accounts'
        verbose_name = '用户账户'
        verbose_name_plural = '用户账户管理'
    
    def __str__(self):
        return self.student_id
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class LoginLog(models.Model):
    """登录日志模型"""
    LOGIN_STATUS = [
        ('success', '成功'),
        ('failed', '失败'),
    ]
    
    student_id = models.CharField('学号', max_length=20)
    ip_address = models.CharField('IP地址', max_length=50)
    user_agent = models.CharField('用户代理', max_length=500, blank=True)
    status = models.CharField('登录状态', max_length=20, choices=LOGIN_STATUS)
    error_message = models.CharField('错误信息', max_length=200, blank=True)
    created_at = models.DateTimeField('登录时间', auto_now_add=True)
    
    class Meta:
        db_table = 'login_logs'
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student_id} - {self.status} - {self.created_at}"


class AccessToken(models.Model):
    """访问令牌模型"""
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='tokens')
    token = models.CharField('令牌', max_length=255, unique=True)
    expires_at = models.DateTimeField('过期时间')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'access_tokens'
        verbose_name = '访问令牌'
        verbose_name_plural = '访问令牌管理'
    
    def is_expired(self):
        return timezone.now() > self.expires_at


# ============================================================
# 菜单管理模块
# ============================================================
class Menu(models.Model):
    """一级菜单"""
    name = models.CharField('菜单名称', max_length=50)
    icon = models.CharField('菜单图标', max_length=50, blank=True)
    path = models.CharField('路由路径', max_length=100, blank=True)
    order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'menus'
        verbose_name = '一级菜单'
        verbose_name_plural = '一级菜单管理'
        ordering = ['order']
    
    def __str__(self):
        return self.name


class SubMenu(models.Model):
    """二级菜单"""
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='submenus')
    name = models.CharField('菜单名称', max_length=50)
    path = models.CharField('路由路径', max_length=100)
    order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'sub_menus'
        verbose_name = '二级菜单'
        verbose_name_plural = '二级菜单管理'
        ordering = ['menu__order', 'order']
    
    def __str__(self):
        return f"{self.menu.name} - {self.name}"


# ============================================================
# 成员管理模块
# ============================================================
class Member(models.Model):
    """学生会成员"""
    STATUS_CHOICES = [
        ('在职', '在职'),
        ('离职', '离职'),
    ]
    
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES)
    student_id = models.CharField('学号', max_length=20, unique=True)
    department = models.CharField('部门', max_length=100)
    position = models.CharField('职位', max_length=50)
    role = models.CharField('角色', max_length=50)
    grade = models.CharField('年级', max_length=20)
    class_name = models.CharField('班级', max_length=100)
    counselor_name = models.CharField('辅导员姓名', max_length=50)
    counselor_phone = models.CharField('辅导员联系方式', max_length=20)
    phone = models.CharField('联系电话', max_length=20)
    email = models.EmailField('邮箱', blank=True)
    join_date = models.DateField('加入日期')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='在职')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'members'
        verbose_name = '学生会成员'
        verbose_name_plural = '学生会成员'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.department} - {self.position}"


# ============================================================
# 活动管理模块
# ============================================================
class Activity(models.Model):
    """活动管理"""
    TYPE_CHOICES = [
        ('文体类', '文体类'),
        ('学术类', '学术类'),
        ('公益类', '公益类'),
        ('交流类', '交流类'),
        ('其他', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('未开始', '未开始'),
        ('进行中', '进行中'),
        ('已结束', '已结束'),
    ]
    
    name = models.CharField('活动名称', max_length=100)
    type = models.CharField('活动类型', max_length=20, choices=TYPE_CHOICES)
    description = models.TextField('活动简介')
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间')
    location = models.CharField('活动地点', max_length=200)
    organizer = models.CharField('主办部门', max_length=100)
    leader = models.CharField('负责人', max_length=50)
    participants_count = models.IntegerField('预计参与人数', default=0)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='未开始')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'activities'
        verbose_name = '活动'
        verbose_name_plural = '活动管理'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.name} - {self.type} - {self.status}"


# ============================================================
# 物资管理模块
# ============================================================
class Material(models.Model):
    """物资信息"""
    CATEGORY_CHOICES = [
        ('电子设备', '电子设备'),
        ('家具', '家具'),
        ('户外活动', '户外活动'),
        ('宣传用品', '宣传用品'),
        ('办公用品', '办公用品'),
        ('其他', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('正常', '正常'),
        ('部分损坏', '部分损坏'),
        ('需要维修', '需要维修'),
        ('报废', '报废'),
    ]
    
    LOCATION_CHOICES = [
        ('仓库A区', '仓库A区'),
        ('仓库B区', '仓库B区'),
        ('仓库C区', '仓库C区'),
        ('办公室', '办公室'),
        ('会议室', '会议室'),
        ('其他', '其他'),
    ]
    
    name = models.CharField('物资名称', max_length=100)
    specification = models.CharField('型号规格', max_length=100)
    category = models.CharField('分类', max_length=50, choices=CATEGORY_CHOICES)
    quantity = models.IntegerField('数量')
    price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    storage_location = models.CharField('存放位置', max_length=100, choices=LOCATION_CHOICES)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='正常')
    description = models.TextField('物资描述', blank=True)
    entry_date = models.DateField('入库日期')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'materials'
        verbose_name = '物资'
        verbose_name_plural = '物资管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.specification}"


class MaterialBorrow(models.Model):
    """物资借用记录"""
    STATUS_CHOICES = [
        ('借用中', '借用中'),
        ('已归还', '已归还'),
    ]
    
    borrower = models.CharField('借用人员', max_length=50)
    borrower_phone = models.CharField('借用人员电话', max_length=20)
    borrow_date = models.DateField('借用日期')
    expected_return_date = models.DateField('预计归还日期')
    actual_return_date = models.DateField('实际归还日期', null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='借用中')
    purpose = models.TextField('借用用途')
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'material_borrows'
        verbose_name = '物资借用记录'
        verbose_name_plural = '物资借用管理'
        ordering = ['-borrow_date']
    
    def __str__(self):
        return f"{self.borrower} - {self.borrow_date}"


class MaterialBorrowItem(models.Model):
    """借用物资明细"""
    borrow = models.ForeignKey(MaterialBorrow, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.IntegerField('借用数量')
    
    class Meta:
        db_table = 'material_borrow_items'
        verbose_name = '借用物资明细'
        verbose_name_plural = '借用物资明细'
    
    def __str__(self):
        return f"{self.material.name} x {self.quantity}"


# ============================================================
# 团务管理模块 - 团员管理
# ============================================================
class LeagueMember(models.Model):
    """团员信息"""
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]
    
    POLITICAL_STATUS_CHOICES = [
        ('共青团员', '共青团员'),
        ('中共党员', '中共党员'),
        ('中共预备党员', '中共预备党员'),
        ('群众', '群众'),
        ('其他', '其他'),
    ]
    
    TRANSFER_STATUS_CHOICES = [
        ('未转接', '未转接'),
        ('转接中', '转接中'),
        ('已完成', '已完成'),
        ('已撤销', '已撤销'),
    ]
    
    ETHNICITY_CHOICES = [
        ('汉族', '汉族'), ('回族', '回族'), ('藏族', '藏族'), ('维吾尔族', '维吾尔族'),
        ('苗族', '苗族'), ('彝族', '彝族'), ('壮族', '壮族'), ('布依族', '布依族'),
        ('朝鲜族', '朝鲜族'), ('满族', '满族'), ('侗族', '侗族'), ('瑶族', '瑶族'),
        ('白族', '白族'), ('土家族', '土家族'), ('哈尼族', '哈尼族'), ('其他', '其他'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES)
    student_id = models.CharField('学号', max_length=20)
    birth_date = models.DateField('出生年月')
    ethnicity = models.CharField('民族', max_length=20, choices=ETHNICITY_CHOICES)
    id_card = models.CharField('身份证号码', max_length=18)
    phone = models.CharField('手机号码', max_length=20)
    college = models.CharField('学院', max_length=100)
    grade = models.CharField('年级', max_length=20)
    organization = models.CharField('组织全称', max_length=200)
    counselor = models.CharField('所属辅导员', max_length=50)
    position = models.CharField('团内职务', max_length=50)
    political_status = models.CharField('政治面貌', max_length=20, choices=POLITICAL_STATUS_CHOICES)
    development_number = models.CharField('团员发展编号', max_length=50)
    join_date = models.DateField('入团年月')
    hometown = models.CharField('户籍地', max_length=200)
    transfer_reason = models.TextField('团组织关系转接原因', blank=True)
    transfer_status = models.CharField('转接状态', max_length=20, choices=TRANSFER_STATUS_CHOICES, default='未转接')
    transfer_address = models.CharField('转接地址', max_length=200, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'league_members'
        verbose_name = '团员'
        verbose_name_plural = '团员管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.college} - {self.organization}"


# ============================================================
# 团务管理模块 - 青马班管理
# ============================================================
class QingmaClass(models.Model):
    """青马班"""
    STATUS_CHOICES = [
        ('筹备中', '筹备中'),
        ('进行中', '进行中'),
        ('已结业', '已结业'),
    ]
    
    name = models.CharField('班级名称', max_length=100)
    code = models.CharField('班级编号', max_length=20, unique=True)
    session = models.CharField('届数', max_length=20)
    headmaster = models.CharField('班主任', max_length=50)
    headmaster_phone = models.CharField('班主任联系方式', max_length=20)
    start_date = models.DateField('开始时间')
    end_date = models.DateField('结束时间')
    max_students = models.IntegerField('班级人数上限', default=50)
    current_students = models.IntegerField('当前人数', default=0)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='筹备中')
    description = models.TextField('班级描述', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'qingma_classes'
        verbose_name = '青马班'
        verbose_name_plural = '青马班管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.session}"


class QingmaStudent(models.Model):
    """青马班学员"""
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]
    
    STATUS_CHOICES = [
        ('在读', '在读'),
        ('已结业', '已结业'),
        ('休学', '休学'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES)
    student_id = models.CharField('学号', max_length=20)
    qingma_class = models.ForeignKey(QingmaClass, on_delete=models.CASCADE, related_name='students')
    department = models.CharField('班级', max_length=100)
    grade = models.CharField('年级', max_length=20)
    phone = models.CharField('联系方式', max_length=20)
    email = models.EmailField('邮箱', blank=True, null=True)
    counselor_name = models.CharField('辅导员姓名', max_length=50)
    counselor_phone = models.CharField('辅导员联系方式', max_length=20)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='在读')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'qingma_students'
        verbose_name = '青马班学员'
        verbose_name_plural = '青马班学员管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.qingma_class.name}"


class QingmaCourse(models.Model):
    """青马班课程"""
    TYPE_CHOICES = [
        ('理论课', '理论课'),
        ('实践课', '实践课'),
        ('研讨课', '研讨课'),
        ('专题讲座', '专题讲座'),
    ]
    
    STATUS_CHOICES = [
        ('未开始', '未开始'),
        ('进行中', '进行中'),
        ('已结束', '已结束'),
    ]
    
    name = models.CharField('课程名称', max_length=100)
    qingma_class = models.ForeignKey(QingmaClass, on_delete=models.CASCADE, related_name='courses')
    teacher = models.CharField('授课教师', max_length=50)
    course_type = models.CharField('课程类型', max_length=20, choices=TYPE_CHOICES)
    hours = models.IntegerField('学时')
    credits = models.DecimalField('学分', max_digits=3, decimal_places=1)
    course_time = models.DateTimeField('上课时间')
    location = models.CharField('上课地点', max_length=200)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='未开始')
    description = models.TextField('课程描述', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'qingma_courses'
        verbose_name = '青马班课程'
        verbose_name_plural = '青马班课程管理'
        ordering = ['course_time']
    
    def __str__(self):
        return f"{self.name} - {self.qingma_class.name}"


# ============================================================
# 团务管理模块 - 团费管理
# ============================================================
class LeagueBranch(models.Model):
    """团支部"""
    name = models.CharField('团支部名称', max_length=100)
    code = models.CharField('团支部编号', max_length=20, unique=True)
    monthly_fee = models.DecimalField('每月缴费金额', max_digits=6, decimal_places=2, default=6)
    total_members = models.IntegerField('应交人数', default=0)
    paid_members = models.IntegerField('已交人数', default=0)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'league_branches'
        verbose_name = '团支部'
        verbose_name_plural = '团支部管理'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class FeeRecord(models.Model):
    """团费缴费记录"""
    STATUS_CHOICES = [
        ('已缴', '已缴'),
        ('未缴', '未缴'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    student_id = models.CharField('学号', max_length=20)
    branch = models.ForeignKey(LeagueBranch, on_delete=models.CASCADE, related_name='fee_records')
    month = models.CharField('缴费月份', max_length=20)
    amount = models.DecimalField('金额', max_digits=6, decimal_places=2)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='已缴')
    pay_date = models.DateField('缴费时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'fee_records'
        verbose_name = '团费缴费记录'
        verbose_name_plural = '团费缴费管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.month}"


# ============================================================
# 党务管理模块 - 党员管理
# ============================================================
class PartyMember(models.Model):
    """党员信息"""
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]
    
    EDUCATION_CHOICES = [
        ('本科', '本科'),
        ('硕士', '硕士'),
        ('博士', '博士'),
    ]
    
    STATUS_CHOICES = [
        ('正常', '正常'),
        ('暂停', '暂停'),
        ('转出', '转出'),
        ('去世', '去世'),
    ]
    
    ETHNICITY_CHOICES = [
        ('汉族', '汉族'), ('回族', '回族'), ('藏族', '藏族'), ('维吾尔族', '维吾尔族'),
        ('苗族', '苗族'), ('彝族', '彝族'), ('壮族', '壮族'), ('布依族', '布依族'),
        ('朝鲜族', '朝鲜族'), ('满族', '满族'), ('侗族', '侗族'), ('瑶族', '瑶族'),
        ('白族', '白族'), ('土家族', '土家族'), ('哈尼族', '哈尼族'), ('其他', '其他'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES)
    ethnicity = models.CharField('民族', max_length=20, choices=ETHNICITY_CHOICES)
    birth_date = models.DateField('出生日期')
    education = models.CharField('学历', max_length=20, choices=EDUCATION_CHOICES)
    join_date = models.DateField('入党时间')
    regular_date = models.DateField('转正时间', null=True, blank=True)
    organization = models.CharField('所属党组织', max_length=200)
    phone = models.CharField('联系电话', max_length=20)
    introducer = models.CharField('入党介绍人', max_length=50)
    status = models.CharField('党员状态', max_length=20, choices=STATUS_CHOICES, default='正常')
    student_id = models.CharField('学号', max_length=20, blank=True)
    grade = models.CharField('年级', max_length=20, blank=True)
    department = models.CharField('学院', max_length=100, blank=True)
    email = models.EmailField('邮箱', blank=True)
    address = models.CharField('地址', max_length=200, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'party_members'
        verbose_name = '党员'
        verbose_name_plural = '党员管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.organization}"


# ============================================================
# 党务管理模块 - 入党积极分子
# ============================================================
class Activist(models.Model):
    """入党积极分子"""
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]
    
    STATUS_CHOICES = [
        ('培养中', '培养中'),
        ('已转发展对象', '已转发展对象'),
        ('已取消', '已取消'),
    ]
    
    EDUCATION_CHOICES = [
        ('本科', '本科'),
        ('硕士', '硕士'),
        ('博士', '博士'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES)
    ethnicity = models.CharField('民族', max_length=20)
    birth_date = models.DateField('出生日期')
    education = models.CharField('学历', max_length=20, choices=EDUCATION_CHOICES)
    application_date = models.DateField('申请时间')
    cultivation_date = models.DateField('培养时间')
    organization = models.CharField('所属党组织', max_length=200)
    phone = models.CharField('联系电话', max_length=20)
    cultivator = models.CharField('培养人', max_length=50)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='培养中')
    student_id = models.CharField('学号', max_length=20, blank=True)
    grade = models.CharField('年级', max_length=20, blank=True)
    department = models.CharField('学院', max_length=100, blank=True)
    email = models.EmailField('邮箱', blank=True)
    address = models.CharField('地址', max_length=200, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'activists'
        verbose_name = '入党积极分子'
        verbose_name_plural = '积极分子管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.organization}"


class CultivationRecord(models.Model):
    """培养记录"""
    activist = models.ForeignKey(Activist, on_delete=models.CASCADE, related_name='cultivation_records')
    activity = models.CharField('培养活动', max_length=200)
    cultivation_date = models.DateField('培养时间')
    content = models.TextField('培养内容')
    cultivator = models.CharField('培养人', max_length=50)
    evaluation = models.TextField('培养人评价', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'cultivation_records'
        verbose_name = '培养记录'
        verbose_name_plural = '培养记录'
        ordering = ['-cultivation_date']
    
    def __str__(self):
        return f"{self.activist.name} - {self.activity}"


# ============================================================
# 党务管理模块 - 发展对象
# ============================================================
class DevelopingMember(models.Model):
    """发展对象"""
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]
    
    STATUS_CHOICES = [
        ('考察中', '考察中'),
        ('已转预备党员', '已转预备党员'),
    ]
    
    CONCLUSION_CHOICES = [
        ('合格', '合格'),
        ('基本合格', '基本合格'),
        ('不合格', '不合格'),
    ]
    
    EDUCATION_CHOICES = [
        ('本科', '本科'),
        ('硕士', '硕士'),
        ('博士', '博士'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES)
    ethnicity = models.CharField('民族', max_length=20)
    birth_date = models.DateField('出生日期')
    education = models.CharField('学历', max_length=20, choices=EDUCATION_CHOICES)
    determined_date = models.DateField('确定时间')
    organization = models.CharField('所属党组织', max_length=200)
    phone = models.CharField('联系电话', max_length=20)
    cultivator = models.CharField('培养人', max_length=50)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='考察中')
    student_id = models.CharField('学号', max_length=20, blank=True)
    grade = models.CharField('年级', max_length=20, blank=True)
    department = models.CharField('学院', max_length=100, blank=True)
    email = models.EmailField('邮箱', blank=True)
    address = models.CharField('地址', max_length=200, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'developing_members'
        verbose_name = '发展对象'
        verbose_name_plural = '发展对象管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.organization}"


class InspectionRecord(models.Model):
    """考察记录"""
    CONCLUSION_CHOICES = [
        ('合格', '合格'),
        ('基本合格', '基本合格'),
        ('不合格', '不合格'),
    ]
    
    developing_member = models.ForeignKey(DevelopingMember, on_delete=models.CASCADE, related_name='inspection_records')
    inspection_date = models.DateField('考察时间')
    content = models.TextField('考察内容')
    inspector = models.CharField('考察人', max_length=50)
    conclusion = models.CharField('考察结论', max_length=20, choices=CONCLUSION_CHOICES)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'inspection_records'
        verbose_name = '考察记录'
        verbose_name_plural = '考察记录'
        ordering = ['-inspection_date']
    
    def __str__(self):
        return f"{self.developing_member.name} - {self.inspection_date}"


# ============================================================
# 党务管理模块 - 预备党员
# ============================================================
class ProbationaryMember(models.Model):
    """预备党员"""
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]
    
    STATUS_CHOICES = [
        ('未申请', '未申请'),
        ('待审批', '待审批'),
        ('已转正', '已转正'),
        ('已拒绝', '已拒绝'),
    ]
    
    EDUCATION_CHOICES = [
        ('本科', '本科'),
        ('硕士', '硕士'),
        ('博士', '博士'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES)
    ethnicity = models.CharField('民族', max_length=20)
    birth_date = models.DateField('出生日期')
    education = models.CharField('学历', max_length=20, choices=EDUCATION_CHOICES)
    join_date = models.DateField('入党时间')
    organization = models.CharField('所属党组织', max_length=200)
    phone = models.CharField('联系电话', max_length=20)
    introducer = models.CharField('入党介绍人', max_length=50)
    application_date = models.DateField('转正申请时间', null=True, blank=True)
    approval_status = models.CharField('转正审批状态', max_length=20, choices=STATUS_CHOICES, default='未申请')
    regular_date = models.DateField('转正时间', null=True, blank=True)
    student_id = models.CharField('学号', max_length=20, blank=True)
    grade = models.CharField('年级', max_length=20, blank=True)
    department = models.CharField('学院', max_length=100, blank=True)
    email = models.EmailField('邮箱', blank=True)
    address = models.CharField('地址', max_length=200, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'probationary_members'
        verbose_name = '预备党员'
        verbose_name_plural = '预备党员管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.organization}"


# ============================================================
# 党务管理模块 - 党员发展流程
# ============================================================
class DevelopmentApplication(models.Model):
    """党员发展申请"""
    STAGE_CHOICES = [
        ('入党申请', '入党申请'),
        ('积极分子', '积极分子'),
        ('发展对象', '发展对象'),
        ('预备党员', '预备党员'),
        ('正式党员', '正式党员'),
    ]
    
    STATUS_CHOICES = [
        ('待审批', '待审批'),
        ('已通过', '已通过'),
        ('已拒绝', '已拒绝'),
        ('已完成', '已完成'),
    ]
    
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=10)
    ethnicity = models.CharField('民族', max_length=20)
    birth_date = models.DateField('出生日期')
    education = models.CharField('学历', max_length=20)
    organization = models.CharField('所属党组织', max_length=200)
    phone = models.CharField('联系电话', max_length=20)
    student_id = models.CharField('学号', max_length=20, blank=True)
    grade = models.CharField('年级', max_length=20, blank=True)
    department = models.CharField('学院', max_length=100, blank=True)
    
    current_stage = models.CharField('当前阶段', max_length=20, choices=STAGE_CHOICES, default='入党申请')
    application_status = models.CharField('审批状态', max_length=20, choices=STATUS_CHOICES, default='待审批')
    application_date = models.DateField('申请日期', auto_now_add=True)
    
    # 入党申请
    application_letter = models.TextField('入党申请书', blank=True)
    application_approved_date = models.DateField('入党申请批准日期', null=True, blank=True)
    
    # 积极分子阶段
    activist_date = models.DateField('确定积极分子日期', null=True, blank=True)
    activist_approved_date = models.DateField('积极分子批准日期', null=True, blank=True)
    
    # 发展对象阶段
    developing_date = models.DateField('确定发展对象日期', null=True, blank=True)
    developing_approved_date = models.DateField('发展对象批准日期', null=True, blank=True)
    
    # 预备党员阶段
    probationary_date = models.DateField('接收预备党员日期', null=True, blank=True)
    probationary_approved_date = models.DateField('预备党员批准日期', null=True, blank=True)
    
    # 正式党员阶段
    regular_date = models.DateField('转正日期', null=True, blank=True)
    regular_approved_date = models.DateField('转正批准日期', null=True, blank=True)
    
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'development_applications'
        verbose_name = '党员发展申请'
        verbose_name_plural = '党员发展流程'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.current_stage}"


class ApprovalRecord(models.Model):
    """审批记录"""
    application = models.ForeignKey(DevelopmentApplication, on_delete=models.CASCADE, related_name='approval_records')
    stage = models.CharField('审批阶段', max_length=20)
    approver = models.CharField('审批人', max_length=50)
    approval_date = models.DateField('审批时间', auto_now_add=True)
    opinion = models.TextField('审批意见')
    result = models.CharField('审批结果', max_length=20)
    
    class Meta:
        db_table = 'approval_records'
        verbose_name = '审批记录'
        verbose_name_plural = '审批记录'
        ordering = ['-approval_date']
    
    def __str__(self):
        return f"{self.application.name} - {self.stage} - {self.result}"
