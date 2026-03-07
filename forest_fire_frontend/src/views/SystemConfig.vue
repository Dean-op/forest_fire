<template>
  <div class="sys-config-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>⚙️ 系统参数配置</h2>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="config-tabs" v-loading="loading">
        <el-tab-pane
          v-for="(group, groupName) in groupedConfigs"
          :key="groupName"
          :label="groupLabels[groupName] || groupName"
          :name="groupName"
        >
          <div class="group-hint">{{ groupHints[groupName] || '参数修改后立即生效' }}</div>
          <div class="config-grid">
            <el-card
              v-for="cfg in group"
              :key="cfg.key"
              class="config-card"
              shadow="never"
            >
              <div class="config-head">
                <div class="config-title" :title="cfg.label || cfg.key">{{ cfg.label || cfg.key }}</div>
                <el-tag size="small" type="info">{{ cfg.key }}</el-tag>
              </div>

              <el-input
                v-model="cfg.value"
                :type="isSensitive(cfg.key) ? 'password' : 'text'"
                :show-password="isSensitive(cfg.key)"
                clearable
                class="config-input"
              />

              <div class="config-foot">
                <el-button
                  type="primary"
                  :loading="!!savingMap[cfg.key]"
                  @click="saveConfig(cfg.key, cfg.value)"
                >
                  <el-icon><Check /></el-icon> 保存
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
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'

const configs = ref([])
const loading = ref(false)
const activeTab = ref('general')
const savingMap = ref({})
const SYSTEM_NAME_STORAGE_KEY = 'system_name'

const groupLabels = {
  general: '⚙️ 通用基础配置',
  ai: '🧠 YOLO 算法参数',
  llm: '🤖 大语言模型 (LLM) 配置'
}

const groupHints = {
  general: '系统通用行为和展示文案',
  ai: '本地视觉识别与阈值参数',
  llm: '云端模型服务地址、秘钥与模型名'
}

const groupedConfigs = computed(() => {
  const groups = {}
  configs.value.forEach(c => {
    if (!groups[c.group]) groups[c.group] = []
    groups[c.group].push(c)
  })
  
  // 确保标签页的顺序: general -> ai -> llm
  const orderedGroups = {}
  const predefinedOrder = ['general', 'ai', 'llm']
  
  // 先按照预定顺序塞入已有数据的组
  predefinedOrder.forEach(key => {
    if (groups[key]) {
      groups[key].sort((a, b) => (a.label || a.key).localeCompare((b.label || b.key), 'zh-CN'))
      orderedGroups[key] = groups[key]
    }
  })
  
  // 补上其他未知的组
  Object.keys(groups).forEach(key => {
    if (!orderedGroups[key]) {
      groups[key].sort((a, b) => (a.label || a.key).localeCompare((b.label || b.key), 'zh-CN'))
      orderedGroups[key] = groups[key]
    }
  })
  
  return orderedGroups
})

const isSensitive = (key) => {
  const text = (key || '').toLowerCase()
  return text.includes('key') || text.includes('secret') || text.includes('token')
}

const fetchConfigs = async () => {
  loading.value = true
  try {
    configs.value = await api.get('/admin/configs')
    // Set first tab as active automatically if current is empty or invalid
    if (Object.keys(groupedConfigs.value).length > 0 && (!activeTab.value || !groupedConfigs.value[activeTab.value])) {
      activeTab.value = 'general' // 强制默认显示通用配置
      if (!groupedConfigs.value['general']) {
         activeTab.value = Object.keys(groupedConfigs.value)[0]
      }
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
    await api.put(`/admin/configs/${key}`, { value })
    if (key === 'system_name') {
      const name = (value || '').trim()
      if (name) {
        localStorage.setItem(SYSTEM_NAME_STORAGE_KEY, name)
        window.dispatchEvent(new CustomEvent('system-name-updated', { detail: { name } }))
      }
    }
    ElMessage.success('已保存修改')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingMap.value[key] = false
  }
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
  gap: 10px;
}
.card-header h2 {
  margin: 0;
  color: #303133;
}
.header-tip {
  color: #909399;
  font-size: 12px;
}
.config-tabs {
  margin-top: 10px;
}
.group-hint {
  margin-bottom: 12px;
  font-size: 13px;
  color: #606266;
}
.config-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 600px;
}
.config-card {
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
}
.config-head {
  display: flex;
  align-items: flex-start; /* 顶部对齐，防止换行后 tag 错位 */
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}
.config-title {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
  line-height: 1.4;
  word-break: break-all;
  white-space: normal; /* 允许换行，不截断 */
}
.config-input {
  margin-bottom: 12px;
}
.config-foot {
  display: flex;
  justify-content: flex-end;
}
</style>
