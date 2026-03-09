<template>
  <div class="dashboard-container">
    <div v-if="fireFlashActive" class="fire-flash-overlay"></div>

    <div class="header-tools">
      <h2>智能监控大屏（双核预警）</h2>
      <div class="header-right">
        <el-button v-if="latestAlert" type="danger" @click="openAlertCenter" class="pulse-btn">
          <el-icon><Warning /></el-icon>
          告警中心
          <el-tag v-if="unreadCount > 0" size="small" type="warning" effect="dark" class="unread-tag">
            {{ unreadCount }}
          </el-tag>
        </el-button>
        <el-tag type="success" v-if="wsConnected">告警连接正常</el-tag>
        <el-tag type="danger" v-else>告警连接中断</el-tag>
      </div>
    </div>

    <transition name="banner-fade">
      <el-alert
        v-if="burstBanner.visible && !showAlertDrawer"
        :type="burstBanner.level"
        show-icon
        :closable="false"
        class="burst-banner"
      >
        <template #title>
          最近 12 秒新增 {{ burstBanner.count }} 条告警，最新来自 {{ burstBanner.lastCamera }}
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
    >
      <div v-if="latestAlert" class="alert-detail">
        <el-alert title="检测到疑似火情" type="error" show-icon :closable="false" style="margin-bottom: 15px" />
        <img :src="latestAlert.image_path" class="alert-image" alt="告警截图" />
        <el-descriptions :column="1" border style="margin-top: 15px">
          <el-descriptions-item label="报警设备">{{ latestAlert.camera_name || '未知设备' }}</el-descriptions-item>
          <el-descriptions-item label="发生时间">{{ latestAlert.timestamp }}</el-descriptions-item>
          <el-descriptions-item label="YOLO 置信度">
            {{ ((latestAlert.yolo_confidence || 0) * 100).toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="大模型复核">
            <el-tag :type="statusTypeSafe(latestAlert.status)">{{ latestAlert.llm_result || '正在分析中...' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusTypeSafe(latestAlert.status)">{{ statusLabelSafe(latestAlert.status) }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <el-empty v-else description="暂无告警" />

      <el-divider content-position="left">告警时间线</el-divider>
      <div v-if="alertFeed.length > 0" class="alert-feed">
        <div
          v-for="item in alertFeed"
          :key="item._key"
          class="feed-item"
          :class="{ active: latestAlert && latestAlert._key === item._key }"
          @click="selectAlert(item)"
        >
          <div class="feed-left">
            <div class="feed-title">{{ item.camera_name || '未知设备' }}</div>
            <div class="feed-time">{{ item.timestamp }}</div>
          </div>
          <div class="feed-right">
            <el-tag size="small" :type="statusTypeSafe(item.status)">{{ statusLabelSafe(item.status) }}</el-tag>
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
          class="video-cell"
          :class="{ offline: cam.status !== 'online' }"
        >
          <div class="cell-title">
            <div class="cell-meta">
              <div class="cell-name">
                <el-icon><VideoCamera /></el-icon>
                {{ cam.name }}
              </div>
              <div class="cell-time">{{ displayTime }}</div>
            </div>
            <div class="cell-actions">
              <el-tag size="small" :type="cam.status === 'online' ? 'success' : 'info'">
                {{ cam.status === 'online' ? '在线' : '离线' }}
              </el-tag>
              <el-button text class="fullscreen-btn" @click.stop="toggleFullscreen(cam.id)" title="全屏/退出全屏">
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </div>
          </div>

          <img v-if="cam.status === 'online'" :src="streamUrl(cam.id)" class="stream-img" :alt="cam.name" />
          <div v-else class="offline-placeholder">
            <el-icon size="48" color="#909399"><VideoPause /></el-icon>
            <p>设备已离线</p>
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
import { FullScreen, VideoCamera, VideoPause, Warning } from '@element-plus/icons-vue'
import api from '../api'

const wsConnected = ref(false)
const ws = ref(null)
const showAlertDrawer = ref(false)
const latestAlert = ref(null)
const alertFeed = ref([])
const unreadCount = ref(0)
const fireFlashActive = ref(false)
const burstBanner = ref({
  visible: false,
  count: 0,
  lastCamera: '',
  lastAt: '',
  level: 'warning'
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
const alarmAudioUrl = ref('/api/admin/public/alarm-audio')
let alarmAudio = null

const statusLabel = (status) => {
  const map = {
    pending: '待核实',
    pending_verify: '待核实',
    confirmed: '已核实真实火灾',
    verified_true: '已核实真实火灾',
    false_alarm: '已核实误报',
    verified_false: '已核实误报',
    dispatched: '已联动消防',
    resolved: '已处理'
  }
  return map[status] || status || '待核实'
}

const statusType = (status) => {
  if (['confirmed', 'verified_true', 'dispatched', 'resolved'].includes(status)) return 'danger'
  if (['false_alarm', 'verified_false', 'archived_low'].includes(status)) return 'info'
  return 'warning'
}

const statusLabelSafe = (status) => {
  if (status === 'reviewing_llm') return 'LLM复核中'
  if (status === 'archived_low') return '低风险归档'
  return statusLabel(status)
}

const statusTypeSafe = (status) => statusType(status)

const displayTime = computed(() => new Date(nowTick.value).toLocaleString('zh-CN', { hour12: false }))

const streamUrl = (cameraId) => `/api/stream/video/${cameraId}`

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
    if (promise && typeof promise.catch === 'function') {
      promise.catch(() => {})
    }
  } catch {
    // Browser auto-play policies can block this; ignore silently.
  }
}

const fetchRuntimeConfig = async () => {
  try {
    const cfg = await api.get('/admin/public/system-name')
    alertSoundEnabled.value = toBool(cfg?.alert_sound, true)
    if (cfg?.alarm_audio_url) {
      alarmAudioUrl.value = cfg.alarm_audio_url
    }
  } catch {
    alertSoundEnabled.value = true
  } finally {
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
    if (document.fullscreenElement === cell) {
      await document.exitFullscreen()
      return
    }
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    }
    await cell.requestFullscreen()
  } catch {
    ElMessage.warning('全屏切换失败，请检查浏览器权限')
  }
}

const openAlertCenter = () => {
  showAlertDrawer.value = true
  unreadCount.value = 0
}

const selectAlert = (item) => {
  latestAlert.value = item
}

const getAlertKey = (data) => {
  if (data.id !== undefined && data.id !== null) return `id:${data.id}`
  return `${data.camera_name || 'unknown'}-${data.timestamp || ''}`
}

const shouldAcceptAlertGlobal = (key) => {
  const nowTs = Date.now()
  if (!window.__ff_seen_alert_map) {
    window.__ff_seen_alert_map = {}
  }
  const seenTs = window.__ff_seen_alert_map[key]
  if (seenTs && nowTs - seenTs < GLOBAL_SEEN_TTL_MS) {
    return false
  }
  window.__ff_seen_alert_map[key] = nowTs
  return true
}

const cleanupSeenAlerts = (nowTs) => {
  for (const [key, ts] of seenAlertMap.entries()) {
    if (nowTs - ts > ALERT_SEEN_TTL_MS) {
      seenAlertMap.delete(key)
    }
  }

  if (!window.__ff_seen_alert_map) return
  Object.keys(window.__ff_seen_alert_map).forEach((key) => {
    if (nowTs - window.__ff_seen_alert_map[key] > GLOBAL_SEEN_TTL_MS) {
      delete window.__ff_seen_alert_map[key]
    }
  })
}

const upsertAlertFeed = (alert, key) => {
  const idx = alertFeed.value.findIndex((item) => item._key === key)
  const merged = { ...(idx >= 0 ? alertFeed.value[idx] : {}), ...alert, _key: key }

  if (idx >= 0) {
    alertFeed.value[idx] = merged
    // Move updated alert to top for timeline readability.
    alertFeed.value.unshift(alertFeed.value.splice(idx, 1)[0])
  } else {
    alertFeed.value.unshift(merged)
    if (alertFeed.value.length > ALERT_FEED_LIMIT) {
      alertFeed.value.length = ALERT_FEED_LIMIT
    }
  }

  latestAlert.value = merged
}

const touchBurstBanner = (alert) => {
  burstBanner.value.visible = true
  burstBanner.value.count += 1
  burstBanner.value.lastCamera = alert.camera_name || '未知设备'
  burstBanner.value.lastAt = alert.timestamp || ''
  burstBanner.value.level = ['confirmed', 'verified_true', 'dispatched', 'resolved'].includes(alert.status) ? 'error' : 'warning'

  if (burstBannerTimer) {
    clearTimeout(burstBannerTimer)
  }
  burstBannerTimer = setTimeout(() => {
    burstBanner.value.visible = false
    burstBanner.value.count = 0
  }, BURST_BANNER_HIDE_MS)
}

const triggerFireFlash = (alert) => {
  const highRiskStatuses = ['pending_verify', 'confirmed', 'verified_true', 'dispatched', 'resolved']
  if (!highRiskStatuses.includes(alert.status)) return
  fireFlashActive.value = true
  if (fireFlashTimer) {
    clearTimeout(fireFlashTimer)
  }
  fireFlashTimer = setTimeout(() => {
    fireFlashActive.value = false
  }, 5000)
}

const clearReconnectTimer = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

const fetchCameras = async () => {
  loading.value = true
  try {
    const res = await api.get('/supervisor/cameras')
    cameras.value = Array.isArray(res) ? res : []
  } catch {
    ElMessage.error('无法获取设备列表')
  } finally {
    loading.value = false
  }
}

const initWebSocket = () => {
  if (!isComponentAlive) return
  if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) return

  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  isManualClosing = false
  ws.value = new WebSocket(`${protocol}://${window.location.host}/ws/alerts`)

  ws.value.onopen = () => {
    wsConnected.value = true
  }

  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      const nowTs = Date.now()
      cleanupSeenAlerts(nowTs)

      const key = getAlertKey(data)
      const isNewAlert = !seenAlertMap.has(key)
      if (isNewAlert) {
        seenAlertMap.set(key, nowTs)
      }

      upsertAlertFeed(data, key)

      // Same alert in current page lifecycle only updates timeline; no repeat remind.
      if (!isNewAlert) return
      // Cross reconnect/global dedupe.
      if (!shouldAcceptAlertGlobal(key)) return

      unreadCount.value += 1
      touchBurstBanner(data)
      triggerFireFlash(data)
      playAlarmSound()
    } catch (error) {
      console.error('解析 WebSocket 数据失败:', error)
    }
  }

  ws.value.onclose = () => {
    wsConnected.value = false
    ws.value = null
    if (!isComponentAlive || isManualClosing) return

    clearReconnectTimer()
    reconnectTimer = setTimeout(() => {
      initWebSocket()
    }, 3000)
  }
}

onMounted(async () => {
  isComponentAlive = true
  clockTimer = setInterval(() => {
    nowTick.value = Date.now()
  }, 1000)

  await fetchRuntimeConfig()
  await fetchCameras()
  initWebSocket()
})

onUnmounted(() => {
  isComponentAlive = false
  isManualClosing = true
  clearReconnectTimer()

  if (ws.value) {
    ws.value.onclose = null
    ws.value.close()
    ws.value = null
  }

  if (burstBannerTimer) {
    clearTimeout(burstBannerTimer)
    burstBannerTimer = null
  }
  if (fireFlashTimer) {
    clearTimeout(fireFlashTimer)
    fireFlashTimer = null
  }
  if (clockTimer) {
    clearInterval(clockTimer)
    clockTimer = null
  }
  if (alarmAudio) {
    alarmAudio.pause()
    alarmAudio = null
  }

  cellRefs.clear()
})
</script>

<style scoped>
.dashboard-container {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.fire-flash-overlay {
  position: absolute;
  inset: 0;
  z-index: 30;
  pointer-events: none;
  background: radial-gradient(circle at 50% 40%, rgba(255, 60, 60, 0.28) 0%, rgba(255, 60, 60, 0.08) 35%, transparent 72%);
  animation: fire-flash 0.8s ease-in-out infinite;
}

.header-tools {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.header-tools h2 {
  margin: 0;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.burst-banner {
  margin-bottom: 12px;
}

.banner-time {
  color: #909399;
  font-size: 12px;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  align-content: start;
}

.video-grid.many-cams {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.video-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  overflow: hidden;
  background: #0f131b;
  aspect-ratio: 16 / 10;
  min-height: 240px;
  border: 1px solid #dcdfe6;
}

.cell-title {
  height: 38px;
  padding: 0 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
  background: rgba(0, 0, 0, 0.65);
  font-size: 13px;
}

.cell-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.cell-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  white-space: nowrap;
}

.cell-time {
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.cell-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.fullscreen-btn {
  color: #fff;
}

.stream-img {
  width: 100%;
  height: auto;
  min-height: 0;
  flex: 1;
  display: block;
  object-fit: cover;
}

.offline-placeholder {
  height: auto;
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.video-cell:fullscreen {
  width: 100vw;
  height: 100vh;
  aspect-ratio: auto;
}

.alert-detail {
  margin-bottom: 6px;
}

.alert-image {
  width: 100%;
  border-radius: 8px;
  display: block;
  max-height: 220px;
  object-fit: cover;
  border: 1px solid #ebeef5;
}

.alert-feed {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow-y: auto;
}

.feed-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.feed-item:hover {
  background: #f5f7fa;
}

.feed-item.active {
  border-color: #f56c6c;
  background: #fff1f0;
}

.feed-title {
  font-weight: 600;
  color: #303133;
}

.feed-time {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.feed-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feed-conf {
  color: #606266;
  font-size: 12px;
  min-width: 42px;
  text-align: right;
}

.unread-tag {
  margin-left: 8px;
}

.pulse-btn {
  animation: pulse-red 1.6s infinite;
}

@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.45); }
  70% { box-shadow: 0 0 0 10px rgba(245, 108, 108, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0); }
}

@keyframes fire-flash {
  0% { opacity: 0.25; }
  50% { opacity: 0.6; }
  100% { opacity: 0.25; }
}

.banner-fade-enter-active,
.banner-fade-leave-active {
  transition: opacity 0.25s ease;
}

.banner-fade-enter-from,
.banner-fade-leave-to {
  opacity: 0;
}

@media (max-width: 1200px) {
  .video-grid,
  .video-grid.many-cams {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .header-tools {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .video-grid,
  .video-grid.many-cams {
    grid-template-columns: 1fr;
  }
}
</style>
