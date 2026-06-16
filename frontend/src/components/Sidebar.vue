<script setup>import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { hasModulePermission } from '../utils/permission';
const emit = defineEmits(['collapse-change']);
const router = useRouter();
const route = useRoute();
const collapsed = ref(false);
const menus = ref([]);
const expandedGroups = ref({});
const iconMap = {
 Home: '🏠',
 Users: '👥',
 Calendar: '📅',
 Package: '📦',
 Flag: '⭐',
 Heart: '♥',
 Lock: '🔐',
 default: '📁'
};
const getIcon = (iconName) => {
 return iconMap[iconName] || iconMap.default;
};
const fetchMenus = async () => {
 try {
 const token = localStorage.getItem('token');
 const response = await fetch('/api/menus/tree/', {
 headers: {
 'Authorization': `Bearer ${token}`
 }
 });
 if (response.ok) {
 const data = await response.json();
 menus.value = filterMenusByPermission(data.data || data);
 }
 }
 catch (error) {
 console.error('获取菜单失败:', error);
 }
};
const filterMenusByPermission = (menuList) => {
 return menuList.filter(menu => {
 if (menu.path && menu.path !== '/') {
 return hasModulePermission(getModuleFromPath(menu.path));
 }
 
 if (menu.submenus && menu.submenus.length > 0) {
 menu.submenus = menu.submenus.filter(submenu => {
 return hasModulePermission(getModuleFromPath(submenu.path));
 });
 return menu.submenus.length > 0;
 }
 
 return true;
 });
};
const getModuleFromPath = (path) => {
 const pathMap = {
 '/members': 'member',
 '/activities': 'activity',
 '/materials': 'material',
 '/materials/borrows': 'material',
 '/league': 'league',
 '/party': 'party',
 '/permission/roles': 'role',
 '/permission/permissions': 'role',
 '/permission/user-roles': 'user',
 '/permission/audit': 'log',
 '/permission/change-logs': 'log'
 };

 for (const [key, value] of Object.entries(pathMap)) {
 if (path.startsWith(key)) {
 return value;
 }
 }

 return 'member';
};
const toggleSidebar = () => {
 collapsed.value = !collapsed.value;
 emit('collapse-change', collapsed.value);
};
const toggleGroup = (menuId) => {
 expandedGroups.value[menuId] = !expandedGroups.value[menuId];
};
const isExpanded = (menuId) => {
 return expandedGroups.value[menuId];
};
const isActive = (path) => {
 return route.path === path;
};
const hasActiveChild = (submenus) => {
 return submenus.some(item => route.path === item.path);
};
const navigate = (path) => {
 router.push(path);
};
const isSingleMenu = (menu) => {
 return !menu.submenus || menu.submenus.length === 0;
};
onMounted(() => {
 fetchMenus();
});
</script>

<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div class="logo" @click="toggleSidebar">
        <span class="logo-icon">🎓</span>
        <span v-if="!collapsed" class="logo-text">学生会</span>
      </div>
    </div>
    
    <nav class="sidebar-nav">
      <ul class="nav-menu">
        <li v-for="menu in menus" :key="menu.id" class="nav-item">
          <!-- 无子菜单的菜单项 -->
          <button 
            v-if="isSingleMenu(menu)"
            class="nav-link" 
            :class="{ active: isActive(menu.path) }"
            @click="navigate(menu.path)"
          >
            <span class="nav-icon">{{ getIcon(menu.icon) }}</span>
            <span v-if="!collapsed" class="nav-text">{{ menu.name }}</span>
          </button>
          
          <!-- 有子菜单的菜单组 -->
          <template v-else>
            <button 
              class="nav-link group-header" 
              :class="{ active: hasActiveChild(menu.submenus), expanded: isExpanded(menu.id) }"
              @click="toggleGroup(menu.id)"
            >
              <span class="nav-icon">{{ getIcon(menu.icon) }}</span>
              <span v-if="!collapsed" class="nav-text">{{ menu.name }}</span>
              <span v-if="!collapsed" class="expand-icon">{{ isExpanded(menu.id) ? '▾' : '▸' }}</span>
            </button>
            <ul v-if="isExpanded(menu.id)" class="submenu">
              <li v-for="sub in menu.submenus" :key="sub.path">
                <button 
                  class="submenu-link"
                  :class="{ active: isActive(sub.path) }"
                  @click="navigate(sub.path)"
                >
                  <span v-if="!collapsed" class="submenu-text">{{ sub.name }}</span>
                  <span v-else class="submenu-icon">•</span>
                </button>
              </li>
            </ul>
          </template>
        </li>
      </ul>
    </nav>
    
    <div class="sidebar-footer">
      <button class="collapse-btn" @click="toggleSidebar">
        {{ collapsed ? '→' : '←' }}
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  background: #ffffff;
  color: #333333;
  position: fixed;
  left: 0;
  top: 0;
  transition: width 0.2s ease;
  overflow: hidden;
  box-shadow: 1px 0 0 rgba(0, 0, 0, 0.06);
  border-right: 1px solid #e8e8e8;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.logo {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 12px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  font-family: 'Microsoft YaHei', sans-serif;
  color: #1a1a1a;
}

.sidebar-nav {
  padding: 16px 12px;
}

.nav-menu {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  margin: 4px 0;
}

.nav-link {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 14px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #555555;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
  gap: 12px;
  font-size: 14px;
}

.nav-link:hover {
  background: #f5f5f5;
  color: #1a1a1a;
}

.nav-link.active {
  background: #e8f4ff;
  color: #1890ff;
  font-weight: 500;
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.nav-text {
  font-size: 14px;
  font-family: 'Microsoft YaHei', sans-serif;
}

.expand-icon {
  margin-left: auto;
  font-size: 10px;
  color: #999999;
}

.nav-group {
  margin: 4px 0;
}

.group-header {
  justify-content: space-between;
}

.group-header.expanded {
  background: #fafafa;
}

.submenu {
  list-style: none;
  padding: 4px 0 4px 12px;
  margin: 0;
}

.submenu li {
  padding: 0;
}

.submenu-link {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 14px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #666666;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
  font-size: 13px;
}

.submenu-link:hover {
  background: #f5f5f5;
  color: #333333;
}

.submenu-link.active {
  background: #e8f4ff;
  color: #1890ff;
  font-weight: 500;
}

.submenu-text {
  font-size: 13px;
  font-family: 'Microsoft YaHei', sans-serif;
}

.submenu-icon {
  font-size: 14px;
  color: #999999;
}

.sidebar-footer {
  position: absolute;
  bottom: 20px;
  width: 100%;
  display: flex;
  justify-content: center;
}

.collapse-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  background: #ffffff;
  color: #666666;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 14px;
  line-height: 1;
}

.collapse-btn:hover {
  background: #f5f5f5;
  color: #333333;
}
</style>