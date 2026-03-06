<template>
  <div>
    <el-card shadow="hover">
      <template #header><h2 style="margin:0;">📢 SOP 与公告查阅</h2></template>
      <el-radio-group v-model="filterCat" style="margin-bottom:15px;" @change="fetchList">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="notice">公告</el-radio-button>
        <el-radio-button value="sop">SOP</el-radio-button>
      </el-radio-group>
      <el-collapse v-loading="loading">
        <el-collapse-item v-for="item in list" :key="item.id" :title="item.title">
          <template #title>
            <el-tag :type="item.category==='sop'?'success':''" size="small" style="margin-right:8px;">{{ item.category==='sop'?'SOP':'公告' }}</el-tag>
            {{ item.title }}
            <span style="color:#909399;font-size:12px;margin-left:auto;">{{ new Date(item.created_at).toLocaleString('zh-CN') }}</span>
          </template>
          <div style="white-space:pre-wrap;line-height:1.8;">{{ item.content }}</div>
        </el-collapse-item>
      </el-collapse>
      <el-empty v-if="!loading && !list.length" description="暂无公告或 SOP" />
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
const list = ref([]); const loading = ref(false); const filterCat = ref('')
const fetchList = async () => { loading.value = true; try { const params = filterCat.value ? { category: filterCat.value } : {}; list.value = await api.get('/admin/announcements', { params }) } catch { ElMessage.error('获取失败') } finally { loading.value = false } }
onMounted(fetchList)
</script>
