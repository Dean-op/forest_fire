<template>
  <div class="tasks-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>📋 现场核实与处置任务</h2>
          <el-tag type="danger" size="large">{{ total }} 条待办</el-tag>
        </div>
      </template>

      <el-table :data="alerts" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="timestamp" label="告警时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column label="AI 风险级别" width="120">
          <template #default="{ row }">
            <el-tag :type="riskType(row)">{{ riskLabel(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="yolo_confidence" label="YOLO 置信度" width="130">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round(row.yolo_confidence * 100)"
              :color="row.yolo_confidence >= 0.8 ? '#F56C6C' : '#E6A23C'"
              :stroke-width="14"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="llm_result" label="AI 建议" min-width="220" show-overflow-tooltip />
        <el-table-column label="任务状态" width="130">
          <template #default="{ row }">
            <el-tag :type="workflowType(row.status)">{{ workflowLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="处置记录" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <div class="action-row">
              <template v-if="isPendingVerify(row.status)">
                <el-button type="danger" size="small" @click="openAction(row, 'verify_true')">
                  核实真火
                </el-button>
                <el-button type="info" size="small" @click="openAction(row, 'verify_false')">
                  标记误报
                </el-button>
              </template>
              <template v-else-if="isVerifiedTrue(row.status)">
                <el-button type="warning" size="small" @click="openAction(row, 'dispatch')">
                  联动消防
                </el-button>
              </template>
              <template v-else-if="row.status === 'dispatched'">
                <el-button type="success" size="small" @click="openAction(row, 'resolve')">
                  完成上报
                </el-button>
              </template>
              <el-tag v-else type="success" size="small">已闭环</el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="540px">
      <div v-if="currentAlert" style="margin-bottom: 15px;">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="告警ID">{{ currentAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="发生时间">{{ formatTime(currentAlert.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="AI 建议">{{ currentAlert.llm_result || '暂无' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <el-form label-width="98px">
        <el-form-item v-if="actionType === 'dispatch'" label="消防联系人">
          <el-input v-model="dispatchContact" placeholder="填写消防队联系人/电话（可选）" />
        </el-form-item>
        <el-form-item label="备注记录">
          <el-input
            v-model="processRemark"
            type="textarea"
            :rows="4"
            placeholder="请填写现场核实、联动过程或上报结果"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAction" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'

const alerts = ref([])
const total = ref(0)
const loading = ref(false)

const dialogVisible = ref(false)
const currentAlert = ref(null)
const actionType = ref('')
const processRemark = ref('')
const dispatchContact = ref('')
const submitting = ref(false)

const isPendingVerify = (status) => ['pending', 'pending_verify'].includes(status)
const isVerifiedTrue = (status) => ['confirmed', 'verified_true'].includes(status)

const workflowLabel = (status) => {
  const map = {
    pending: '待核实',
    pending_verify: '待核实',
    confirmed: '已核实真火',
    verified_true: '已核实真火',
    false_alarm: '已核实误报',
    verified_false: '已核实误报',
    dispatched: '已联动消防',
    resolved: '处置已完成'
  }
  return map[status] || status
}

const workflowType = (status) => {
  if (['confirmed', 'verified_true', 'dispatched', 'resolved'].includes(status)) return 'danger'
  if (['false_alarm', 'verified_false'].includes(status)) return 'info'
  return 'warning'
}

const riskLabel = (row) => {
  if ((row.yolo_confidence || 0) >= 0.8) return '高风险'
  if ((row.yolo_confidence || 0) >= 0.5) return '中风险'
  return '低风险'
}

const riskType = (row) => {
  if ((row.yolo_confidence || 0) >= 0.8) return 'danger'
  if ((row.yolo_confidence || 0) >= 0.5) return 'warning'
  return 'success'
}

const dialogTitle = computed(() => {
  const map = {
    verify_true: '核实为真实火灾',
    verify_false: '核实为误报',
    dispatch: '联动林区消防队',
    resolve: '上报并完成闭环'
  }
  return map[actionType.value] || '处理任务'
})

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

const fetchAlerts = async () => {
  loading.value = true
  try {
    const res = await api.get('/alerts', { params: { status: 'operator_queue' } })
    alerts.value = res.items
    total.value = res.total
  } catch {
    ElMessage.error('获取任务失败')
  } finally {
    loading.value = false
  }
}

const openAction = (row, type) => {
  currentAlert.value = row
  actionType.value = type
  processRemark.value = ''
  dispatchContact.value = ''
  dialogVisible.value = true
}

const submitAction = async () => {
  if (!currentAlert.value) return
  submitting.value = true
  try {
    if (actionType.value === 'verify_true') {
      await api.put(`/alerts/${currentAlert.value.id}/process`, {
        status: 'confirmed',
        remark: processRemark.value
      })
      ElMessage.success('已核实为真实火灾')
    } else if (actionType.value === 'verify_false') {
      await api.put(`/alerts/${currentAlert.value.id}/process`, {
        status: 'false_alarm',
        remark: processRemark.value
      })
      ElMessage.success('已标记为误报')
    } else if (actionType.value === 'dispatch') {
      await api.put(`/alerts/${currentAlert.value.id}/dispatch`, {
        contact: dispatchContact.value,
        note: processRemark.value
      })
      ElMessage.success('已记录联动消防信息')
    } else if (actionType.value === 'resolve') {
      await api.put(`/alerts/${currentAlert.value.id}/resolve`, {
        remark: processRemark.value
      })
      ElMessage.success('任务已闭环完成')
    }

    dialogVisible.value = false
    fetchAlerts()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
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
.action-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
