<template>
  <div class="template-detail">
    <el-card class="box-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>模板详情</span>
          <div class="header-actions">
            <el-button type="primary" @click="editTemplate">
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
      
      <div class="detail-content" v-if="template">
        <!-- 基本信息 -->
        <div class="info-section">
          <h3 class="section-title">基本信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="模板名称">
              <div class="template-name">
                {{ template.name }}
                <el-tag v-if="template.is_default" type="success" size="small" style="margin-left: 8px">
                  默认
                </el-tag>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="模板类型">
              <el-tag :type="getTypeTagType(template.type)">
                {{ getTypeText(template.type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="启用状态">
              <el-tag :type="template.is_active ? 'success' : 'danger'">
                {{ template.is_active ? '启用' : '禁用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatTime(template.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatTime(template.updated_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="模板描述" :span="2">
              {{ template.description || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 模板内容 -->
        <div class="info-section">
          <h3 class="section-title">模板内容</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="告警标题模板">
              <div class="template-content">
                {{ template.alert_title_template || '-' }}
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="告警内容模板">
              <div class="template-content content-template">
                {{ template.alert_content_template || '-' }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 渠道配置 -->
        <div class="info-section" v-if="template.config && Object.keys(template.config).length > 0">
          <h3 class="section-title">渠道配置</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item 
              v-if="template.config.webhook_url" 
              label="Webhook URL"
            >
              <div class="webhook-url">
                {{ template.config.webhook_url }}
              </div>
            </el-descriptions-item>
            <el-descriptions-item 
              v-for="(value, key) in getOtherConfigs(template.config)" 
              :key="key"
              :label="key"
            >
              {{ value }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 操作按钮 -->
        <div class="action-section">
          <div class="action-buttons">
            <el-button
              type="primary"
              size="small"
              @click="editTemplate"
            >
              <el-icon><Edit /></el-icon>
              编辑模板
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="duplicateTemplate"
            >
              <el-icon><CopyDocument /></el-icon>
              复制模板
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="toggleTemplate"
              :loading="toggleLoading"
            >
              {{ template.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-popconfirm
              title="确定要删除这个模板吗？"
              @confirm="deleteTemplate"
            >
              <template #reference>
                <el-button type="danger" size="small">
                  <el-icon><Delete /></el-icon>
                  删除模板
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
  Edit, 
  ArrowLeft, 
  CopyDocument, 
  Delete 
} from '@element-plus/icons-vue'
import { alertsApi } from '@/api/services'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const toggleLoading = ref(false)
const template = ref(null)

// 获取模板详情
const fetchTemplate = async () => {
  try {
    loading.value = true
    const templateId = route.params.id
    const response = await alertsApi.getAlertTemplate(templateId)
    template.value = response
  } catch (error) {
    console.error('获取模板详情失败:', error)
    ElMessage.error('获取模板详情失败')
    router.push('/templates')
  } finally {
    loading.value = false
  }
}

// 编辑模板
const editTemplate = () => {
  router.push(`/templates/${route.params.id}/edit`)
}

// 复制模板
const duplicateTemplate = () => {
  const templateData = template.value
  router.push({
    path: '/templates/create',
    query: {
      duplicate: 'true',
      sourceId: templateData.id,
      name: `${templateData.name} - 副本`,
      type: templateData.type,
      description: templateData.description || '',
      alert_title_template: templateData.alert_title_template || '',
      alert_content_template: templateData.alert_content_template || '',
      webhook_url: templateData.config?.webhook_url || ''
    }
  })
}

// 切换模板状态
const toggleTemplate = async () => {
  try {
    toggleLoading.value = true
    const templateId = route.params.id
    const newStatus = !template.value.is_active
    
    await alertsApi.updateAlertTemplate(templateId, {
      ...template.value,
      is_active: newStatus
    })
    
    template.value.is_active = newStatus
    ElMessage.success(`模板已${newStatus ? '启用' : '禁用'}`)
  } catch (error) {
    console.error('切换模板状态失败:', error)
    ElMessage.error('切换模板状态失败')
  } finally {
    toggleLoading.value = false
  }
}

// 删除模板
const deleteTemplate = async () => {
  try {
    const templateId = route.params.id
    await alertsApi.deleteAlertTemplate(templateId)
    ElMessage.success('删除成功')
    router.push('/templates')
  } catch (error) {
    console.error('删除模板失败:', error)
    ElMessage.error('删除模板失败')
  }
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 获取类型标签类型
const getTypeTagType = (type) => {
  const typeMap = {
    'email': 'primary',
    'feishu': 'success',
    'wechat': 'warning'
  }
  return typeMap[type] || 'info'
}

// 获取类型文本
const getTypeText = (type) => {
  const typeMap = {
    'email': '邮件',
    'feishu': '飞书',
    'wechat': '微信'
  }
  return typeMap[type] || '未知'
}

// 获取其他配置项（排除已单独显示的）
const getOtherConfigs = (config) => {
  if (!config) return {}
  const { webhook_url, alert_title_template, alert_content_template, ...others } = config
  return others
}

// 格式化时间
const formatTime = (time) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
}

// 页面加载时获取数据
onMounted(() => {
  fetchTemplate()
})
</script>

<style scoped>
.template-detail {
  padding: 0;
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
}

.template-name {
  display: flex;
  align-items: center;
}

.template-content {
  font-family: monospace;
  font-size: 12px;
  color: var(--custom-text-color-regular);
  word-break: break-all;
  white-space: pre-wrap;
}

.content-template {
  max-height: 200px;
  overflow-y: auto;
  background-color: var(--custom-bg-color-page);
  padding: 8px;
  border-radius: 4px;
}

.webhook-url {
  font-family: monospace;
  font-size: 12px;
  color: var(--custom-text-color-regular);
  word-break: break-all;
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
}

.el-descriptions :deep(.el-descriptions__content) {
  color: var(--custom-text-color-primary);
}
</style>