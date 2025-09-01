<template>
  <div class="alert-detail">
    <el-card class="box-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>告警配置详情</span>
          <el-button type="text" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
        </div>
      </template>
      
      <div class="detail-content" v-if="alertConfig">
        <!-- 基本信息 -->
        <div class="info-section">
          <h3 class="section-title">基本信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="配置名称">
              {{ alertConfig.name }}
            </el-descriptions-item>
            <el-descriptions-item label="关联服务">
              <el-button
                type="text"
                size="small"
                @click="viewServiceDetail(alertConfig.service_id)"
                v-if="alertConfig.service_id"
              >
                {{ alertConfig.service_name }}
              </el-button>
              <span v-else>{{ alertConfig.service_name }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="告警类型">
              <el-tag :type="getAlertTypeTagType(alertConfig.type)">
                {{ getAlertTypeText(alertConfig.type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="启用状态">
              <el-tag :type="alertConfig.is_active ? 'success' : 'danger'">
                {{ alertConfig.is_active ? '启用' : '禁用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(alertConfig.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDateTime(alertConfig.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 告警配置 -->
        <div class="info-section">
          <h3 class="section-title">告警配置</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="告警目标">
              <div class="alert-target">
                {{ getAlertTarget(alertConfig) }}
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="告警条件">
              <div class="alert-conditions">
                <el-tag
                  v-for="condition in getAlertConditions(alertConfig.alert_conditions)"
                  :key="condition.value"
                  type="info"
                  class="condition-tag"
                >
                  {{ condition.label }}
                </el-tag>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="响应时间阈值" v-if="alertConfig.response_threshold">
              {{ alertConfig.response_threshold }} 毫秒
            </el-descriptions-item>
            <el-descriptions-item label="告警频率">
              {{ getAlertFrequencyText(alertConfig.alert_frequency) }}
            </el-descriptions-item>
            <el-descriptions-item label="描述" v-if="alertConfig.description">
              {{ alertConfig.description }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 测试记录 -->
        <div class="info-section" v-if="alertConfig.last_test_time">
          <h3 class="section-title">最近测试记录</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="测试时间">
              {{ formatDateTime(alertConfig.last_test_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="测试结果">
              <el-tag :type="alertConfig.last_test_result === 'success' ? 'success' : 'danger'">
                {{ alertConfig.last_test_result === 'success' ? '成功' : '失败' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="测试消息" v-if="alertConfig.last_test_message">
              {{ alertConfig.last_test_message }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 操作按钮 -->
        <div class="action-section">
          <div class="action-buttons">
            <el-button
              type="primary"
              size="small"
              @click="testAlert"
              :loading="testLoading"
            >
              测试告警
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="editAlert"
            >
              编辑配置
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="toggleAlert"
              :loading="toggleLoading"
            >
              {{ alertConfig.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-popconfirm
              title="确定要删除这个告警配置吗？"
              @confirm="deleteAlert"
            >
              <template #reference>
                <el-button type="danger" size="small">
                  删除配置
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft,
  Bell,
  Edit,
  Switch,
  Delete
} from '@element-plus/icons-vue'
import { 
  getAlertConfig, 
  testAlertConfig, 
  updateAlertConfig, 
  deleteAlertConfig 
} from '@/api/services'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const testLoading = ref(false)
const toggleLoading = ref(false)
const alertConfig = ref(null)

// 获取告警配置详情
const fetchAlertConfig = async () => {
  try {
    loading.value = true
    const alertId = route.params.id
    const response = await getAlertConfig(alertId)
    alertConfig.value = response
  } catch (error) {
    console.error('获取告警配置详情失败:', error)
    ElMessage.error('获取告警配置详情失败')
    router.push('/alerts')
  } finally {
    loading.value = false
  }
}

// 获取告警目标（显示收件人信息）
const getAlertTarget = (config) => {
  if (!config.config) return '-'
  
  if (config.type === 'email' && config.config.to_emails) {
    return config.config.to_emails.join(', ')
  } else if (config.type === 'feishu') {
    return '飞书告警'
  } else if (config.type === 'wechat') {
    return '微信告警'
  }
  
  return '-'
}

// 获取告警条件
const getAlertConditions = (conditions) => {
  if (!conditions) return []
  
  const conditionMap = {
    'service_down': '服务不可用',
    'response_slow': '响应时间过慢',
    'status_code_error': 'HTTP状态码异常'
  }
  
  const conditionList = conditions.split(',').filter(c => c.trim())
  return conditionList.map(condition => ({
    value: condition.trim(),
    label: conditionMap[condition.trim()] || condition.trim()
  }))
}

// 获取告警频率文本
const getAlertFrequencyText = (frequency) => {
  const frequencyMap = {
    'immediate': '立即告警',
    'once_per_hour': '每小时最多一次',
    'once_per_day': '每天最多一次'
  }
  return frequencyMap[frequency] || frequency
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
    'email': '邮件告警',
    'feishu': '飞书告警',
    'wechat': '微信告警'
  }
  return texts[alertType] || '未知类型'
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 测试告警
const testAlert = async () => {
  try {
    testLoading.value = true
    const alertId = route.params.id
    await testAlertConfig(alertId)
    ElMessage.success('测试告警发送成功，请检查接收端')
    // 重新获取配置以更新测试记录
    await fetchAlertConfig()
  } catch (error) {
    console.error('测试告警失败:', error)
    ElMessage.error(error.message || '测试告警失败')
  } finally {
    testLoading.value = false
  }
}

// 编辑告警配置
const editAlert = () => {
  const alertId = route.params.id
  router.push(`/alerts/${alertId}/edit`)
}

// 切换告警状态
const toggleAlert = async () => {
  try {
    toggleLoading.value = true
    const alertId = route.params.id
    const newStatus = !alertConfig.value.is_active
    
    await updateAlertConfig(alertId, {
      ...alertConfig.value,
      is_active: newStatus
    })
    
    alertConfig.value.is_active = newStatus
    ElMessage.success(`告警配置已${newStatus ? '启用' : '禁用'}`)
  } catch (error) {
    console.error('切换告警状态失败:', error)
    ElMessage.error('切换告警状态失败')
  } finally {
    toggleLoading.value = false
  }
}

// 删除告警配置
const deleteAlert = async () => {
  try {
    const alertId = route.params.id
    await deleteAlertConfig(alertId)
    ElMessage.success('删除成功')
    router.push('/alerts')
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

// 返回上一页
const goBack = () => {
  router.back()
}

// 页面加载时获取数据
onMounted(() => {
  fetchAlertConfig()
})
</script>

<style scoped>
.alert-detail {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-content {
  max-width: 1000px;
}

.info-section {
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--custom-text-color-primary);
  border-left: 4px solid var(--el-color-primary);
  padding-left: 12px;
  font-family: var(--custom-font-family);
}

.alert-target {
  font-family: var(--custom-font-family);
  font-size: 12px;
  color: var(--custom-text-color-regular);
  word-break: break-all;
}

.alert-conditions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.condition-tag {
  margin: 0;
}

.action-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--custom-border-color-lighter);
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

.el-descriptions {
  margin-bottom: 0;
}

.el-descriptions :deep(.el-descriptions__label) {
  font-weight: 600;
  color: var(--custom-text-color-regular);
  width: 120px;
  font-family: var(--custom-font-family);
}

.el-descriptions :deep(.el-descriptions__content) {
  color: var(--custom-text-color-primary);
  font-family: var(--custom-font-family);
}
</style>