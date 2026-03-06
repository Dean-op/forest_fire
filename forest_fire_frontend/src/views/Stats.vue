<template>
  <div class="stats-container" v-loading="loading">
    <!-- 第一行：6 个渐变 KPI 卡片 -->
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

    <!-- 第二行：趋势面积图 + 占比环形图 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="16">
        <div class="chart-card">
          <div class="chart-title">📈 近 7 天告警趋势（堆叠面积）</div>
          <div ref="trendChart" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="chart-card">
          <div class="chart-title">🍩 告警类别占比</div>
          <div ref="pieChart" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第三行：仪表盘 + 24h 热力柱状图 + 置信度分布 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="8">
        <div class="chart-card">
          <div class="chart-title">🎯 设备在线率</div>
          <div ref="gaugeChart" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="chart-card">
          <div class="chart-title">🕐 24 小时告警热力分布</div>
          <div ref="hourlyChart" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="chart-card">
          <div class="chart-title">🔬 YOLO 置信度分布</div>
          <div ref="confChart" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第四行：设备状态列表 + 最近告警 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="10">
        <div class="chart-card" style="padding: 20px;">
          <div class="chart-title" style="margin-bottom: 15px;">📷 设备状态一览</div>
          <div class="device-grid">
            <div v-for="cam in stats.camera_list" :key="cam.name" class="device-item">
              <div class="device-dot" :class="cam.status"></div>
              <div class="device-info">
                <div class="device-name">{{ cam.name }}</div>
                <div class="device-loc">{{ cam.location }}</div>
              </div>
              <el-tag :type="cam.status==='online'?'success':'danger'" size="small">
                {{ cam.status==='online'?'在线':'离线' }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="14">
        <div class="chart-card" style="padding: 20px;">
          <div class="chart-title" style="margin-bottom: 15px;">🔥 最近告警动态</div>
          <el-table :data="stats.recent_alerts" stripe size="small" style="width:100%">
            <el-table-column prop="id" label="#" width="50" />
            <el-table-column prop="timestamp" label="时间" width="120" />
            <el-table-column prop="confidence" label="置信度" width="100">
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
                <el-tag :type="{pending:'warning',confirmed:'danger',false_alarm:'info'}[row.status]" size="small">
                  {{ {pending:'待处理',confirmed:'真实',false_alarm:'误报'}[row.status] }}
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
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import api from '../api'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

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
  { icon: '🔥', value: stats.value.total_alerts, label: '总告警次数', bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { icon: '🚨', value: stats.value.confirmed, label: '确认火灾', bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { icon: '✅', value: stats.value.false_alarm, label: '误报次数', bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { icon: '⏳', value: stats.value.pending, label: '待处理', bg: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
  { icon: '🎯', value: stats.value.avg_confidence, label: '平均置信度', bg: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)' },
  { icon: '📊', value: stats.value.accuracy, unit: '%', label: '检测精准率', bg: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)' },
])

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

const renderCharts = (data) => {
  charts.forEach(c => c.dispose())
  charts = []

  // 1. 趋势面积图（堆叠）
  const t = echarts.init(trendChart.value)
  charts.push(t)
  t.setOption({
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

  // 2. 南丁格尔玫瑰图
  const p = echarts.init(pieChart.value)
  charts.push(p)
  p.setOption({
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

  // 3. 仪表盘
  const g = echarts.init(gaugeChart.value)
  charts.push(g)
  g.setOption({
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
      title: { offsetCenter: [0, '30%'], fontSize: 14, color: '#666' },
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

  // 4. 24h 渐变柱状图
  const h = echarts.init(hourlyChart.value)
  charts.push(h)
  h.setOption({
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

  // 5. 置信度分布柱状图
  const cf = echarts.init(confChart.value)
  charts.push(cf)
  const confData = data.confidence_distribution
  cf.setOption({
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

  // 全局 resize
  window.addEventListener('resize', () => charts.forEach(c => c.resize()))
}

onMounted(fetchStats)
onUnmounted(() => {
  charts.forEach(c => c.dispose())
})
</script>

<style scoped>
.stats-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* KPI 卡片网格 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
}

.kpi-card {
  border-radius: 14px;
  padding: 18px 16px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: default;
}

.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.25);
}

.kpi-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.kpi-value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
}

.kpi-unit {
  font-size: 16px;
  font-weight: 400;
  opacity: 0.8;
}

.kpi-label {
  font-size: 12px;
  opacity: 0.85;
  margin-top: 4px;
}

/* 图表卡片 */
.chart-row {
  /* el-row handles gutter */
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.chart-title {
  padding: 14px 18px 0;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.chart-body {
  height: 280px;
  padding: 8px;
}

/* 设备状态网格 */
.device-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background: #f5f7fa;
  transition: background 0.2s;
}

.device-item:hover {
  background: #ecf5ff;
}

.device-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.device-dot.online {
  background: #67C23A;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.6);
  animation: pulse 2s infinite;
}

.device-dot.offline {
  background: #F56C6C;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 4px rgba(103, 194, 58, 0.4); }
  50% { box-shadow: 0 0 12px rgba(103, 194, 58, 0.8); }
}

.device-info {
  flex: 1;
}

.device-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.device-loc {
  font-size: 12px;
  color: #909399;
}
</style>
