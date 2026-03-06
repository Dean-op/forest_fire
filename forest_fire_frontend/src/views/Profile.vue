<template>
  <el-card shadow="hover">
    <h2>个人中心</h2>
    <el-descriptions border :column="1">
      <el-descriptions-item label="用户名">{{ userStore.user?.username }}</el-descriptions-item>
      <el-descriptions-item label="角色">
        <el-tag :type="roleType">{{ roleName }}</el-tag>
      </el-descriptions-item>
    </el-descriptions>
    
    <div style="margin-top: 20px;">
      <h3>修改密码</h3>
      <el-form :model="pwForm" label-width="100px" style="max-width: 400px; margin-top: 15px;">
        <el-form-item label="原密码">
          <el-input v-model="pwForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="updatePassword" :loading="loading">确认修改</el-button>
        </el-form-item>
      </el-form>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useUserStore } from '../stores/user'
import api from '../api'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)

const roleMap = {
  'operator': '操作员',
  'supervisor': '主管',
  'admin': '系统管理员'
}

const roleTypeMap = {
  'operator': 'warning',
  'supervisor': 'success',
  'admin': 'danger'
}

const roleName = computed(() => roleMap[userStore.role] || '未知')
const roleType = computed(() => roleTypeMap[userStore.role] || 'info')

const pwForm = reactive({
  old_password: '',
  new_password: ''
})

const updatePassword = async () => {
  if (!pwForm.old_password || !pwForm.new_password) {
    ElMessage.warning('请填写完整密码')
    return
  }
  
  loading.value = true
  try {
    await api.put('/auth/password', pwForm)
    ElMessage.success('密码修改成功，请妥善保管')
    pwForm.old_password = ''
    pwForm.new_password = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改失败，可能是原密码错误')
  } finally {
    loading.value = false
  }
}
</script>
