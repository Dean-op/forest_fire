<template>
  <div>
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>📢 SOP 与公告管理</h2>
          <div>
            <el-radio-group v-model="filterCat" style="margin-right:10px;" @change="fetchList">
              <el-radio-button value="">全部</el-radio-button>
              <el-radio-button value="notice">公告</el-radio-button>
              <el-radio-button value="sop">SOP</el-radio-button>
            </el-radio-group>
            <el-button type="primary" @click="openAdd"><el-icon><Plus /></el-icon> 新增</el-button>
          </div>
        </div>
      </template>
      <el-table :data="list" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="category" label="类型" width="100">
          <template #default="{ row }"><el-tag :type="row.category==='sop'?'success':''">{{ row.category==='sop'?'SOP':'公告' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="is_published" label="已发布" width="80">
          <template #default="{ row }"><el-switch v-model="row.is_published" @change="togglePublish(row)" /></template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="handleDelete(row.id)"><template #reference><el-button text type="danger">删除</el-button></template></el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-dialog v-model="formVisible" :title="isEdit?'编辑':'新增'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="form.category"><el-option label="公告" value="notice" /><el-option label="SOP" value="sop" /></el-select></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="8" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible=false">取消</el-button><el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
const list = ref([]); const loading = ref(false); const formVisible = ref(false); const isEdit = ref(false); const editId = ref(null); const submitting = ref(false); const filterCat = ref('')
const form = reactive({ title: '', content: '', category: 'notice' })
const fetchList = async () => { loading.value = true; try { const params = filterCat.value ? { category: filterCat.value } : {}; list.value = await api.get('/admin/announcements', { params }) } catch { ElMessage.error('获取列表失败') } finally { loading.value = false } }
const openAdd = () => { isEdit.value = false; editId.value = null; Object.assign(form, { title: '', content: '', category: 'notice' }); formVisible.value = true }
const openEdit = (row) => { isEdit.value = true; editId.value = row.id; Object.assign(form, { title: row.title, content: row.content, category: row.category }); formVisible.value = true }
const submitForm = async () => { submitting.value = true; try { if (isEdit.value) { await api.put(`/admin/announcements/${editId.value}`, form) } else { await api.post('/admin/announcements', form) } ElMessage.success('保存成功'); formVisible.value = false; fetchList() } catch { ElMessage.error('操作失败') } finally { submitting.value = false } }
const togglePublish = async (row) => { try { await api.put(`/admin/announcements/${row.id}`, { is_published: row.is_published }); ElMessage.success('已更新') } catch { ElMessage.error('更新失败') } }
const handleDelete = async (id) => { try { await api.delete(`/admin/announcements/${id}`); ElMessage.success('已删除'); fetchList() } catch { ElMessage.error('删除失败') } }
onMounted(fetchList)
</script>
<style scoped>.card-header{display:flex;justify-content:space-between;align-items:center;}.card-header h2{margin:0;}</style>
