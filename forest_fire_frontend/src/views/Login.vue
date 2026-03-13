<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>森林火灾预警系统</h2>
          <span class="subtitle">AI 智能监控平台</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" @keyup.enter="handleLogin">
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="用户名"
                :prefix-icon="User"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" class="primary-btn" @click="handleLogin" :loading="loginLoading">
                登录系统
              </el-button>
            </el-form-item>
          </el-form>

          <div class="test-accounts">
            <p>测试账号(密码皆为123456):</p>
            <el-tag size="small" @click="fill('admin')">admin</el-tag>
            <el-tag size="small" type="success" @click="fill('manager')">manager</el-tag>
            <el-tag size="small" type="warning" @click="fill('operator')">operator</el-tag>
          </div>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" @keyup.enter="handleRegister">
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入 3-32 位用户名"
                :prefix-icon="User"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入不少于 6 位密码"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                :prefix-icon="CircleCheck"
                show-password
              />
            </el-form-item>

            <div class="register-tip">自助注册账号默认创建为“操作员”角色。</div>

            <el-form-item>
              <el-button type="primary" class="primary-btn" @click="handleRegister" :loading="registerLoading">
                注册账号
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock, CircleCheck } from '@element-plus/icons-vue'

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
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}

.login-card {
  width: 400px;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
  display: inline-block;
}

.primary-btn {
  width: 100%;
  font-size: 16px;
  padding: 12px;
}

.register-tip {
  margin: -4px 0 16px;
  font-size: 12px;
  color: #909399;
}

.test-accounts {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: #909399;
}

.test-accounts .el-tag {
  margin: 0 4px;
  cursor: pointer;
}
</style>
