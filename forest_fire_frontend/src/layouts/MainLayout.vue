<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo">
        <el-icon :size="24" color="#fff"><Monitor /></el-icon>
        <span v-show="!isCollapse" class="title">{{ systemName }}</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        :collapse="isCollapse"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
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
        
        <el-menu-item index="/history" v-if="hasRole(['operator', 'admin'])">
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
    
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="toggle-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse"/>
            <Expand v-else/>
          </el-icon>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="username">{{ userStore.user?.username }} ({{ roleName }})</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
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
import { ElMessage } from 'element-plus'
import api from '../api'
import { 
  Monitor, DataBoard, Bell, List, DataLine, 
  Camera, Fold, Expand, ArrowDown, UserFilled, Notebook,
  ChatDotSquare, Setting 
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

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
    const configs = await api.get('/admin/configs')
    const target = configs.find(item => item.key === 'system_name')
    const name = (target?.value || '').trim()
    if (name) {
      systemName.value = name
      localStorage.setItem(SYSTEM_NAME_STORAGE_KEY, name)
    }
  } catch {
    // Ignore fetch failures and keep local fallback.
  }
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
}

.aside {
  background-color: #304156;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  background-color: #2b3643;
  overflow: hidden;
}

.logo .title {
  margin-left: 10px;
  white-space: nowrap;
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 20px;
}

.toggle-btn {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
  transition: color 0.3s;
}

.toggle-btn:hover {
  color: #409EFF;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0 10px;
}

.username {
  margin-left: 8px;
  font-size: 14px;
  color: #606266;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

/* 路由过渡动画 */
.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
