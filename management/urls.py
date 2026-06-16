from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'menus', views.MenuViewSet, basename='menu')
router.register(r'submenus', views.SubMenuViewSet, basename='submenu')
router.register(r'members', views.MemberViewSet, basename='member')
router.register(r'activities', views.ActivityViewSet, basename='activity')
router.register(r'materials', views.MaterialViewSet, basename='material')
router.register(r'material-borrows', views.MaterialBorrowViewSet, basename='material-borrow')
router.register(r'league-members', views.LeagueMemberViewSet, basename='league-member')
router.register(r'qingma-classes', views.QingmaClassViewSet, basename='qingma-class')
router.register(r'qingma-students', views.QingmaStudentViewSet, basename='qingma-student')
router.register(r'qingma-courses', views.QingmaCourseViewSet, basename='qingma-course')
router.register(r'league-branches', views.LeagueBranchViewSet, basename='league-branch')
router.register(r'fee-records', views.FeeRecordViewSet, basename='fee-record')
router.register(r'party-members', views.PartyMemberViewSet, basename='party-member')
router.register(r'activists', views.ActivistViewSet, basename='activist')
router.register(r'cultivation-records', views.CultivationRecordViewSet, basename='cultivation-record')
router.register(r'developing-members', views.DevelopingMemberViewSet, basename='developing-member')
router.register(r'inspection-records', views.InspectionRecordViewSet, basename='inspection-record')
router.register(r'probationary-members', views.ProbationaryMemberViewSet, basename='probationary-member')
router.register(r'development-applications', views.DevelopmentApplicationViewSet, basename='development-application')
router.register(r'approval-records', views.ApprovalRecordViewSet, basename='approval-record')
router.register(r'roles', views.RoleViewSet, basename='role')
router.register(r'user-accounts', views.UserAccountViewSet, basename='user-account')
router.register(r'login-logs', views.LoginLogViewSet, basename='login-log')
router.register(r'permission-change-logs', views.PermissionChangeLogViewSet, basename='permission-change-log')
router.register(r'data-dictionaries', views.DataDictionaryViewSet, basename='data-dictionary')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('user-info/', views.get_user_info, name='user-info'),
]