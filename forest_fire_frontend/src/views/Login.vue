<template>
  <div class="login-container">
    <!-- Animated background elements (sparks/embers effect) -->
    <div class="firefly"></div>
    <div class="firefly"></div>
    <div class="firefly"></div>
    <div class="firefly"></div>
    <div class="firefly"></div>

    <div class="login-box">
      <div class="login-header">
        <el-icon class="header-icon"><Monitor /></el-icon>
        <h2>森林火灾预警系统</h2>
        <span class="subtitle">AI 智能监控平台</span>
      </div>

      <el-tabs v-model="activeTab" stretch class="custom-tabs">
        <el-tab-pane label="系统登录" name="login">
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" @keyup.enter="handleLogin" size="large">
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
                class="glass-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                class="glass-input"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" class="primary-btn glass-btn" @click="handleLogin" :loading="loginLoading">
                登录系统
              </el-button>
            </el-form-item>
          </el-form>

          <div class="test-accounts">
            <span>快速体验：</span>
            <el-tag effect="dark" size="small" @click="fill('admin')" class="demo-tag admin-tag">admin</el-tag>
            <el-tag effect="dark" size="small" type="success" @click="fill('manager')" class="demo-tag manager-tag">manager</el-tag>
            <el-tag effect="dark" size="small" type="warning" @click="fill('operator')" class="demo-tag operator-tag">operator</el-tag>
          </div>
        </el-tab-pane>

        <el-tab-pane label="注册账号" name="register">
          <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" @keyup.enter="handleRegister" size="large">
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入 3-32 位用户名"
                :prefix-icon="User"
                class="glass-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入不少于 6 位密码"
                :prefix-icon="Lock"
                show-password
                class="glass-input"
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                :prefix-icon="CircleCheck"
                show-password
                class="glass-input"
              />
            </el-form-item>

            <div class="register-tip"><el-icon><InfoFilled /></el-icon> 自助注册账号默认创建为“操作员”角色。</div>

            <el-form-item>
              <el-button type="primary" class="primary-btn glass-btn" @click="handleRegister" :loading="registerLoading">
                注册账号
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock, CircleCheck, Monitor, InfoFilled } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loginFormRef = ref(null)
const registerFormRef = ref(null)
const loginLoading = ref(false)
const registerLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const validateConfirmPassword = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
    return
  }
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '用户名长度需为 3-32 位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度需为 6-64 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const fill = (uname) => {
  loginForm.username = uname
  loginForm.password = '123456'
  activeTab.value = 'login'
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loginLoading.value = true
      try {
        await userStore.login(loginForm.username, loginForm.password)
        ElMessage.success('登录成功')
        router.push('/')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '登录失败，请检查账号密码')
      } finally {
        loginLoading.value = false
      }
    }
  })
}

const resetRegisterForm = () => {
  registerForm.username = ''
  registerForm.password = ''
  registerForm.confirmPassword = ''
  registerFormRef.value?.clearValidate()
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      registerLoading.value = true
      try {
        await userStore.register(
          registerForm.username,
          registerForm.password,
          registerForm.confirmPassword
        )
        ElMessage.success('注册成功，请使用新账号登录')
        loginForm.username = registerForm.username
        loginForm.password = ''
        resetRegisterForm()
        activeTab.value = 'login'
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '注册失败')
      } finally {
        registerLoading.value = false
      }
    }
  })
}
</script>

<style scoped>
/* Main Container with Dark Tech Gradient and Image/Pattern overlay */
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #0b1120;
  background-image: 
    radial-gradient(circle at 15% 50%, rgba(20, 83, 168, 0.15), transparent 25%),
    radial-gradient(circle at 85% 30%, rgba(220, 38, 38, 0.1), transparent 25%),
    linear-gradient(to bottom right, #0b1120 0%, #0f172a 100%);
  position: relative;
  overflow: hidden;
}

/* Glassmorphism Box */
.login-box {
  width: 440px;
  padding: 40px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 20px rgba(59, 130, 246, 0.1);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  z-index: 10;
  animation: slideUpFade 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUpFade {
  0% {
    opacity: 0;
    transform: translateY(40px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Header Styling */
.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.header-icon {
  font-size: 42px;
  color: #3b82f6;
  margin-bottom: 10px;
  filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.6));
}

.login-header h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  color: #f8fafc;
  letter-spacing: 1px;
}

.subtitle {
  font-size: 14px;
  color: #94a3b8;
  margin-top: 8px;
  display: inline-block;
  letter-spacing: 2px;
}

/* Form Styles Override for Dark Glass Theme */
:deep(.el-tabs__item) {
  color: #94a3b8;
  font-size: 16px;
  transition: all 0.3s;
}

:deep(.el-tabs__item.is-active) {
  color: #ffffff;
  font-weight: 600;
}

:deep(.el-tabs__nav-wrap::after) {
  background-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  background-color: rgba(255, 255, 255, 0.08);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #3b82f6 inset !important;
  background-color: rgba(15, 23, 42, 0.8);
}

:deep(.el-input__inner) {
  color: #f8fafc;
}

:deep(.el-input__prefix-inner), :deep(.el-input__suffix-inner) {
  color: #94a3b8;
}

/* Button Styling */
.primary-btn {
  width: 100%;
  margin-top: 10px;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 1px;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border: none;
  box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39);
  transition: all 0.3s ease;
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.primary-btn:active {
  transform: translateY(0);
}

/* Tip & Accounts Styling */
.register-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: -4px 0 16px;
  font-size: 13px;
  color: #94a3b8;
}

.test-accounts {
  margin-top: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #94a3b8;
}

.demo-tag {
  margin: 0 6px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  transition: all 0.3s ease;
  background-color: rgba(255, 255, 255, 0.05) !important;
  color: #94a3b8 !important;
}

.admin-tag:hover { border-color: #409eff !important; color: #409eff !important; background-color: rgba(64,158,255,0.1) !important; }
.manager-tag:hover { border-color: #67c23a !important; color: #67c23a !important; background-color: rgba(103,194,58,0.1) !important;}
.operator-tag:hover { border-color: #e6a23c !important; color: #e6a23c !important; background-color: rgba(230,162,60,0.1) !important;}

/* Fireflies/Sparks Animation */
.firefly {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #fca5a5;
  border-radius: 50%;
  filter: blur(2px);
  animation: float 10s infinite;
  opacity: 0;
  z-index: 1;
}

.firefly:nth-child(1) { left: 20%; animation-duration: 8s; animation-delay: 0s; }
.firefly:nth-child(2) { left: 60%; animation-duration: 12s; animation-delay: 2s; background: #fbbf24; }
.firefly:nth-child(3) { left: 80%; animation-duration: 9s; animation-delay: 4s; }
.firefly:nth-child(4) { left: 40%; animation-duration: 11s; animation-delay: 1s; background: #60a5fa; }
.firefly:nth-child(5) { left: 10%; animation-duration: 14s; animation-delay: 5s; }

@keyframes float {
  0% {
    transform: translateY(100vh) scale(0);
    opacity: 0;
  }
  20% {
    opacity: 0.8;
  }
  80% {
    opacity: 0.6;
  }
  100% {
    transform: translateY(-20vh) translateX(20px) scale(1.5);
    opacity: 0;
  }
}
</style>
