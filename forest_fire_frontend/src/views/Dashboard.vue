<template>
  <div class="dashboard-container">
    <div class="header-tools">
      <h2>🔥 智能监控大屏 (双核预警)</h2>
      <div style="display: flex; gap: 15px; align-items: center;">
        <el-button v-if="latestAlert" type="danger" @click="showAlertDrawer = true" class="pulse-btn">
          <el-icon><Warning /></el-icon> 查看最新告警
        </el-button>
        <el-tag type="success" v-if="wsConnected">实时告警连接正常</el-tag>
        <el-tag type="danger" v-else>告警连接断开</el-tag>
      </div>
    </div>

    <!-- 告警弹出抽屉 -->
    <el-drawer
      v-model="showAlertDrawer"
      title="最新火情告警"
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
            <el-tag :type="latestAlert.llm_result?.includes('火') ? 'danger' : 'warning'">
              {{ latestAlert.llm_result || '正在分析中...' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>

    <!-- 动态瀑布流视频墙 -->
    <div class="video-grid" :class="{'many-cams': cameras.length > 4}" v-loading="loading">
      <template v-if="cameras.length > 0">
        <div class="video-cell" v-for="cam in cameras" :key="cam.id" :class="{ 'offline': cam.status !== 'online' }">
          <div class="cell-title">
            <el-icon><VideoCamera /></el-icon> {{ cam.name }}
            <el-tag size="small" :type="cam.status==='online'?'success':'info'" style="float:right;">
              {{ cam.status==='online'?'在线':'离线' }}
            </el-tag>
          </div>
          <!-- 在线设备请求后端真实的带 YOLO 的视频流 -->
          <img v-if="cam.status === 'online'" :src="`http://localhost:8000/api/stream/video/${cam.id}`" class="stream-img" :alt="cam.name" />
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
import { ref, onMounted, onUnmounted } from 'vue'
import { ElNotification, ElMessage } from 'element-plus'
import { VideoCamera, VideoPause, Warning } from '@element-plus/icons-vue'
import api from '../api'

const wsConnected = ref(false)
const ws = ref(null)
const showAlertDrawer = ref(false)
const latestAlert = ref(null)
let notifyInstance = null // 保存单例通知，防止弹窗风暴

const cameras = ref([])
const loading = ref(false)

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
  ws.value = new WebSocket('ws://localhost:8000/ws/alerts')
  
  ws.value.onopen = () => {
    wsConnected.value = true
  }
  
  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      latestAlert.value = data
      
      // 关闭上一个通知，保证屏幕上只有一个通知（消除弹窗风暴）
      if (notifyInstance) {
        notifyInstance.close()
      }
      
      notifyInstance = ElNotification({
        title: `🚨 最新警报: ${data.camera_name || '设备'}`,
        message: `在 ${data.timestamp} 检测到异常。\n点击此处查看抓拍详情`,
        type: 'error',
        duration: 8000,
        position: 'top-right',
        onClick: () => {
          showAlertDrawer.value = true
          if (notifyInstance) notifyInstance.close()
        }
      })
      
      // 牺牲强制提醒：不再自动弹出侧边抽屉打断用户看监控
      // showAlertDrawer.value = true
    } catch (e) {
      console.error("解析 WebSocket 数据失败:", e)
    }
  }
  
  ws.value.onclose = () => {
    wsConnected.value = false
    setTimeout(initWebSocket, 3000)
  }
}

onMounted(() => {
  fetchCameras()
  initWebSocket()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  height: 100%;
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
  align-items: center;
  gap: 6px;
}

.stream-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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

@keyframes pulse {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.7); }
  70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(245, 108, 108, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(245, 108, 108, 0); }
}
</style>
