<template>
  <div class="backup-page">
    <el-card shadow="hover">
      <template #header>
        <h2 class="title">一键备份数据库</h2>
      </template>

      <div class="backup-body">
        <el-icon :size="64" color="#409EFF"><FolderChecked /></el-icon>
        <p class="hint">点击下方按钮执行完整 SQL 备份，并可立即下载备份文件。</p>
        <el-button type="primary" size="large" :loading="backing" :icon="Download" @click="doBackup">
          {{ backing ? '正在备份...' : '一键备份数据库' }}
        </el-button>

        <div v-if="backupResult" class="result-wrap">
          <el-result icon="success" title="备份完成">
            <template #extra>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="备份文件">{{ backupResult.filename }}</el-descriptions-item>
                <el-descriptions-item label="文件大小">{{ backupResult.size }}</el-descriptions-item>
                <el-descriptions-item label="生成时间">{{ backupResult.created_at }}</el-descriptions-item>
              </el-descriptions>
              <div class="download-btn-wrap">
                <el-button type="success" :icon="Download" @click="downloadBackup">下载备份文件</el-button>
              </div>
            </template>
          </el-result>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { FolderChecked, Download } from '@element-plus/icons-vue'
import api from '../api'

const backing = ref(false)
const backupResult = ref(null)

const doBackup = async () => {
  backing.value = true
  backupResult.value = null
  try {
    const res = await api.post('/admin/backup')
    backupResult.value = res
    ElMessage.success('备份成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '备份失败')
  } finally {
    backing.value = false
  }
}

const downloadBackup = async () => {
  if (!backupResult.value?.download_url) return
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(backupResult.value.download_url, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('download failed')

    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = backupResult.value.filename || 'database_backup.sql'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载备份失败')
  }
}
</script>

<style scoped>
.backup-page {
  padding: 0;
}

.title {
  margin: 0;
}

.backup-body {
  text-align: center;
  padding: 40px 0;
}

.hint {
  color: #909399;
  margin: 16px 0 24px;
}

.result-wrap {
  margin-top: 24px;
}

.download-btn-wrap {
  margin-top: 16px;
}
</style>
