<template>
  <div class="tasks-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>📋 我的待处理任务</h2>
          <el-tag type="danger" size="large">{{ total }} 条待处理</el-tag>
        </div>
      </template>

      <el-table :data="alerts" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="timestamp" label="告警时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="yolo_confidence" label="YOLO 置信度" width="120">
          <template #default="{ row }">
            <el-progress 
              :percentage="Math.round(row.yolo_confidence * 100)" 
              :color="row.yolo_confidence > 0.8 ? '#F56C6C' : '#E6A23C'"
              :stroke-width="14"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="llm_result" label="大模型判定" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="openProcess(row, 'confirmed')">
              <el-icon><WarningFilled /></el-icon> 确认火灾
            </el-button>
            <el-button type="info" size="small" @click="openProcess(row, 'false_alarm')">
              误报
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 处理对话框 -->
    <el-dialog v-model="dialogVisible" title="处理告警事件" width="500px">
      <div v-if="currentAlert" style="margin-bottom: 15px;">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="告警ID">{{ currentAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(currentAlert.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="大模型分析">{{ currentAlert.llm_result }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <el-input v-model="processRemark" type="textarea" :rows="3" placeholder="请填写处理备注（可选）" />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitProcess" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'

const alerts = ref([])
const total = ref(0)
const loading = ref(false)
const dialogVisible = ref(false)
const currentAlert = ref(null)
const processStatus = ref('')
const processRemark = ref('')
const submitting = ref(false)

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

const fetchAlerts = async () => {
  loading.value = true
  try {
    const res = await api.get('/alerts', { params: { status: 'pending' } })
    alerts.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error('获取待处理任务失败')
  } finally {
    loading.value = false
  }
}

const openProcess = (row, status) => {
  currentAlert.value = row
  processStatus.value = status
  processRemark.value = ''
  dialogVisible.value = true
}

const submitProcess = async () => {
  submitting.value = true
  try {
    await api.put(`/alerts/${currentAlert.value.id}/process`, {
      status: processStatus.value,
      remark: processRemark.value
    })
    ElMessage.success(processStatus.value === 'confirmed' ? '已确认为真实火灾' : '已标记为误报')
    dialogVisible.value = false
    fetchAlerts()
  } catch (e) {
    ElMessage.error('处理失败')
  } finally {
    submitting.value = false
  }
}

onMounted(fetchAlerts)
</script>

<style scoped>
.tasks-container {
  padding: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h2 {
  margin: 0;
}
</style>
