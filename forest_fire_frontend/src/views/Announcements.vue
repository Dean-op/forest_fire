<template>
  <div class="ann-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="title-wrap">
            <h2>公告管理 / SOP</h2>
          </div>
          <div class="toolbar">
            <el-radio-group v-model="filterCat" @change="fetchList">
              <el-radio-button value="">全部</el-radio-button>
              <el-radio-button value="notice">公告</el-radio-button>
              <el-radio-button value="sop">SOP</el-radio-button>
            </el-radio-group>
            <el-button type="primary" @click="openAdd">
              <el-icon><Plus /></el-icon>
              新增
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" stripe border v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" sortable />
        <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
        <el-table-column prop="category" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.category === 'sop' ? 'success' : 'info'">{{ row.category === 'sop' ? 'SOP' : '公告' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_published" label="发布" width="90" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.is_published" @change="togglePublish(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button link type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="formVisible" :title="isEdit ? '编辑公告/SOP' : '新增公告/SOP'" width="680px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.category" style="width: 180px">
            <el-option label="公告" value="notice" />
            <el-option label="SOP" value="sop" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../api'

const list = ref([])
const loading = ref(false)
const formVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const filterCat = ref('')

const form = reactive({ title: '', content: '', category: 'notice' })

const sortByIdAsc = (items) => [...items].sort((a, b) => Number(a.id || 0) - Number(b.id || 0))
const formatTime = (val) => (val ? new Date(val).toLocaleString('zh-CN') : '-')

const fetchList = async () => {
  loading.value = true
  try {
    const params = filterCat.value ? { category: filterCat.value } : {}
    const data = await api.get('/admin/announcements', { params })
    list.value = sortByIdAsc(Array.isArray(data) ? data : [])
  } catch {
    ElMessage.error('获取公告列表失败')
  } finally {
    loading.value = false
  }
}

const openAdd = () => {
  isEdit.value = false
  editId.value = null
  Object.assign(form, { title: '', content: '', category: 'notice' })
  formVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    title: row.title || '',
    content: row.content || '',
    category: row.category || 'notice'
  })
  formVisible.value = true
}

const submitForm = async () => {
  if (!String(form.title || '').trim()) {
    ElMessage.warning('标题不能为空')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/admin/announcements/${editId.value}`, form)
    } else {
      await api.post('/admin/announcements', form)
    }
    ElMessage.success('保存成功')
    formVisible.value = false
    await fetchList()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

const togglePublish = async (row) => {
  try {
    await api.put(`/admin/announcements/${row.id}`, { is_published: row.is_published })
    ElMessage.success('发布状态已更新')
  } catch {
    row.is_published = !row.is_published
    ElMessage.error('发布状态更新失败')
  }
}

const handleDelete = async (id) => {
  try {
    await api.delete(`/admin/announcements/${id}`)
    ElMessage.success('删除成功')
    await fetchList()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(fetchList)
</script>

<style scoped>
.ann-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-wrap h2 {
  margin: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.row-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}
</style>
