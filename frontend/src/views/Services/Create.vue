<template>
  <div class="service-create">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>添加服务</span>
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
        class="service-form"
      >
        <el-form-item label="服务名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入服务名称"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="监控URL" prop="url">
          <el-input
            v-model="form.url"
            placeholder="请输入监控URL，如：https://api.example.com/health"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="请求方法" prop="method">
          <el-select v-model="form.method" placeholder="请选择请求方法">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="超时时间" prop="timeout">
          <el-input-number
            v-model="form.timeout"
            :min="30"
            :max="300"
            :step="30"
            placeholder="秒"
          />
          <span class="input-suffix">秒</span>
        </el-form-item>
        
        <el-form-item label="监控间隔" prop="interval">
          <el-input-number
            v-model="form.interval"
            :min="30"
            :max="86400"
            :step="30"
            placeholder="秒"
          />
          <span class="input-suffix">秒</span>
        </el-form-item>
        
        <el-form-item label="服务描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入服务描述（可选）"
          />
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
            创建服务
          </el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { createService } from '@/api/services'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

// 表单数据
const form = reactive({
  name: '',
  url: '',
  method: 'GET',
  timeout: 30,
  interval: 300,
  description: '',
  is_active: true
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入服务名称', trigger: 'blur' },
    { min: 2, max: 50, message: '服务名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入监控URL', trigger: 'blur' },
    { 
      pattern: /^https?:\/\/.+/, 
      message: '请输入有效的URL地址', 
      trigger: 'blur' 
    }
  ],
  method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ],
  timeout: [
    { required: true, message: '请输入超时时间', trigger: 'blur' },
    { type: 'number', min: 1, max: 300, message: '超时时间必须在1-300秒之间', trigger: 'blur' }
  ],
  interval: [
    { required: true, message: '请输入监控间隔', trigger: 'blur' },
    { type: 'number', min: 30, max: 86400, message: '监控间隔必须在30-86400秒之间', trigger: 'blur' }
  ]
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    
    await createService(form)
    
    ElMessage.success('服务创建成功')
    router.push('/services')
  } catch (error) {
    console.error('创建服务失败:', error)
    ElMessage.error(error.message || '创建服务失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (!formRef.value) return
  formRef.value.resetFields()
}

// 返回上一页
const goBack = () => {
  router.back()
}
</script>

<style scoped>
.service-create {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.service-form {
  max-width: 600px;
}

.input-suffix {
  margin-left: 8px;
  color: var(--custom-text-color-secondary);
  font-size: 14px;
}

.el-form-item {
  margin-bottom: 22px;
}
</style>