from django.contrib import admin
from .models import (
    Menu, SubMenu, Role, UserAccount, LoginLog, AccessToken,
    Member, Activity,
    Material, MaterialBorrow, MaterialBorrowItem,
    LeagueMember, QingmaClass, QingmaStudent, QingmaCourse,
    LeagueBranch, FeeRecord,
    PartyMember, Activist, CultivationRecord,
    DevelopingMember, InspectionRecord,
    ProbationaryMember, DevelopmentApplication, ApprovalRecord,
    DataDictionary, PermissionLog, PermissionChangeLog
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'role', 'is_active', 'last_login', 'login_count', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('student_id',)


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'ip_address', 'status', 'error_message', 'created_at')
    list_filter = ('status',)
    search_fields = ('student_id', 'ip_address')
    readonly_fields = ('student_id', 'ip_address', 'user_agent', 'status', 'error_message', 'created_at')


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'created_at')
    search_fields = ('user__student_id', 'token')

# ============================================================
# 菜单管理
# ============================================================
class SubMenuInline(admin.TabularInline):
    model = SubMenu
    extra = 1

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'order', 'is_active')
    list_filter = ('is_active',)
    ordering = ('order',)
    inlines = [SubMenuInline]

@admin.register(SubMenu)
class SubMenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu', 'path', 'order', 'is_active')
    list_filter = ('menu', 'is_active')
    ordering = ('menu__order', 'order')

# ============================================================
# 成员管理
# ============================================================
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id', 'department', 'position', 'status')
    list_filter = ('department', 'status')
    search_fields = ('name', 'student_id')

# ============================================================
# 活动管理
# ============================================================
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'status', 'start_time', 'location')
    list_filter = ('type', 'status')
    search_fields = ('name', 'location')

# ============================================================
# 物资管理
# ============================================================
class MaterialBorrowItemInline(admin.TabularInline):
    model = MaterialBorrowItem
    extra = 1

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'specification', 'category', 'quantity', 'status', 'storage_location')
    list_filter = ('category', 'status', 'storage_location')
    search_fields = ('name', 'specification')

@admin.register(MaterialBorrow)
class MaterialBorrowAdmin(admin.ModelAdmin):
    list_display = ('borrower', 'borrow_date', 'expected_return_date', 'status')
    list_filter = ('status',)
    search_fields = ('borrower',)
    inlines = [MaterialBorrowItemInline]

# ============================================================
# 团务管理 - 团员管理
# ============================================================
@admin.register(LeagueMember)
class LeagueMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id', 'college', 'organization', 'transfer_status')
    list_filter = ('college', 'transfer_status')
    search_fields = ('name', 'student_id')

# ============================================================
# 团务管理 - 青马班管理
# ============================================================
@admin.register(QingmaClass)
class QingmaClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'session', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('name', 'code')

@admin.register(QingmaStudent)
class QingmaStudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id', 'qingma_class', 'status')
    list_filter = ('qingma_class', 'status')
    search_fields = ('name', 'student_id')

@admin.register(QingmaCourse)
class QingmaCourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'qingma_class', 'teacher', 'course_type', 'course_time')
    list_filter = ('qingma_class', 'course_type', 'status')
    search_fields = ('name', 'teacher')

# ============================================================
# 团务管理 - 团费管理
# ============================================================
@admin.register(LeagueBranch)
class LeagueBranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'monthly_fee', 'total_members', 'paid_members')
    search_fields = ('name', 'code')

@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id', 'branch', 'month', 'amount', 'status')
    list_filter = ('branch', 'status')
    search_fields = ('name', 'student_id')

# ============================================================
# 党务管理 - 党员管理
# ============================================================
@admin.register(PartyMember)
class PartyMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'join_date', 'status')
    list_filter = ('status', 'gender')
    search_fields = ('name', 'student_id')

# ============================================================
# 党务管理 - 入党积极分子
# ============================================================
class CultivationRecordInline(admin.TabularInline):
    model = CultivationRecord
    extra = 1

@admin.register(Activist)
class ActivistAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'status', 'application_date')
    list_filter = ('status',)
    search_fields = ('name', 'student_id')
    inlines = [CultivationRecordInline]

@admin.register(CultivationRecord)
class CultivationRecordAdmin(admin.ModelAdmin):
    list_display = ('activist', 'activity', 'cultivation_date', 'cultivator')
    search_fields = ('activist__name', 'activity')

# ============================================================
# 党务管理 - 发展对象
# ============================================================
class InspectionRecordInline(admin.TabularInline):
    model = InspectionRecord
    extra = 1

@admin.register(DevelopingMember)
class DevelopingMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'status', 'determined_date')
    list_filter = ('status',)
    search_fields = ('name', 'student_id')
    inlines = [InspectionRecordInline]

@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ('developing_member', 'inspection_date', 'conclusion', 'inspector')
    list_filter = ('conclusion',)
    search_fields = ('developing_member__name',)

# ============================================================
# 党务管理 - 预备党员
# ============================================================
@admin.register(ProbationaryMember)
class ProbationaryMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'join_date', 'approval_status')
    list_filter = ('approval_status',)
    search_fields = ('name', 'student_id')

# ============================================================
# 党务管理 - 党员发展流程
# ============================================================
class ApprovalRecordInline(admin.TabularInline):
    model = ApprovalRecord
    extra = 1

@admin.register(DevelopmentApplication)
class DevelopmentApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_stage', 'application_status', 'application_date')
    list_filter = ('current_stage', 'application_status')
    search_fields = ('name', 'student_id')
    inlines = [ApprovalRecordInline]

@admin.register(ApprovalRecord)
class ApprovalRecordAdmin(admin.ModelAdmin):
    list_display = ('application', 'stage', 'approver', 'result', 'approval_date')
    list_filter = ('stage', 'result')
    search_fields = ('application__name', 'approver')


# ============================================================
# 权限管理 - 数据字典
# ============================================================
@admin.register(DataDictionary)
class DataDictionaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'is_active', 'sort_order')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('category', 'sort_order')


# ============================================================
# 权限管理 - 权限日志
# ============================================================
@admin.register(PermissionLog)
class PermissionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'role', 'required_permission', 'method', 'path', 'created_at')
    list_filter = ('role', 'method')
    search_fields = ('student_id', 'required_permission')
    readonly_fields = ('user', 'student_id', 'role', 'required_permission', 'method', 'path', 'ip', 'created_at')


# ============================================================
# 权限管理 - 权限变更日志
# ============================================================
@admin.register(PermissionChangeLog)
class PermissionChangeLogAdmin(admin.ModelAdmin):
    list_display = ('operator_name', 'operation_type', 'target_type', 'target_name', 'created_at')
    list_filter = ('operation_type', 'target_type')
    search_fields = ('operator_name', 'target_name')
    readonly_fields = ('operator', 'operator_student_id', 'operator_name', 'operation_type', 'target_type', 'target_id', 'target_name', 'change_detail', 'before_value', 'after_value', 'ip_address', 'created_at')