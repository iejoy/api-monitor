<template>
  <div class="service-detail">
    <el-card class="box-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>服务详情</span>
          <div class="header-actions">
            <el-button type="primary" @click="editService">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="text" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="service-info" v-if="service">
        <!-- 基本信息 -->
        <div class="info-section">
          <h3>基本信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="服务名称">
              {{ service.name }}
            </el-descriptions-item>
            <el-descriptions-item label="监控URL">
              <el-link :href="service.url" target="_blank" type="primary">
                {{ service.url }}
              </el-link>
            </el-descriptions-item>
            <el-descriptions-item label="请求方法">
              <el-tag :type="getMethodTagType(service.method)">
                {{ service.method }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="超时时间">
              {{ service.timeout }}秒
            </el-descriptions-item>
            <el-descriptions-item label="监控间隔">
              {{ service.interval }}秒
            </el-descriptions-item>
            <el-descriptions-item label="启用状态">
              <el-tag :type="service.is_active ? 'success' : 'danger'">
                {{ service.is_active ? '启用' : '禁用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间" :span="2">
              {{ formatDateTime(service.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间" :span="2">
              {{ formatDateTime(service.updated_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="服务描述" :span="2" v-if="service.description">
              {{ service.description }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <!-- 监控状态 -->
        <div class="info-section">
          <h3>监控状态</h3>
          <div class="status-cards">
            <el-card class="status-card">
              <div class="status-item">
                <div class="status-label">当前状态</div>
                <div class="status-value">
                  <el-tag :type="getStatusTagType(service.last_status)">
                    {{ getStatusText(service.last_status) }}
                  </el-tag>
                </div>
              </div>
            </el-card>
            
            <el-card class="status-card">
              <div class="status-item">
                <div class="status-label">最后检查时间</div>
                <div class="status-value">
                  {{ service.last_check_time ? formatDateTime(service.last_check_time) : '未检查' }}
                </div>
              </div>
            </el-card>
            
            <el-card class="status-card">
              <div class="status-item">
                <div class="status-label">平均响应时间</div>
                <div class="status-value">
                  {{ service.avg_response_time ? service.avg_response_time + 'ms' : '-' }}
                </div>
              </div>
            </el-card>
            
            <el-card class="status-card">
              <div class="status-item">
                <div class="status-label">可用率</div>
                <div class="status-value">
                  {{ service.uptime_rate ? (service.uptime_rate * 100).toFixed(2) + '%' : '-' }}
                </div>
              </div>
            </el-card>
          </div>
        </div>
        
        <!-- 最近监控记录 -->
        <div class="info-section">
          <div class="section-header">
            <h3>最近监控记录</h3>
            <el-button type="text" @click="viewAllLogs">
              查看全部
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
          
          <el-table :data="recentLogs" stripe>
            <el-table-column prop="created_at" label="检查时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="response_time" label="响应时间" width="120">
              <template #default="{ row }">
                {{ row.response_time }}ms
              </template>
            </el-table-column>
            <el-table-column prop="status_code" label="状态码" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusCodeTagType(row.status_code)">
                  {{ row.status_code || '-' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.error_message || '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { getService, getServiceLogs } from '@/api/services'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const service = ref(null)
const recentLogs = ref([])

// 获取服务详情
const fetchService = async () => {
  try {
    loading.value = true
    const serviceId = route.params.id
    const response = await getService(serviceId)
    service.value = response
    
    // 获取最近的监控记录
    await fetchRecentLogs(serviceId)
  } catch (error) {
    console.error('获取服务详情失败:', error)
    ElMessage.error('获取服务详情失败')
    router.push('/services')
  } finally {
    loading.value = false
  }
}

// 获取最近监控记录
const fetchRecentLogs = async (serviceId) => {
  try {
    const response = await getServiceLogs(serviceId, { page: 1, size: 10 })
    recentLogs.value = response.items || []
  } catch (error) {
    console.error('获取监控记录失败:', error)
  }
}

// 编辑服务
const editService = () => {
  router.push(`/services/${route.params.id}/edit`)
}

// 查看全部日志
const viewAllLogs = () => {
  router.push(`/logs?service_id=${route.params.id}`)
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 获取方法标签类型
const getMethodTagType = (method) => {
  const types = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'DELETE': 'danger'
  }
  return types[method] || 'info'
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  const types = {
    'success': 'success',
    'failed': 'danger',
    'timeout': 'warning'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    'success': '正常',
    'failed': '失败',
    'timeout': '超时'
  }
  return texts[status] || '未知'
}

// 获取状态码标签类型
const getStatusCodeTagType = (statusCode) => {
  if (!statusCode) return 'info'
  if (statusCode >= 200 && statusCode < 300) return 'success'
  if (statusCode >= 400 && statusCode < 500) return 'warning'
  if (statusCode >= 500) return 'danger'
  return 'info'
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 页面加载时获取数据
onMounted(() => {
  fetchService()
})
</script>

<style scoped>
.service-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.header-actions .el-button {
  margin-left: 0 !important;
  margin-right: 0 !important;
  flex-shrink: 0;
}

.info-section {
  margin-bottom: 30px;
}

.info-section h3 {
  margin: 0 0 16px 0;
  color: var(--custom-text-color-primary);
  font-size: 16px;
  font-weight: 600;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.status-card {
  text-align: center;
}

.status-item {
  padding: 10px;
}

.status-label {
  font-size: 14px;
  color: var(--custom-text-color-secondary);
  margin-bottom: 8px;
}

.status-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--custom-text-color-primary);
}

:deep(.el-descriptions__label) {
  font-weight: 600;
}
</style>