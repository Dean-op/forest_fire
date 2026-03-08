<template>
  <div class="sys-config-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>系统参数配置</h2>
          <el-tag type="info">仅管理员可修改</el-tag>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="config-tabs" v-loading="loading">
        <el-tab-pane
          v-for="(group, groupName) in groupedConfigs"
          :key="groupName"
          :label="groupLabels[groupName] || groupName"
          :name="groupName"
        >
          <div class="group-head">
            <div class="group-hint">{{ groupHints[groupName] || '参数修改后会立即生效。' }}</div>
            <div v-if="groupName === 'ai'" class="preset-actions">
              <span class="preset-title">推荐预设:</span>
              <el-button size="small" @click="applyAiPreset('performance')">省资源</el-button>
              <el-button size="small" type="primary" @click="applyAiPreset('balanced')">平衡(推荐)</el-button>
              <el-button size="small" type="warning" @click="applyAiPreset('sensitive')">高灵敏</el-button>
            </div>
          </div>

          <div class="config-grid">
            <el-card
              v-for="cfg in group"
              :key="cfg.key"
              class="config-card"
              shadow="never"
            >
              <div class="config-head">
                <div class="config-title-wrap">
                  <div class="config-title">{{ cfg.label || cfg.key }}</div>
                  <div v-if="configMeta[cfg.key]?.desc" class="config-desc">{{ configMeta[cfg.key].desc }}</div>
                </div>
                <el-tag size="small" type="info">{{ cfg.key }}</el-tag>
              </div>

              <template v-if="isRange(cfg.key)">
                <el-slider
                  v-model="cfg.value"
                  :min="configMeta[cfg.key].min"
                  :max="configMeta[cfg.key].max"
                  :step="configMeta[cfg.key].step"
                  show-input
                  :show-input-controls="false"
                />
              </template>

              <template v-else-if="isNumber(cfg.key)">
                <el-input-number
                  v-model="cfg.value"
                  :min="configMeta[cfg.key].min"
                  :max="configMeta[cfg.key].max"
                  :step="configMeta[cfg.key].step || 1"
                  controls-position="right"
                  style="width: 100%"
                />
              </template>

              <template v-else-if="isBoolean(cfg.key)">
                <el-switch
                  v-model="cfg.value"
                  inline-prompt
                  active-text="开"
                  inactive-text="关"
                />
              </template>

              <template v-else>
                <el-input
                  v-model="cfg.value"
                  :type="isSensitive(cfg.key) ? 'password' : 'text'"
                  :show-password="isSensitive(cfg.key)"
                  :disabled="configMeta[cfg.key]?.readonly"
                  clearable
                />
              </template>

              <div class="config-foot">
                <el-button
                  type="primary"
                  :loading="!!savingMap[cfg.key]"
                  :disabled="configMeta[cfg.key]?.readonly"
                  @click="saveConfig(cfg.key, cfg.value)"
                >
                  保存
                </el-button>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const configs = ref([])
const loading = ref(false)
const activeTab = ref('general')
const savingMap = ref({})
const SYSTEM_NAME_STORAGE_KEY = 'system_name'

const groupLabels = {
  general: '通用配置',
  ai: 'YOLO 算法参数',
  llm: '大模型配置'
}

const groupHints = {
  general: '系统名称与常规行为设置。',
  ai: '当前策略：YOLO>=高阈值直接高风险，YOLO<低阈值直接低风险，其余交给LLM复核。',
  llm: '用于二次识别建议，不替代人工处置。'
}

const configMeta = {
  yolo_interval: { type: 'number', min: 0.5, max: 10, step: 0.5, desc: '越大越省资源，但响应越慢。' },
  yolo_infer_scale: { type: 'range', min: 0.2, max: 1.0, step: 0.05, desc: '越小越省算力，但识别细节会下降。' },
  yolo_low_threshold: { type: 'range', min: 0.1, max: 0.8, step: 0.01, desc: '低于该值直接低风险静默归档（Operator不可见）。' },
  yolo_high_threshold: { type: 'range', min: 0.5, max: 0.99, step: 0.01, desc: '高于该值直接高风险进入Operator队列。' },
  alert_cooldown: { type: 'number', min: 3, max: 120, step: 1, desc: '同一路告警触发后冷却时长。' },
  alert_sound: { type: 'boolean', desc: '监控大屏收到新告警时播放警报音。' },
  fire_dispatch_phone: { desc: '消防联动电话，SOP默认自动带入，可按次覆盖。' },
  yolo_model_path: { readonly: true, desc: '当前版本由后端固定模型加载，此项暂不生效。' }
}

const aiPresets = {
  performance: {
    yolo_interval: 2.5,
    yolo_infer_scale: 0.5,
    yolo_low_threshold: 0.4,
    yolo_high_threshold: 0.92,
    alert_cooldown: 12,
  },
  balanced: {
    yolo_interval: 2,
    yolo_infer_scale: 0.6,
    yolo_low_threshold: 0.4,
    yolo_high_threshold: 0.9,
    alert_cooldown: 10,
  },
  sensitive: {
    yolo_interval: 1,
    yolo_infer_scale: 0.8,
    yolo_low_threshold: 0.35,
    yolo_high_threshold: 0.85,
    alert_cooldown: 8,
  }
}

const groupedConfigs = computed(() => {
  const groups = {}
  configs.value.forEach(c => {
    if (!groups[c.group]) groups[c.group] = []
    groups[c.group].push(c)
  })

  const order = ['general', 'ai', 'llm']
  const ordered = {}
  order.forEach(key => {
    if (groups[key]) ordered[key] = groups[key]
  })
  Object.keys(groups).forEach(key => {
    if (!ordered[key]) ordered[key] = groups[key]
  })
  return ordered
})

const isSensitive = (key) => {
  const text = (key || '').toLowerCase()
  return text.includes('key') || text.includes('secret') || text.includes('token')
}

const isNumber = (key) => configMeta[key]?.type === 'number'
const isRange = (key) => configMeta[key]?.type === 'range'
const isBoolean = (key) => configMeta[key]?.type === 'boolean'

const normalizeConfigValues = () => {
  configs.value.forEach(cfg => {
    if (isNumber(cfg.key) || isRange(cfg.key)) {
      cfg.value = Number(cfg.value)
    } else if (isBoolean(cfg.key)) {
      const text = String(cfg.value ?? '').toLowerCase()
      cfg.value = ['true', '1', 'yes', 'on'].includes(text)
    }
  })
}

const fetchConfigs = async () => {
  loading.value = true
  try {
    configs.value = await api.get('/admin/configs')
    normalizeConfigValues()
    if (!groupedConfigs.value[activeTab.value]) {
      activeTab.value = Object.keys(groupedConfigs.value)[0] || 'general'
    }
  } catch {
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

const saveConfig = async (key, value) => {
  savingMap.value[key] = true
  try {
    const normalized = isBoolean(key) ? (value ? 'true' : 'false') : String(value)
    await api.put(`/admin/configs/${key}`, { value: normalized })
    if (key === 'system_name') {
      const name = String(value || '').trim()
      if (name) {
        localStorage.setItem(SYSTEM_NAME_STORAGE_KEY, name)
        window.dispatchEvent(new CustomEvent('system-name-updated', { detail: { name } }))
      }
    }
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingMap.value[key] = false
  }
}

const applyAiPreset = async (presetKey) => {
  const preset = aiPresets[presetKey]
  if (!preset) return

  Object.entries(preset).forEach(([key, value]) => {
    const target = configs.value.find(item => item.key === key)
    if (target) target.value = value
  })

  for (const [key, value] of Object.entries(preset)) {
    await saveConfig(key, value)
  }

  ElMessage.success('已应用 YOLO 预设参数')
}

onMounted(fetchConfigs)
</script>

<style scoped>
.sys-config-container {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h2 {
  margin: 0;
}

.config-tabs {
  margin-top: 8px;
}

.group-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.group-hint {
  color: #606266;
  font-size: 13px;
}

.preset-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preset-title {
  font-size: 12px;
  color: #909399;
}

.config-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 760px;
}

.config-card {
  border: 1px solid #ebeef5;
}

.config-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 10px;
}

.config-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.config-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.config-foot {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

@media (max-width: 900px) {
  .group-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
