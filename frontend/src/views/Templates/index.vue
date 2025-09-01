<template>
  <div class="templates-page">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>配置模板</span>
          <div class="header-actions">
            <el-button type="primary" @click="$router.push('/templates/create')">
              <el-icon><Plus /></el-icon>
              添加模板
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索和筛选 -->
      <div class="filter-section">
        <el-form :model="searchForm" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="searchForm.search"
              placeholder="模板名称或描述"
              clearable
              style="width: 250px"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="类型">
            <el-select
              v-model="searchForm.type"
              placeholder="全部类型"
              clearable
              style="width: 150px"
            >
              <el-option label="邮件" value="email" />
              <el-option label="飞书" value="feishu" />
              <el-option label="微信" value="wechat" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 模板列表 -->
      <div class="table-section">
        <el-table
          :data="templateList"
          v-loading="loading"
          row-key="id"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="name" label="模板名称" min-width="150">
            <template #default="{ row }">
              <div class="template-name">
                <strong>{{ row.name }}</strong>
                <el-tag v-if="row.is_default" type="success" size="small" style="margin-left: 8px">
                  默认
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.type)">
                {{ getTypeText(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="alert_title_template" label="告警标题模板" min-width="200" show-overflow-tooltip />
          <el-table-column label="启用状态" width="100">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                @change="handleToggleStatus(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="150">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  type="text"
                  size="small"
                  @click="$router.push(`/templates/${row.id}/detail`)"
                >
                  查看
                </el-button>
                <el-button
                  type="text"
                  size="small"
                  @click="$router.push(`/templates/${row.id}/edit`)"
                >
                  编辑
                </el-button>
                <el-button
                  type="text"
                  size="small"
                  @click="handleDuplicate(row)"
                >
                  复制
                </el-button>
                <el-popconfirm
                  title="确定要删除这个模板吗？"
                  @confirm="handleDelete(row)"
                >
                  <template #reference>
                    <el-button type="text" size="small" class="danger">
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-section">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Search,
  Refresh
} from '@element-plus/icons-vue'
import { alertsApi } from '@/api/services'
import dayjs from 'dayjs'

const router = useRouter()

// 数据状态
const templateList = ref([])
const loading = ref(false)

// 搜索表单
const searchForm = reactive({
  search: '',
  type: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取模板列表
const getTemplateList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    if (searchForm.search && searchForm.search.trim()) {
      params.search = searchForm.search.trim()
    }
    
    if (searchForm.type) {
      params.type = searchForm.type
    }
    
    const response = await alertsApi.getAlertTemplates(params)
    
    templateList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取模板列表失败:', error)
    ElMessage.error('获取模板列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  getTemplateList()
}

// 重置
const handleReset = () => {
  searchForm.search = ''
  searchForm.type = ''
  pagination.page = 1
  getTemplateList()
}

// 分页变化
const handleSizeChange = () => {
  pagination.page = 1
  getTemplateList()
}

const handlePageChange = () => {
  getTemplateList()
}

// 复制模板 - 跳转到创建页面并传递数据
const handleDuplicate = (row) => {
  // 通过路由参数传递复制的模板数据
  router.push({
    path: '/templates/create',
    query: {
      duplicate: 'true',
      sourceId: row.id,
      name: `${row.name} - 副本`,
      type: row.type,
      description: row.description || '',
      alert_title_template: row.alert_title_template || '',
      alert_content_template: row.alert_content_template || '',
      webhook_url: row.config?.webhook_url || ''
    }
  })
}

// 切换状态
const handleToggleStatus = async (row) => {
  try {
    await alertsApi.updateAlertTemplate(row.id, { is_active: row.is_active })
    ElMessage.success(`模板已${row.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('操作失败')
    row.is_active = !row.is_active // 回滚状态
  }
}

// 删除模板
const handleDelete = async (row) => {
  try {
    await alertsApi.deleteAlertTemplate(row.id)
    ElMessage.success('删除成功')
    getTemplateList()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 工具函数
const getTypeTagType = (type) => {
  const typeMap = {
    'email': 'primary',
    'feishu': 'success',
    'wechat': 'warning'
  }
  return typeMap[type] || 'info'
}

const getTypeText = (type) => {
  const typeMap = {
    'email': '邮件',
    'feishu': '飞书',
    'wechat': '微信'
  }
  return typeMap[type] || '未知'
}

const formatTime = (time) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
}

onMounted(() => {
  getTemplateList()
})
</script>

<style scoped>
.templates-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-section {
  margin-bottom: 16px;
  padding: 16px;
  background-color: var(--custom-bg-color-page);
  border-radius: 4px;
}

.template-name {
  display: flex;
  align-items: center;
}

.table-section {
  margin-top: 16px;
}

.pagination-section {
  margin-top: 16px;
  text-align: right;
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  align-items: center;
}

.action-buttons .el-button {
  margin-left: 0 !important;
  margin-right: 0 !important;
  flex-shrink: 0;
}

.danger {
  color: var(--el-color-danger);
  
  &:hover {
    color: var(--el-color-danger);
  }
}

:deep(.el-descriptions__label) {
  font-weight: 600;
}
</style>