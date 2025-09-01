<template>
  <div class="alert-edit">
    <el-card class="box-card" v-loading="pageLoading">
      <template #header>
        <div class="card-header">
          <span>编辑告警配置</span>
          <el-button type="text" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        class="alert-form"
      >
        <el-form-item label="选择服务" prop="service_id">
          <el-select
            v-model="form.service_id"
            placeholder="请选择要配置告警的服务"
            style="width: 100%"
            @change="handleServiceChange"
          >
            <el-option
              v-for="service in availableServices"
              :key="service.id"
              :label="service.name"
              :value="service.id"
              :disabled="service.hasAlert && service.id !== originalServiceId"
            >
              <div class="service-option">
                <span>{{ service.name }}</span>
                <span class="service-url">{{ service.url }}</span>
                <span v-if="service.hasAlert && service.id !== originalServiceId" class="service-alert-status">已配置告警</span>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">
            每个服务只能配置一个告警渠道
          </div>
        </el-form-item>
        
        <el-form-item label="告警类型" prop="alert_type">
          <el-radio-group v-model="form.alert_type" @change="handleTypeChange">
            <el-radio label="email">
              <el-icon><Message /></el-icon>
              邮件告警
            </el-radio>
            <el-radio label="feishu">
              <el-icon><ChatDotRound /></el-icon>
              飞书告警
            </el-radio>
            <el-radio label="wechat">
              <el-icon><ChatLineRound /></el-icon>
              微信告警
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 邮件告警配置 -->
        <template v-if="form.alert_type === 'email'">
          <el-form-item label="配置模板" prop="alert_target">
            <el-select
              v-model="form.alert_target"
              placeholder="请选择邮件配置模板"
              style="width: 100%"
            >
              <el-option
                v-for="template in availableTemplates"
                :key="template.id"
                :label="template.name"
                :value="template.id"
              >
                <div class="template-option">
                  <span>{{ template.name }}</span>
                  <span class="template-description">{{ template.description || '无描述' }}</span>
                </div>
              </el-option>
            </el-select>
            <div class="form-tip">
              请在配置模板页面创建邮件配置模板，然后在此处选择
            </div>
          </el-form-item>
          
          <el-form-item label="收件人" prop="email_recipients" v-if="form.alert_target">
            <el-input
              v-model="form.email_recipients"
              placeholder="请输入收件人邮箱地址"
              clearable
            />
            <div class="form-tip">
              支持多个邮箱地址，用英文逗号分隔
            </div>
          </el-form-item>
        </template>
        
        <!-- 飞书告警配置 -->
        <template v-if="form.alert_type === 'feishu'">
          <el-form-item label="配置模板" prop="alert_target">
            <el-select
              v-model="form.alert_target"
              placeholder="请选择飞书配置模板"
              style="width: 100%"
            >
              <el-option
                v-for="template in availableTemplates"
                :key="template.id"
                :label="template.name"
                :value="template.id"
              >
                <div class="template-option">
                  <span>{{ template.name }}</span>
                  <span class="template-description">{{ template.description || '无描述' }}</span>
                </div>
              </el-option>
            </el-select>
            <div class="form-tip">
              请在配置模板页面创建飞书配置模板，然后在此处选择
            </div>
          </el-form-item>
        </template>
        
        <!-- 微信告警配置 -->
        <template v-if="form.alert_type === 'wechat'">
          <el-form-item label="配置模板" prop="alert_target">
            <el-select
              v-model="form.alert_target"
              placeholder="请选择微信配置模板"
              style="width: 100%"
            >
              <el-option
                v-for="template in availableTemplates"
                :key="template.id"
                :label="template.name"
                :value="template.id"
              >
                <div class="template-option">
                  <span>{{ template.name }}</span>
                  <span class="template-description">{{ template.description || '无描述' }}</span>
                </div>
              </el-option>
            </el-select>
            <div class="form-tip">
              请在配置模板页面创建微信配置模板，然后在此处选择
            </div>
          </el-form-item>
        </template>
        
        <el-form-item label="告警条件">
          <el-checkbox-group v-model="form.alert_conditions">
            <el-checkbox label="service_down">服务不可用</el-checkbox>
            <el-checkbox label="response_slow">响应时间过慢</el-checkbox>
            <el-checkbox label="status_code_error">HTTP状态码异常</el-checkbox>
          </el-checkbox-group>
          <div class="form-tip">
            选择触发告警的条件
          </div>
        </el-form-item>
        
        <el-form-item label="响应时间阈值" v-if="form.alert_conditions.includes('response_slow')">
          <el-input-number
            v-model="form.response_threshold"
            :min="100"
            :max="30000"
            :step="100"
            placeholder="毫秒"
          />
          <span class="input-suffix">毫秒</span>
          <div class="form-tip">
            当响应时间超过此阈值时触发告警
          </div>
        </el-form-item>
        
        <el-form-item label="告警频率">
          <el-radio-group v-model="form.alert_frequency">
            <el-radio label="immediate">立即告警</el-radio>
            <el-radio label="once_per_hour">每小时最多一次</el-radio>
            <el-radio label="once_per_day">每天最多一次</el-radio>
          </el-radio-group>
          <div class="form-tip">
            控制告警发送的频率，避免频繁告警
          </div>
        </el-form-item>
        
        <el-form-item label="启用状态" prop="is_active">
          <el-switch
            v-model="form.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitForm" :loading="loading">
            更新告警配置
          </el-button>
          <el-button @click="testAlert" :loading="testLoading" :disabled="!canTest">
            测试告警
          </el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, 
  Message, 
  ChatDotRound, 
  ChatLineRound 
} from '@element-plus/icons-vue'
import { getAlertConfig, updateAlertConfig, testAlertConfig } from '@/api/services'
import { servicesApi, alertsApi } from '@/api/services'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)
const testLoading = ref(false)
const pageLoading = ref(false)
const services = ref([])
const serviceAlertStatus = ref({}) // 存储服务告警配置状态
const originalServiceId = ref(null) // 原始服务ID
const templates = ref([]) // 存储配置模板

// 表单数据
const form = reactive({
  service_id: '',
  alert_type: 'email',
  alert_target: '',
  email_recipients: '', // 邮件收件人
  alert_conditions: ['service_down'],
  response_threshold: 2000,
  alert_frequency: 'immediate',
  is_active: true
})

// 原始数据备份
let originalData = {}

// 可用服务列表（排除已配置告警的服务，但允许当前配置的服务）
const availableServices = computed(() => {
  return services.value.map(service => ({
    ...service,
    hasAlert: serviceAlertStatus.value[service.id] || false
  }))
})

// 根据当前告警类型过滤可用模板
const availableTemplates = computed(() => {
  return templates.value.filter(template => 
    template.type === form.alert_type && template.is_active
  )
})

// 表单验证规则
const rules = {
  service_id: [
    { required: true, message: '请选择服务', trigger: 'change' }
  ],
  alert_type: [
    { required: true, message: '请选择告警类型', trigger: 'change' }
  ],
  alert_target: [
    { required: true, message: '请选择配置模板', trigger: 'change' }
  ],
  email_recipients: [
    { validator: validateEmailRecipients, trigger: 'blur' }
  ]
}

// 验证邮件收件人
function validateEmailRecipients(rule, value, callback) {
  if (form.alert_type === 'email' && form.alert_target) {
    if (!value) {
      callback(new Error('请输入收件人邮箱地址'))
      return
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    const emails = value.split(',').map(email => email.trim())
    const invalidEmails = emails.filter(email => !emailRegex.test(email))
    
    if (invalidEmails.length > 0) {
      callback(new Error('请输入有效的邮箱地址'))
      return
    }
  }
  
  callback()
}

// 是否可以测试告警
const canTest = computed(() => {
  if (form.alert_type === 'email') {
    return form.service_id && form.alert_type && form.alert_target && form.email_recipients
  }
  return form.service_id && form.alert_type && form.alert_target
})

// 获取配置模板列表
const fetchTemplates = async () => {
  try {
    const response = await alertsApi.getAlertTemplates()
    templates.value = response.items || []
  } catch (error) {
    console.error('获取配置模板失败:', error)
    // 不显示错误消息，因为模板是可选功能
  }
}

// 获取告警配置详情
const fetchAlertConfig = async () => {
  try {
    pageLoading.value = true
    const alertId = route.params.id
    const response = await getAlertConfig(alertId)
    
    console.log('告警配置详情:', response)
    
    // 记录原始服务ID
    originalServiceId.value = response.service_id
    
    // 从配置中提取告警目标和收件人
    let alert_target = ''
    let email_recipients = ''
    if (response.config) {
      if (response.type === 'email') {
        alert_target = response.config.template_id || ''
        email_recipients = response.config.to_emails ? response.config.to_emails.join(', ') : ''
      } else if ((response.type === 'feishu' || response.type === 'wechat') && response.config.template_id) {
        alert_target = response.config.template_id
      }
    }
    
    // 解析告警条件
    let alert_conditions = ['service_down'] // 默认条件
    if (response.alert_conditions) {
      alert_conditions = response.alert_conditions.split(',').filter(condition => condition.trim())
    }
    
    // 填充表单数据
    const formData = {
      service_id: response.service_id || '',
      alert_type: response.type || 'email',
      alert_target: alert_target,
      email_recipients: email_recipients,
      alert_conditions: alert_conditions,
      response_threshold: response.response_threshold || 2000,
      alert_frequency: response.alert_frequency || 'immediate',
      is_active: response.is_active !== undefined ? response.is_active : true
    }
    
    Object.assign(form, formData)
    originalData = { ...formData }
    
  } catch (error) {
    console.error('获取告警配置详情失败:', error)
    ElMessage.error('获取告警配置详情失败')
    router.push('/alerts')
  } finally {
    pageLoading.value = false
  }
}

// 获取服务列表
const fetchServices = async () => {
  try {
    const response = await servicesApi.getServices()
    services.value = response.items || []
    
    // 检查每个服务的告警配置状态
    await checkServicesAlertStatus()
  } catch (error) {
    console.error('获取服务列表失败:', error)
    ElMessage.error('获取服务列表失败')
  }
}

// 检查服务告警配置状态
const checkServicesAlertStatus = async () => {
  const statusMap = {}
  
  for (const service of services.value) {
    try {
      const response = await alertsApi.getServiceAlertConfig(service.id)
      statusMap[service.id] = response.has_config
    } catch (error) {
      console.error(`检查服务 ${service.id} 告警配置失败:`, error)
      statusMap[service.id] = false
    }
  }
  
  serviceAlertStatus.value = statusMap
}

// 服务选择改变
const handleServiceChange = async (serviceId) => {
  if (!serviceId) return
  
  // 如果选择的是原始服务，允许
  if (serviceId === originalServiceId.value) {
    return
  }
  
  // 检查该服务是否已经有告警配置
  if (serviceAlertStatus.value[serviceId]) {
    const serviceName = services.value.find(s => s.id === serviceId)?.name || '该服务'
    ElMessage.warning(`${serviceName} 已经配置了告警渠道，每个服务只能配置一个告警渠道`)
    // 恢复到原始服务
    form.service_id = originalServiceId.value
    return
  }
}

// 告警类型改变
const handleTypeChange = (type) => {
  form.alert_target = ''
  form.email_recipients = ''
}

// 监听告警类型变化，重新获取模板
watch(() => form.alert_type, () => {
  form.alert_target = ''
  form.email_recipients = ''
  fetchTemplates()
})

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const alertId = route.params.id
    const alertData = {
      service_id: form.service_id,
      alert_type: form.alert_type,
      alert_target: form.alert_target,
      email_recipients: form.alert_type === 'email' ? form.email_recipients : undefined,
      alert_conditions: form.alert_conditions, // 直接传递数组，后端会处理
      response_threshold: form.alert_conditions.includes('response_slow') 
        ? form.response_threshold 
        : null,
      alert_frequency: form.alert_frequency,
      is_active: form.is_active,
      description: form.description || ''
    }
    
    console.log('提交的数据:', alertData)
    
    await updateAlertConfig(alertId, alertData)
    
    ElMessage.success('告警配置更新成功')
    router.push('/alerts')
  } catch (error) {
    console.error('更新告警配置失败:', error)
    if (error.response?.status === 400 && error.response?.data?.detail?.includes('已经配置了告警渠道')) {
      ElMessage.error(error.response.data.detail)
      // 重新检查服务告警状态
      await checkServicesAlertStatus()
      // 恢复到原始服务
      form.service_id = originalServiceId.value
    } else {
      ElMessage.error(error.message || '更新告警配置失败')
    }
  } finally {
    loading.value = false
  }
}

// 测试告警
const testAlert = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    testLoading.value = true
    
    const alertId = route.params.id
    await testAlertConfig(alertId)
    ElMessage.success('测试告警发送成功，请检查接收端')
  } catch (error) {
    console.error('测试告警失败:', error)
    ElMessage.error(error.message || '测试告警失败')
  } finally {
    testLoading.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (!formRef.value) return
  
  // 恢复到原始数据
  Object.assign(form, originalData)
  formRef.value.clearValidate()
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 页面加载时获取数据
onMounted(() => {
  fetchServices()
  fetchTemplates()
  fetchAlertConfig()
})
</script>

<style scoped>
.alert-edit {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-form {
  max-width: 600px;
}

.service-option {
  display: flex;
  flex-direction: column;
}

.service-url {
  font-size: 12px;
  color: var(--custom-text-color-secondary);
  margin-top: 2px;
}

.service-alert-status {
  font-size: 12px;
  color: var(--el-color-danger);
  margin-top: 2px;
}

.template-option {
  display: flex;
  flex-direction: column;
}

.template-description {
  font-size: 12px;
  color: var(--custom-text-color-secondary);
  margin-top: 2px;
}

.form-tip {
  font-size: 12px;
  color: var(--custom-text-color-secondary);
  margin-top: 4px;
  line-height: 1.4;
}

.input-suffix {
  margin-left: 8px;
  color: var(--custom-text-color-secondary);
  font-size: 14px;
}

.el-form-item {
  margin-bottom: 22px;
}

.el-radio {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.el-radio .el-icon {
  margin-right: 4px;
}

.el-checkbox {
  margin-bottom: 8px;
}
</style>