import uuid
import json
from datetime import datetime, timedelta
from django.db.models import Sum
from django.db.models import Count
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import BasePermission
from .authentication import AccessTokenAuthentication
from rest_framework.authtoken.models import Token


class HasPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user:
            return False

        if not request.user.role:
            return False

        permissions = request.user.role.get_permissions()

        required_permission = getattr(view, 'permission_code', None)
        if required_permission:
            if required_permission not in permissions:
                # 记录权限不足的尝试
                self._log_permission_denied(request, required_permission)
                return False
            return True

        return False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

    def _log_permission_denied(self, request, required_permission):
        try:
            from .models import PermissionLog
            PermissionLog.objects.create(
                user=request.user,
                student_id=request.user.student_id,
                role=request.user.role.name if request.user.role else '无',
                required_permission=required_permission,
                method=request.method,
                path=request.path,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
        except Exception:
            pass

from .models import (
    Menu, SubMenu, Role, UserAccount, LoginLog, AccessToken, PermissionChangeLog, DataDictionary,
    Member, Activity, Material, MaterialBorrow, MaterialBorrowItem,
    LeagueMember, QingmaClass, QingmaStudent, QingmaCourse,
    LeagueBranch, FeeRecord,
    PartyMember, Activist, CultivationRecord,
    DevelopingMember, InspectionRecord,
    ProbationaryMember, DevelopmentApplication, ApprovalRecord
)
from .serializers import (
    LoginSerializer, UserInfoSerializer, RoleSerializer, UserAccountSerializer, LoginLogSerializer,
    MenuSerializer, SubMenuSerializer, PermissionChangeLogSerializer, DataDictionarySerializer,
    MemberSerializer, ActivitySerializer, MaterialSerializer,
    MaterialBorrowSerializer, MaterialBorrowItemSerializer,
    LeagueMemberSerializer,
    QingmaClassSerializer, QingmaStudentSerializer, QingmaCourseSerializer,
    LeagueBranchSerializer, FeeRecordSerializer,
    PartyMemberSerializer, ActivistSerializer, CultivationRecordSerializer,
    DevelopingMemberSerializer, InspectionRecordSerializer,
    ProbationaryMemberSerializer, DevelopmentApplicationSerializer, ApprovalRecordSerializer
)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_permission_change(request, operation_type, target_type, target_id, target_name,
                          before_value=None, after_value=None, change_detail=None):
    """记录权限变更日志"""
    try:
        operator = request.user if hasattr(request, 'user') else None
        operator_name = ''
        if operator and operator.member:
            operator_name = operator.member.name
        elif operator:
            operator_name = operator.student_id

        PermissionChangeLog.objects.create(
            operator=operator,
            operator_student_id=operator.student_id if operator else '',
            operator_name=operator_name,
            operation_type=operation_type,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            change_detail=change_detail or '',
            before_value=before_value or '',
            after_value=after_value or '',
            ip_address=get_client_ip(request)
        )
    except Exception as e:
        print(f'记录权限变更日志失败: {e}')


def create_access_token(user):
    token = uuid.uuid4().hex
    expires_at = timezone.now() + timedelta(hours=24)
    AccessToken.objects.filter(user=user).delete()
    access_token = AccessToken.objects.create(user=user, token=token, expires_at=expires_at)
    return access_token


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        LoginLog.objects.create(
            student_id=request.data.get('student_id', ''),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='failed',
            error_message='参数验证失败'
        )
        return Response({'code': 400, 'message': '参数错误'}, status=status.HTTP_400_BAD_REQUEST)
    
    student_id = serializer.validated_data['student_id']
    password = serializer.validated_data['password']
    
    recent_failures = LoginLog.objects.filter(
        student_id=student_id,
        status='failed',
        created_at__gte=timezone.now() - timedelta(minutes=5)
    ).count()
    
    if recent_failures >= 5:
        LoginLog.objects.create(
            student_id=student_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='failed',
            error_message='登录失败次数过多，请稍后重试'
        )
        return Response({'code': 429, 'message': '登录失败次数过多，请5分钟后重试'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    try:
        user = UserAccount.objects.get(student_id=student_id)
    except UserAccount.DoesNotExist:
        LoginLog.objects.create(
            student_id=student_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='failed',
            error_message='学号不存在'
        )
        return Response({'code': 401, 'message': '学号或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        LoginLog.objects.create(
            student_id=student_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='failed',
            error_message='账户已被禁用'
        )
        return Response({'code': 403, 'message': '账户已被禁用'}, status=status.HTTP_403_FORBIDDEN)
    
    if not user.check_password(password):
        LoginLog.objects.create(
            student_id=student_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='failed',
            error_message='密码错误'
        )
        return Response({'code': 401, 'message': '学号或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
    
    user.last_login = timezone.now()
    user.login_count += 1
    user.save()
    
    access_token = create_access_token(user)
    
    LoginLog.objects.create(
        student_id=student_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        status='success',
        error_message=''
    )
    
    user_info = UserInfoSerializer(user).data
    
    return Response({
        'code': 200,
        'message': '登录成功',
        'data': {
            'token': access_token.token,
            'expires_at': access_token.expires_at,
            'user': user_info
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        AccessToken.objects.filter(token=token).delete()
    return Response({'code': 200, 'message': '退出成功'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        access_token = AccessToken.objects.get(token=token)
        if access_token.is_expired():
            return Response({'code': 401, 'message': '登录已过期'}, status=status.HTTP_401_UNAUTHORIZED)
        user = access_token.user
        user_info = UserInfoSerializer(user).data
        
        permissions = []
        if user.role:
            permissions = user.role.get_permissions()
        
        user_info['permissions'] = permissions
        
        return Response({
            'code': 200,
            'message': 'success',
            'data': user_info
        }, status=status.HTTP_200_OK)
    except AccessToken.DoesNotExist:
        return Response({'code': 401, 'message': '未登录'}, status=status.HTTP_401_UNAUTHORIZED)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    authentication_classes = [AccessTokenAuthentication]
    permission_code = 'role:view'

    def create(self, request, *args, **kwargs):
        self.permission_code = 'role:add'
        response = super().create(request, *args, **kwargs)

        if response.status_code == 201:
            data = response.data
            log_permission_change(
                request=request,
                operation_type='create_role',
                target_type='角色',
                target_id=data.get('id'),
                target_name=data.get('name', ''),
                after_value=json.dumps(data),
                change_detail=f'创建角色: {data.get("name", "")}'
            )

        return response

    def update(self, request, *args, **kwargs):
        self.permission_code = 'role:edit'
        instance = self.get_object()
        before_data = RoleSerializer(instance).data
        before_permissions = instance.get_permissions()

        response = super().update(request, *args, **kwargs)

        if response.status_code == 200:
            after_data = response.data
            after_permissions = json.loads(after_data.get('permissions', '[]'))

            # 检查权限是否变更
            if before_permissions != after_permissions:
                change_detail = f'权限变更: 从 {len(before_permissions)} 个权限变为 {len(after_permissions)} 个权限'
                log_permission_change(
                    request=request,
                    operation_type='change_permissions',
                    target_type='角色',
                    target_id=instance.id,
                    target_name=instance.name,
                    before_value=json.dumps(before_permissions),
                    after_value=json.dumps(after_permissions),
                    change_detail=change_detail
                )

            # 记录角色编辑
            log_permission_change(
                request=request,
                operation_type='edit_role',
                target_type='角色',
                target_id=instance.id,
                target_name=instance.name,
                before_value=json.dumps(before_data),
                after_value=json.dumps(after_data),
                change_detail=f'编辑角色: {instance.name}'
            )

        return response

    def destroy(self, request, *args, **kwargs):
        self.permission_code = 'role:delete'
        instance = self.get_object()
        before_data = RoleSerializer(instance).data

        response = super().destroy(request, *args, **kwargs)

        if response.status_code == 204:
            log_permission_change(
                request=request,
                operation_type='delete_role',
                target_type='角色',
                target_id=instance.id,
                target_name=instance.name,
                before_value=json.dumps(before_data),
                change_detail=f'删除角色: {instance.name}'
            )

        return response


class UserAccountViewSet(viewsets.ModelViewSet):
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    authentication_classes = [AccessTokenAuthentication]
    permission_code = 'user:view'

    def create(self, request, *args, **kwargs):
        self.permission_code = 'user:add'
        response = super().create(request, *args, **kwargs)

        if response.status_code == 201:
            data = response.data
            role_name = ''
            if data.get('role'):
                try:
                    role = Role.objects.get(id=data.get('role'))
                    role_name = role.name
                except:
                    pass

            log_permission_change(
                request=request,
                operation_type='create_user',
                target_type='用户',
                target_id=data.get('id'),
                target_name=data.get('student_id', ''),
                after_value=json.dumps(data),
                change_detail=f'创建用户账户: {data.get("student_id", "")}, 角色: {role_name}'
            )

        return response

    def update(self, request, *args, **kwargs):
        self.permission_code = 'user:edit'
        instance = self.get_object()
        before_data = UserAccountSerializer(instance).data
        before_role = instance.role.name if instance.role else '无角色'

        response = super().update(request, *args, **kwargs)

        if response.status_code == 200:
            after_data = response.data
            after_role = ''
            if after_data.get('role'):
                try:
                    role = Role.objects.get(id=after_data.get('role'))
                    after_role = role.name
                except:
                    after_role = '无角色'

            # 检查角色是否变更
            if before_role != after_role:
                change_detail = f'角色变更: 从 "{before_role}" 变为 "{after_role}"'
                log_permission_change(
                    request=request,
                    operation_type='assign_role',
                    target_type='用户',
                    target_id=instance.id,
                    target_name=instance.student_id,
                    before_value=before_role,
                    after_value=after_role,
                    change_detail=change_detail
                )

            # 记录用户编辑
            log_permission_change(
                request=request,
                operation_type='edit_user',
                target_type='用户',
                target_id=instance.id,
                target_name=instance.student_id,
                before_value=json.dumps(before_data),
                after_value=json.dumps(after_data),
                change_detail=f'编辑用户账户: {instance.student_id}'
            )

        return response

    def destroy(self, request, *args, **kwargs):
        self.permission_code = 'user:delete'
        instance = self.get_object()
        before_data = UserAccountSerializer(instance).data

        response = super().destroy(request, *args, **kwargs)

        if response.status_code == 204:
            log_permission_change(
                request=request,
                operation_type='delete_user',
                target_type='用户',
                target_id=instance.id,
                target_name=instance.student_id,
                before_value=json.dumps(before_data),
                change_detail=f'删除用户账户: {instance.student_id}'
            )

        return response

    @action(detail=False, methods=['POST'])
    def create_account(self, request):
        self.permission_code = 'user:add'
        student_id = request.data.get('student_id')
        password = request.data.get('password')
        role_id = request.data.get('role_id')

        if not student_id or not password:
            return Response({'code': 400, 'message': '学号和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证角色是否存在
        role_name = ''
        if role_id:
            try:
                role_id = int(role_id)
                role = Role.objects.filter(id=role_id).first()
                if not role:
                    return Response({'code': 400, 'message': '选择的角色不存在'}, status=status.HTTP_400_BAD_REQUEST)
                role_name = role.name
            except (ValueError, TypeError):
                return Response({'code': 400, 'message': '角色ID无效'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            existing_account = UserAccount.objects.filter(student_id=student_id).first()

            if existing_account:
                # 更新密码和角色
                before_role = existing_account.role.name if existing_account.role else '无角色'
                existing_account.set_password(password)
                if role_id:
                    existing_account.role_id = role_id
                existing_account.save()
                after_role = existing_account.role.name if existing_account.role else '无角色'

                # 记录角色变更
                if before_role != after_role:
                    log_permission_change(
                        request=request,
                        operation_type='assign_role',
                        target_type='用户',
                        target_id=existing_account.id,
                        target_name=student_id,
                        before_value=before_role,
                        after_value=after_role,
                        change_detail=f'为用户 {student_id} 分配角色: {after_role}'
                    )

                return Response({'code': 200, 'message': '角色更新成功', 'role': existing_account.role.name if existing_account.role else None}, status=status.HTTP_200_OK)

            member = Member.objects.filter(student_id=student_id).first()

            user = UserAccount()
            user.student_id = student_id
            user.set_password(password)
            if role_id:
                user.role_id = role_id
            if member:
                user.member = member
            user.save()

            # 记录用户创建
            log_permission_change(
                request=request,
                operation_type='create_user',
                target_type='用户',
                target_id=user.id,
                target_name=student_id,
                after_value=json.dumps({'student_id': student_id, 'role': role_name}),
                change_detail=f'创建用户账户: {student_id}, 角色: {role_name}'
            )

            return Response({'code': 200, 'message': '账户创建成功', 'role': user.role.name if user.role else None}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'code': 500, 'message': f'创建账户失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['POST'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'code': 400, 'message': '旧密码错误'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'code': 200, 'message': '密码修改成功'}, status=status.HTTP_200_OK)


class LoginLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoginLog.objects.all()
    serializer_class = LoginLogSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'])
    def statistics(self, request):
        today = timezone.now().date()
        today_logs = LoginLog.objects.filter(created_at__date=today)
        success_count = today_logs.filter(status='success').count()
        failed_count = today_logs.filter(status='failed').count()

        return Response({
            'code': 200,
            'data': {
                'today_success': success_count,
                'today_failed': failed_count,
                'total_records': LoginLog.objects.count()
            }
        })


class PermissionChangeLogViewSet(viewsets.ReadOnlyModelViewSet):
    """权限变更日志ViewSet"""
    queryset = PermissionChangeLog.objects.all()
    serializer_class = PermissionChangeLogSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    authentication_classes = [AccessTokenAuthentication]
    permission_code = 'log:view'

    @action(detail=False, methods=['GET'])
    def statistics(self, request):
        """获取权限变更统计"""
        today = timezone.now().date()
        today_logs = PermissionChangeLog.objects.filter(created_at__date=today)

        # 按操作类型统计
        operation_stats = {}
        for op_type in PermissionChangeLog.OPERATION_TYPES:
            op_code, op_name = op_type
            count = PermissionChangeLog.objects.filter(operation_type=op_code).count()
            operation_stats[op_name] = count

        return Response({
            'code': 200,
            'data': {
                'today_count': today_logs.count(),
                'total_count': PermissionChangeLog.objects.count(),
                'operation_stats': operation_stats
            }
        })


class DataDictionaryViewSet(viewsets.ModelViewSet):
    """数据字典ViewSet"""
    queryset = DataDictionary.objects.all()
    serializer_class = DataDictionarySerializer

    def get_permission_classes(self):
        if self.action in ['by_category', 'categories']:
            return [IsAuthenticated]
        return [IsAuthenticated, HasPermission]

    def check_permissions(self, request):
        if self.action in ['by_category', 'categories']:
            self.permission_code = None
            super().check_permissions(request)
            return
        if self.action == 'create':
            self.permission_code = 'menu:edit'
        elif self.action in ['update', 'partial_update']:
            self.permission_code = 'menu:edit'
        elif self.action == 'destroy':
            self.permission_code = 'menu:delete'
        else:
            self.permission_code = 'menu:view'
        super().check_permissions(request)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            data = response.data
            log_permission_change(
                request=request,
                operation_type='create_role',
                target_type='数据字典',
                target_id=data.get('id'),
                target_name=data.get('name', ''),
                after_value=json.dumps(data),
                change_detail=f'创建数据字典项: {data.get("category_display", "")} - {data.get("name", "")}'
            )
        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        before_data = DataDictionarySerializer(instance).data
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            after_data = response.data
            log_permission_change(
                request=request,
                operation_type='edit_role',
                target_type='数据字典',
                target_id=instance.id,
                target_name=instance.name,
                before_value=json.dumps(before_data),
                after_value=json.dumps(after_data),
                change_detail=f'编辑数据字典项: {instance.name}'
            )
        return response

    def destroy(self, request, *args, **kwargs):
        self.permission_code = 'menu:edit'
        instance = self.get_object()
        before_data = DataDictionarySerializer(instance).data
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == 204:
            log_permission_change(
                request=request,
                operation_type='delete_role',
                target_type='数据字典',
                target_id=instance.id,
                target_name=instance.name,
                before_value=json.dumps(before_data),
                change_detail=f'删除数据字典项: {instance.name}'
            )
        return response

    @action(detail=False, methods=['GET'])
    def by_category(self, request):
        """按分类获取数据字典"""
        category = request.query_params.get('category')
        if not category:
            return Response({'code': 400, 'message': '请提供分类参数'}, status=status.HTTP_400_BAD_REQUEST)

        items = DataDictionary.objects.filter(category=category, is_active=True).order_by('sort_order', 'name')
        serializer = DataDictionarySerializer(items, many=True)
        return Response({'code': 200, 'data': serializer.data})

    @action(detail=False, methods=['GET'])
    def categories(self, request):
        """获取所有分类（从数据库动态查询，支持自定义分类）"""
        category_choices = list(DataDictionary.CATEGORY_CHOICES)
        
        db_categories = DataDictionary.objects.values_list('category', flat=True).distinct()
        for cat in db_categories:
            found = False
            for choice in category_choices:
                if choice[0] == cat:
                    found = True
                    break
            if not found:
                category_choices.append((cat, cat))
        
        return Response({'code': 200, 'data': category_choices})


# ============================================================
# 菜单管理视图集
# ============================================================
class MenuViewSet(viewsets.ModelViewSet):
    """
    一级菜单管理API
    """
    queryset = Menu.objects.filter(is_active=True).order_by('order')
    serializer_class = MenuSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取菜单树结构（包含二级菜单）"""
        menus = Menu.objects.filter(is_active=True).order_by('order').prefetch_related('submenus')
        serializer = MenuSerializer(menus, many=True)
        return Response({'code': 200, 'data': serializer.data})


class SubMenuViewSet(viewsets.ModelViewSet):
    """
    二级菜单管理API
    """
    queryset = SubMenu.objects.filter(is_active=True).order_by('order')
    serializer_class = SubMenuSerializer


# ============================================================
# 成员管理视图集
# ============================================================
class MemberViewSet(viewsets.ModelViewSet):
    """
    学生会成员管理API
    """
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    authentication_classes = [AccessTokenAuthentication]
    permission_code = 'member:view'

    def check_permissions(self, request):
        if self.action == 'create':
            self.permission_code = 'member:add'
        elif self.action in ['update', 'partial_update']:
            self.permission_code = 'member:edit'
        elif self.action == 'destroy':
            self.permission_code = 'member:delete'
        else:
            self.permission_code = 'member:view'
        super().check_permissions(request)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        department = self.request.query_params.get('department', None)
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if department:
            queryset = queryset.filter(department=department)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = Member.objects.count()
        working = Member.objects.filter(status='在职').count()
        resigned = Member.objects.filter(status='离职').count()
        
        return Response({
            'total': total,
            'working': working,
            'resigned': resigned
        })
    
    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """批量导入成员数据"""
        data = request.data.get('data', [])
        
        if not data:
            return Response({'code': 400, 'message': '没有数据需要导入'}, status=status.HTTP_400_BAD_REQUEST)
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for index, item in enumerate(data):
            try:
                # 检查学号是否已存在
                if Member.objects.filter(student_id=item.get('studentId')).exists():
                    failed_count += 1
                    errors.append({
                        'row': index + 1,
                        'studentId': item.get('studentId'),
                        'name': item.get('name'),
                        'error': '学号已存在'
                    })
                    continue
                
                member = Member(
                    name=item.get('name'),
                    gender=item.get('gender'),
                    student_id=item.get('studentId'),
                    department=item.get('department'),
                    position=item.get('position'),
                    grade=item.get('grade'),
                    class_name=item.get('className'),
                    counselor_name=item.get('counselorName'),
                    counselor_phone=item.get('counselorPhone'),
                    phone=item.get('phone'),
                    email=item.get('email'),
                    join_date=item.get('joinDate'),
                    status='在职'
                )
                member.save()
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({
                    'row': index + 1,
                    'studentId': item.get('studentId'),
                    'name': item.get('name'),
                    'error': str(e)
                })
        
        return Response({
            'code': 200,
            'message': '导入完成',
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        })


# ============================================================
# 活动管理视图集
# ============================================================
class ActivityViewSet(viewsets.ModelViewSet):
    """
    活动管理API
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated, HasPermission]
    authentication_classes = [AccessTokenAuthentication]
    permission_code = 'activity:view'

    def check_permissions(self, request):
        if self.action == 'create':
            self.permission_code = 'activity:add'
        elif self.action in ['update', 'partial_update']:
            self.permission_code = 'activity:edit'
        elif self.action == 'destroy':
            self.permission_code = 'activity:delete'
        else:
            self.permission_code = 'activity:view'
        super().check_permissions(request)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        activity_type = self.request.query_params.get('type', None)
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if activity_type:
            queryset = queryset.filter(type=activity_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = Activity.objects.count()
        ongoing = Activity.objects.filter(status='进行中').count()
        finished = Activity.objects.filter(status='已结束').count()
        upcoming = Activity.objects.filter(status='未开始').count()
        
        return Response({
            'total': total,
            'ongoing': ongoing,
            'finished': finished,
            'upcoming': upcoming
        })


# ============================================================
# 物资管理视图集
# ============================================================
class MaterialViewSet(viewsets.ModelViewSet):
    """
    物资管理API
    """
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    authentication_classes = [AccessTokenAuthentication]
    permission_code = 'material:view'

    def check_permissions(self, request):
        if self.action == 'create':
            self.permission_code = 'material:add'
        elif self.action in ['update', 'partial_update']:
            self.permission_code = 'material:edit'
        elif self.action == 'destroy':
            self.permission_code = 'material:delete'
        else:
            self.permission_code = 'material:view'
        super().check_permissions(request)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category=category)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = Material.objects.count()
        total_quantity = Material.objects.aggregate(total=Sum('quantity'))['total'] or 0
        normal = Material.objects.filter(status='正常').count()
        
        return Response({
            'total': total,
            'total_quantity': total_quantity,
            'normal': normal
        })


class MaterialBorrowViewSet(viewsets.ModelViewSet):
    """
    物资借用管理API
    """
    queryset = MaterialBorrow.objects.all()
    serializer_class = MaterialBorrowSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    authentication_classes = [AccessTokenAuthentication]
    permission_code = 'material:view'

    def check_permissions(self, request):
        if self.action == 'create':
            self.permission_code = 'material:add'
        elif self.action in ['update', 'partial_update']:
            self.permission_code = 'material:edit'
        elif self.action == 'destroy':
            self.permission_code = 'material:delete'
        else:
            self.permission_code = 'material:view'
        super().check_permissions(request)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        borrow_status = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if borrow_status:
            queryset = queryset.filter(status=borrow_status)
        if search:
            queryset = queryset.filter(borrower__icontains=search)
        
        return queryset
    
    def perform_create(self, serializer):
        """创建借用记录时更新物资库存"""
        borrow = serializer.save()
        
        # 更新借用物资的库存
        for item in borrow.items.all():
            material = item.material
            material.quantity -= item.quantity
            material.save()
    
    @action(detail=True, methods=['post'])
    def return_borrow(self, request, pk=None):
        """归还借用"""
        borrow = self.get_object()
        borrow.status = '已归还'
        borrow.actual_return_date = timezone.now().date()
        borrow.save()
        
        # 更新物资库存
        for item in borrow.items.all():
            material = item.material
            material.quantity += item.quantity
            material.save()
        
        serializer = MaterialBorrowSerializer(borrow)
        return Response({'status': '归还成功', 'data': serializer.data})


# ============================================================
# 团务管理视图集 - 团员管理
# ============================================================
class LeagueMemberViewSet(viewsets.ModelViewSet):
    """
    团员管理API
    """
    queryset = LeagueMember.objects.all()
    serializer_class = LeagueMemberSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        college = self.request.query_params.get('college', None)
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if college:
            queryset = queryset.filter(college=college)
        if status_filter:
            queryset = queryset.filter(transfer_status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = LeagueMember.objects.count()
        active = LeagueMember.objects.filter(transfer_status='已完成').count()
        transferring = LeagueMember.objects.filter(transfer_status='转接中').count()
        
        return Response({
            'total': total,
            'active': active,
            'transferring': transferring
        })
    
    def format_date(self, date_str):
        """将日期字符串转换为YYYY-MM-DD格式，支持20050626和2025-05格式"""
        if not date_str:
            return None
        date_str = str(date_str).strip()
        # 处理20050626格式
        if len(date_str) == 8 and date_str.isdigit():
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        # 处理2025-05格式（只有年月）
        elif len(date_str) == 7 and date_str.count('-') == 1:
            parts = date_str.split('-')
            if len(parts[0]) == 4 and len(parts[1]) == 2:
                return f"{date_str}-01"
        # 已经是YYYY-MM-DD格式
        elif len(date_str) == 10 and date_str.count('-') == 2:
            return date_str
        return None
    
    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """批量导入团员数据"""
        data = request.data.get('data', [])
        
        if not data:
            return Response({'code': 400, 'message': '没有数据需要导入'}, status=status.HTTP_400_BAD_REQUEST)
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for index, item in enumerate(data):
            try:
                # 检查学号是否已存在
                if LeagueMember.objects.filter(student_id=item.get('studentId')).exists():
                    failed_count += 1
                    errors.append({
                        'row': index + 1,
                        'studentId': item.get('studentId'),
                        'name': item.get('name'),
                        'error': '学号已存在'
                    })
                    continue
                
                member = LeagueMember(
                    name=item.get('name') or '',
                    gender=item.get('gender') or '男',
                    student_id=item.get('studentId') or '',
                    birth_date=self.format_date(item.get('birthDate')),
                    ethnicity=item.get('nationality') or '汉族',
                    id_card=item.get('idCard') or '',
                    phone=item.get('phone') or '',
                    college=item.get('college') or '',
                    grade=item.get('grade') or '',
                    organization=item.get('organization') or '',
                    counselor=item.get('counselor') or '',
                    position=item.get('position') or '',
                    political_status=item.get('politicalStatus') or '共青团员',
                    development_number=item.get('memberCode') or '',
                    join_date=self.format_date(item.get('joinDate')),
                    hometown=item.get('residence') or '',
                    transfer_reason=item.get('transferReason') or '',
                    transfer_status=item.get('transferStatus') or '未转接',
                    transfer_address=item.get('transferAddress') or '',
                    notes=item.get('remark') or ''
                )
                member.save()
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({
                    'row': index + 1,
                    'studentId': item.get('studentId'),
                    'name': item.get('name'),
                    'error': str(e)
                })
        
        return Response({
            'code': 200,
            'message': '导入完成',
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        })


# ============================================================
# 团务管理视图集 - 青马班管理
# ============================================================
class QingmaClassViewSet(viewsets.ModelViewSet):
    """
    青马班管理API
    """
    queryset = QingmaClass.objects.all()
    serializer_class = QingmaClassSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = QingmaClass.objects.count()
        ongoing = QingmaClass.objects.filter(status='进行中').count()
        preparing = QingmaClass.objects.filter(status='筹备中').count()
        finished = QingmaClass.objects.filter(status='已结业').count()
        
        return Response({
            'total': total,
            'ongoing': ongoing,
            'preparing': preparing,
            'finished': finished
        })


class QingmaStudentViewSet(viewsets.ModelViewSet):
    """
    青马班学员管理API
    """
    queryset = QingmaStudent.objects.all()
    serializer_class = QingmaStudentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        qingma_class = self.request.query_params.get('class_id', None)
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if qingma_class:
            queryset = queryset.filter(qingma_class_id=qingma_class)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    def perform_create(self, serializer):
        """创建学员时更新班级人数"""
        student = serializer.save()
        qingma_class = student.qingma_class
        qingma_class.current_students += 1
        qingma_class.save()
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = QingmaStudent.objects.count()
        studying = QingmaStudent.objects.filter(status='在读').count()
        graduated = QingmaStudent.objects.filter(status='已结业').count()
        
        return Response({
            'total': total,
            'studying': studying,
            'graduated': graduated
        })
    
    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """批量导入学员数据"""
        data = request.data.get('data', [])
        
        if not data:
            return Response({'code': 400, 'message': '没有数据需要导入'}, status=status.HTTP_400_BAD_REQUEST)
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for index, item in enumerate(data):
            try:
                if QingmaStudent.objects.filter(student_id=item.get('studentId')).exists():
                    failed_count += 1
                    errors.append({
                        'row': index + 1,
                        'studentId': item.get('studentId'),
                        'name': item.get('name'),
                        'error': '学号已存在'
                    })
                    continue
                
                qingma_class_id = item.get('classId')
                if not qingma_class_id:
                    failed_count += 1
                    errors.append({
                        'row': index + 1,
                        'studentId': item.get('studentId'),
                        'name': item.get('name'),
                        'error': '请选择青马班班级'
                    })
                    continue
                
                student = QingmaStudent(
                    name=item.get('name'),
                    gender=item.get('gender'),
                    student_id=item.get('studentId'),
                    qingma_class_id=qingma_class_id,
                    department=item.get('department'),
                    grade=item.get('grade'),
                    phone=item.get('phone'),
                    email=item.get('email'),
                    counselor_name=item.get('counselorName'),
                    counselor_phone=item.get('counselorPhone'),
                    status=item.get('status', '在读')
                )
                student.save()
                
                qingma_class = student.qingma_class
                qingma_class.current_students += 1
                qingma_class.save()
                
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({
                    'row': index + 1,
                    'studentId': item.get('studentId'),
                    'name': item.get('name'),
                    'error': str(e)
                })
        
        return Response({
            'code': 200,
            'message': '导入完成',
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        })


class QingmaCourseViewSet(viewsets.ModelViewSet):
    """
    青马班课程管理API
    """
    queryset = QingmaCourse.objects.all()
    serializer_class = QingmaCourseSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        qingma_class = self.request.query_params.get('class_id', None)
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if qingma_class:
            queryset = queryset.filter(qingma_class_id=qingma_class)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


# ============================================================
# 团务管理视图集 - 团费管理
# ============================================================
class LeagueBranchViewSet(viewsets.ModelViewSet):
    """
    团支部管理API
    """
    queryset = LeagueBranch.objects.all()
    serializer_class = LeagueBranchSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def batch_pay(self, request, pk=None):
        """批量缴费"""
        branch = self.get_object()
        # 实现批量缴费逻辑
        return Response({'status': '批量缴费成功'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = LeagueBranch.objects.count()
        total_members = LeagueBranch.objects.aggregate_sum('total_members') or 0
        paid_members = LeagueBranch.objects.aggregate_sum('paid_members') or 0
        
        return Response({
            'total': total,
            'total_members': total_members,
            'paid_members': paid_members
        })


class FeeRecordViewSet(viewsets.ModelViewSet):
    """
    团费缴费记录管理API
    """
    queryset = FeeRecord.objects.all()
    serializer_class = FeeRecordSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        branch = self.request.query_params.get('branch_id', None)
        fee_status = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if branch:
            queryset = queryset.filter(branch_id=branch)
        if fee_status:
            queryset = queryset.filter(status=fee_status)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


# ============================================================
# 党务管理视图集 - 党员管理
# ============================================================
class PartyMemberViewSet(viewsets.ModelViewSet):
    """
    党员管理API
    """
    queryset = PartyMember.objects.all()
    serializer_class = PartyMemberSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.query_params.get('organization', None)
        status_filter = self.request.query_params.get('status', None)
        gender = self.request.query_params.get('gender', None)
        search = self.request.query_params.get('search', None)
        
        if organization:
            queryset = queryset.filter(organization=organization)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if gender:
            queryset = queryset.filter(gender=gender)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = PartyMember.objects.count()
        regular = PartyMember.objects.filter(regular_date__isnull=False).count()
        probationary = PartyMember.objects.filter(regular_date__isnull=True).count()
        normal = PartyMember.objects.filter(status='正常').count()
        
        return Response({
            'total': total,
            'regular': regular,
            'probationary': probationary,
            'normal': normal
        })


# ============================================================
# 党务管理视图集 - 入党积极分子
# ============================================================
class ActivistViewSet(viewsets.ModelViewSet):
    """
    入党积极分子管理API
    """
    queryset = Activist.objects.all()
    serializer_class = ActivistSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.query_params.get('organization', None)
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if organization:
            queryset = queryset.filter(organization=organization)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = Activist.objects.count()
        cultivating = Activist.objects.filter(status='培养中').count()
        transferred = Activist.objects.filter(status='已转发展对象').count()
        
        return Response({
            'total': total,
            'cultivating': cultivating,
            'transferred': transferred
        })


class CultivationRecordViewSet(viewsets.ModelViewSet):
    """
    培养记录管理API
    """
    queryset = CultivationRecord.objects.all()
    serializer_class = CultivationRecordSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        activist_id = self.request.query_params.get('activist_id', None)
        
        if activist_id:
            queryset = queryset.filter(activist_id=activist_id)
        
        return queryset


# ============================================================
# 党务管理视图集 - 发展对象
# ============================================================
class DevelopingMemberViewSet(viewsets.ModelViewSet):
    """
    发展对象管理API
    """
    queryset = DevelopingMember.objects.all()
    serializer_class = DevelopingMemberSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.query_params.get('organization', None)
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if organization:
            queryset = queryset.filter(organization=organization)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = DevelopingMember.objects.count()
        inspecting = DevelopingMember.objects.filter(status='考察中').count()
        transferred = DevelopingMember.objects.filter(status='已转预备党员').count()
        
        return Response({
            'total': total,
            'inspecting': inspecting,
            'transferred': transferred
        })


class InspectionRecordViewSet(viewsets.ModelViewSet):
    """
    考察记录管理API
    """
    queryset = InspectionRecord.objects.all()
    serializer_class = InspectionRecordSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        member_id = self.request.query_params.get('member_id', None)
        
        if member_id:
            queryset = queryset.filter(developing_member_id=member_id)
        
        return queryset


# ============================================================
# 党务管理视图集 - 预备党员
# ============================================================
class ProbationaryMemberViewSet(viewsets.ModelViewSet):
    """
    预备党员管理API
    """
    queryset = ProbationaryMember.objects.all()
    serializer_class = ProbationaryMemberSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.query_params.get('organization', None)
        approval_status = self.request.query_params.get('approval_status', None)
        search = self.request.query_params.get('search', None)
        
        if organization:
            queryset = queryset.filter(organization=organization)
        if approval_status:
            queryset = queryset.filter(approval_status=approval_status)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def submit_regularization(self, request, pk=None):
        """提交转正申请"""
        member = self.get_object()
        member.approval_status = '待审批'
        member.save()
        return Response({'status': '转正申请已提交'})
    
    @action(detail=True, methods=['post'])
    def approve_regularization(self, request, pk=None):
        """审批转正"""
        member = self.get_object()
        member.approval_status = '已转正'
        
        # 获取转正时间，优先使用请求中的时间，否则使用当前时间
        regular_date = request.data.get('regular_date')
        if regular_date:
            member.regular_date = regular_date
        
        member.save()
        
        # 自动创建正式党员记录
        PartyMember.objects.create(
            name=member.name,
            gender=member.gender,
            ethnicity=member.ethnicity,
            birth_date=member.birth_date,
            education=member.education,
            join_date=member.join_date,
            regular_date=member.regular_date,
            organization=member.organization,
            phone=member.phone,
            introducer=member.introducer,
            status='正常',
            student_id=member.student_id,
            grade=member.grade,
            department=member.department,
            email=member.email,
            address=member.address,
            notes=member.notes
        )
        
        return Response({'status': '转正审批已通过，已自动创建正式党员记录'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = ProbationaryMember.objects.count()
        pending = ProbationaryMember.objects.filter(approval_status='待审批').count()
        regularized = ProbationaryMember.objects.filter(approval_status='已转正').count()
        
        return Response({
            'total': total,
            'pending': pending,
            'regularized': regularized
        })


# ============================================================
# 党务管理视图集 - 党员发展流程
# ============================================================
class DevelopmentApplicationViewSet(viewsets.ModelViewSet):
    """
    党员发展申请管理API
    """
    queryset = DevelopmentApplication.objects.all()
    serializer_class = DevelopmentApplicationSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        current_stage = self.request.query_params.get('stage', None)
        application_status = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if current_stage:
            queryset = queryset.filter(current_stage=current_stage)
        if application_status:
            queryset = queryset.filter(application_status=application_status)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批通过"""
        application = self.get_object()
        application.application_status = '已通过'
        
        stages = ['入党申请', '积极分子', '发展对象', '预备党员', '正式党员']
        current_index = stages.index(application.current_stage)
        
        application.save()
        return Response({'status': '审批已通过', 'current_stage': application.current_stage})
    
    @action(detail=True, methods=['post'])
    def advance_stage(self, request, pk=None):
        """推进到下一阶段"""
        application = self.get_object()
        
        stages = ['入党申请', '积极分子', '发展对象', '预备党员', '正式党员']
        current_index = stages.index(application.current_stage)
        
        if application.current_stage == '入党申请':
            Activist.objects.create(
                name=application.name,
                gender=application.gender,
                ethnicity=application.ethnicity,
                birth_date=application.birth_date,
                education=application.education,
                application_date=application.application_date,
                organization=application.organization,
                phone=application.phone,
                cultivator='',
                status='培养中',
                student_id=application.student_id,
                grade=application.grade,
                department=application.department
            )
            application.application_approved_date = timezone.now().date()
            
        elif application.current_stage == '积极分子':
            DevelopingMember.objects.create(
                name=application.name,
                gender=application.gender,
                ethnicity=application.ethnicity,
                birth_date=application.birth_date,
                education=application.education,
                determined_date=timezone.now().date(),
                organization=application.organization,
                phone=application.phone,
                cultivator='',
                status='考察中',
                student_id=application.student_id,
                grade=application.grade,
                department=application.department
            )
            application.activist_approved_date = timezone.now().date()
            
        elif application.current_stage == '发展对象':
            ProbationaryMember.objects.create(
                name=application.name,
                gender=application.gender,
                ethnicity=application.ethnicity,
                birth_date=application.birth_date,
                education=application.education,
                join_date=timezone.now().date(),
                organization=application.organization,
                phone=application.phone,
                introducer='',
                approval_status='待审批',
                student_id=application.student_id,
                grade=application.grade,
                department=application.department
            )
            application.developing_approved_date = timezone.now().date()
            
        elif application.current_stage == '预备党员':
            PartyMember.objects.create(
                name=application.name,
                gender=application.gender,
                ethnicity=application.ethnicity,
                birth_date=application.birth_date,
                education=application.education,
                join_date=application.probationary_date or timezone.now().date(),
                regular_date=timezone.now().date(),
                organization=application.organization,
                phone=application.phone,
                introducer='',
                status='正常',
                student_id=application.student_id,
                grade=application.grade,
                department=application.department
            )
            application.regular_approved_date = timezone.now().date()
            
        # 进入下一阶段
        if current_index < len(stages) - 1:
            application.current_stage = stages[current_index + 1]
            application.application_status = '待审批'
        else:
            application.application_status = '已完成'
        
        application.save()
        return Response({'status': '已推进到下一阶段', 'current_stage': application.current_stage})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """审批拒绝"""
        application = self.get_object()
        application.application_status = '已拒绝'
        application.save()
        return Response({'status': '审批已拒绝'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计数据"""
        total = DevelopmentApplication.objects.count()
        pending = DevelopmentApplication.objects.filter(application_status='待审批').count()
        approved = DevelopmentApplication.objects.filter(application_status='已通过').count()
        rejected = DevelopmentApplication.objects.filter(application_status='已拒绝').count()
        
        return Response({
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected
        })


class ApprovalRecordViewSet(viewsets.ModelViewSet):
    """
    审批记录管理API
    """
    queryset = ApprovalRecord.objects.all()
    serializer_class = ApprovalRecordSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        application_id = self.request.query_params.get('application_id', None)
        
        if application_id:
            queryset = queryset.filter(application_id=application_id)
        
        return queryset
