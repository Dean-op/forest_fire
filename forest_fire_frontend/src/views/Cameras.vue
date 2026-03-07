<template>
  <div class="cameras-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>📷 视频源 / 设备管理</h2>
          <el-button type="primary" @click="openAdd">
            <el-icon><Plus /></el-icon> 新增设备
          </el-button>
        </div>
      </template>

      <el-table :data="cameras" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="设备名称" width="160" />
        <el-table-column prop="rtsp_url" label="RTSP 地址" min-width="220" show-overflow-tooltip />
        <el-table-column prop="location" label="安装位置" width="160" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="290" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 5px; flex-wrap: nowrap;">
              <el-button
                size="small"
                :type="row.status === 'online' ? 'warning' : 'success'"
                @click="toggleStatus(row)"
              >
                {{ row.status === 'online' ? '置为离线' : '置为在线' }}
              </el-button>
              <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="info" @click="viewLogs(row)">日志</el-button>
              <el-popconfirm title="确认删除此设备?" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="formVisible" :title="isEdit ? '编辑设备' : '新增设备'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="设备名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="RTSP 地址"><el-input v-model="form.rtsp_url" placeholder="rtsp://..." /></el-form-item>
        <el-form-item label="安装位置"><el-input v-model="form.location" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 设备日志对话框 -->
    <el-dialog v-model="logVisible" :title="`设备日志：${logCameraName}`" width="500px">
      <el-timeline>
        <el-timeline-item
          v-for="log in cameraLogs"
          :key="log.id"
          :timestamp="new Date(log.timestamp).toLocaleString('zh-CN')"
          placement="top"
          :type="log.event.includes('掉线') ? 'danger' : 'success'"
        >
          {{ log.event }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!cameraLogs.length" description="暂无日志" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const cameras = ref([])
const loading = ref(false)
const formVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const logVisible = ref(false)
const logCameraName = ref('')
const cameraLogs = ref([])

const form = reactive({ name: '', rtsp_url: '', location: '' })

const fetchCameras = async () => {
  loading.value = true
  try {
    cameras.value = await api.get('/supervisor/cameras')
  } catch { ElMessage.error('获取设备列表失败') }
  finally { loading.value = false }
}

const openAdd = () => {
  isEdit.value = false; editId.value = null
  Object.assign(form, { name: '', rtsp_url: '', location: '' })
  formVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true; editId.value = row.id
  Object.assign(form, { name: row.name, rtsp_url: row.rtsp_url, location: row.location })
  formVisible.value = true
}

const toggleStatus = async (row) => {
  const nextStatus = row.status === 'online' ? 'offline' : 'online'
  try {
    await api.put(`/supervisor/cameras/${row.id}`, { status: nextStatus })
    row.status = nextStatus
    ElMessage.success(`设备 ${row.name} 已切换为${nextStatus === 'online' ? '在线' : '离线'}`)
  } catch {
    ElMessage.error('状态切换失败')
  }
}

const submitForm = async () => {
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/supervisor/cameras/${editId.value}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/supervisor/cameras', form)
      ElMessage.success('新增成功')
    }
    formVisible.value = false
    fetchCameras()
  } catch { ElMessage.error('操作失败') }
  finally { submitting.value = false }
}

const handleDelete = async (id) => {
  try {
    await api.delete(`/supervisor/cameras/${id}`)
    ElMessage.success('已删除')
    fetchCameras()
  } catch { ElMessage.error('删除失败') }
}

const viewLogs = async (row) => {
  logCameraName.value = row.name
  try {
    cameraLogs.value = await api.get(`/supervisor/cameras/${row.id}/logs`)
  } catch { cameraLogs.value = [] }
  logVisible.value = true
}

onMounted(fetchCameras)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header h2 { margin: 0; }
</style>
