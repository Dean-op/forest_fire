<template>
  <div>
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>👤 用户权限管理</h2>
          <el-button type="primary" @click="openAdd"><el-icon><Plus /></el-icon> 新增用户</el-button>
        </div>
      </template>
      <el-table :data="users" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="{admin:'danger',supervisor:'success',operator:'warning'}[row.role]">{{ {admin:'管理员',supervisor:'主管',operator:'操作员'}[row.role] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-select v-model="row.role" size="small" style="width:90px;margin-right:8px;" @change="updateUser(row.id, { role: row.role })">
              <el-option label="管理员" value="admin" /><el-option label="主管" value="supervisor" /><el-option label="操作员" value="operator" />
            </el-select>
            <el-switch v-model="row.is_active" @change="updateUser(row.id, { is_active: row.is_active })" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-dialog v-model="addVisible" title="新增用户" width="400px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="addForm.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="addForm.password" type="password" show-password /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="addForm.role"><el-option label="操作员" value="operator" /><el-option label="主管" value="supervisor" /><el-option label="管理员" value="admin" /></el-select>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="addVisible=false">取消</el-button><el-button type="primary" @click="submitAdd" :loading="submitting">创建</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
const users = ref([]); const loading = ref(false); const addVisible = ref(false); const submitting = ref(false)
const addForm = reactive({ username: '', password: '', role: 'operator' })
const fetchUsers = async () => { loading.value = true; try { users.value = await api.get('/admin/users') } catch { ElMessage.error('获取用户列表失败') } finally { loading.value = false } }
const openAdd = () => { Object.assign(addForm, { username: '', password: '', role: 'operator' }); addVisible.value = true }
const submitAdd = async () => { submitting.value = true; try { await api.post('/admin/users', addForm); ElMessage.success('创建成功'); addVisible.value = false; fetchUsers() } catch(e) { ElMessage.error(e.response?.data?.detail || '创建失败') } finally { submitting.value = false } }
const updateUser = async (id, data) => { try { await api.put(`/admin/users/${id}`, data); ElMessage.success('已更新') } catch { ElMessage.error('更新失败'); fetchUsers() } }
onMounted(fetchUsers)
</script>
<style scoped>.card-header{display:flex;justify-content:space-between;align-items:center;}.card-header h2{margin:0;}</style>
