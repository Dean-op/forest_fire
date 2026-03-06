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
          <div class="form-wrapper">
            <el-form label-width="220px" label-position="right" size="large">
              <el-form-item
                v-for="cfg in group"
                :key="cfg.key"
                :label="cfg.label"
              >
                <div class="input-row">
                  <el-input v-model="cfg.value" class="config-input" />
                  <el-button type="primary" @click="saveConfig(cfg.key, cfg.value)">
                    <el-icon><Check /></el-icon> 保存
                  </el-button>
                </div>
              </el-form-item>
            </el-form>
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

const groupLabels = {
  general: '⚙️ 通用基础配置',
  ai: '🧠 YOLO 算法参数',
  llm: '🤖 大语言模型 (LLM) 配置'
}

const groupedConfigs = computed(() => {
  const groups = {}
  configs.value.forEach(c => {
    if (!groups[c.group]) groups[c.group] = []
    groups[c.group].push(c)
  })
  return groups
})

const fetchConfigs = async () => {
  loading.value = true
  try {
    configs.value = await api.get('/admin/configs')
    // Set first tab as active automatically if current is empty or invalid
    if (Object.keys(groupedConfigs.value).length > 0 && !groupedConfigs.value[activeTab.value]) {
      activeTab.value = Object.keys(groupedConfigs.value)[0]
    }
  } catch {
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

const saveConfig = async (key, value) => {
  try {
    await api.put(`/admin/configs/${key}`, { value })
    ElMessage.success('已保存修改')
  } catch {
    ElMessage.error('保存失败')
  }
}

onMounted(fetchConfigs)
</script>

<style scoped>
.sys-config-container {
  padding: 20px;
}
.card-header h2 {
  margin: 0;
  color: #303133;
}
.config-tabs {
  margin-top: 10px;
}
.form-wrapper {
  padding: 30px 20px;
  max-width: 800px;
}
.input-row {
  display: flex;
  align-items: center;
  gap: 15px;
  width: 100%;
}
.config-input {
  width: 400px;
}
</style>
