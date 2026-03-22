<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo">
        <el-icon :size="24" color="var(--el-color-primary)" class="logo-icon"><Monitor /></el-icon>
        <transition name="fade">
          <span v-show="!isCollapse" class="title">{{ systemName }}</span>
        </transition>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical custom-menu"
        :collapse="isCollapse"
        router
      >
        <el-menu-item index="/stats">
          <el-icon><DataLine /></el-icon>
          <template #title>统计看板</template>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>监控大屏</template>
        </el-menu-item>
        <el-menu-item index="/tasks" v-if="hasRole(['operator', 'admin'])">
          <el-icon><Bell /></el-icon>
          <template #title>我的任务</template>
        </el-menu-item>
        <el-menu-item index="/history" v-if="hasRole(['operator', 'supervisor', 'admin'])">
          <el-icon><List /></el-icon>
          <template #title>历史回溯</template>
        </el-menu-item>
        <el-menu-item index="/cameras" v-if="hasRole(['supervisor', 'admin'])">
          <el-icon><Camera /></el-icon>
          <template #title>设备管理</template>
        </el-menu-item>
        <el-menu-item index="/shift-logs" v-if="hasRole(['supervisor', 'admin'])">
          <el-icon><Notebook /></el-icon>
          <template #title>交接班日志</template>
        </el-menu-item>
        <el-menu-item index="/notices">
          <el-icon><ChatDotSquare /></el-icon>
          <template #title>公告 / SOP</template>
        </el-menu-item>
        <el-sub-menu index="admin-group" v-if="hasRole(['admin'])">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/admin/users">用户管理</el-menu-item>
          <el-menu-item index="/admin/config">系统参数</el-menu-item>
          <el-menu-item index="/admin/announcements">公告管理</el-menu-item>
          <el-menu-item index="/admin/logs">系统日志</el-menu-item>
          <el-menu-item index="/admin/backup">数据库备份</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    
    <el-container class="main-container-wrapper">
      <el-header class="header">
        <div class="header-left">
          <el-icon class="toggle-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse"/>
            <Expand v-else/>
          </el-icon>
        </div>
        
        <div class="header-right">
          <!-- Theme Switcher -->
          <div class="theme-switch" @click="themeStore.toggleTheme" title="切换主题">
            <el-icon v-if="themeStore.isDark"><Moon /></el-icon>
            <el-icon v-else><Sunny /></el-icon>
          </div>

          <el-dropdown @command="handleCommand" trigger="click">
            <span class="user-dropdown">
              <el-avatar :size="32" icon="UserFilled" class="user-avatar" />
              <div class="user-info">
                <span class="username">{{ userStore.user?.username }}</span>
                <span class="role-badge">{{ roleName }}</span>
              </div>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu class="custom-dropdown">
                <el-dropdown-item command="profile">
                  <el-icon><UserFilled /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" class="logout-item">
                  <el-icon><Setting /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useThemeStore } from '../stores/theme'
import { ElMessage } from 'element-plus'
import api from '../api'
import { 
  Monitor, DataBoard, Bell, List, DataLine, 
  Camera, Fold, Expand, ArrowDown, UserFilled, Notebook,
  ChatDotSquare, Setting, Moon, Sunny 
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()

const SYSTEM_NAME_STORAGE_KEY = 'system_name'
const DEFAULT_SYSTEM_NAME = '防火预警系统'

const isCollapse = ref(false)
const systemName = ref(localStorage.getItem(SYSTEM_NAME_STORAGE_KEY) || DEFAULT_SYSTEM_NAME)
const activeMenu = computed(() => route.path)

const roleMap = {
  'operator': '操作员',
  'supervisor': '主管',
  'admin': '系统管理员'
}

const roleName = computed(() => roleMap[userStore.role] || '用户')
const hasRole = (roles) => roles.includes(userStore.role)

const syncSystemNameFromStorage = (event) => {
  const eventName = event?.detail?.name
  const localName = localStorage.getItem(SYSTEM_NAME_STORAGE_KEY)
  const nextName = (eventName || localName || '').trim()
  systemName.value = nextName || DEFAULT_SYSTEM_NAME
}

const fetchSystemName = async () => {
  try {
    const data = await api.get('/admin/public/system-name')
    const name = (data?.system_name || '').trim()
    if (name) {
      systemName.value = name
      localStorage.setItem(SYSTEM_NAME_STORAGE_KEY, name)
    }
  } catch {}
}

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

onMounted(() => {
  window.addEventListener('system-name-updated', syncSystemNameFromStorage)
  fetchSystemName()
})

onUnmounted(() => {
  window.removeEventListener('system-name-updated', syncSystemNameFromStorage)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--el-bg-color-page);
}

.aside {
  background-color: var(--el-bg-color); /* Light mode base */
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 12px 0 rgba(0,0,0,0.06);
  z-index: 10;
  border-right: 1px solid var(--el-border-color-light);
}

/* Force dark mode aside menu color specifically if in dark mode */
html.dark .aside { 
  background-color: #0b1120;
  box-shadow: 2px 0 12px 0 rgba(0,0,0,0.5); 
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-primary);
  font-size: 18px;
  font-weight: 600;
  overflow: hidden;
  letter-spacing: 1px;
  border-bottom: 1px solid var(--el-border-color-light);
}
html.dark .logo { background-color: #0b1120; }

.logo-icon {
  filter: drop-shadow(0 0 5px rgba(59,130,246,0.6));
}

.logo .title {
  margin-left: 10px;
  white-space: nowrap;
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
}

/* Custom Menu Styling */
:deep(.custom-menu) {
  --el-menu-bg-color: var(--el-bg-color);
  --el-menu-hover-bg-color: var(--el-color-primary-light-9);
}
html.dark :deep(.custom-menu) {
  --el-menu-bg-color: #0b1120;
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.05);
}

:deep(.custom-menu .el-menu-item) {
  margin: 4px 8px;
  border-radius: 6px;
  height: 44px;
  line-height: 44px;
}
:deep(.custom-menu .el-sub-menu__title) {
  margin: 4px 8px;
  border-radius: 6px;
  height: 44px;
  line-height: 44px;
}

:deep(.custom-menu .el-menu-item.is-active) {
  background: linear-gradient(90deg, var(--el-color-primary) 0%, var(--el-color-primary-dark-2) 100%) !important;
  box-shadow: 0 4px 10px rgba(37,99,235,0.3);
  color: #ffffff !important;
  font-weight: 500;
}
:deep(.custom-menu .el-menu-item.is-active .el-icon) {
  color: #ffffff !important;
}

.main-container-wrapper {
  display: flex;
  flex-direction: column;
}

.header {
  background-color: var(--el-bg-color);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 20px;
  z-index: 5;
}
html.dark .header { background-color: transparent; }

.header-right {
  display: flex;
  align-items: center;
}

.toggle-btn {
  font-size: 22px;
  cursor: pointer;
  color: var(--el-text-color-regular);
  transition: all 0.3s ease;
}
.toggle-btn:hover {
  color: var(--el-color-primary);
  transform: scale(1.1);
}
html.dark .toggle-btn:hover { filter: drop-shadow(0 0 8px rgba(59,130,246,0.5)); }

.theme-switch {
  margin-right: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  transition: all 0.3s;
}
.theme-switch:hover {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 20px;
  transition: background 0.3s ease;
}
.user-dropdown:hover {
  background-color: var(--el-fill-color-light);
}

.user-avatar {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

.user-info {
  display: flex;
  flex-direction: column;
  margin-left: 10px;
  justify-content: center;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.role-badge {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 2px;
  line-height: 1.2;
}

.el-icon--right {
  margin-left: 8px;
  color: var(--el-text-color-regular);
}

.main-content {
  background-color: var(--el-bg-color-page);
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}
html.dark .main-content {
  background-color: transparent;
  background-image: radial-gradient(circle at 50% 0%, rgba(30, 58, 138, 0.1), transparent 50%);
}

.fade-transform-leave-active, .fade-transform-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.fade-transform-enter-from { opacity: 0; transform: translateX(-20px); }
.fade-transform-leave-to { opacity: 0; transform: translateX(20px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
