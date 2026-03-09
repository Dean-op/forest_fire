<template>
  <div class="logs-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>系统日志</h2>
        </div>
      </template>

      <el-table :data="logs" stripe border v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
        </el-table-column>
        <el-table-column prop="user" label="操作用户" width="120" />
        <el-table-column prop="action" label="操作" width="180" show-overflow-tooltip />
        <el-table-column prop="detail" label="详情" min-width="300" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="150" />
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const logs = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)

const formatTime = (val) => (val ? new Date(val).toLocaleString('zh-CN') : '-')

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/logs', {
      params: { page: page.value, size: size.value }
    })
    logs.value = Array.isArray(res.items) ? res.items : []
    total.value = Number(res.total || 0)
  } catch {
    ElMessage.error('获取系统日志失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>

<style scoped>
.logs-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
