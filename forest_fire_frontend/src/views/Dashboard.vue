<template>
  <div class="dashboard-container">
    <div v-if="fireFlashActive" class="fire-flash-overlay"></div>

    <div class="header-tools">
      <h2 class="dashboard-title">
        <el-icon class="title-icon"><Monitor /></el-icon>
        智能监控大屏
        <span class="title-glow">双核预警引擎</span>
      </h2>
      <div class="header-right">
        <el-button v-if="latestAlert" type="danger" @click="openAlertCenter" class="pulse-btn glass-btn-red">
          <el-icon><Warning /></el-icon>
          告警中心
          <el-tag v-if="unreadCount > 0" size="small" type="warning" effect="dark" class="unread-tag">
            {{ unreadCount }}
          </el-tag>
        </el-button>
        <el-tag type="success" effect="dark" v-if="wsConnected" class="status-tag">
          <div class="dot online"></div>告警连接正常
        </el-tag>
        <el-tag type="danger" effect="dark" v-else class="status-tag">
          <div class="dot offline"></div>告警连接中断
        </el-tag>
      </div>
    </div>

    <transition name="banner-fade">
      <el-alert
        v-if="burstBanner.visible && !showAlertDrawer"
        :type="burstBanner.level"
        show-icon
        :closable="false"
        class="burst-banner glass-alert"
      >
        <template #title>
          最近 12 秒新增 {{ burstBanner.count }} 条告警，最新来自 <span class="highlight-text">{{ burstBanner.lastCamera }}</span>
          <span v-if="burstBanner.lastAt" class="banner-time">（{{ burstBanner.lastAt }}）</span>
        </template>
        <template #default>告警已聚合到告警中心，请点击右上角“告警中心”查看详情。</template>
      </el-alert>
    </transition>

    <el-drawer
      v-model="showAlertDrawer"
      :title="`告警中心（最近 ${alertFeed.length} 条）`"
      direction="rtl"
      size="40%"
      class="theme-drawer"
    >
      <div v-if="latestAlert" class="alert-detail">
        <el-alert title="检测到疑似火情" type="error" show-icon :closable="false" style="margin-bottom: 15px" class="glass-alert" />
        <img :src="assetUrl(latestAlert.image_path)" class="alert-image glass-img" alt="告警截图" />
        <el-descriptions :column="1" border style="margin-top: 15px">
          <el-descriptions-item label="报警设备">
            <el-icon><VideoCamera /></el-icon> {{ latestAlert.camera_name || '未知设备' }}
          </el-descriptions-item>
          <el-descriptions-item label="发生时间">
            <el-icon><Calendar /></el-icon> {{ latestAlert.timestamp }}
          </el-descriptions-item>
          <el-descriptions-item label="YOLO 置信度">
            <el-progress 
              :percentage="Math.round((latestAlert.yolo_confidence || 0) * 100)"
              :color="(latestAlert.yolo_confidence || 0) > 0.85 ? '#F56C6C' : '#E6A23C'"
            />
          </el-descriptions-item>
          <el-descriptions-item label="大模型复核">
            <el-tag :type="statusTypeSafe(latestAlert.status)" effect="dark">{{ latestAlert.llm_result || '正在分析中...' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusTypeSafe(latestAlert.status)" effect="dark" round>
              {{ statusLabelSafe(latestAlert.status) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <el-empty v-else description="暂无告警" />

      <el-divider content-position="left">告警时间线</el-divider>
      <div v-if="alertFeed.length > 0" class="alert-feed">
        <div
          v-for="item in alertFeed"
          :key="item._key"
          class="feed-item glass-card"
          :class="{ active: latestAlert && latestAlert._key === item._key }"
          @click="selectAlert(item)"
        >
          <div class="feed-left">
            <div class="feed-title">{{ item.camera_name || '未知设备' }}</div>
            <div class="feed-time">{{ item.timestamp }}</div>
          </div>
          <div class="feed-right">
            <el-tag size="small" :type="statusTypeSafe(item.status)" effect="dark">{{ statusLabelSafe(item.status) }}</el-tag>
            <span class="feed-conf">{{ Math.round((item.yolo_confidence || 0) * 100) }}%</span>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无时间线数据" />
    </el-drawer>

    <div class="video-grid" :class="{ 'many-cams': cameras.length > 4 }" v-loading="loading">
      <template v-if="cameras.length > 0">
        <div
          v-for="cam in cameras"
          :key="cam.id"
          :ref="el => setCellRef(cam.id, el)"
          class="video-cell glass-card tech-border"
          :class="{ offline: cam.status !== 'online' }"
        >
          <div class="cell-title">
            <div class="cell-meta">
              <div class="cell-name">
                <el-icon class="cam-icon"><VideoCamera /></el-icon>
                {{ cam.name }}
              </div>
              <div class="cell-time">{{ displayTime }}</div>
            </div>
            <div class="cell-actions">
              <el-tag size="small" :type="cam.status === 'online' ? 'success' : 'info'" effect="dark">
                {{ cam.status === 'online' ? '在线' : '离线' }}
              </el-tag>
              <el-button text class="fullscreen-btn" @click.stop="toggleFullscreen(cam.id)" title="全屏/退出全屏">
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </div>
          </div>

          <img v-if="cam.status === 'online'" :src="streamUrl(cam.id)" class="stream-img" :alt="cam.name" />
          <div v-else class="offline-placeholder">
            <el-icon size="48" color="var(--el-text-color-placeholder)"><VideoPause /></el-icon>
            <p>设备信号丢失</p>
          </div>
        </div>
      </template>
      <el-empty v-else description="暂无设备接入，请先在设备管理中添加视频源" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { FullScreen, VideoCamera, VideoPause, Warning, Monitor, Calendar } from '@element-plus/icons-vue'
import api from '../api'
import { buildBackendUrl, buildBackendWsUrl, ensureBackendOrigin, normalizeAssetUrl } from '../api/backend'

const wsConnected = ref(false)
const ws = ref(null)
const showAlertDrawer = ref(false)
const latestAlert = ref(null)
const alertFeed = ref([])
const unreadCount = ref(0)
const fireFlashActive = ref(false)
const burstBanner = ref({
  visible: false, count: 0, lastCamera: '', lastAt: '', level: 'warning'
})

const ALERT_FEED_LIMIT = 30
const ALERT_SEEN_TTL_MS = 30 * 60 * 1000
const GLOBAL_SEEN_TTL_MS = 5 * 60 * 1000
const BURST_BANNER_HIDE_MS = 12000

const seenAlertMap = new Map()
let reconnectTimer = null
let burstBannerTimer = null
let fireFlashTimer = null
let clockTimer = null
let isComponentAlive = false
let isManualClosing = false

const cameras = ref([])
const loading = ref(false)
const nowTick = ref(Date.now())
const cellRefs = new Map()

const alertSoundEnabled = ref(true)
const alarmAudioUrl = ref('')
let alarmAudio = null

const statusLabel = (status) => {
  const map = {
    pending: '待核实', pending_verify: '待核实',
    confirmed: '已核实真实火灾', verified_true: '已核实真实火灾',
    false_alarm: '已核实误报', verified_false: '已核实误报',
    dispatched: '已联动消防', resolved: '已处理'
  }
  return map[status] || status || '待核实'
}

const statusType = (status) => {
  if (['confirmed', 'verified_true', 'dispatched', 'resolved'].includes(status)) return 'danger'
  if (['false_alarm', 'verified_false', 'archived_low'].includes(status)) return 'info'
  return 'warning'
}
const statusLabelSafe = (s) => s === 'reviewing_llm' ? 'LLM分析中' : s === 'archived_low' ? '低风险归档' : statusLabel(s)
const statusTypeSafe = (s) => statusType(s)

const displayTime = computed(() => new Date(nowTick.value).toLocaleString('zh-CN', { hour12: false }))
const streamUrl = (cameraId) => buildBackendUrl(`/api/stream/video/${cameraId}`)
const assetUrl = (path) => normalizeAssetUrl(path)

const setCellRef = (cameraId, el) => {
  if (el) cellRefs.set(cameraId, el)
  else cellRefs.delete(cameraId)
}

const toBool = (value, fallback = true) => {
  if (typeof value === 'boolean') return value
  const text = String(value ?? '').toLowerCase()
  if (['true', '1', 'yes', 'on'].includes(text)) return true
  if (['false', '0', 'no', 'off'].includes(text)) return false
  return fallback
}

const initAlarmAudio = () => {
  if (typeof Audio === 'undefined') return
  alarmAudio = new Audio(alarmAudioUrl.value)
  alarmAudio.preload = 'auto'
}

const playAlarmSound = () => {
  if (!alertSoundEnabled.value || !alarmAudio) return
  try {
    alarmAudio.currentTime = 0
    const promise = alarmAudio.play()
    if (promise && typeof promise.catch === 'function') promise.catch(() => {})
  } catch {}
}

const fetchRuntimeConfig = async () => {
  try {
    const cfg = await api.get('/admin/public/system-name')
    alertSoundEnabled.value = toBool(cfg?.alert_sound, true)
    if (cfg?.alarm_audio_url) alarmAudioUrl.value = assetUrl(cfg.alarm_audio_url)
  } catch {
    alertSoundEnabled.value = true
  } finally {
    if (!alarmAudioUrl.value) alarmAudioUrl.value = buildBackendUrl('/api/admin/public/alarm-audio')
    initAlarmAudio()
  }
}

const toggleFullscreen = async (cameraId) => {
  const cell = cellRefs.get(cameraId)
  if (!cell || !cell.requestFullscreen) {
    ElMessage.warning('当前浏览器不支持全屏')
    return
  }
  try {
    if (document.fullscreenElement === cell) await document.exitFullscreen()
    else {
      if (document.fullscreenElement) await document.exitFullscreen()
      await cell.requestFullscreen()
    }
  } catch {
    ElMessage.warning('全屏切换失败')
  }
}

const openAlertCenter = () => { showAlertDrawer.value = true; unreadCount.value = 0 }
const selectAlert = (item) => { latestAlert.value = item }
const getAlertKey = (data) => (data.id !== undefined && data.id !== null) ? `id:${data.id}` : `${data.camera_name || 'unknown'}-${data.timestamp || ''}`

const shouldAcceptAlertGlobal = (key) => {
  const nowTs = Date.now()
  if (!window.__ff_seen_alert_map) window.__ff_seen_alert_map = {}
  if (window.__ff_seen_alert_map[key] && nowTs - window.__ff_seen_alert_map[key] < GLOBAL_SEEN_TTL_MS) return false
  window.__ff_seen_alert_map[key] = nowTs
  return true
}

const cleanupSeenAlerts = (nowTs) => {
  for (const [key, ts] of seenAlertMap.entries()) {
    if (nowTs - ts > ALERT_SEEN_TTL_MS) seenAlertMap.delete(key)
  }
  if (!window.__ff_seen_alert_map) return
  Object.keys(window.__ff_seen_alert_map).forEach(k => {
    if (nowTs - window.__ff_seen_alert_map[k] > GLOBAL_SEEN_TTL_MS) delete window.__ff_seen_alert_map[k]
  })
}

const upsertAlertFeed = (alert, key) => {
  const idx = alertFeed.value.findIndex(item => item._key === key)
  const merged = { ...(idx >= 0 ? alertFeed.value[idx] : {}), ...alert, _key: key }
  if (idx >= 0) {
    alertFeed.value[idx] = merged
    alertFeed.value.unshift(alertFeed.value.splice(idx, 1)[0])
  } else {
    alertFeed.value.unshift(merged)
    if (alertFeed.value.length > ALERT_FEED_LIMIT) alertFeed.value.length = ALERT_FEED_LIMIT
  }
  latestAlert.value = merged
}

const touchBurstBanner = (alert) => {
  burstBanner.value.visible = true
  burstBanner.value.count += 1
  burstBanner.value.lastCamera = alert.camera_name || '未知设备'
  burstBanner.value.lastAt = alert.timestamp || ''
  burstBanner.value.level = ['confirmed', 'verified_true', 'dispatched', 'resolved'].includes(alert.status) ? 'error' : 'warning'
  if (burstBannerTimer) clearTimeout(burstBannerTimer)
  burstBannerTimer = setTimeout(() => { burstBanner.value.visible = false; burstBanner.value.count = 0 }, BURST_BANNER_HIDE_MS)
}

const triggerFireFlash = (alert) => {
  const highRiskStatuses = ['pending_verify', 'confirmed', 'verified_true', 'dispatched', 'resolved']
  if (!highRiskStatuses.includes(alert.status)) return
  fireFlashActive.value = true
  if (fireFlashTimer) clearTimeout(fireFlashTimer)
  fireFlashTimer = setTimeout(() => { fireFlashActive.value = false }, 5000)
}

const clearReconnectTimer = () => { if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null } }

const fetchCameras = async () => {
  loading.value = true
  try {
    const res = await api.get('/supervisor/cameras')
    cameras.value = Array.isArray(res) ? res : []
  } catch {
    ElMessage.error('无法获取设备列表')
  } finally { loading.value = false }
}

const initWebSocket = () => {
  if (!isComponentAlive || (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING))) return
  isManualClosing = false
  ws.value = new WebSocket(buildBackendWsUrl('/ws/alerts'))
  ws.value.onopen = () => { wsConnected.value = true }
  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      const nowTs = Date.now()
      cleanupSeenAlerts(nowTs)
      const key = getAlertKey(data)
      const isNewAlert = !seenAlertMap.has(key)
      if (isNewAlert) seenAlertMap.set(key, nowTs)
      upsertAlertFeed(data, key)
      if (!isNewAlert || !shouldAcceptAlertGlobal(key)) return
      unreadCount.value += 1
      touchBurstBanner(data)
      triggerFireFlash(data)
      playAlarmSound()
    } catch (e) { console.error('WS:', e) }
  }
  ws.value.onclose = () => {
    wsConnected.value = false; ws.value = null
    if (!isComponentAlive || isManualClosing) return
    clearReconnectTimer()
    reconnectTimer = setTimeout(() => initWebSocket(), 3000)
  }
}

onMounted(async () => {
  isComponentAlive = true
  await ensureBackendOrigin()
  clockTimer = setInterval(() => { nowTick.value = Date.now() }, 1000)
  await fetchRuntimeConfig()
  await fetchCameras()
  initWebSocket()
})

onUnmounted(() => {
  isComponentAlive = false; isManualClosing = true
  clearReconnectTimer()
  if (ws.value) { ws.value.onclose = null; ws.value.close(); ws.value = null }
  if (burstBannerTimer) clearTimeout(burstBannerTimer)
  if (fireFlashTimer) clearTimeout(fireFlashTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (alarmAudio) { alarmAudio.pause(); alarmAudio = null }
  cellRefs.clear()
})
</script>

<style scoped>
.dashboard-container { position: relative; display: flex; flex-direction: column; height: 100%; }

.fire-flash-overlay {
  position: fixed; inset: 0; z-index: 9999; pointer-events: none;
  background: radial-gradient(circle at 50% 50%, rgba(245, 108, 108, 0.15) 0%, transparent 60%);
  box-shadow: inset 0 0 120px rgba(245, 108, 108, 0.5);
  animation: fire-flash 1s ease-in-out infinite alternate;
}
@keyframes fire-flash { 0% { opacity: 0.1; } 100% { opacity: 1; } }

.header-tools { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.dashboard-title {
  display: flex; align-items: center; gap: 10px; margin: 0;
  color: var(--el-text-color-primary); font-size: 22px; font-weight: 600;
}
html.dark .dashboard-title { color: #f8fafc; text-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }

.title-icon { color: #3b82f6; font-size: 26px; }
.title-glow {
  font-size: 13px; background: linear-gradient(90deg, #3b82f6, #60a5fa); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  padding: 2px 8px; border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 12px; margin-left: 8px;
}
.header-right { display: flex; align-items: center; gap: 15px; }
.status-tag { display: flex; align-items: center; gap: 6px; border: none; font-weight: 500; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.online { background: #67C23A; box-shadow: 0 0 6px #67C23A; }
.dot.offline { background: #F56C6C; box-shadow: 0 0 6px #F56C6C; }

/* 响应式卡片样式 */
.glass-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
}
html.dark .glass-card {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.glass-alert {
  background: var(--el-fill-color-light) !important;
  border: 1px solid var(--el-color-warning) !important;
  color: var(--el-text-color-primary) !important;
}
html.dark .glass-alert {
  background: rgba(15, 23, 42, 0.8) !important;
  color: #f8fafc !important;
}
.glass-alert.el-alert--error { border-color: var(--el-color-danger) !important; }

.highlight-text { color: var(--el-color-warning); font-weight: bold; }
.pulse-btn { animation: pulse-red 2s infinite; border: none; }
.glass-btn-red { background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4); }
.glass-btn-red:hover { background: linear-gradient(135deg, #f87171 0%, #ef4444 100%); }
@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
  70% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.video-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; align-content: start; }
.video-grid.many-cams { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.video-cell { position: relative; display: flex; flex-direction: column; border-radius: 8px; overflow: hidden; aspect-ratio: 16 / 10; min-height: 240px; }

/* 科技边框仅在深色模式下闪烁比较好看，浅色模式微调 */
html.dark .tech-border::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.2); pointer-events: none; z-index: 5;
}
html.dark .tech-border::after {
  content: ''; position: absolute; top: -1px; left: -1px; right: -1px; bottom: -1px;
  background: linear-gradient(90deg, #3b82f6 0%, #3b82f6 10px, transparent 10px) top left no-repeat, linear-gradient(0deg, #3b82f6 0%, #3b82f6 10px, transparent 10px) top left no-repeat, linear-gradient(270deg, #3b82f6 0%, #3b82f6 10px, transparent 10px) top right no-repeat, linear-gradient(0deg, #3b82f6 0%, #3b82f6 10px, transparent 10px) top right no-repeat, linear-gradient(90deg, #3b82f6 0%, #3b82f6 10px, transparent 10px) bottom left no-repeat, linear-gradient(180deg, #3b82f6 0%, #3b82f6 10px, transparent 10px) bottom left no-repeat, linear-gradient(270deg, #3b82f6 0%, #3b82f6 10px, transparent 10px) bottom right no-repeat, linear-gradient(180deg, #3b82f6 0%, #3b82f6 10px, transparent 10px) bottom right no-repeat;
  background-size: 12px 12px; pointer-events: none; z-index: 6; border-radius: 8px;
}

.cell-title {
  height: 44px; padding: 0 14px; display: flex; justify-content: space-between; align-items: center;
  font-size: 14px; position: absolute; top: 0; left: 0; right: 0; z-index: 10;
  background: var(--el-fill-color-light); color: var(--el-text-color-primary);
}
html.dark .cell-title {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(15, 23, 42, 0.3) 100%);
  color: #f8fafc;
}

.cell-meta { display: flex; align-items: center; gap: 12px; }
.cell-name { display: flex; align-items: center; gap: 6px; font-weight: 600; color: var(--el-text-color-primary); }
html.dark .cell-name { color: #e2e8f0; }

.cam-icon { color: #3b82f6; }
.cell-time { color: var(--el-text-color-regular); font-size: 12px; font-variant-numeric: tabular-nums; letter-spacing: 1px; }
.cell-actions { display: flex; align-items: center; gap: 8px; }
.fullscreen-btn { color: var(--el-text-color-regular); }
.fullscreen-btn:hover { color: #3b82f6; }
.stream-img { width: 100%; height: 100%; flex: 1; display: block; object-fit: cover; }
.offline-placeholder {
  height: 100%; flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: var(--el-text-color-placeholder);
  background: repeating-linear-gradient(45deg, rgba(0,0,0,0.02) 0, rgba(0,0,0,0.02) 10px, transparent 10px, transparent 20px);
}
html.dark .offline-placeholder {
  background: repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0, rgba(255,255,255,0.02) 10px, transparent 10px, transparent 20px);
}

.video-cell:fullscreen { width: 100vw; height: 100vh; aspect-ratio: auto; }

/* 告警中心弹窗 */
html.dark :deep(.theme-drawer .el-drawer__body) { background: #0b1120; }
html.dark :deep(.theme-drawer .el-drawer__header) {
  margin-bottom: 0; padding: 16px 20px; background: #0f172a; color: #f8fafc; border-bottom: 1px solid rgba(255,255,255,0.05);
}

.glass-img { width: 100%; border-radius: 8px; max-height: 240px; object-fit: cover; border: 1px solid var(--el-border-color-light); }
html.dark .glass-img { border: 1px solid rgba(255, 255, 255, 0.1); }

.alert-feed { display: flex; flex-direction: column; gap: 10px; max-height: 50vh; overflow-y: auto; padding-right: 8px; }
.feed-item {
  border-radius: 8px; padding: 12px 14px; display: flex; justify-content: space-between; align-items: center;
  cursor: pointer; transition: all 0.2s ease;
}
.feed-item:hover { background: var(--el-color-primary-light-9); border-color: var(--el-color-primary-light-7); }
html.dark  .feed-item:hover { background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.3); }

.feed-item.active {
  background: var(--el-color-danger-light-9); border-color: #ef4444; box-shadow: 0 0 15px rgba(239, 68, 68, 0.1);
}
html.dark .feed-item.active {
  background: rgba(239, 68, 68, 0.15); box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);
}

.feed-title { font-weight: 600; color: var(--el-text-color-primary); font-size: 14px; }
html.dark .feed-title { color: #e2e8f0; }

.feed-time { font-size: 12px; color: var(--el-text-color-regular); margin-top: 4px; }
.feed-right { display: flex; align-items: center; gap: 10px; }
.feed-conf { color: var(--el-text-color-regular); font-size: 13px; font-weight: 500; min-width: 42px; text-align: right; }
</style>
