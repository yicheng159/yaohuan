import { createRouter, createWebHistory } from 'vue-router'
import { authMiddleware } from '../middleware/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue')
  },
  {
    path: '/members',
    name: 'Members',
    component: () => import('../views/Members.vue')
  },
  {
    path: '/activities',
    name: 'Activities',
    component: () => import('../views/Activities.vue')
  },
  // 物资管理
  {
    path: '/materials',
    name: 'Materials',
    component: () => import('../views/Materials.vue')
  },
  {
    path: '/materials/borrows',
    name: 'MaterialBorrows',
    component: () => import('../views/materials/MaterialBorrowManagement.vue')
  },
  // 团务管理
  {
    path: '/league/members',
    name: 'LeagueMembers',
    component: () => import('../views/league/MemberManagement.vue')
  },
  {
    path: '/league/qingma',
    name: 'Qingma',
    component: () => import('../views/league/QingmaManagement.vue')
  },
  {
    path: '/league/qingma-students',
    name: 'QingmaStudents',
    component: () => import('../views/league/QingmaStudentManagement.vue')
  },
  {
    path: '/league/qingma-courses',
    name: 'QingmaCourses',
    component: () => import('../views/league/QingmaCourseManagement.vue')
  },
  {
    path: '/league/branches',
    name: 'LeagueBranches',
    component: () => import('../views/league/LeagueBranchManagement.vue')
  },
  {
    path: '/league/fees',
    name: 'LeagueFees',
    component: () => import('../views/league/FeeManagement.vue')
  },
  // 党务管理
  {
    path: '/party/members',
    name: 'PartyMembers',
    component: () => import('../views/party/MemberManagement.vue')
  },
  {
    path: '/party/activists',
    name: 'Activists',
    component: () => import('../views/party/ActivistManagement.vue')
  },
  {
    path: '/party/cultivation',
    name: 'CultivationRecords',
    component: () => import('../views/party/CultivationRecordManagement.vue')
  },
  {
    path: '/party/developing',
    name: 'Developing',
    component: () => import('../views/party/DevelopingManagement.vue')
  },
  {
    path: '/party/inspection',
    name: 'InspectionRecords',
    component: () => import('../views/party/InspectionRecordManagement.vue')
  },
  {
    path: '/party/probationary',
    name: 'Probationary',
    component: () => import('../views/party/ProbationaryManagement.vue')
  },
  {
    path: '/party/full',
    name: 'FullMembers',
    component: () => import('../views/party/FullMemberManagement.vue')
  },
  {
    path: '/party/development',
    name: 'DevelopmentApplication',
    component: () => import('../views/party/DevelopmentApplicationManagement.vue')
  },
  // 权限管理
  {
    path: '/permission/roles',
    name: 'RoleManagement',
    component: () => import('../views/permission/RoleManagement.vue')
  },
  {
    path: '/permission/permissions',
    name: 'PermissionManagement',
    component: () => import('../views/permission/PermissionManagement.vue')
  },
  {
    path: '/permission/user-roles',
    name: 'UserRole',
    component: () => import('../views/permission/UserRole.vue')
  },
  {
    path: '/permission/audit',
    name: 'AuditLog',
    component: () => import('../views/permission/AuditLog.vue')
  },
  {
    path: '/permission/change-logs',
    name: 'PermissionChangeLog',
    component: () => import('../views/permission/PermissionChangeLog.vue')
  },
  {
    path: '/permission/dictionary',
    name: 'DataDictionary',
    component: () => import('../views/permission/DataDictionary.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach(authMiddleware)

export default router
