<template>
  <div class="history-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>历史事件与处置回溯</h2>
          <div class="header-actions">
            <el-select v-model="filterStatus" placeholder="筛选状态" clearable style="width: 180px; margin-right: 10px;">
              <el-option label="全部" value="" />
              <el-option label="待核实" value="pending_verify" />
              <el-option label="已核实真实火灾" value="verified_true" />
              <el-option label="已核实误报" value="verified_false" />
              <el-option label="已联动消防" value="dispatched" />
              <el-option label="已完成上报" value="resolved" />
              <el-option label="低风险归档" value="low_archived" />
              <el-option v-if="isAdmin" label="可删除记录" value="done" />
            </el-select>

            <el-button
              v-if="isAdmin"
              type="danger"
              :disabled="selectedIds.length === 0"
              @click="batchDelete"
              style="margin-right: 10px;"
            >
              <el-icon><Delete /></el-icon> 批量删除 ({{ selectedIds.length }})
            </el-button>

            <el-button type="success" @click="exportCSV">
              <el-icon><Download /></el-icon> 导出 CSV
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="alerts" stripe style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column v-if="isAdmin" type="selection" width="45" :selectable="isRowSelectable" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="timestamp" label="告警时间" width="180">
          <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
        </el-table-column>
        <el-table-column prop="camera_name" label="设备" width="140" show-overflow-tooltip />
        <el-table-column prop="yolo_confidence" label="置信度" width="110">
          <template #default="{ row }">{{ ((row.yolo_confidence || 0) * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="llm_result" label="AI 建议" min-width="220" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="130">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="处理备注" min-width="180" show-overflow-tooltip />
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

    <el-dialog v-model="detailVisible" title="告警详情" width="640px">
      <div v-if="currentAlert">
        <div class="detail-image-wrapper" v-if="currentAlert.image_path">
          <img :src="currentAlert.image_path" class="detail-image" />
        </div>
        <el-descriptions :column="1" border style="margin-top: 15px;">
          <el-descriptions-item label="告警 ID">{{ currentAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="发生时间">{{ formatTime(currentAlert.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="设备">{{ currentAlert.camera_name || '未知设备' }}</el-descriptions-item>
          <el-descriptions-item label="YOLO 置信度">
            <el-progress
              :percentage="Math.round((currentAlert.yolo_confidence || 0) * 100)"
              :color="(currentAlert.yolo_confidence || 0) > 0.8 ? '#F56C6C' : '#E6A23C'"
              :stroke-width="14"
              :text-inside="true"
              style="width: 240px;"
            />
          </el-descriptions-item>
          <el-descriptions-item label="AI 分析">
            <div style="white-space: pre-wrap;">{{ currentAlert.llm_result || '暂无' }}</div>
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
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download } from '@element-plus/icons-vue'
import api from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.role === 'admin')

const alerts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const filterStatus = ref('')
const detailVisible = ref(false)
const currentAlert = ref(null)
const selectedIds = ref([])
const deletableStatuses = new Set(['verified_false', 'false_alarm', 'resolved', 'archived_low'])

const formatTime = (t) => (t ? new Date(t).toLocaleString('zh-CN') : '')

const statusLabel = (s) => ({
  pending: '待核实',
  pending_verify: '待核实',
  reviewing_llm: 'LLM复核中',
  confirmed: '已核实真实火灾',
  verified_true: '已核实真实火灾',
  false_alarm: '已核实误报',
  verified_false: '已核实误报',
  dispatched: '已联动消防',
  resolved: '已完成上报',
  archived_low: '低风险归档'
}[s] || s)

const statusType = (s) => ({
  pending: 'warning',
  pending_verify: 'warning',
  reviewing_llm: 'warning',
  confirmed: 'danger',
  verified_true: 'danger',
  dispatched: 'danger',
  resolved: 'success',
  false_alarm: 'info',
  verified_false: 'info',
  archived_low: 'info'
}[s] || 'info')

const canDeleteStatus = (status) => deletableStatuses.has(status)

const isRowSelectable = (row) => canDeleteStatus(row.status)

const fetchAlerts = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: pageSize }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await api.get('/alerts', { params })
    alerts.value = res.items || []
    total.value = res.total || 0
    selectedIds.value = []
  } catch {
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
  fetch(`/api/alerts/export/csv${params}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
    .then(res => res.blob())
    .then(blob => {
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.href = url
      link.setAttribute('download', 'alerts.csv')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    })
    .catch(() => ElMessage.error('导出失败'))
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.filter(r => canDeleteStatus(r.status)).map(r => r.id)
}

const batchDelete = async () => {
  if (!isAdmin.value || selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${selectedIds.value.length} 条记录？`, '批量删除', { type: 'warning' })
    const res = await api.post('/alerts/batch-delete', { ids: selectedIds.value })
    const deleted = Number(res?.deleted || 0)
    const blocked = Array.isArray(res?.blocked) ? res.blocked.length : 0
    const notFound = Array.isArray(res?.not_found) ? res.not_found.length : 0

    if (deleted > 0) {
      ElMessage.success(`已删除 ${deleted} 条记录`)
    }
    if (blocked > 0 || notFound > 0) {
      ElMessage.warning(`未删除 ${blocked + notFound} 条记录（未闭环或不存在）`)
    }
    if (deleted === 0 && blocked === 0 && notFound === 0) {
      ElMessage.info('没有可删除的记录')
    }

    selectedIds.value = []
    await fetchAlerts()
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
  gap: 12px;
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
