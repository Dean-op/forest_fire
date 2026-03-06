<template>
  <div>
    <el-card shadow="hover">
      <template #header><h2 style="margin:0;">📋 系统日志</h2></template>
      <el-table :data="logs" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">{{ new Date(row.timestamp).toLocaleString('zh-CN') }}</template>
        </el-table-column>
        <el-table-column prop="user" label="操作用户" width="120" />
        <el-table-column prop="action" label="操作" width="160" />
        <el-table-column prop="detail" label="详情" min-width="250" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="140" />
      </el-table>
      <div style="display:flex;justify-content:center;margin-top:20px;">
        <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="total, prev, pager, next" @current-change="fetchLogs" />
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
const logs = ref([]); const total = ref(0); const page = ref(1); const loading = ref(false)
const fetchLogs = async () => { loading.value = true; try { const res = await api.get('/admin/logs', { params: { page: page.value, size: 20 } }); logs.value = res.items; total.value = res.total } catch { ElMessage.error('获取日志失败') } finally { loading.value = false } }
onMounted(fetchLogs)
</script>
