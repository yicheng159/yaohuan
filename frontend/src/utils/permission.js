export const getPermissions = () => {
  const permissions = localStorage.getItem('permissions');
  return permissions ? JSON.parse(permissions) : [];
};

export const hasPermission = (permission) => {
  const permissions = getPermissions();
  return permissions.includes(permission);
};

export const hasAnyPermission = (permissions) => {
  const userPermissions = getPermissions();
  return permissions.some(p => userPermissions.includes(p));
};

export const hasModulePermission = (module) => {
  const permissions = getPermissions();
  return permissions.some(p => p.startsWith(`${module}:`));
};

export const clearPermissions = () => {
  localStorage.removeItem('permissions');
  localStorage.removeItem('roleName');
};

export const routePermissions = {
  '/members': ['member:view'],
  '/activities': ['activity:view'],
  '/materials': ['material:view'],
  '/materials/borrows': ['material:view'],
  '/league/members': ['league:view'],
  '/league/qingma': ['league:view'],
  '/league/qingma-students': ['league:view'],
  '/league/qingma-courses': ['league:view'],
  '/league/branches': ['league:view'],
  '/league/fees': ['league:view'],
  '/party/members': ['party:view'],
  '/party/activists': ['party:view'],
  '/party/cultivation': ['party:view'],
  '/party/developing': ['party:view'],
  '/party/inspection': ['party:view'],
  '/party/probationary': ['party:view'],
  '/party/full': ['party:view'],
  '/party/development': ['party:view'],
  '/permission/roles': ['role:view'],
  '/permission/permissions': ['role:view'],
  '/permission/user-roles': ['user:view'],
  '/permission/audit': ['log:view']
};

export const checkRoutePermission = (routePath) => {
  const requiredPermissions = routePermissions[routePath];
  if (!requiredPermissions) return true;
  
  return hasAnyPermission(requiredPermissions);
};