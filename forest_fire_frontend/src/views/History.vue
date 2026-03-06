<template>
  <div class="history-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>📖 历史事件回溯</h2>
          <div class="header-actions">
            <el-select v-model="filterStatus" placeholder="筛选状态" clearable style="width: 140px; margin-right: 10px;">
              <el-option label="全部" value="" />
              <el-option label="待处理" value="pending" />
              <el-option label="真实火灾" value="confirmed" />
              <el-option label="误报" value="false_alarm" />
            </el-select>
            <el-button type="danger" :disabled="selectedIds.length === 0" @click="batchDelete" style="margin-right: 10px;">
              <el-icon><Delete /></el-icon> 批量删除 ({{ selectedIds.length }})
            </el-button>
            <el-button type="success" @click="exportCSV">
              <el-icon><Download /></el-icon> 导出 CSV
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="alerts" stripe style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="timestamp" label="告警时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="yolo_confidence" label="YOLO 置信度" width="120">
          <template #default="{ row }">
            {{ (row.yolo_confidence * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column prop="llm_result" label="大模型判定" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="处理备注" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchAlerts"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="告警详情" width="600px">
      <div v-if="currentAlert">
        <div class="detail-image-wrapper" v-if="currentAlert.image_path">
          <img :src="currentAlert.image_path" class="detail-image" />
        </div>
        <el-descriptions :column="1" border style="margin-top: 15px;">
          <el-descriptions-item label="告警 ID">{{ currentAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="发生时间">{{ formatTime(currentAlert.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="YOLO 置信度">
            <el-progress 
              :percentage="Math.round(currentAlert.yolo_confidence * 100)" 
              :color="currentAlert.yolo_confidence > 0.8 ? '#F56C6C' : '#E6A23C'"
              :stroke-width="14" :text-inside="true" style="width: 200px;"
            />
          </el-descriptions-item>
          <el-descriptions-item label="大模型分析报告">
            <div style="white-space: pre-wrap;">{{ currentAlert.llm_result }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusType(currentAlert.status)" size="large">{{ statusLabel(currentAlert.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="处理备注">{{ currentAlert.remark || '暂无' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete } from '@element-plus/icons-vue'

const alerts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const filterStatus = ref('')
const detailVisible = ref(false)
const currentAlert = ref(null)
const selectedIds = ref([])

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

const statusLabel = (s) => ({ 'pending': '待处理', 'confirmed': '真实火灾', 'false_alarm': '误报' }[s] || s)
const statusType = (s) => ({ 'pending': 'warning', 'confirmed': 'danger', 'false_alarm': 'info' }[s] || '')

const fetchAlerts = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: pageSize }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await api.get('/alerts', { params })
    alerts.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error('获取告警历史失败')
  } finally {
    loading.value = false
  }
}

watch(filterStatus, () => {
  page.value = 1
  fetchAlerts()
})

const showDetail = (row) => {
  currentAlert.value = row
  detailVisible.value = true
}

const exportCSV = () => {
  const token = localStorage.getItem('token')
  const params = filterStatus.value ? `?status=${filterStatus.value}` : ''
  // 使用临时 a 标签触发下载
  const link = document.createElement('a')
  link.href = `/api/alerts/export/csv${params}`
  link.setAttribute('download', 'alerts.csv')
  
  // 需要通过 fetch 带 token
  fetch(`/api/alerts/export/csv${params}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
    .then(res => res.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob)
      link.href = url
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    })
    .catch(() => ElMessage.error('导出失败'))
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map(r => r.id)
}

const batchDelete = async () => {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${selectedIds.value.length} 条记录？`, '批量删除', { type: 'warning' })
    await api.post('/alerts/batch-delete', { ids: selectedIds.value })
    ElMessage.success(`已删除 ${selectedIds.value.length} 条记录`)
    selectedIds.value = []
    fetchAlerts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(fetchAlerts)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h2 {
  margin: 0;
}
.header-actions {
  display: flex;
  align-items: center;
}
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
.detail-image-wrapper {
  text-align: center;
}
.detail-image {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
</style>
