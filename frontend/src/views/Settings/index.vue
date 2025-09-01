<template>
  <div class="settings-page">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
          <div class="header-actions">
            <el-button type="primary" @click="saveSettings" :loading="saving">
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" class="settings-tabs">
        <!-- 邮件配置 -->
        <el-tab-pane label="邮件配置" name="email">
          <el-form
            ref="emailFormRef"
            :model="emailSettings"
            :rules="emailRules"
            label-width="140px"
            class="settings-form"
          >
            <el-form-item label="SMTP服务器" prop="smtp_server">
              <el-input
                v-model="emailSettings.smtp_server"
                placeholder="如：smtp.gmail.com"
                clearable
              />
            </el-form-item>
            
            <el-form-item label="SMTP端口" prop="smtp_port">
              <el-input-number
                v-model="emailSettings.smtp_port"
                :min="1"
                :max="65535"
                placeholder="如：587"
              />
            </el-form-item>
            
            <el-form-item label="用户名" prop="smtp_username">
              <el-input
                v-model="emailSettings.smtp_username"
                placeholder="邮箱账号"
                clearable
              />
            </el-form-item>
            
            <el-form-item label="密码" prop="smtp_password">
              <el-input
                v-model="emailSettings.smtp_password"
                type="password"
                placeholder="邮箱密码或应用专用密码"
                show-password
                clearable
              />
            </el-form-item>
            
            <el-form-item label="发件人邮箱" prop="smtp_from_email">
              <el-input
                v-model="emailSettings.smtp_from_email"
                placeholder="发送告警邮件的邮箱地址"
                clearable
              />
            </el-form-item>
            
            <el-form-item label="启用TLS" prop="smtp_use_tls">
              <el-switch
                v-model="emailSettings.smtp_use_tls"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button @click="testEmailConfig" :loading="testingEmail">
                测试邮件配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 监控配置 -->
        <el-tab-pane label="监控配置" name="monitor">
          <el-form
            ref="monitorFormRef"
            :model="monitorSettings"
            :rules="monitorRules"
            label-width="140px"
            class="settings-form"
          >
            <el-form-item label="默认监控间隔" prop="default_interval">
              <el-input-number
                v-model="monitorSettings.default_interval"
                :min="1"
                :max="1440"
                :step="1"
              />
              <span class="input-suffix">分钟</span>
              <div class="form-tip">
                新创建服务的默认监控间隔
              </div>
            </el-form-item>
            
            <el-form-item label="默认超时时间" prop="default_timeout">
              <el-input-number
                v-model="monitorSettings.default_timeout"
                :min="1"
                :max="300"
                :step="1"
              />
              <span class="input-suffix">秒</span>
              <div class="form-tip">
                新创建服务的默认超时时间
              </div>
            </el-form-item>
            
            <el-form-item label="数据保留天数" prop="data_retention_days">
              <el-input-number
                v-model="monitorSettings.data_retention_days"
                :min="1"
                :max="365"
                :step="1"
              />
              <span class="input-suffix">天</span>
              <div class="form-tip">
                监控日志数据保留天数，超过此时间的数据将被自动清理
              </div>
            </el-form-item>
            
            <el-form-item label="并发监控数" prop="max_concurrent_checks">
              <el-input-number
                v-model="monitorSettings.max_concurrent_checks"
                :min="1"
                :max="100"
                :step="1"
              />
              <div class="form-tip">
                同时进行监控检查的最大服务数量
              </div>
            </el-form-item>
            
            <el-form-item label="启用监控" prop="monitoring_enabled">
              <el-switch
                v-model="monitorSettings.monitoring_enabled"
                active-text="启用"
                inactive-text="禁用"
              />
              <div class="form-tip">
                全局监控开关，关闭后所有监控任务将停止
              </div>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 系统信息 -->
        <el-tab-pane label="系统信息" name="system">
          <div class="system-info">
            <el-descriptions title="系统信息" :column="2" border>
              <el-descriptions-item label="系统版本">
                {{ systemInfo.version }}
              </el-descriptions-item>
              <el-descriptions-item label="Python版本">
                {{ systemInfo.python_version }}
              </el-descriptions-item>
              <el-descriptions-item label="数据库类型">
                {{ systemInfo.database_type }}
              </el-descriptions-item>
              <el-descriptions-item label="启动时间">
                {{ formatDateTime(systemInfo.start_time) }}
              </el-descriptions-item>
              <el-descriptions-item label="运行时长">
                {{ systemInfo.uptime }}
              </el-descriptions-item>
              <el-descriptions-item label="服务数量">
                {{ systemInfo.service_count }}
              </el-descriptions-item>
              <el-descriptions-item label="告警配置数">
                {{ systemInfo.alert_config_count }}
              </el-descriptions-item>
              <el-descriptions-item label="今日监控次数">
                {{ systemInfo.today_check_count }}
              </el-descriptions-item>
            </el-descriptions>
            
            <div class="system-actions">
              <el-button @click="refreshSystemInfo" :loading="loadingSystemInfo">
                <el-icon><Refresh /></el-icon>
                刷新信息
              </el-button>
              <el-button @click="clearLogs" type="warning">
                <el-icon><Delete /></el-icon>
                清理日志
              </el-button>
              <el-button @click="exportData" type="success">
                <el-icon><Download /></el-icon>
                导出数据
              </el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Check,
  Refresh,
  Delete,
  Download
} from '@element-plus/icons-vue'
import { 
  getSystemSettings, 
  updateSystemSettings, 
  testEmailConfig as apiTestEmailConfig,
  getSystemInfo,
  clearSystemLogs,
  exportSystemData
} from '@/api/services'

const activeTab = ref('email')
const saving = ref(false)
const testingEmail = ref(false)
const loadingSystemInfo = ref(false)

// 表单引用
const emailFormRef = ref()
const monitorFormRef = ref()

// 邮件设置
const emailSettings = reactive({
  smtp_server: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_from_email: '',
  smtp_use_tls: true
})

// 监控设置
const monitorSettings = reactive({
  default_interval: 5,
  default_timeout: 30,
  data_retention_days: 30,
  max_concurrent_checks: 10,
  monitoring_enabled: true
})

// 系统信息
const systemInfo = reactive({
  version: '',
  python_version: '',
  database_type: '',
  start_time: '',
  uptime: '',
  service_count: 0,
  alert_config_count: 0,
  today_check_count: 0
})

// 验证规则
const emailRules = {
  smtp_server: [
    { required: true, message: '请输入SMTP服务器', trigger: 'blur' }
  ],
  smtp_port: [
    { required: true, message: '请输入SMTP端口', trigger: 'blur' }
  ],
  smtp_username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  smtp_password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  smtp_from_email: [
    { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const monitorRules = {
  default_interval: [
    { required: true, message: '请输入默认监控间隔', trigger: 'blur' }
  ],
  default_timeout: [
    { required: true, message: '请输入默认超时时间', trigger: 'blur' }
  ],
  data_retention_days: [
    { required: true, message: '请输入数据保留天数', trigger: 'blur' }
  ],
  max_concurrent_checks: [
    { required: true, message: '请输入并发监控数', trigger: 'blur' }
  ]
}

// 获取系统设置
const fetchSettings = async () => {
  try {
    const response = await getSystemSettings()
    const settings = response
    
    // 填充各个设置
    Object.assign(emailSettings, settings.email || {})
    Object.assign(monitorSettings, settings.monitor || {})
  } catch (error) {
    console.error('获取系统设置失败:', error)
    ElMessage.error('获取系统设置失败')
  }
}

// 获取系统信息
const fetchSystemInfo = async () => {
  try {
    loadingSystemInfo.value = true
    const response = await getSystemInfo()
    Object.assign(systemInfo, response)
  } catch (error) {
    console.error('获取系统信息失败:', error)
    ElMessage.error('获取系统信息失败')
  } finally {
    loadingSystemInfo.value = false
  }
}

// 保存设置
const saveSettings = async () => {
  try {
    saving.value = true
    
    const settings = {
      email: emailSettings,
      monitor: monitorSettings
    }
    
    await updateSystemSettings(settings)
    ElMessage.success('设置保存成功')
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

// 测试邮件配置
const testEmailConfig = async () => {
  if (!emailFormRef.value) return
  
  try {
    await emailFormRef.value.validate()
    testingEmail.value = true
    
    await apiTestEmailConfig(emailSettings)
    ElMessage.success('邮件配置测试成功')
  } catch (error) {
    console.error('邮件配置测试失败:', error)
    ElMessage.error(error.message || '邮件配置测试失败')
  } finally {
    testingEmail.value = false
  }
}

// 刷新系统信息
const refreshSystemInfo = () => {
  fetchSystemInfo()
}

// 清理日志
const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理历史监控日志吗？此操作不可恢复。',
      '确认清理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await clearSystemLogs()
    ElMessage.success('日志清理成功')
    fetchSystemInfo()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清理日志失败:', error)
      ElMessage.error('清理日志失败')
    }
  }
}

// 导出数据
const exportData = async () => {
  try {
    const response = await exportSystemData()
    
    // 创建下载链接
    const blob = new Blob([response], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `monitor-data-${new Date().toISOString().split('T')[0]}.json`
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('数据导出成功')
  } catch (error) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出数据失败')
  }
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 页面加载时获取数据
onMounted(() => {
  fetchSettings()
  fetchSystemInfo()
})
</script>

<style scoped>
.settings-page {
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

.settings-tabs {
  margin-top: 16px;
}

.settings-form {
  max-width: 600px;
  padding: 20px 0;
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

.system-info {
  padding: 20px 0;
}

.system-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.el-form-item {
  margin-bottom: 22px;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
}
</style>