<template>
  <div>
    <el-card shadow="hover">
      <template #header><h2 style="margin:0;">⚙️ 系统参数配置</h2></template>
      <el-form label-width="200px" style="max-width:600px;" v-loading="loading">
        <template v-for="(group, groupName) in groupedConfigs" :key="groupName">
          <el-divider content-position="left">{{ groupLabels[groupName] || groupName }}</el-divider>
          <el-form-item v-for="cfg in group" :key="cfg.key" :label="cfg.label">
            <el-input v-model="cfg.value" style="width:300px;" />
            <el-button type="primary" text @click="saveConfig(cfg.key, cfg.value)" style="margin-left:10px;">保存</el-button>
          </el-form-item>
        </template>
      </el-form>
    </el-card>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
const configs = ref([]); const loading = ref(false)
const groupLabels = { general: '通用配置', ai: 'AI 算法参数', llm: '大语言模型配置' }
const groupedConfigs = computed(() => {
  const groups = {}
  configs.value.forEach(c => { (groups[c.group] = groups[c.group] || []).push(c) })
  return groups
})
const fetchConfigs = async () => { loading.value = true; try { configs.value = await api.get('/admin/configs') } catch { ElMessage.error('获取配置失败') } finally { loading.value = false } }
const saveConfig = async (key, value) => { try { await api.put(`/admin/configs/${key}`, { value }); ElMessage.success('已保存') } catch { ElMessage.error('保存失败') } }
onMounted(fetchConfigs)
</script>
