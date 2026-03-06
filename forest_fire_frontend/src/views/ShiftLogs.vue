<template>
  <div class="shift-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>📝 交接班日志</h2>
          <el-button type="primary" @click="openAdd">
            <el-icon><Plus /></el-icon> 新增记录
          </el-button>
        </div>
      </template>

      <el-table :data="logs" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="operator" label="值班人员" width="120" />
        <el-table-column prop="shift_time" label="班次时间" width="220" />
        <el-table-column prop="content" label="交接内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="created_at" label="记录时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-popconfirm title="确认删除此记录?" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="formVisible" title="新增交接班记录" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="值班人员"><el-input v-model="form.operator" /></el-form-item>
        <el-form-item label="班次时间"><el-input v-model="form.shift_time" placeholder="如 2026-03-05 08:00 - 16:00" /></el-form-item>
        <el-form-item label="交接内容"><el-input v-model="form.content" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const logs = ref([])
const loading = ref(false)
const formVisible = ref(false)
const submitting = ref(false)
const form = reactive({ operator: '', shift_time: '', content: '' })

const fetchLogs = async () => {
  loading.value = true
  try { logs.value = await api.get('/supervisor/shift-logs') }
  catch { ElMessage.error('获取交接班日志失败') }
  finally { loading.value = false }
}

const openAdd = () => {
  Object.assign(form, { operator: '', shift_time: '', content: '' })
  formVisible.value = true
}

const submitForm = async () => {
  submitting.value = true
  try {
    await api.post('/supervisor/shift-logs', form)
    ElMessage.success('添加成功')
    formVisible.value = false
    fetchLogs()
  } catch { ElMessage.error('添加失败') }
  finally { submitting.value = false }
}

const handleDelete = async (id) => {
  try {
    await api.delete(`/supervisor/shift-logs/${id}`)
    ElMessage.success('已删除')
    fetchLogs()
  } catch { ElMessage.error('删除失败') }
}

onMounted(fetchLogs)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header h2 { margin: 0; }
</style>
