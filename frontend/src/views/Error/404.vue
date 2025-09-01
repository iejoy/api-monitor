<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-code">404</div>
      <div class="error-message">页面不存在</div>
      <div class="error-description">
        抱歉，您访问的页面不存在或已被删除
      </div>
      <div class="error-actions">
        <el-button type="primary" @click="goHome">
          返回首页
        </el-button>
        <el-button @click="goBack">
          返回上页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style lang="scss" scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--el-bg-color-page);
  
  .error-content {
    text-align: center;
    
    .error-code {
      font-size: 120px;
      font-weight: bold;
      color: var(--el-color-primary);
      line-height: 1;
      margin-bottom: 20px;
    }
    
    .error-message {
      font-size: 24px;
      color: var(--el-text-color-primary);
      margin-bottom: 12px;
    }
    
    .error-description {
      font-size: 16px;
      color: var(--el-text-color-regular);
      margin-bottom: 30px;
    }
    
    .error-actions {
      .el-button {
        margin: 0 8px;
      }
    }
  }
}
</style>