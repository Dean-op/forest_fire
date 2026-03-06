<template>
  <div>
    <el-card shadow="hover">
      <template #header><h2 style="margin:0;">💾 数据库备份</h2></template>
      <div style="text-align:center;padding:40px 0;">
        <el-icon :size="64" color="#409EFF" style="margin-bottom:20px;"><FolderChecked /></el-icon>
        <p style="color:#909399;margin-bottom:30px;">点击下方按钮执行一键数据库备份</p>
        <el-button type="primary" size="large" @click="doBackup" :loading="backing" :icon="Download">
          {{ backing ? '正在备份...' : '一键备份数据库' }}
        </el-button>
        <div v-if="backupResult" style="margin-top:30px;">
          <el-result icon="success" title="备份完成">
            <template #extra>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="备份文件">{{ backupResult.filename }}</el-descriptions-item>
                <el-descriptions-item label="文件大小">{{ backupResult.size }}</el-descriptions-item>
              </el-descriptions>
            </template>
          </el-result>
        </div>
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { FolderChecked, Download } from '@element-plus/icons-vue'
const backing = ref(false); const backupResult = ref(null)
const doBackup = async () => {
  backing.value = true; backupResult.value = null
  try { const res = await api.post('/admin/backup'); backupResult.value = res; ElMessage.success('备份成功！') }
  catch { ElMessage.error('备份失败') }
  finally { backing.value = false }
}
</script>
