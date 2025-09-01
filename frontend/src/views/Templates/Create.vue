<template>
  <div class="template-create">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>{{ isDuplicate ? '复制配置模板' : '创建配置模板' }}</span>
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
        class="template-form"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入模板名称"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="模板类型" prop="type">
          <el-radio-group v-model="form.type" @change="handleTypeChange">
            <el-radio label="email">
              <el-icon><Message /></el-icon>
              邮件模板
            </el-radio>
            <el-radio label="feishu">
              <el-icon><ChatDotRound /></el-icon>
              飞书模板
            </el-radio>
            <el-radio label="wechat">
              <el-icon><ChatLineRound /></el-icon>
              微信模板
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 告警内容模板 -->
        <el-form-item label="告警标题模板" prop="alert_title_template">
          <el-input
            v-model="form.alert_title_template"
            placeholder="如：【告警】{service_name} 服务异常"
            clearable
          />
          <div class="form-tip">
            支持变量：{service_name}, {service_url}, {alert_type}, {timestamp}
          </div>
        </el-form-item>

        <el-form-item label="告警内容模板" prop="alert_content_template">
          <el-input
            v-model="form.alert_content_template"
            type="textarea"
            :rows="6"
            placeholder="请输入告警内容模板"
          />
          <div class="form-tip">
            支持变量：{service_name}, {service_url}, {alert_type}, {alert_condition}, {response_time}, {status_code}, {error_message}, {timestamp}
          </div>
        </el-form-item>

        <!-- 渠道特定配置 -->
        <template v-if="form.type === 'feishu'">
          <el-form-item label="默认Webhook" prop="webhook_url">
            <el-input
              v-model="form.webhook_url"
              placeholder="飞书机器人Webhook URL（可选）"
              clearable
            />
          </el-form-item>
        </template>

        <template v-if="form.type === 'wechat'">
          <el-form-item label="默认Webhook" prop="webhook_url">
            <el-input
              v-model="form.webhook_url"
              placeholder="企业微信机器人Webhook URL（可选）"
              clearable
            />
          </el-form-item>
        </template>
        
        <el-form-item label="设为默认" prop="is_default">
          <el-switch
            v-model="form.is_default"
            active-text="是"
            inactive-text="否"
          />
          <div class="form-tip">
            每种类型只能有一个默认模板
          </div>
        </el-form-item>
        
        <el-form-item label="启用状态" prop="is_active">
          <el-switch
            v-model="form.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
        
        <el-form-item label="模板描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitForm" :loading="loading">
            {{ isDuplicate ? '复制模板' : '创建模板' }}
          </el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, 
  Message, 
  ChatDotRound, 
  ChatLineRound 
} from '@element-plus/icons-vue'
import { alertsApi } from '@/api/services'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)

// 是否为复制模板
const isDuplicate = computed(() => route.query.duplicate === 'true')

// 表单数据
const form = reactive({
  name: '',
  type: 'email',
  description: '',
  alert_title_template: '',
  alert_content_template: '',
  webhook_url: '',
  is_default: false,
  is_active: true
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择模板类型', trigger: 'change' }
  ],
  alert_title_template: [
    { required: true, message: '请输入告警标题模板', trigger: 'blur' }
  ],
  alert_content_template: [
    { required: true, message: '请输入告警内容模板', trigger: 'blur' }
  ]
}

// 类型改变
const handleTypeChange = (type) => {
  form.webhook_url = ''
  if (!isDuplicate.value) {
    setDefaultTemplates()
  }
}

// 设置默认模板内容
const setDefaultTemplates = () => {
  if (!form.alert_title_template) {
    form.alert_title_template = '【告警】{service_name} 服务异常'
  }
  
  if (!form.alert_content_template) {
    const defaultTemplates = {
      email: `服务告警通知

服务名称：{service_name}
服务地址：{service_url}
告警类型：{alert_type}
告警条件：{alert_condition}
响应时间：{response_time}ms
状态码：{status_code}
错误信息：{error_message}
告警时间：{timestamp}

请及时处理！`,
      feishu: `**服务告警通知**

**服务名称：** {service_name}
**服务地址：** {service_url}
**告警类型：** {alert_type}
**告警条件：** {alert_condition}
**响应时间：** {response_time}ms
**状态码：** {status_code}
**错误信息：** {error_message}
**告警时间：** {timestamp}

请及时处理！`,
      wechat: `服务告警通知

服务名称：{service_name}
服务地址：{service_url}
告警类型：{alert_type}
告警条件：{alert_condition}
响应时间：{response_time}ms
状态码：{status_code}
错误信息：{error_message}
告警时间：{timestamp}

请及时处理！`
    }
    
    form.alert_content_template = defaultTemplates[form.type] || defaultTemplates.email
  }
}

// 初始化表单数据
const initializeForm = () => {
  if (isDuplicate.value) {
    // 处理复制模板的情况
    form.name = route.query.name || ''
    form.type = route.query.type || 'email'
    form.description = route.query.description || ''
    form.alert_title_template = route.query.alert_title_template || ''
    form.alert_content_template = route.query.alert_content_template || ''
    form.webhook_url = route.query.webhook_url || ''
    form.is_default = false // 副本不能是默认模板
    form.is_active = true
  } else {
    // 普通创建模板
    setDefaultTemplates()
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const templateData = {
      name: form.name,
      type: form.type,
      description: form.description,
      alert_title_template: form.alert_title_template,
      alert_content_template: form.alert_content_template,
      is_default: form.is_default,
      is_active: form.is_active
    }
    
    // 添加渠道特定配置
    if (form.type === 'feishu' || form.type === 'wechat') {
      templateData.config = {
        webhook_url: form.webhook_url
      }
    }
    
    await alertsApi.createAlertTemplate(templateData)
    
    ElMessage.success(isDuplicate.value ? '模板复制成功' : '模板创建成功')
    router.push('/templates')
  } catch (error) {
    console.error('创建模板失败:', error)
    ElMessage.error(error.message || '创建模板失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (!formRef.value) return
  formRef.value.resetFields()
  initializeForm()
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 页面初始化
onMounted(() => {
  initializeForm()
})
</script>

<style scoped>
.template-create {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-form {
  max-width: 600px;
}

.form-tip {
  font-size: 12px;
  color: var(--custom-text-color-secondary);
  margin-top: 4px;
  line-height: 1.4;
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
</style>