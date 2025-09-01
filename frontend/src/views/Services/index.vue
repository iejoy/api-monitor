<template>
  <div class="services-page">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>服务管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="$router.push('/services/create')">
              <el-icon><Plus /></el-icon>
              添加服务
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
              placeholder="服务名称、URL或描述"
              clearable
              style="width: 250px"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.status"
              placeholder="全部状态"
              clearable
              style="width: 150px"
            >
              <el-option label="正常" value="success" />
              <el-option label="异常" value="failed" />
              <el-option label="超时" value="timeout" />
              <el-option label="未知" value="unknown" />
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

      <!-- 服务列表 -->
      <div class="table-section">
        <el-table
          :data="serviceList"
          v-loading="loading"
          row-key="id"
          stripe
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="服务名称" min-width="150">
            <template #default="{ row }">
              <div class="service-name">
                <strong>{{ row.name }}</strong>
                <div class="service-tags" v-if="row.tags">
                  <el-tag
                    v-for="tag in row.tags.split(',')"
                    :key="tag"
                    size="small"
                    type="info"
                  >
                    {{ tag.trim() }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="url" label="监控地址" min-width="200" show-overflow-tooltip />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="监控间隔" width="100">
            <template #default="{ row }">
              {{ formatInterval(row.interval) }}
            </template>
          </el-table-column>
          <el-table-column label="最后检查" width="150">
            <template #default="{ row }">
              {{ formatTime(row.last_check_time) }}
            </template>
          </el-table-column>
          <el-table-column label="启用状态" width="100">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                @change="handleToggleStatus(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  type="text"
                  size="small"
                  @click="handleTest(row)"
                  :loading="row.testing"
                >
                  测试
                </el-button>
                <el-button
                  type="text"
                  size="small"
                  @click="$router.push(`/services/${row.id}/detail`)"
                >
                  详情
                </el-button>
                <el-button
                  type="text"
                  size="small"
                  @click="$router.push(`/services/${row.id}/edit`)"
                >
                  编辑
                </el-button>
                <el-popconfirm
                  title="确定要删除这个服务吗？"
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

    <!-- 批量操作 -->
    <div class="batch-actions" v-if="selectedServices.length > 0">
      <div class="batch-info">
        已选择 {{ selectedServices.length }} 个服务
      </div>
      <div class="batch-buttons">
        <el-button @click="handleBatchEnable">批量启用</el-button>
        <el-button @click="handleBatchDisable">批量禁用</el-button>
        <el-button type="danger" @click="handleBatchDelete">批量删除</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { servicesApi } from '@/api/services'
import dayjs from 'dayjs'

// 数据状态
const serviceList = ref([])
const selectedServices = ref([])
const loading = ref(false)

// 搜索表单
const searchForm = reactive({
  search: '',
  status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取服务列表
const getServiceList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    // 只有当搜索条件不为空时才添加到参数中
    if (searchForm.search && searchForm.search.trim()) {
      params.search = searchForm.search.trim()
    }
    
    if (searchForm.status) {
      params.status = searchForm.status
    }
    
    console.log('搜索表单数据:', searchForm)
    console.log('搜索参数:', params)
    
    const response = await servicesApi.getServices(params)
    
    console.log('servicesApi响应:', response)
    
    serviceList.value = (response.items || []).map(item => ({
      ...item,
      testing: false
    }))
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取服务列表失败:', error)
    ElMessage.error('获取服务列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  getServiceList()
}

// 重置
const handleReset = () => {
  searchForm.search = ''
  searchForm.status = ''
  pagination.page = 1
  getServiceList()
}

// 分页变化
const handleSizeChange = () => {
  pagination.page = 1
  getServiceList()
}

const handlePageChange = () => {
  getServiceList()
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedServices.value = selection
}

// 切换状态
const handleToggleStatus = async (row) => {
  try {
    await servicesApi.toggleService(row.id)
    ElMessage.success(`服务已${row.is_active ? '启用' : '禁用'}`)
    getServiceList()
  } catch (error) {
    ElMessage.error('操作失败')
    row.is_active = !row.is_active // 回滚状态
  }
}

// 测试服务
const handleTest = async (row) => {
  row.testing = true
  try {
    const result = await servicesApi.testService(row.id)
    // 根据测试结果状态显示不同风格的提示
    if (result.status === 'success') {
      ElMessage.success(`测试成功：服务正常响应 (${result.response_time}ms)`)
    } else if (result.status === 'timeout') {
      ElMessage.warning(`测试超时：服务响应超时 (${result.error_message})`)
    } else if (result.status === 'failed') {
      ElMessage.error(`测试失败：${result.error_message || '服务异常'}`)
    } else {
      ElMessage.info(`测试完成：${result.status}`)
    }
    getServiceList()
  } catch (error) {
    ElMessage.error('测试失败')
  } finally {
    row.testing = false
  }
}

// 删除服务
const handleDelete = async (row) => {
  try {
    await servicesApi.deleteService(row.id)
    ElMessage.success('删除成功')
    getServiceList()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 批量操作
const handleBatchEnable = async () => {
  ElMessage.info('批量启用功能开发中...')
}

const handleBatchDisable = async () => {
  ElMessage.info('批量禁用功能开发中...')
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedServices.value.length} 个服务吗？`,
      '批量删除',
      {
        type: 'warning'
      }
    )
    ElMessage.info('批量删除功能开发中...')
  } catch {
    // 用户取消
  }
}

// 工具函数
const getStatusTagType = (status) => {
  const statusMap = {
    'success': 'success',
    'failed': 'danger',
    'timeout': 'warning',
    'unknown': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'success': '正常',
    'failed': '异常',
    'timeout': '超时',
    'unknown': '未知'
  }
  return statusMap[status] || '未知'
}

const formatInterval = (seconds) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时`
}

const formatTime = (time) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
}

onMounted(() => {
  getServiceList()
})
</script>

<style scoped>
.services-page {
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

.service-name {
  .service-tags {
    margin-top: 4px;
    
    .el-tag {
      margin-right: 4px;
    }
  }
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

.batch-actions {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px 24px;
  box-shadow: var(--el-box-shadow);
  display: flex;
  align-items: center;
  gap: 16px;
  z-index: 100;
  
  .batch-info {
    color: var(--el-text-color-primary);
    font-weight: 500;
  }
}

.danger {
  color: var(--el-color-danger);
  
  &:hover {
    color: var(--el-color-danger);
  }
}
</style>