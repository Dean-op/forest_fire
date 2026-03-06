<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>森林火灾预警系统</h2>
          <span class="subtitle">AI 智能监控平台</span>
        </div>
      </template>
      
      <el-form :model="loginForm" :rules="rules" ref="formRef" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="User" />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock" 
            show-password />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading">
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
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const fill = (uname) => {
  loginForm.username = uname
  loginForm.password = '123456'
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.login(loginForm.username, loginForm.password)
        ElMessage.success('登录成功')
        router.push('/')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '登录失败，请检查账号密码')
      } finally {
        loading.value = false
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

.login-btn {
  width: 100%;
  font-size: 16px;
  padding: 12px;
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
