<template>
  <div class="header">
    <div class="header-left">
      <!-- 折叠按钮 -->
      <el-button
        type="text"
        class="collapse-btn"
        @click="themeStore.toggleSidebar"
      >
        <el-icon>
          <Expand v-if="themeStore.sidebarCollapsed" />
          <Fold v-else />
        </el-icon>
      </el-button>
      
      <!-- 面包屑导航 -->
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item 
          v-for="item in breadcrumbList" 
          :key="item.path"
          :to="item.path === route.path ? '' : item.path"
        >
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    
    <div class="header-right">
      <!-- 刷新按钮 -->
      <el-tooltip content="刷新页面" placement="bottom">
        <el-button
          type="text"
          class="header-btn"
          @click="refreshPage"
        >
          <el-icon>
            <Refresh />
          </el-icon>
        </el-button>
      </el-tooltip>
      
      <!-- 全屏按钮 -->
      <el-tooltip content="全屏" placement="bottom">
        <el-button
          type="text"
          class="header-btn"
          @click="toggleFullscreen"
        >
          <el-icon>
            <FullScreen />
          </el-icon>
        </el-button>
      </el-tooltip>
      
      <!-- 主题切换 -->
      <el-tooltip :content="themeStore.isDark ? '切换到亮色主题' : '切换到暗色主题'" placement="bottom">
        <el-button
          type="text"
          class="header-btn"
          @click="themeStore.toggleTheme"
        >
          <el-icon>
            <Sunny v-if="themeStore.isDark" />
            <Moon v-else />
          </el-icon>
        </el-button>
      </el-tooltip>
      
      <!-- 系统状态 -->
      <div class="system-status">
        <el-badge 
          :value="displayAlerts" 
          :hidden="displayAlerts === 0"
          type="danger"
        >
          <el-dropdown @command="handleAlertCommand">
            <el-button
              type="text"
              class="header-btn"
            >
              <el-icon>
                <Bell />
              </el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="view">
                  <el-icon><View /></el-icon>
                  查看告警
                </el-dropdown-item>
                <el-dropdown-item command="clear" :disabled="displayAlerts === 0">
                  <el-icon><Delete /></el-icon>
                  清除数字
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-badge>
      </div>
      
      <!-- 用户菜单 -->
      <el-dropdown class="user-dropdown" @command="handleUserCommand">
        <div class="user-info">
          <el-avatar :size="32" class="user-avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="user-name">管理员</span>
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人信息
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              系统设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dashboardApi } from '@/api/services'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()

// 系统状态
const systemStatus = ref({
  alerts: 0,
  services: 0,
  healthy: 0
})

// 告警清除状态
const alertsCleared = ref(false)
const alertsClearedTime = ref(0)

// 显示的告警数量（考虑清除状态）
const displayAlerts = computed(() => {
  if (alertsCleared.value) {
    return 0
  }
  return systemStatus.value.alerts
})

// 面包屑导航
const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  const breadcrumbs = []
  
  // 添加首页
  if (route.path !== '/dashboard') {
    breadcrumbs.push({
      path: '/dashboard',
      title: '首页'
    })
  }
  
  // 添加当前路由
  matched.forEach(item => {
    if (item.path !== '/') {
      breadcrumbs.push({
        path: item.path,
        title: item.meta.title
      })
    }
  })
  
  return breadcrumbs
})

// 刷新页面
const refreshPage = () => {
  window.location.reload()
}

// 全屏切换
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

// 检查告警清除状态
const checkAlertsClearedStatus = () => {
  const cleared = localStorage.getItem('alertsCleared')
  const clearedTime = localStorage.getItem('alertsClearedTime')
  
  if (cleared === 'true' && clearedTime) {
    const timeDiff = Date.now() - parseInt(clearedTime)
    // 如果清除时间超过1小时，重置清除状态
    if (timeDiff > 60 * 60 * 1000) {
      localStorage.removeItem('alertsCleared')
      localStorage.removeItem('alertsClearedTime')
      alertsCleared.value = false
    } else {
      alertsCleared.value = true
      alertsClearedTime.value = parseInt(clearedTime)
    }
  }
}

// 告警菜单操作
const handleAlertCommand = (command) => {
  switch (command) {
    case 'view':
      router.push('/logs')
      break
    case 'clear':
      ElMessageBox.confirm(
        '确定要清除告警数字吗？这不会删除实际的告警记录，清除状态将保持1小时。',
        '确认清除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(() => {
        alertsCleared.value = true
        alertsClearedTime.value = Date.now()
        localStorage.setItem('alertsCleared', 'true')
        localStorage.setItem('alertsClearedTime', alertsClearedTime.value.toString())
        ElMessage.success('告警数字已清除，1小时后自动恢复')
      }).catch(() => {
        // 用户取消操作
      })
      break
  }
}

// 用户菜单操作
const handleUserCommand = (command) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人信息功能开发中...')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      ElMessage.info('退出登录功能开发中...')
      break
  }
}

// 获取系统状态
const getSystemStatus = async () => {
  try {
    const data = await dashboardApi.getOverview()
    systemStatus.value = {
      alerts: data.alerts?.today_alerts || 0,
      services: data.services?.total || 0,
      healthy: data.services?.healthy || 0
    }
    
    // 检查是否有新的告警，如果有则重置清除状态
    if (data.alerts?.recent_alerts > 0 && alertsCleared.value) {
      const clearedTime = alertsClearedTime.value
      const lastUpdateTime = data.alerts?.last_alert_time ? new Date(data.alerts.last_alert_time).getTime() : 0
      
      // 如果有新告警产生在清除时间之后，重置清除状态
      if (lastUpdateTime > clearedTime) {
        alertsCleared.value = false
        localStorage.removeItem('alertsCleared')
        localStorage.removeItem('alertsClearedTime')
      }
    }
  } catch (error) {
    console.error('获取系统状态失败:', error)
  }
}

onMounted(() => {
  checkAlertsClearedStatus()
  getSystemStatus()
  // 定时更新系统状态
  setInterval(getSystemStatus, 30000) // 30秒更新一次
})
</script>

<style lang="scss" scoped>
.header {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--el-bg-color);
  
  &-left {
    display: flex;
    align-items: center;
    
    .collapse-btn {
      margin-right: 16px;
      color: var(--el-text-color-regular);
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      padding: 0;
      
      &:hover {
        color: var(--el-color-primary);
        background: var(--el-bg-color-page);
      }
      
      .el-icon {
        font-size: 18px;
      }
    }
    
    .breadcrumb {
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: var(--el-text-color-regular);
          font-weight: normal;
          
          &:hover {
            color: var(--el-color-primary);
          }
        }
        
        &:last-child {
          .el-breadcrumb__inner {
            color: var(--el-text-color-primary);
            font-weight: 500;
          }
        }
      }
    }
  }
  
  &-right {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .header-btn {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      color: var(--el-text-color-regular);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;
      
      &:hover {
        background: var(--el-bg-color-page);
        color: var(--el-color-primary);
      }
      
      .el-icon {
        font-size: 18px;
      }
    }
    
    .system-status {
      margin: 0 8px;
    }
    
    .user-dropdown {
      margin-left: 8px;
      
      .user-info {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-radius: 20px;
        cursor: pointer;
        transition: var(--transition);
        
        &:hover {
          background: var(--el-bg-color-page);
        }
        
        .user-avatar {
          margin-right: 8px;
        }
        
        .user-name {
          margin-right: 4px;
          font-size: 14px;
          color: var(--el-text-color-primary);
        }
        
        .dropdown-icon {
          font-size: 12px;
          color: var(--el-text-color-regular);
        }
      }
    }
  }
}

// 移动端适配
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
    
    &-left {
      .breadcrumb {
        display: none;
      }
    }
    
    &-right {
      .user-name {
        display: none;
      }
    }
  }
}
</style>