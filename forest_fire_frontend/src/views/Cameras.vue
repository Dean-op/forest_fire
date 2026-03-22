<template>
  <div class="cameras-page">
    <section class="hero-panel">
      <div class="hero-main">
        <p class="hero-kicker">Device Console</p>
        <h2>设备管理</h2>
        <p class="hero-subtitle">统一管理视频源、在线状态与 AI 检测开关。</p>
      </div>
      <div class="hero-metrics">
        <div class="metric-item">
          <div class="metric-label">设备总数</div>
          <div class="metric-value">{{ cameras.length }}</div>
        </div>
        <div class="metric-item success">
          <div class="metric-label">在线设备</div>
          <div class="metric-value">{{ onlineCount }}</div>
        </div>
        <div class="metric-item danger">
          <div class="metric-label">离线设备</div>
          <div class="metric-value">{{ offlineCount }}</div>
        </div>
        <div class="metric-item info">
          <div class="metric-label">AI 已开启</div>
          <div class="metric-value">{{ aiEnabledCount }}</div>
        </div>
      </div>
    </section>

    <el-card class="control-card" shadow="never">
      <div class="control-row">
        <div class="filter-group">
          <el-radio-group v-model="statusFilter" size="large">
            <el-radio-button value="all">全部设备</el-radio-button>
            <el-radio-button value="online">在线</el-radio-button>
            <el-radio-button value="offline">离线</el-radio-button>
            <el-radio-button value="ai_on">AI 已开启</el-radio-button>
          </el-radio-group>
        </div>

        <div class="control-actions">
          <el-input
            v-model="keyword"
            placeholder="搜索设备名或安装位置"
            clearable
            class="search-input"
          />
          <el-button @click="fetchCameras" :loading="loading">刷新</el-button>
          <el-button type="primary" @click="openAdd">
            <el-icon><Plus /></el-icon>
            新增设备
          </el-button>
        </div>
      </div>
    </el-card>

    <div class="camera-grid" v-loading="loading">
      <el-empty v-if="!loading && filteredCameras.length === 0" description="当前条件下没有设备" />

      <article v-for="camera in filteredCameras" :key="camera.id" class="camera-card">
        <header class="card-head">
          <div class="head-main">
            <div class="camera-name">{{ camera.name }}</div>
            <div class="camera-location">{{ camera.location || '未填写安装位置' }}</div>
          </div>
          <el-tag :type="camera.status === 'online' ? 'success' : 'danger'" effect="dark">
            {{ camera.status === 'online' ? '在线' : '离线' }}
          </el-tag>
        </header>

        <div class="camera-body">
          <div class="camera-preview" :class="camera.status">
            <div class="preview-orb"></div>
            <div class="preview-label">{{ camera.status === 'online' ? '视频源可用' : '设备离线' }}</div>
          </div>

          <div class="camera-meta">
            <div class="meta-item">
              <span class="meta-label">Source</span>
              <span class="meta-value mono">{{ camera.rtsp_url || '未配置' }}</span>
            </div>
            <div class="meta-item compact">
              <span class="meta-label">AI 检测</span>
              <el-switch
                v-model="camera.enable_ai"
                inline-prompt
                active-text="开"
                inactive-text="关"
                @change="toggleAI(camera)"
              />
            </div>
          </div>
        </div>

        <footer class="card-actions">
          <el-button
            size="small"
            :type="camera.status === 'online' ? 'warning' : 'success'"
            @click="toggleStatus(camera)"
          >
            {{ camera.status === 'online' ? '设为离线' : '设为在线' }}
          </el-button>
          <el-button size="small" type="primary" plain @click="openEdit(camera)">编辑</el-button>
          <el-button size="small" type="info" plain @click="viewLogs(camera)">日志</el-button>
          <el-popconfirm title="确认删除该设备？" @confirm="handleDelete(camera.id)">
            <template #reference>
              <el-button size="small" type="danger" plain>删除</el-button>
            </template>
          </el-popconfirm>
        </footer>
      </article>
    </div>

    <el-dialog v-model="formVisible" :title="isEdit ? '编辑设备' : '新增设备'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="设备名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="Video Source">
          <el-input v-model="form.rtsp_url" placeholder="rtsp://... or demo.mp4" />
          <div class="source-presets">
            <el-button text size="small" @click="applySourceTemplate('demo.mp4')">demo.mp4</el-button>
            <el-button text size="small" @click="applySourceTemplate('firework.mp4')">firework.mp4</el-button>
            <el-button text size="small" @click="applySourceTemplate('fire.mp4')">fire.mp4</el-button>
            <el-button text size="small" @click="applySourceTemplate('sunset.mp4')">sunset.mp4</el-button>
          </div>
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="form.location" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="logVisible" :title="`${logCameraName} 日志`" width="560px">
      <el-timeline>
        <el-timeline-item
          v-for="log in cameraLogs"
          :key="log.id"
          :timestamp="new Date(log.timestamp).toLocaleString('zh-CN')"
          placement="top"
          :type="String(log.event || '').includes('掉线') ? 'danger' : 'success'"
        >
          {{ log.event }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!cameraLogs.length" description="暂无日志" />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../api'

const cameras = ref([])
const loading = ref(false)
const formVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const logVisible = ref(false)
const logCameraName = ref('')
const cameraLogs = ref([])
const statusFilter = ref('all')
const keyword = ref('')

const form = reactive({ name: '', rtsp_url: '', location: '' })

const onlineCount = computed(() => cameras.value.filter((item) => item.status === 'online').length)
const offlineCount = computed(() => cameras.value.filter((item) => item.status !== 'online').length)
const aiEnabledCount = computed(() => cameras.value.filter((item) => item.enable_ai).length)

const filteredCameras = computed(() => {
  const term = keyword.value.trim().toLowerCase()
  return cameras.value.filter((item) => {
    const byStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'online' && item.status === 'online') ||
      (statusFilter.value === 'offline' && item.status !== 'online') ||
      (statusFilter.value === 'ai_on' && !!item.enable_ai)

    if (!byStatus) return false
    if (!term) return true

    const name = String(item.name || '').toLowerCase()
    const location = String(item.location || '').toLowerCase()
    return name.includes(term) || location.includes(term)
  })
})

const fetchCameras = async () => {
  loading.value = true
  try {
    cameras.value = await api.get('/supervisor/cameras')
  } catch {
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

const openAdd = () => {
  isEdit.value = false
  editId.value = null
  Object.assign(form, { name: '', rtsp_url: '', location: '' })
  formVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
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

const toggleAI = async (row) => {
  const nextEnable = !!row.enable_ai
  try {
    await api.put(`/supervisor/cameras/${row.id}`, { enable_ai: nextEnable })
    ElMessage.success(`设备 ${row.name} AI 检测已${nextEnable ? '开启' : '关闭'}`)
  } catch {
    row.enable_ai = !nextEnable
    ElMessage.error('AI 检测切换失败')
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
    await fetchCameras()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await api.delete(`/supervisor/cameras/${id}`)
    ElMessage.success('删除成功')
    await fetchCameras()
  } catch {
    ElMessage.error('删除失败')
  }
}

const viewLogs = async (row) => {
  logCameraName.value = row.name
  try {
    cameraLogs.value = await api.get(`/supervisor/cameras/${row.id}/logs`)
  } catch {
    cameraLogs.value = []
  }
  logVisible.value = true
}


const applySourceTemplate = (value) => {
  form.rtsp_url = value
}
onMounted(fetchCameras)
</script>

<style scoped>
.cameras-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-panel {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  border-radius: 14px;
  background:
    radial-gradient(circle at 18% 10%, rgba(255, 210, 120, 0.28), transparent 38%),
    linear-gradient(125deg, #16324f, #24506b 45%, #3b7a6f);
  color: #fff;
}

.hero-main h2 {
  margin: 4px 0 8px;
  font-size: 32px;
  line-height: 1.1;
}

.hero-kicker {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.85;
}

.hero-subtitle {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 10px;
  min-width: 320px;
}

.metric-item {
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(4px);
}

.metric-item.success {
  background: rgba(103, 194, 58, 0.28);
}

.metric-item.danger {
  background: rgba(245, 108, 108, 0.28);
}

.metric-item.info {
  background: rgba(64, 158, 255, 0.24);
}

.metric-label {
  font-size: 12px;
  opacity: 0.9;
}

.metric-value {
  margin-top: 4px;
  font-size: 22px;
  font-weight: 700;
}

.control-card {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
}

.control-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-group {
  flex: 1;
}

.control-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input {
  width: 260px;
}

.source-presets {
  margin-top: 6px;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.camera-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  min-height: 180px;
}

.camera-card {
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
  background: var(--el-bg-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.camera-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 26px rgba(15, 39, 67, 0.12);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}

.head-main {
  min-width: 0;
}

.camera-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.camera-location {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.camera-body {
  display: grid;
  grid-template-columns: 170px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
}

.camera-preview {
  position: relative;
  min-height: 132px;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  padding: 12px;
  color: #fff;
}

.camera-preview.online {
  background:
    radial-gradient(circle at 30% 25%, rgba(99, 255, 170, 0.3), transparent 34%),
    linear-gradient(135deg, #12304b, #1f6b68);
}

.camera-preview.offline {
  background:
    radial-gradient(circle at 35% 25%, rgba(255, 120, 120, 0.24), transparent 34%),
    linear-gradient(135deg, #1a2233, #3b4254);
}

.preview-orb {
  position: absolute;
  width: 70px;
  height: 70px;
  border-radius: 50%;
  top: 16px;
  right: 16px;
  background: rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}

.preview-label {
  position: relative;
  z-index: 1;
  font-size: 14px;
  font-weight: 600;
}

.camera-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
}

.meta-item.compact {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.meta-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.meta-value {
  font-size: 13px;
  color: var(--el-text-color-primary);
  word-break: break-all;
}

.mono {
  font-family: Consolas, 'Courier New', monospace;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 14px 14px;
  flex-wrap: wrap;
}

@media (max-width: 1280px) {
  .camera-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .hero-panel {
    flex-direction: column;
  }

  .hero-main h2 {
    font-size: 28px;
  }

  .hero-metrics {
    min-width: 0;
  }

  .search-input {
    width: 100%;
  }

  .camera-body {
    grid-template-columns: 1fr;
  }

  .card-actions {
    justify-content: stretch;
  }

  .card-actions .el-button {
    flex: 1;
  }
}
</style>
