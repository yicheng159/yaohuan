<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import TopHeader from './components/TopHeader.vue'

const route = useRoute()
const sidebarCollapsed = ref(false)

const handleCollapseChange = (collapsed) => {
  sidebarCollapsed.value = collapsed
}

const isLoginPage = () => {
  return route.path === '/login'
}
</script>

<template>
  <div v-if="isLoginPage()">
    <router-view />
  </div>
  <div v-else class="app-container" :class="{ collapsed: sidebarCollapsed }">
    <Sidebar @collapse-change="handleCollapseChange" />
    <TopHeader :class="{ collapsed: sidebarCollapsed }" />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
}

.app-container {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: 220px;
  margin-top: 60px;
  min-height: calc(100vh - 60px);
  transition: margin-left 0.3s ease;
}

.app-container.collapsed .main-content {
  margin-left: 64px;
}
</style>