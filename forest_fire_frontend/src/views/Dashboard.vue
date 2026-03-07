<template>
  <div class="dashboard-container">
    <div v-if="fireFlashActive" class="fire-flash-overlay"></div>
    <div class="header-tools">
      <h2>🔥 智能监控大屏 (双核预警)</h2>
      <div style="display: flex; gap: 15px; align-items: center;">
        <el-button v-if="latestAlert" type="danger" @click="openAlertCenter" class="pulse-btn">
          <el-icon><Warning /></el-icon> 告警中心
          <el-tag
            v-if="unreadCount > 0"
            size="small"
            type="warning"
            effect="dark"
            class="unread-tag"
          >
            {{ unreadCount }}
          </el-tag>
        </el-button>
        <el-tag type="success" v-if="wsConnected">实时告警连接正常</el-tag>
        <el-tag type="danger" v-else>告警连接断开</el-tag>
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
          近12秒新增 {{ burstBanner.count }} 条告警，最新来自 {{ burstBanner.lastCamera }}
          <span v-if="burstBanner.lastAt" class="banner-time">（{{ burstBanner.lastAt }}）</span>
        </template>
        <template #default>
          已聚合到告警中心，点击右上角“告警中心”查看详情。
        </template>
      </el-alert>
    </transition>

    <!-- 告警中心抽屉 -->
    <el-drawer
      v-model="showAlertDrawer"
      :title="`告警中心（最近 ${alertFeed.length} 条）`"
      direction="rtl"
      size="40%"
    >
      <div v-if="latestAlert" class="alert-detail">
        <el-alert title="检测到疑似火灾！" type="error" show-icon :closable="false" style="margin-bottom: 15px;" />
        <img :src="latestAlert.image_path" class="alert-image" />
        <el-descriptions :column="1" border style="margin-top: 15px;">
          <el-descriptions-item label="报警设备">{{ latestAlert.camera_name || '未知设备' }}</el-descriptions-item>
          <el-descriptions-item label="发生时间">{{ latestAlert.timestamp }}</el-descriptions-item>
          <el-descriptions-item label="YOLO 置信度">{{ (latestAlert.yolo_confidence * 100).toFixed(1) }}%</el-descriptions-item>
          <el-descriptions-item label="大模型复核">
            <el-tag :type="statusType(latestAlert.status)">
              {{ latestAlert.llm_result || '正在分析中...' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusType(latestAlert.status)">
              {{ statusLabel(latestAlert.status) }}
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
          class="feed-item"
          :class="{ active: latestAlert && latestAlert._key === item._key }"
          @click="selectAlert(item)"
        >
          <div class="feed-left">
            <div class="feed-title">{{ item.camera_name || '未知设备' }}</div>
            <div class="feed-time">{{ item.timestamp }}</div>
          </div>
          <div class="feed-right">
            <el-tag size="small" :type="statusType(item.status)">
              {{ statusLabel(item.status) }}
            </el-tag>
            <span class="feed-conf">{{ Math.round((item.yolo_confidence || 0) * 100) }}%</span>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无时间线数据" />
    </el-drawer>

    <!-- 动态瀑布流视频墙 -->
    <div class="video-grid" :class="{'many-cams': cameras.length > 4}" v-loading="loading">
      <template v-if="cameras.length > 0">
        <div
          class="video-cell"
          v-for="cam in cameras"
          :key="cam.id"
          :ref="el => setCellRef(cam.id, el)"
          :class="{ 'offline': cam.status !== 'online' }"
        >
          <div class="cell-title">
            <div class="cell-meta">
              <div class="cell-name">
                <el-icon><VideoCamera /></el-icon> {{ cam.name }}
              </div>
              <div class="cell-time">{{ displayTime }}</div>
            </div>
            <div class="cell-actions">
              <el-tag size="small" :type="cam.status==='online'?'success':'info'">
                {{ cam.status==='online'?'在线':'离线' }}
              </el-tag>
              <el-button
                text
                class="fullscreen-btn"
                @click.stop="toggleFullscreen(cam.id)"
                title="全屏/退出全屏"
              >
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </div>
          </div>
          <!-- 在线设备请求后端真实的带 YOLO 的视频流 -->
          <img v-if="cam.status === 'online'" :src="streamUrl(cam.id)" class="stream-img" :alt="cam.name" />
          <!-- 离线设备显示占位 -->
          <div v-else class="offline-placeholder">
            <el-icon size="48" color="#909399"><VideoPause /></el-icon>
            <p>设备已离线</p>
          </div>
        </div>
      </template>
      <el-empty v-else description="暂无设备接入，请先在终端添加设备" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera, VideoPause, Warning, FullScreen } from '@element-plus/icons-vue'
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
  level: 'warning',
})

const ALERT_FEED_LIMIT = 30
const ALERT_SEEN_TTL_MS = 30 * 60 * 1000
const GLOBAL_SEEN_TTL_MS = 5 * 60 * 1000
const BURST_BANNER_HIDE_MS = 12000

const seenAlertMap = new Map() // key -> first seen time
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

const statusLabel = (status) => {
  const map = {
    pending: '待核实',
    pending_verify: '待核实',
    confirmed: '已核实真实火灾',
    verified_true: '已核实真实火灾',
    false_alarm: '已核实误报',
    verified_false: '已核实误报',
    dispatched: '已联动消防',
    resolved: '处置已完成'
  }
  return map[status] || status || '待核实'
}

const statusType = (status) => {
  if (['confirmed', 'verified_true', 'dispatched', 'resolved'].includes(status)) return 'danger'
  if (['false_alarm', 'verified_false'].includes(status)) return 'info'
  return 'warning'
}

const displayTime = computed(() => (
  new Date(nowTick.value).toLocaleString('zh-CN', { hour12: false })
))

const streamUrl = (cameraId) => `/api/stream/video/${cameraId}`

const setCellRef = (cameraId, el) => {
  if (el) {
    cellRefs.set(cameraId, el)
  } else {
    cellRefs.delete(cameraId)
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
  const globalMap = window.__ff_seen_alert_map
  const seenTs = globalMap[key]
  if (seenTs && (nowTs - seenTs) < GLOBAL_SEEN_TTL_MS) {
    return false
  }
  globalMap[key] = nowTs
  return true
}

const touchBurstBanner = (alert) => {
  burstBanner.value.visible = true
  burstBanner.value.count += 1
  burstBanner.value.lastCamera = alert.camera_name || '未知设备'
  burstBanner.value.lastAt = alert.timestamp || ''
  burstBanner.value.level = (alert.status === 'pending_verify' && String(alert.llm_result || '').includes('高危')) ? 'error' : 'warning'

  if (burstBannerTimer) {
    clearTimeout(burstBannerTimer)
  }
  burstBannerTimer = setTimeout(() => {
    burstBanner.value.visible = false
    burstBanner.value.count = 0
  }, BURST_BANNER_HIDE_MS)
}

const triggerFireFlash = (alert) => {
  const isHighRiskAi = alert.status === 'pending_verify' && String(alert.llm_result || '').includes('高危')
  const isTrueFireWorkflow = ['confirmed', 'verified_true', 'dispatched', 'resolved'].includes(alert.status)
  if (!isHighRiskAi && !isTrueFireWorkflow) return
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

const cleanupSeenAlerts = (nowTs) => {
  for (const [key, seenTs] of seenAlertMap.entries()) {
    if (nowTs - seenTs > ALERT_SEEN_TTL_MS) {
      seenAlertMap.delete(key)
    }
  }

  if (window.__ff_seen_alert_map) {
    for (const key in window.__ff_seen_alert_map) {
      if ((nowTs - window.__ff_seen_alert_map[key]) > GLOBAL_SEEN_TTL_MS) {
        delete window.__ff_seen_alert_map[key]
      }
    }
  }
}

const upsertAlertFeed = (alert, key) => {
  const idx = alertFeed.value.findIndex(item => item._key === key)
  const merged = { ...(idx >= 0 ? alertFeed.value[idx] : {}), ...alert, _key: key }

  if (idx >= 0) {
    alertFeed.value[idx] = merged
    // 更新后移到顶部，确保时间线优先展示最新状态
    alertFeed.value.unshift(alertFeed.value.splice(idx, 1)[0])
  } else {
    alertFeed.value.unshift(merged)
    if (alertFeed.value.length > ALERT_FEED_LIMIT) {
      alertFeed.value.length = ALERT_FEED_LIMIT
    }
  }

  latestAlert.value = merged
  return idx < 0
}

const fetchCameras = async () => {
  loading.value = true
  try {
    // 操作员也可以看监控设备列表，所以这里调用 supervisor 接口，需要后端放开权限或者前端用已有数据
    const res = await api.get('/supervisor/cameras')
    cameras.value = res
  } catch (e) {
    ElMessage.error('无法获取设备列表')
  } finally {
    loading.value = false
  }
}

const initWebSocket = () => {
  if (!isComponentAlive) return
  if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) {
    return
  }

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

      // 同一实例内重复消息只更新时间线，不重复提醒
      if (!isNewAlert) return

      // 跨实例/重复连接去重：同一 key 仅处理一次提醒
      if (!shouldAcceptAlertGlobal(key)) return

      unreadCount.value += 1
      touchBurstBanner(data)
      triggerFireFlash(data)
    } catch (e) {
      console.error('解析 WebSocket 数据失败:', e)
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

onMounted(() => {
  isComponentAlive = true
  clockTimer = setInterval(() => {
    nowTick.value = Date.now()
  }, 1000)
  fetchCameras()
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

.burst-banner {
  margin-bottom: 12px;
}

.banner-time {
  color: #909399;
  font-size: 12px;
  font-weight: 400;
}

.banner-fade-enter-active,
.banner-fade-leave-active {
  transition: all 0.2s ease;
}

.banner-fade-enter-from,
.banner-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* 动态网格布局：不超过 4 个时自适应 2x2，超过 4 个时变成自动填充的多列瀑布流 */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 15px;
  flex: 1;
  overflow-y: auto;
  align-content: start;
}

.video-grid:not(.many-cams) {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, minmax(300px, 1fr));
}

.video-cell {
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.video-cell.offline {
  background-color: #2c2c2c;
  border: 1px dashed #555;
}

.cell-title {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 14px;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cell-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.cell-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.cell-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.88);
}

.cell-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.fullscreen-btn {
  color: #fff;
  padding: 4px;
}

.fullscreen-btn:hover {
  color: #409EFF;
}

.stream-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-cell:fullscreen {
  border-radius: 0;
}

.video-cell:fullscreen .stream-img {
  object-fit: contain;
}

.offline-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
}

.alert-detail {
  padding: 10px;
}

.alert-image {
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.pulse-btn {
  animation: pulse 2s infinite;
}

.unread-tag {
  margin-left: 8px;
}

.alert-feed {
  max-height: 320px;
  overflow: auto;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.feed-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #f2f6fc;
  cursor: pointer;
  transition: background-color 0.2s;
}

.feed-item:last-child {
  border-bottom: none;
}

.feed-item:hover {
  background-color: #f5f7fa;
}

.feed-item.active {
  background-color: #ecf5ff;
}

.feed-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feed-title {
  font-weight: 600;
  color: #303133;
}

.feed-time {
  font-size: 12px;
  color: #909399;
}

.feed-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feed-conf {
  min-width: 44px;
  text-align: right;
  font-size: 12px;
  color: #606266;
}

@keyframes pulse {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.7); }
  70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(245, 108, 108, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(245, 108, 108, 0); }
}

@keyframes fire-flash {
  0%, 100% { opacity: 0.25; }
  50% { opacity: 0.85; }
}
</style>
