<template>
  <div class="alerts-page">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>告警配置</span>
          <div class="header-actions">
            <el-button type="primary" @click="createAlert">
              <el-icon><Plus /></el-icon>
              添加告警配置
            </el-button>
            <el-button @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 筛选条件 -->
      <div class="filter-section">
        <el-form :model="filters" inline>
          <el-form-item label="关联服务">
            <el-select
              v-model="filters.service_id"
              placeholder="选择服务"
              clearable
              style="width: 200px"
            >
              <el-option
                v-for="service in services"
                :key="service.id"
                :label="service.name"
                :value="service.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="告警渠道">
            <el-select
              v-model="filters.alert_type"
              placeholder="选择告警渠道"
              clearable
              style="width: 150px"
            >
              <el-option label="邮件" value="email" />
              <el-option label="飞书" value="feishu" />
              <el-option label="微信" value="wechat" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="filters.is_active"
              placeholder="选择状态"
              clearable
              style="width: 120px"
            >
              <el-option label="启用" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 告警配置列表 -->
      <div class="table-section">
        <el-table
          :data="alerts"
          v-loading="loading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="service_name" label="关联服务" width="150">
            <template #default="{ row }">
              <el-link
                type="primary"
                @click="viewServiceDetail(row.service_id)"
                v-if="row.service_id"
              >
                {{ row.service_name }}
              </el-link>
              <span v-else>{{ row.service_name }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="name" label="配置名称" width="180">
            <template #default="{ row }">
              <span>{{ row.name }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="alert_type" label="告警渠道" width="120">
            <template #default="{ row }">
              <el-tag :type="getAlertTypeTagType(row.alert_type)">
                {{ getAlertTypeText(row.alert_type) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="alert_target" label="告警目标" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="alert-target">{{ row.alert_target }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="updated_at" label="更新时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.updated_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="启用状态" width="100">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                @change="toggleAlert(row)"
                :loading="row.toggling"
              />
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  type="text"
                  size="small"
                  @click="testAlert(row)"
                  :loading="row.testing"
                >
                  测试
                </el-button>
                <el-button
                  type="text"
                  size="small"
                  @click="viewAlert(row)"
                >
                  详情
                </el-button>
                <el-button
                  type="text"
                  size="small"
                  @click="editAlert(row)"
                >
                  编辑
                </el-button>
                <el-popconfirm
                  title="确定要删除这个告警配置吗？"
                  @confirm="deleteAlert(row)"
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
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Refresh,
  Search,
  RefreshLeft
} from '@element-plus/icons-vue'
import { 
  getAlertConfigs, 
  deleteAlertConfig, 
  updateAlertConfig,
  testAlertConfig,
  } from '@/api/services'
import { servicesApi } from '@/api/services'

const router = useRouter()
const loading = ref(false)
const alerts = ref([])
const services = ref([])

// 筛选条件
const filters = reactive({
  service_id: '',
  alert_type: '',
  is_active: ''
})

// 分页信息
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取服务列表
const fetchServices = async () => {
  try {
    const response = await servicesApi.getServices()
    services.value = response.items || []
  } catch (error) {
    console.error('获取服务列表失败:', error)
  }
}

// 获取告警配置列表
const fetchAlerts = async () => {
  try {
    loading.value = true
    
    const params = {
      page: pagination.page,
      size: pagination.size,
      service_id: filters.service_id || undefined,
      alert_type: filters.alert_type || undefined,
      is_active: filters.is_active !== '' ? filters.is_active : undefined
    }
    
    const response = await getAlertConfigs(params)
    alerts.value = (response.items || []).map(item => ({
      ...item,
      testing: false,
      toggling: false
    }))
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取告警配置失败:', error)
    ElMessage.error('获取告警配置失败')
  } finally {
    loading.value = false
  }
}

// 创建告警配置
const createAlert = () => {
  router.push('/alerts/create')
}

// 查看告警配置详情
const viewAlert = (alert) => {
  router.push(`/alerts/${alert.id}/detail`)
}

// 编辑告警配置
const editAlert = (alert) => {
  router.push(`/alerts/${alert.id}/edit`)
}

// 测试告警配置
const testAlert = async (alert) => {
  try {
    alert.testing = true
    
    const result = await testAlertConfig(alert.id) 
    
    // 根据测试结果状态显示不同风格的提示
    if (result.success) {
      ElMessage.success(`测试成功：${result.message}`)
    } else {
      ElMessage.error(`测试失败：${result.message}`)
    }
  } catch (error) {
    console.error('测试告警失败:', error)
    ElMessage.error(error.message || '测试告警失败')
  } finally {
    alert.testing = false
  }
}

// 切换告警状态
const toggleAlert = async (alert) => {
  try {
    alert.toggling = true
    const newStatus = !alert.is_active
    await updateAlertConfig(alert.id, {
      ...alert,
      is_active: newStatus
    })
    alert.is_active = newStatus
    ElMessage.success(`告警配置已${newStatus ? '启用' : '禁用'}`)
  } catch (error) {
    console.error('切换告警状态失败:', error)
    ElMessage.error('切换告警状态失败')
    // 回滚状态
    alert.is_active = !alert.is_active
  } finally {
    alert.toggling = false
  }
}

// 删除告警配置
const deleteAlert = async (alert) => {
  try {
    await deleteAlertConfig(alert.id)
    ElMessage.success('删除成功')
    fetchAlerts()
  } catch (error) {
    console.error('删除告警配置失败:', error)
    ElMessage.error('删除告警配置失败')
  }
}

// 查看服务详情
const viewServiceDetail = (serviceId) => {
  if (serviceId) {
    router.push(`/services/${serviceId}/detail`)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchAlerts()
}

// 重置筛选条件
const handleReset = () => {
  filters.service_id = ''
  filters.alert_type = ''
  filters.is_active = ''
  pagination.page = 1
  fetchAlerts()
}

// 刷新数据
const refreshData = () => {
  fetchAlerts()
}

// 分页大小改变
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchAlerts()
}

// 当前页改变
const handleCurrentChange = (page) => {
  pagination.page = page
  fetchAlerts()
}

// 获取告警类型标签类型
const getAlertTypeTagType = (alertType) => {
  const types = {
    'email': 'primary',
    'feishu': 'success',
    'wechat': 'warning'
  }
  return types[alertType] || 'info'
}

// 获取告警类型文本
const getAlertTypeText = (alertType) => {
  const texts = {
    'email': '邮件',
    'feishu': '飞书',
    'wechat': '微信'
  }
  return texts[alertType] || '未知'
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 页面加载时获取数据
onMounted(() => {
  fetchServices()
  fetchAlerts()
})
</script>

<style scoped>
.alerts-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-section {
  margin-bottom: 16px;
  padding: 16px;
  background-color: var(--custom-bg-color-page);
  border-radius: 4px;
}

.table-section {
  margin-top: 16px;
}

.pagination-section {
  margin-top: 16px;
  text-align: right;
}

.alert-target {
  font-family: var(--custom-font-family);
  font-size: 12px;
  color: var(--custom-text-color-regular);
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
</style>