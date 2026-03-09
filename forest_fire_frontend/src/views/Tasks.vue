<template>
  <div class="tasks-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="title-wrap">
            <h2>Operator 任务中心</h2>
            <el-tag type="danger">仅高/中风险可见</el-tag>
          </div>
          <div class="header-tools">
            <el-select v-model="filterStatus" placeholder="筛选状态" clearable style="width: 180px" @change="onFilterChange">
              <el-option label="全部" value="" />
              <el-option label="待处置" value="pending_verify" />
              <el-option label="已联动消防" value="dispatched" />
              <el-option label="已处理" value="resolved" />
            </el-select>
            <el-tag type="info">共 {{ total }} 条</el-tag>
            <el-button @click="fetchAlerts" :loading="loading">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="displayAlerts" stripe border v-loading="loading" style="width: 100%" row-key="id">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="timestamp" label="告警时间" width="170">
          <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
        </el-table-column>
        <el-table-column label="事故地点" min-width="210">
          <template #default="{ row }">
            <div class="location-cell">
              <div class="cam-name">{{ row.camera_name || '未知设备' }}</div>
              <div class="cam-loc">{{ row.camera_location || '位置未配置' }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="现场截图" width="132" align="center">
          <template #default="{ row }">
            <el-image
              v-if="row.image_path"
              :src="row.image_path"
              :preview-src-list="[row.image_path]"
              fit="cover"
              class="snapshot"
              preview-teleported
            />
            <div v-else class="snapshot placeholder">无截图</div>
          </template>
        </el-table-column>
        <el-table-column label="风险级别" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="riskType(row)">{{ riskLabel(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="llm_result" label="AI建议" min-width="240" show-overflow-tooltip />
        <el-table-column label="任务状态" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="workflowType(row.status)">{{ workflowLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作处理" width="190" fixed="right" align="center">
          <template #default="{ row }">
            <div class="op-actions">
              <template v-if="isPendingVerify(row.status)">
                <el-button class="op-btn" type="danger" size="small" @click="openSopExecute(row, 'SOP1')">执行SOP1</el-button>
                <el-button class="op-btn" type="warning" size="small" @click="openSopExecute(row, 'SOP2')">执行SOP2</el-button>
              </template>
              <template v-else-if="row.status === 'dispatched'">
                <el-button class="op-btn" type="success" size="small" @click="openResolve(row)">完成上报</el-button>
              </template>
              <el-tag v-else type="success" size="small">已闭环</el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 30, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="onPageSizeChange"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="actionVisible" :title="actionTitle" width="700px">
      <div v-if="currentAlert">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="告警ID">{{ currentAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="事故地点">{{ currentAlert.camera_name || '未知设备' }} / {{ currentAlert.camera_location || '位置未配置' }}</el-descriptions-item>
          <el-descriptions-item label="风险级别">
            <el-tag :type="riskType(currentAlert)">{{ riskLabel(currentAlert) }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div v-if="actionType === 'SOP1'" class="sop-section">
        <h4>SOP1：高风险紧急处置（确诊火情）</h4>
        <ol class="sop-list">
          <li>人工视检：3秒内确认是否为明显明火/浓烟。</li>
          <li>消防联动：拨打消防电话，通报火灾地点与火势初判。</li>
          <li>内部调度：通知护林员/应急小组前往现场。</li>
          <li>归档结单：记录接警人与调度对象，状态改为“已处理”。</li>
        </ol>
      </div>

      <div v-if="actionType === 'SOP2'" class="sop-section">
        <h4>SOP2：中风险现场核实（疑似火情）</h4>
        <ol class="sop-list">
          <li>人工视检：结合截图和 LLM 解释判断是否疑似误报。</li>
          <li>现场复核：调度最近护林员或无人机赴现场核实。</li>
          <li>决断分流：真实火灾则升级 SOP1；误报则归档。</li>
          <li>归档结单：填写复核人与误报原因（若为误报）。</li>
        </ol>
      </div>

      <el-form label-width="120px" class="action-form">
        <el-form-item v-if="actionType === 'SOP2'" label="SOP2结果">
          <el-radio-group v-model="sop2Outcome">
            <el-radio value="true_fire">真实火灾（升级SOP1）</el-radio>
            <el-radio value="false_alarm">现场误报</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="actionType === 'SOP1' || (actionType === 'SOP2' && sop2Outcome === 'true_fire')" label="消防电话">
          <el-input v-model="dispatchContact" placeholder="为空则使用系统默认消防电话" />
          <div class="field-tip">系统默认：{{ fireDispatchPhone }}</div>
        </el-form-item>

        <el-form-item v-if="actionType === 'SOP1' || (actionType === 'SOP2' && sop2Outcome === 'true_fire')" label="接警人">
          <el-input v-model="receiverName" placeholder="填写接警人" />
        </el-form-item>

        <el-form-item v-if="actionType === 'SOP1' || (actionType === 'SOP2' && sop2Outcome === 'true_fire')" label="调度对象">
          <el-input v-model="dispatchTarget" placeholder="填写护林员/应急小组" />
        </el-form-item>

        <el-form-item v-if="actionType === 'SOP2'" label="复核人">
          <el-input v-model="verifierName" placeholder="填写现场复核人" />
        </el-form-item>

        <el-form-item v-if="actionType === 'SOP2' && sop2Outcome === 'false_alarm'" label="误报原因">
          <el-input v-model="falseReason" placeholder="如：晚霞反光、合规焚烧秸秆" />
        </el-form-item>

        <el-form-item label="处理备注">
          <el-input v-model="processRemark" type="textarea" :rows="4" placeholder="补充现场情况、联动详情、上报结果" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="actionVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAction" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const alerts = ref([])
const total = ref(0)
const loading = ref(false)
const cameraLocationMap = ref({})

const filterStatus = ref('')
const page = ref(1)
const pageSize = ref(10)

const fireDispatchPhone = ref('119')
const yoloHighThreshold = ref(0.9)
const yoloLowThreshold = ref(0.4)

const actionVisible = ref(false)
const actionType = ref('')
const actionTitle = ref('')
const currentAlert = ref(null)
const processRemark = ref('')
const dispatchContact = ref('')
const receiverName = ref('')
const dispatchTarget = ref('')
const verifierName = ref('')
const falseReason = ref('')
const sop2Outcome = ref('false_alarm')
const submitting = ref(false)

const isPendingVerify = (status) => ['pending', 'pending_verify', 'confirmed', 'verified_true'].includes(status)

const workflowLabel = (status) => {
  const map = {
    pending: '待处置',
    pending_verify: '待处置',
    reviewing_llm: 'LLM复核中',
    confirmed: '已核实真火',
    verified_true: '已核实真火',
    false_alarm: '已核实误报',
    verified_false: '已处理(误报)',
    dispatched: '已联动消防',
    resolved: '已处理',
    archived_low: '低风险归档'
  }
  return map[status] || status
}

const workflowType = (status) => {
  if (['dispatched', 'resolved', 'confirmed', 'verified_true'].includes(status)) return 'danger'
  if (['false_alarm', 'verified_false', 'archived_low'].includes(status)) return 'info'
  return 'warning'
}

const detectRiskFromText = (text) => {
  const t = String(text || '')
  if (t.includes('高风险')) return 'high'
  if (t.includes('中风险')) return 'medium'
  if (t.includes('低风险')) return 'low'
  return ''
}

const riskLevel = (row) => {
  const llmRisk = detectRiskFromText(row?.llm_result)
  if (llmRisk) return llmRisk
  const conf = Number(row?.yolo_confidence || 0)
  if (conf > yoloHighThreshold.value) return 'high'
  if (conf < yoloLowThreshold.value) return 'low'
  return 'medium'
}

const riskLabel = (row) => ({ high: '高风险', medium: '中风险', low: '低风险' }[riskLevel(row)] || '中风险')
const riskType = (row) => ({ high: 'danger', medium: 'warning', low: 'success' }[riskLevel(row)] || 'warning')

const displayAlerts = computed(() =>
  alerts.value.map((item) => ({
    ...item,
    camera_location: cameraLocationMap.value[item.camera_name] || '位置未配置'
  }))
)

const formatTime = (t) => (t ? new Date(t).toLocaleString('zh-CN') : '-')

const fetchOpsConfig = async () => {
  try {
    const res = await api.get('/admin/public/system-name')
    fireDispatchPhone.value = String(res.fire_dispatch_phone || '119')
    yoloHighThreshold.value = Number(res.yolo_high_threshold || 0.9)
    yoloLowThreshold.value = Number(res.yolo_low_threshold || 0.4)
  } catch {
    fireDispatchPhone.value = '119'
    yoloHighThreshold.value = 0.9
    yoloLowThreshold.value = 0.4
  }
}

const fetchCameraMap = async () => {
  try {
    const cameras = await api.get('/supervisor/cameras')
    const map = {}
    cameras.forEach((cam) => {
      map[cam.name] = cam.location || '位置未配置'
    })
    cameraLocationMap.value = map
  } catch {
    cameraLocationMap.value = {}
  }
}

const fetchAlerts = async () => {
  loading.value = true
  try {
    const params = {
      status: filterStatus.value || 'operator_queue',
      page: page.value,
      size: pageSize.value
    }
    const res = await api.get('/alerts', { params })
    alerts.value = res.items || []
    total.value = res.total || 0
  } catch {
    ElMessage.error('获取任务失败')
  } finally {
    loading.value = false
  }
}

const onFilterChange = () => {
  page.value = 1
  fetchAlerts()
}

const onPageChange = (val) => {
  page.value = val
  fetchAlerts()
}

const onPageSizeChange = (val) => {
  pageSize.value = val
  page.value = 1
  fetchAlerts()
}

const resetActionState = () => {
  processRemark.value = ''
  dispatchContact.value = fireDispatchPhone.value
  receiverName.value = ''
  dispatchTarget.value = ''
  verifierName.value = ''
  falseReason.value = ''
  sop2Outcome.value = 'false_alarm'
}

const openSopExecute = (row, sopType) => {
  currentAlert.value = row
  actionType.value = sopType
  actionTitle.value = sopType === 'SOP1' ? '执行SOP1（高风险紧急处置）' : '执行SOP2（中风险现场核实）'
  resetActionState()
  actionVisible.value = true
}

const openResolve = (row) => {
  currentAlert.value = row
  actionType.value = 'resolve'
  actionTitle.value = '完成上报并闭环'
  resetActionState()
  actionVisible.value = true
}

const buildSopNote = () => {
  if (actionType.value === 'SOP1') {
    return [
      `接警人:${receiverName.value || '未填'}`,
      `调度对象:${dispatchTarget.value || '未填'}`,
      processRemark.value || ''
    ].filter(Boolean).join('；')
  }

  if (actionType.value === 'SOP2') {
    return [
      `复核人:${verifierName.value || '未填'}`,
      sop2Outcome.value === 'false_alarm' ? `误报原因:${falseReason.value || '未填'}` : `升级SOP1接警人:${receiverName.value || '未填'}`,
      sop2Outcome.value === 'true_fire' ? `调度对象:${dispatchTarget.value || '未填'}` : '',
      processRemark.value || ''
    ].filter(Boolean).join('；')
  }

  return processRemark.value || ''
}

const submitAction = async () => {
  if (!currentAlert.value) return

  if (actionType.value === 'SOP1' && (!receiverName.value || !dispatchTarget.value)) {
    ElMessage.warning('请填写接警人和调度对象')
    return
  }

  if (actionType.value === 'SOP2') {
    if (!verifierName.value) {
      ElMessage.warning('请填写复核人')
      return
    }
    if (sop2Outcome.value === 'false_alarm' && !falseReason.value) {
      ElMessage.warning('请填写误报原因')
      return
    }
    if (sop2Outcome.value === 'true_fire' && (!receiverName.value || !dispatchTarget.value)) {
      ElMessage.warning('升级SOP1时请填写接警人和调度对象')
      return
    }
  }

  submitting.value = true
  try {
    if (actionType.value === 'SOP1' || actionType.value === 'SOP2') {
      await api.put(`/alerts/${currentAlert.value.id}/execute-sop`, {
        sop_type: actionType.value,
        outcome: actionType.value === 'SOP2' ? sop2Outcome.value : null,
        contact: dispatchContact.value,
        note: buildSopNote()
      })
      ElMessage.success(`${actionType.value} 已执行`)
    } else if (actionType.value === 'resolve') {
      await api.put(`/alerts/${currentAlert.value.id}/resolve`, {
        remark: processRemark.value
      })
      ElMessage.success('任务已完成上报')
    }

    actionVisible.value = false
    await fetchAlerts()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchOpsConfig(), fetchCameraMap()])
  await fetchAlerts()
})
</script>

<style scoped>
.tasks-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-wrap h2 {
  margin: 0;
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.location-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cam-name {
  font-weight: 600;
  color: #303133;
}

.cam-loc {
  font-size: 12px;
  color: #909399;
}

.snapshot {
  width: 96px;
  height: 56px;
  border-radius: 6px;
  background: #f2f3f5;
}

.snapshot.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 12px;
}

.op-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.op-btn {
  width: 132px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.sop-section {
  margin-top: 12px;
}

.sop-section h4 {
  margin: 0 0 8px;
}

.sop-list {
  margin: 0;
  padding-left: 20px;
  line-height: 1.8;
}

.action-form {
  margin-top: 14px;
}

.field-tip {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
}
</style>
