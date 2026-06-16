import { checkRoutePermission, getPermissions, hasModulePermission } from '../utils/permission';

export const authMiddleware = async (to, from, next) => {
  const token = localStorage.getItem('token');
  
  if (to.path === '/login') {
    if (token) {
      next('/');
    } else {
      next();
    }
    return;
  }
  
  if (!token) {
    next('/login');
    return;
  }
  
  const permissions = getPermissions();
  if (permissions.length === 0) {
    try {
      const response = await fetch('/api/user-info/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      if (data.code === 200) {
        localStorage.setItem('permissions', JSON.stringify(data.data.permissions || []));
        localStorage.setItem('roleName', data.data.role_name || '');
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
    }
  }
  
  if (!checkRoutePermission(to.path)) {
    next('/');
    return;
  }
  
  next();
};

export default authMiddleware;