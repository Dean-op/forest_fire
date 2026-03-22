<template>
  <div class="stats-container" v-loading="loading">
    <div class="kpi-grid">
      <div class="kpi-card" v-for="(kpi, idx) in kpiList" :key="idx" :style="{ background: kpi.bg }">
        <div class="kpi-icon">{{ kpi.icon }}</div>
        <div class="kpi-info">
          <div class="kpi-value">
            <span class="count-up">{{ kpi.value }}</span>
            <span class="kpi-unit" v-if="kpi.unit">{{ kpi.unit }}</span>
          </div>
          <div class="kpi-label">{{ kpi.label }}</div>
        </div>
      </div>
    </div>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="16">
        <div class="chart-card glass-card">
          <div class="chart-title">📈 近 7 天告警趋势（堆叠面积）</div>
          <div ref="trendChart" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="chart-card glass-card">
          <div class="chart-title">🍩 告警类别占比</div>
          <div ref="pieChart" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="8">
        <div class="chart-card glass-card">
          <div class="chart-title">🎯 设备在线率</div>
          <div ref="gaugeChart" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="chart-card glass-card">
          <div class="chart-title">🕐 24 小时告警热力分布</div>
          <div ref="hourlyChart" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="chart-card glass-card">
          <div class="chart-title">🔬 YOLO 置信度分布</div>
          <div ref="confChart" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="10">
        <div class="chart-card glass-card" style="padding: 20px;">
          <div class="chart-title" style="margin-bottom: 15px; padding: 0;">📷 设备状态一览</div>
          <div class="device-grid">
            <div v-for="cam in stats.camera_list" :key="cam.name" class="device-item">
              <div class="device-dot" :class="cam.status"></div>
              <div class="device-info">
                <div class="device-name">{{ cam.name }}</div>
                <div class="device-loc">{{ cam.location }}</div>
              </div>
              <el-tag :type="cam.status==='online'?'success':'danger'" effect="dark" size="small">
                {{ cam.status==='online'?'在线':'离线' }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="14">
        <div class="chart-card glass-card" style="padding: 20px;">
          <div class="chart-title" style="margin-bottom: 15px; padding: 0;">🔥 最近告警动态</div>
          <el-table :data="stats.recent_alerts" stripe size="small" class="transparent-table">
            <el-table-column prop="id" label="#" width="50" />
            <el-table-column prop="timestamp" label="时间" width="140" />
            <el-table-column prop="confidence" label="置信度" width="120">
              <template #default="{ row }">
                <el-progress 
                  :percentage="Math.round(row.confidence * 100)"
                  :color="row.confidence > 0.85 ? '#F56C6C' : row.confidence > 0.7 ? '#E6A23C' : '#67C23A'"
                  :stroke-width="10" :text-inside="true" style="width: 100%;"
                />
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" effect="dark" size="small">
                  {{ statusTagLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue'
import api from '../api'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useThemeStore } from '../stores/theme'

const themeStore = useThemeStore()

const loading = ref(false)
const stats = ref({
  total_alerts: 0, confirmed: 0, false_alarm: 0, pending: 0,
  total_cameras: 0, online_cameras: 0, online_rate: 0,
  avg_confidence: 0, accuracy: 0,
  trend: [], hourly: [], confidence_distribution: {},
  camera_list: [], recent_alerts: []
})

const trendChart = ref(null)
const pieChart = ref(null)
const gaugeChart = ref(null)
const hourlyChart = ref(null)
const confChart = ref(null)

let charts = []

const kpiList = computed(() => [
  { icon: '🔥', value: stats.value.total_alerts, label: '总告警次数', bg: 'linear-gradient(135deg, #1e3a8a 0%, #312e81 100%)' },
  { icon: '🚨', value: stats.value.confirmed, label: '确认火灾', bg: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)' },
  { icon: '✅', value: stats.value.false_alarm, label: '误报次数', bg: 'linear-gradient(135deg, #164e63 0%, #0c4a6e 100%)' },
  { icon: '⏳', value: stats.value.pending, label: '待核实/处置', bg: 'linear-gradient(135deg, #78350f 0%, #a16207 100%)' },
  { icon: '🎯', value: stats.value.avg_confidence, label: '平均置信度', bg: 'linear-gradient(135deg, #4c1d95 0%, #5b21b6 100%)' },
  { icon: '📊', value: stats.value.accuracy, unit: '%', label: '检测精准率', bg: 'linear-gradient(135deg, #064e3b 0%, #065f46 100%)' },
])

const statusTagLabel = (status) => ({
  pending: '待核实',
  pending_verify: '待核实',
  confirmed: '真火',
  verified_true: '真火',
  dispatched: '已联动',
  resolved: '已完成',
  false_alarm: '误报',
  verified_false: '误报'
}[status] || status)

const statusTagType = (status) => ({
  pending: 'warning',
  pending_verify: 'warning',
  confirmed: 'danger',
  verified_true: 'danger',
  dispatched: 'danger',
  resolved: 'success',
  false_alarm: 'info',
  verified_false: 'info'
}[status] || 'info')

const fetchStats = async () => {
  loading.value = true
  try {
    const res = await api.get('/supervisor/stats')
    stats.value = res
    await nextTick()
    renderCharts(res)
  } catch (e) {
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

watch(() => themeStore.isDark, () => {
  if (stats.value.total_alerts !== undefined) {
    nextTick(() => renderCharts(stats.value))
  }
})

const renderCharts = (data) => {
  charts.forEach(c => c.dispose())
  charts = []

  const themeStr = themeStore.isDark ? 'dark' : null
  
  const t = echarts.init(trendChart.value, themeStr)
  charts.push(t)
  t.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['真实火灾', '误报', '总计'], bottom: 0 },
    grid: { top: 20, right: 20, bottom: 50, left: 50 },
    xAxis: { type: 'category', data: data.trend.map(t => t.date), boundaryGap: false },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '真实火灾', type: 'line', stack: 'a', smooth: true, areaStyle: { opacity: 0.5 }, lineStyle: { width: 2 }, itemStyle: { color: '#F56C6C' }, data: data.trend.map(t => t.confirmed) },
      { name: '误报', type: 'line', stack: 'a', smooth: true, areaStyle: { opacity: 0.4 }, lineStyle: { width: 2 }, itemStyle: { color: '#909399' }, data: data.trend.map(t => t.false_alarm) },
      { name: '总计', type: 'line', smooth: true, lineStyle: { width: 3, type: 'dashed' }, itemStyle: { color: '#409EFF' }, data: data.trend.map(t => t.total) },
    ]
  })

  const p = echarts.init(pieChart.value, themeStr)
  charts.push(p)
  p.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['30%', '70%'], center: ['50%', '48%'],
      roseType: 'area',
      itemStyle: { borderRadius: 8 },
      data: [
        { value: data.confirmed, name: '真实火灾', itemStyle: { color: '#F56C6C' } },
        { value: data.false_alarm, name: '误报', itemStyle: { color: '#909399' } },
        { value: data.pending, name: '待处理', itemStyle: { color: '#E6A23C' } },
      ],
      label: { formatter: '{b}\n{d}%', fontSize: 12 },
      animationType: 'scale', animationEasing: 'elasticOut'
    }]
  })

  const g = echarts.init(gaugeChart.value, themeStr)
  charts.push(g)
  g.setOption({
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge', 
      startAngle: 200, endAngle: -20,
      min: 0, max: 100,
      progress: { show: true, width: 18 },
      pointer: { show: false },
      axisLine: { lineStyle: { width: 18 } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      title: { offsetCenter: [0, '30%'], fontSize: 14, color: '#94a3b8' },
      detail: { 
        valueAnimation: true, fontSize: 36, fontWeight: 'bold',
        offsetCenter: [0, '-10%'],
        formatter: '{value}%',
        color: data.online_rate > 80 ? '#67C23A' : data.online_rate > 50 ? '#E6A23C' : '#F56C6C'
      },
      data: [{ value: data.online_rate, name: `${data.online_cameras}/${data.total_cameras} 台在线` }],
      itemStyle: {
        color: {
          type: 'linear', x: 0, y: 1, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#67C23A' },
            { offset: 1, color: '#409EFF' }
          ]
        }
      }
    }]
  })

  const h = echarts.init(hourlyChart.value, themeStr)
  charts.push(h)
  h.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', formatter: '{b}时: {c} 次' },
    grid: { top: 15, right: 15, bottom: 30, left: 35 },
    xAxis: { 
      type: 'category', 
      data: Array.from({ length: 24 }, (_, i) => `${i}`),
      axisLabel: { interval: 2, fontSize: 10 }
    },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 10 } },
    series: [{
      type: 'bar', barWidth: '60%',
      data: data.hourly,
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: (params) => {
          const colors = [
            { offset: 0, color: '#1890ff' },
            { offset: 1, color: '#70d6ff' }
          ]
          if (params.value > 2) {
            colors[0].color = '#ff4d4f'
            colors[1].color = '#ff9a9e'
          }
          return new echarts.graphic.LinearGradient(0, 0, 0, 1, colors)
        }
      }
    }]
  })

  const cf = echarts.init(confChart.value, themeStr)
  charts.push(cf)
  const confData = data.confidence_distribution
  cf.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { top: 15, right: 15, bottom: 30, left: 35 },
    xAxis: { type: 'category', data: Object.keys(confData), axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 10 } },
    series: [{
      type: 'bar', barWidth: '50%',
      data: Object.values(confData),
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: (params) => {
          const colorList = ['#91cc75', '#fac858', '#ee6666', '#cc0000']
          return colorList[params.dataIndex] || '#409EFF'
        }
      },
      label: { show: true, position: 'top', fontSize: 12, fontWeight: 'bold' }
    }]
  })

  window.addEventListener('resize', handleResize)
}

const handleResize = () => charts.forEach(c => c.resize())

onMounted(fetchStats)
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  charts.forEach(c => c.dispose())
})
</script>

<style scoped>
.stats-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
}

.kpi-card {
  border-radius: 12px;
  padding: 18px 16px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: default;
}
html.dark .kpi-card { box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4); border: 1px solid rgba(255,255,255,0.05); }

.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
}
html.dark .kpi-card:hover { box-shadow: 0 10px 24px rgba(0, 0, 0, 0.6); }

.kpi-icon { font-size: 32px; flex-shrink: 0; }
.kpi-value { font-size: 28px; font-weight: 800; line-height: 1; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.kpi-unit { font-size: 16px; font-weight: 400; opacity: 0.8; }
.kpi-label { font-size: 12px; opacity: 0.9; margin-top: 4px; }

/* Light/Dark Cards */
.glass-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
html.dark .glass-card {
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.chart-title {
  padding: 16px 20px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  letter-spacing: 0.5px;
}

.chart-body {
  height: 280px;
  padding: 8px;
}

.device-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 380px;
  overflow-y: auto;
  padding-right: 8px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  transition: all 0.2s;
}
html.dark .device-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.device-item:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}
html.dark .device-item:hover {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

.device-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.device-dot.online {
  background: #67C23A;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.6);
  animation: pulse 2s infinite;
}
.device-dot.offline { background: #F56C6C; }

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 4px rgba(103, 194, 58, 0.4); }
  50% { box-shadow: 0 0 12px rgba(103, 194, 58, 0.8); }
}

.device-info { flex: 1; }
.device-name { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); }
.device-loc { font-size: 12px; color: var(--el-text-color-regular); margin-top: 2px; }

:deep(.transparent-table.el-table) {
  background-color: transparent !important;
  color: var(--el-text-color-primary);
}
:deep(.transparent-table .el-table__cell) { background-color: transparent !important; }
</style>
