<template>
  <div class="tasks-page">
    <section class="hero-panel">
      <div class="hero-main">
        <p class="hero-kicker">Operator Console</p>
        <h2>我的任务</h2>
        <p class="hero-subtitle">仅展示高/中风险任务，支持 SOP 快速处置、撤销与闭环。</p>
      </div>
      <div class="hero-metrics">
        <div class="metric-item">
          <div class="metric-label">当前页任务</div>
          <div class="metric-value">{{ displayAlerts.length }}</div>
        </div>
        <div class="metric-item warning">
          <div class="metric-label">待处置</div>
          <div class="metric-value">{{ pendingCount }}</div>
        </div>
        <div class="metric-item danger">
          <div class="metric-label">已联动消防</div>
          <div class="metric-value">{{ dispatchedCount }}</div>
        </div>
        <div class="metric-item success">
          <div class="metric-label">已完成上报</div>
          <div class="metric-value">{{ resolvedCount }}</div>
        </div>
      </div>
    </section>

    <el-card class="control-card" shadow="never">
      <div class="control-row">
        <el-radio-group v-model="filterStatus" @change="onFilterChange" size="large" class="status-switch">
          <el-radio-button value="">运营队列</el-radio-button>
          <el-radio-button value="pending_verify">待处置</el-radio-button>
          <el-radio-button value="dispatched">已联动消防</el-radio-button>
          <el-radio-button value="resolved">已完成上报</el-radio-button>
          <el-radio-button v-if="isAdmin" value="done">可删除记录</el-radio-button>
        </el-radio-group>

        <div class="control-actions">
          <el-tag type="info">总计 {{ total }} 条</el-tag>
          <el-tag v-if="isAdmin && batchMode" type="warning">已选 {{ selectedIds.length }} 条</el-tag>
          <el-select v-model="pageSize" style="width: 120px" @change="onPageSizeChange">
            <el-option :value="10" label="10 / 页" />
            <el-option :value="20" label="20 / 页" />
            <el-option :value="30" label="30 / 页" />
            <el-option :value="50" label="50 / 页" />
          </el-select>
          <el-button v-if="isAdmin" @click="toggleBatchMode">
            {{ batchMode ? '退出批量' : '批量选择' }}
          </el-button>
          <el-button
            v-if="isAdmin && batchMode"
            type="danger"
            :disabled="selectedIds.length === 0 || deleting"
            :loading="deleting"
            @click="deleteSelected"
          >
            删除所选
          </el-button>
          <el-button :loading="loading" @click="fetchAlerts">刷新</el-button>
        </div>
      </div>
    </el-card>

    <div class="task-grid" v-loading="loading">
      <el-empty v-if="!loading && displayAlerts.length === 0" description="当前筛选条件下没有任务" />

      <article v-for="row in displayAlerts" :key="row.id" class="task-card">
        <header class="task-head">
          <div class="head-left">
            <el-checkbox
              v-if="isAdmin && batchMode"
              :model-value="selectedIds.includes(row.id)"
              @change="(checked) => toggleSelect(row.id, checked)"
            />
            <span class="task-id">#{{ row.id }}</span>
            <span class="task-time">{{ formatTime(row.timestamp) }}</span>
          </div>
          <el-tag size="small" :type="workflowType(row.status)">{{ workflowLabel(row.status) }}</el-tag>
        </header>

        <div class="task-main">
          <el-image
            v-if="row.image_path"
            :src="assetUrl(row.image_path)"
            :preview-src-list="previewList(row.image_path)"
            fit="cover"
            class="snapshot"
            preview-teleported
          />
          <div v-else class="snapshot placeholder">暂无截图</div>

          <div class="task-meta">
            <div class="meta-location">
              <div class="cam-name">{{ row.camera_name || '未知设备' }}</div>
              <div class="cam-loc">{{ row.camera_location || '位置未配置' }}</div>
            </div>

            <div class="meta-risk">
              <el-tag :type="riskType(row)">{{ riskLabel(row) }}</el-tag>
              <span class="conf-text">YOLO {{ Math.round((row.yolo_confidence || 0) * 100) }}%</span>
            </div>

            <el-progress
              :percentage="Math.round((row.yolo_confidence || 0) * 100)"
              :stroke-width="8"
              :show-text="false"
              :color="progressColor(row)"
            />

            <p class="ai-advice">{{ row.llm_result || '暂无 AI 建议' }}</p>
          </div>
        </div>

        <footer class="task-foot">
          <template v-if="isPendingVerify(row.status)">
            <el-button class="action-btn" type="danger" @click="openSopExecute(row, 'SOP1')">执行 SOP1</el-button>
            <el-button class="action-btn" type="warning" @click="openSopExecute(row, 'SOP2')">执行 SOP2</el-button>
            <el-button
              v-if="isAdmin && canCancelStatus(row.status)"
              class="action-btn"
              type="info"
              plain
              @click="cancelOne(row)"
            >
              撤销任务
            </el-button>
          </template>
          <template v-else-if="row.status === 'dispatched'">
            <el-button class="action-btn" type="success" @click="openResolve(row)">完成上报</el-button>
          </template>
          <el-tag v-else type="success" effect="dark">已闭环</el-tag>

          <el-button
            v-if="isAdmin"
            class="action-btn delete-btn"
            type="danger"
            plain
            :disabled="!canDeleteStatus(row.status) || deleting"
            @click="deleteOne(row)"
          >
            删除
          </el-button>
        </footer>
      </article>
    </div>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="onPageChange"
      />
    </div>

    <el-dialog v-model="actionVisible" :title="actionTitle" width="720px">
      <div v-if="currentAlert">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="告警 ID">{{ currentAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="事故地点">
            {{ currentAlert.camera_name || '未知设备' }} / {{ currentAlert.camera_location || '位置未配置' }}
          </el-descriptions-item>
          <el-descriptions-item label="风险级别">
            <el-tag :type="riskType(currentAlert)">{{ riskLabel(currentAlert) }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div v-if="actionType === 'SOP1'" class="sop-section">
        <h4>SOP1：高风险紧急处置（确诊火情）</h4>
        <ol class="sop-list">
          <li>先看截图和摄像头位置，30秒内确认是不是明火或大面积浓烟。</li>
          <li>确认为真火后，立即拨打消防电话，按“位置+火势+是否蔓延”三项报清楚。</li>
          <li>同步通知最近的护林员或应急小组先赶到现场，做外围隔离和人员疏散。</li>
          <li>把接警人、调度对象、现场情况写进备注，提交后进入已联动状态。</li>
        </ol>
      </div>

      <div v-if="actionType === 'SOP2'" class="sop-section">
        <h4>SOP2：中风险现场核实（疑似火情）</h4>
        <ol class="sop-list">
          <li>先按截图和AI分析做初判，判断更像真火还是反光/烟尘误报。</li>
          <li>安排最近值守人员或无人机到点位复核，优先确认“有无明火、烟雾来源、扩散方向”。</li>
          <li>现场回报为真火就立刻升级到 SOP1；回报为误报就选择误报归档。</li>
          <li>备注里写清复核人、复核时间和结论原因，便于后续追溯。</li>
        </ol>
      </div>

      <el-form label-width="120px" class="action-form">
        <el-form-item v-if="actionType === 'SOP2'" label="SOP2 结果">
          <el-radio-group v-model="sop2Outcome">
            <el-radio value="true_fire">真实火灾（升级 SOP1）</el-radio>
            <el-radio value="false_alarm">现场误报</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="actionType === 'SOP1' || (actionType === 'SOP2' && sop2Outcome === 'true_fire')"
          label="消防电话"
        >
          <el-input v-model="dispatchContact" placeholder="为空则使用系统默认消防电话" />
          <div class="field-tip">系统默认：{{ fireDispatchPhone }}</div>
        </el-form-item>

        <el-form-item
          v-if="actionType === 'SOP1' || (actionType === 'SOP2' && sop2Outcome === 'true_fire')"
          label="接警人"
        >
          <el-input v-model="receiverName" placeholder="填写接警人姓名" />
        </el-form-item>

        <el-form-item
          v-if="actionType === 'SOP1' || (actionType === 'SOP2' && sop2Outcome === 'true_fire')"
          label="调度对象"
        >
          <el-input v-model="dispatchTarget" placeholder="填写护林员或应急小组" />
        </el-form-item>

        <el-form-item v-if="actionType === 'SOP2'" label="复核人">
          <el-input v-model="verifierName" placeholder="填写现场复核人" />
        </el-form-item>

        <el-form-item v-if="actionType === 'SOP2' && sop2Outcome === 'false_alarm'" label="误报原因">
          <el-input v-model="falseReason" placeholder="如：晚霞反光、合规焚烧秸秆" />
        </el-form-item>

        <el-form-item label="处理备注">
          <el-input
            v-model="processRemark"
            type="textarea"
            :rows="4"
            placeholder="补充现场情况、联动详情与处置结果"
          />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { normalizeAssetUrl } from '../api/backend'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

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
const deleting = ref(false)
const batchMode = ref(false)
const selectedIds = ref([])

const isAdmin = computed(() => userStore.role === 'admin')
const deletableStatuses = new Set(['verified_false', 'false_alarm', 'resolved', 'archived_low', 'cancelled_pending'])
const cancellableStatuses = new Set(['pending', 'pending_verify'])
const assetUrl = (path) => normalizeAssetUrl(path)
const previewList = (path) => {
  const url = assetUrl(path)
  return url ? [url] : []
}

const isPendingVerify = (status) => ['pending', 'pending_verify', 'confirmed', 'verified_true'].includes(status)

const workflowLabel = (status) => {
  const map = {
    pending: '待处置',
    pending_verify: '待处置',
    reviewing_llm: 'LLM 复核中',
    confirmed: '已核实真火',
    verified_true: '已核实真火',
    false_alarm: '已核实误报',
    verified_false: '已处理（误报）',
    dispatched: '已联动消防',
    resolved: '已完成上报',
    archived_low: '低风险归档',
    cancelled_pending: '已撤销待处置'
  }
  return map[status] || status
}

const workflowType = (status) => {
  if (['dispatched', 'confirmed', 'verified_true'].includes(status)) return 'danger'
  if (status === 'resolved') return 'success'
  if (['false_alarm', 'verified_false', 'archived_low', 'cancelled_pending'].includes(status)) return 'info'
  return 'warning'
}

const canDeleteStatus = (status) => deletableStatuses.has(status)
const canCancelStatus = (status) => cancellableStatuses.has(status)

const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedIds.value = []
  }
}

const toggleSelect = (id, checked) => {
  const selected = new Set(selectedIds.value)
  if (checked) {
    selected.add(id)
  } else {
    selected.delete(id)
  }
  selectedIds.value = [...selected]
}

const detectRiskFromText = (text) => {
  const normalized = String(text || '').toLowerCase()
  if (normalized.includes('复核结论:真实火灾') || normalized.includes('true_fire')) return 'high'
  if (normalized.includes('复核结论:误报') || normalized.includes('false_alarm')) return 'low'
  if (normalized.includes('高风险') || normalized.includes('high')) return 'high'
  if (normalized.includes('中风险') || normalized.includes('medium')) return 'medium'
  if (normalized.includes('低风险') || normalized.includes('low')) return 'low'
  return ''
}

const riskLevel = (row) => {
  const llmRisk = detectRiskFromText(row?.llm_result)
  if (llmRisk) return llmRisk

  const confidence = Number(row?.yolo_confidence || 0)
  if (confidence > yoloHighThreshold.value) return 'high'
  if (confidence < yoloLowThreshold.value) return 'low'
  return 'medium'
}

const riskLabel = (row) => ({
  high: '高风险',
  medium: '中风险',
  low: '低风险'
}[riskLevel(row)] || '中风险')

const riskType = (row) => ({
  high: 'danger',
  medium: 'warning',
  low: 'success'
}[riskLevel(row)] || 'warning')

const progressColor = (row) => {
  const level = riskLevel(row)
  if (level === 'high') return '#f56c6c'
  if (level === 'low') return '#67c23a'
  return '#e6a23c'
}

const displayAlerts = computed(() => alerts.value.map((item) => ({
  ...item,
  camera_location: cameraLocationMap.value[item.camera_name] || '位置未配置'
})))

const pendingCount = computed(() => displayAlerts.value.filter((item) => isPendingVerify(item.status)).length)
const dispatchedCount = computed(() => displayAlerts.value.filter((item) => item.status === 'dispatched').length)
const resolvedCount = computed(() => displayAlerts.value.filter((item) => item.status === 'resolved').length)

const formatTime = (value) => (value ? new Date(value).toLocaleString('zh-CN') : '-')

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
    const nextMap = {}
    cameras.forEach((camera) => {
      nextMap[camera.name] = camera.location || '位置未配置'
    })
    cameraLocationMap.value = nextMap
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
    const pageIds = new Set((alerts.value || []).map((item) => item.id))
    selectedIds.value = selectedIds.value.filter((id) => pageIds.has(id))
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

const onPageChange = (value) => {
  page.value = value
  fetchAlerts()
}

const onPageSizeChange = (value) => {
  pageSize.value = value
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
  actionTitle.value = sopType === 'SOP1' ? '执行 SOP1（高风险紧急处置）' : '执行 SOP2（中风险现场核实）'
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

const cancelOne = async (row) => {
  if (!isAdmin.value || !canCancelStatus(row.status)) return

  try {
    const { value } = await ElMessageBox.prompt(
      `请输入撤销任务 #${row.id} 的原因`,
      '撤销任务',
      {
        confirmButtonText: '确认撤销',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：重复告警、现场核查后确认无需处置',
        inputValidator: (input) => (String(input || '').trim() ? true : '请填写撤销原因')
      }
    )

    deleting.value = true
    await api.put(`/alerts/${row.id}/cancel`, { reason: value })
    ElMessage.success('任务已撤销')
    await fetchAlerts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '撤销失败')
    }
  } finally {
    deleting.value = false
  }
}

const deleteOne = async (row) => {
  if (!isAdmin.value) return
  if (!canDeleteStatus(row.status)) {
    ElMessage.warning('仅已闭环或归档记录可删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认删除任务 #${row.id} 吗？删除后不可恢复。`,
      '删除任务',
      { type: 'warning' }
    )
  } catch {
    return
  }

  deleting.value = true
  try {
    await api.delete(`/alerts/${row.id}`)
    selectedIds.value = selectedIds.value.filter((id) => id !== row.id)
    ElMessage.success('删除成功')
    await fetchAlerts()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

const deleteSelected = async () => {
  if (!isAdmin.value || selectedIds.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确认批量删除 ${selectedIds.value.length} 条记录吗？删除后不可恢复。`,
      '批量删除',
      { type: 'warning' }
    )
  } catch {
    return
  }

  deleting.value = true
  try {
    const res = await api.post('/alerts/batch-delete', { ids: selectedIds.value })
    const deleted = Number(res?.deleted || 0)
    const blocked = Array.isArray(res?.blocked) ? res.blocked.length : 0
    const notFound = Array.isArray(res?.not_found) ? res.not_found.length : 0

    if (deleted > 0) {
      ElMessage.success(`已删除 ${deleted} 条`)
    }
    if (blocked > 0 || notFound > 0) {
      ElMessage.warning(`未删除 ${blocked + notFound} 条（未闭环或不存在）`)
    }

    selectedIds.value = []
    await fetchAlerts()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '批量删除失败')
  } finally {
    deleting.value = false
  }
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
      sop2Outcome.value === 'false_alarm'
        ? `误报原因:${falseReason.value || '未填'}`
        : `升级SOP1接警人:${receiverName.value || '未填'}`,
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
      ElMessage.warning('升级 SOP1 时请填写接警人和调度对象')
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
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
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
    radial-gradient(circle at 15% 10%, rgba(63, 158, 255, 0.3), transparent 42%),
    linear-gradient(120deg, #0e2a47, #1b4d75 45%, #246898);
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

.metric-item.warning {
  background: rgba(230, 162, 60, 0.28);
}

.metric-item.danger {
  background: rgba(245, 108, 108, 0.28);
}

.metric-item.success {
  background: rgba(103, 194, 58, 0.28);
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
  border: 1px solid #dce8f3;
  border-radius: 12px;
}

.control-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.status-switch {
  flex-wrap: wrap;
}

.control-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  min-height: 180px;
}

.task-card {
  border: 1px solid #dde4ee;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 26px rgba(15, 39, 67, 0.12);
}

.task-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid #edf2f7;
  background: #fbfdff;
}

.head-left {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
}

.task-id {
  font-weight: 700;
  color: #1f2d3d;
}

.task-time {
  font-size: 12px;
  color: #7b8a9b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-main {
  padding: 12px 14px;
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: 12px;
}

.snapshot {
  width: 140px;
  height: 96px;
  border-radius: 10px;
  background: #f4f5f7;
}

.snapshot.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #909399;
}

.task-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-location {
  min-width: 0;
}

.cam-name {
  font-size: 16px;
  font-weight: 700;
  color: #1f2d3d;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cam-loc {
  font-size: 12px;
  color: #8896a7;
  margin-top: 2px;
}

.meta-risk {
  display: flex;
  align-items: center;
  gap: 8px;
}

.conf-text {
  font-size: 12px;
  color: #6b7787;
}

.ai-advice {
  margin: 0;
  color: #4d5a68;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-line;
  max-height: 60px;
  overflow: hidden;
}

.task-foot {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 14px 14px;
}

.action-btn {
  min-width: 110px;
}

.delete-btn {
  margin-left: auto;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 4px;
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

@media (max-width: 1280px) {
  .task-grid {
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

  .task-main {
    grid-template-columns: 1fr;
  }

  .snapshot {
    width: 100%;
    height: 180px;
  }

  .task-foot {
    justify-content: stretch;
  }

  .action-btn {
    flex: 1;
  }
}
</style>
