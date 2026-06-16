from rest_framework import serializers
from .models import (
    Menu, SubMenu, Role, UserAccount, LoginLog, AccessToken, PermissionChangeLog, DataDictionary,
    Member, Activity, Material, MaterialBorrow, MaterialBorrowItem,
    LeagueMember, QingmaClass, QingmaStudent, QingmaCourse,
    LeagueBranch, FeeRecord,
    PartyMember, Activist, CultivationRecord,
    DevelopingMember, InspectionRecord,
    ProbationaryMember, DevelopmentApplication, ApprovalRecord
)


class LoginSerializer(serializers.Serializer):
    student_id = serializers.CharField(max_length=20)
    password = serializers.CharField(max_length=128)


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessToken
        fields = ['token', 'expires_at']


class UserInfoSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_permissions = serializers.JSONField(source='role.permissions', read_only=True)
    member_name = serializers.CharField(source='member.name', read_only=True)
    member_department = serializers.CharField(source='member.department', read_only=True)
    member_position = serializers.CharField(source='member.position', read_only=True)
    
    class Meta:
        model = UserAccount
        fields = ['student_id', 'role_name', 'role_permissions', 'member_name', 'member_department', 'member_position']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserAccountSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = UserAccount
        fields = ['id', 'student_id', 'role', 'role_id', 'is_active', 'last_login', 'login_count', 'created_at']


class LoginLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginLog
        fields = ['id', 'student_id', 'ip_address', 'user_agent', 'status', 'error_message', 'created_at']


class SubMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubMenu
        fields = ['id', 'name', 'path', 'order', 'is_active']


class MenuSerializer(serializers.ModelSerializer):
    submenus = SubMenuSerializer(many=True, read_only=True)
    
    class Meta:
        model = Menu
        fields = ['id', 'name', 'icon', 'path', 'order', 'is_active', 'submenus']

# ============================================================
# 成员管理序列化器
# ============================================================
class MemberSerializer(serializers.ModelSerializer):
    account = UserAccountSerializer(read_only=True)

    class Meta:
        model = Member
        fields = ['id', 'name', 'gender', 'student_id', 'department', 'position',
                  'role', 'grade', 'class_name', 'counselor_name', 'counselor_phone',
                  'phone', 'email', 'join_date', 'status', 'created_at', 'updated_at', 'account']
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 活动管理序列化器
# ============================================================
class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 物资管理序列化器
# ============================================================
class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class MaterialBorrowItemSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    
    class Meta:
        model = MaterialBorrowItem
        fields = ['id', 'material', 'material_name', 'quantity']


class MaterialBorrowSerializer(serializers.ModelSerializer):
    items = MaterialBorrowItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = MaterialBorrow
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 团务管理序列化器 - 团员管理
# ============================================================
class LeagueMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueMember
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 团务管理序列化器 - 青马班管理
# ============================================================
class QingmaClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = QingmaClass
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class QingmaStudentSerializer(serializers.ModelSerializer):
    session = serializers.SerializerMethodField()
    
    class Meta:
        model = QingmaStudent
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_session(self, obj):
        return obj.qingma_class.session if obj.qingma_class else None


class QingmaCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QingmaCourse
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 团务管理序列化器 - 团费管理
# ============================================================
class LeagueBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueBranch
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class FeeRecordSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = FeeRecord
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 党务管理序列化器 - 党员管理
# ============================================================
class PartyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyMember
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 党务管理序列化器 - 入党积极分子
# ============================================================
class CultivationRecordSerializer(serializers.ModelSerializer):
    activist_name = serializers.CharField(source='activist.name', read_only=True)
    
    class Meta:
        model = CultivationRecord
        fields = '__all__'
        read_only_fields = ['created_at']


class ActivistSerializer(serializers.ModelSerializer):
    cultivation_records = CultivationRecordSerializer(many=True, read_only=True)
    
    class Meta:
        model = Activist
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 党务管理序列化器 - 发展对象
# ============================================================
class InspectionRecordSerializer(serializers.ModelSerializer):
    developing_member_name = serializers.CharField(source='developing_member.name', read_only=True)
    
    class Meta:
        model = InspectionRecord
        fields = '__all__'
        read_only_fields = ['created_at']


class DevelopingMemberSerializer(serializers.ModelSerializer):
    inspection_records = InspectionRecordSerializer(many=True, read_only=True)
    
    class Meta:
        model = DevelopingMember
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 党务管理序列化器 - 预备党员
# ============================================================
class ProbationaryMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProbationaryMember
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 党务管理序列化器 - 党员发展流程
# ============================================================
class ApprovalRecordSerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source='application.name', read_only=True)
    
    class Meta:
        model = ApprovalRecord
        fields = '__all__'
        read_only_fields = ['approval_date']


class DevelopmentApplicationSerializer(serializers.ModelSerializer):
    approval_records = ApprovalRecordSerializer(many=True, read_only=True)

    class Meta:
        model = DevelopmentApplication
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# 权限管理序列化器 - 权限变更日志
# ============================================================
class PermissionChangeLogSerializer(serializers.ModelSerializer):
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)

    class Meta:
        model = PermissionChangeLog
        fields = '__all__'


class DataDictionarySerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = DataDictionary
        fields = '__all__'
