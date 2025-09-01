<template>
  <div class="sidebar">
    <!-- Logo区域 -->
    <div class="sidebar-logo">
      <div class="logo-container">
        <el-icon class="logo-icon">
          <Monitor />
        </el-icon>
        <span v-show="!themeStore.sidebarCollapsed" class="logo-text">
          应用监控平台
        </span>
      </div>
    </div>
    
    <!-- 菜单区域 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="themeStore.sidebarCollapsed"
      :unique-opened="true"
      router
      class="sidebar-menu"
    >
      <template v-for="route in menuRoutes" :key="route.path">
        <el-menu-item 
          v-if="!route.meta?.hidden"
          :index="route.path"
          class="menu-item"
        >
          <el-icon>
            <component :is="route.meta?.icon || 'Document'" />
          </el-icon>
          <template #title>
            <span>{{ route.meta?.title || route.name }}</span>
          </template>
        </el-menu-item>
      </template>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()

// 当前激活的菜单
const activeMenu = computed(() => {
  const { path } = route
  // 处理子路由，返回父级路由
  if (path.includes('/create') || path.includes('/edit') || path.includes('/detail')) {
    return '/' + path.split('/')[1]
  }
  return path
})

// 菜单路由
const menuRoutes = computed(() => {
  return router.getRoutes().filter(route => {
    return route.path !== '/' && !route.meta?.hidden && route.meta?.title
  })
})
</script>

<style lang="scss" scoped>
.sidebar {
  height: 100vh;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  
  &-logo {
    height: var(--header-height);
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid var(--el-border-color-light);
    padding: 0 20px;
    
    .logo-container {
      display: flex;
      align-items: center;
      color: var(--el-color-primary);
      font-weight: 600;
      font-size: 18px;
      
      .logo-icon {
        font-size: 24px;
        margin-right: 12px;
      }
      
      .logo-text {
        white-space: nowrap;
        transition: var(--transition);
      }
    }
  }
  
  &-menu {
    flex: 1;
    border: none;
    
    :deep(.el-menu-item) {
      height: 50px;
      line-height: 50px;
      margin: 4px 8px;
      border-radius: 6px;
      
      &:hover {
        background: var(--el-color-primary-light-9);
        color: var(--el-color-primary);
      }
      
      &.is-active {
        background: var(--el-color-primary);
        color: white;
        
        &::before {
          display: none;
        }
      }
      
      .el-icon {
        margin-right: 8px;
        font-size: 18px;
      }
    }
    
    // 折叠状态下的样式
    &.el-menu--collapse {
      :deep(.el-menu-item) {
        margin: 4px 0;
        padding: 0 4px;
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        box-sizing: border-box;
        
        .el-icon {
          margin-right: 0;
        }
        
        &.is-active {
          background: var(--el-color-primary) !important;
          color: white !important;
          margin: 4px 0 !important;
          padding: 0 4px !important;
        }
        
        &:hover {
          background: var(--el-color-primary-light-9) !important;
          color: var(--el-color-primary) !important;
        }
      }
    }
  }
}

// 全局折叠状态样式
:global(.layout-sidebar.collapsed) {
  .sidebar-logo {
    .logo-container {
      justify-content: center;
      
      .logo-icon {
        margin-right: 0;
      }
      
      .logo-text {
        display: none;
      }
    }
  }
  
  .sidebar-menu {
    :deep(.el-menu-item) {
      display: flex;
      justify-content: center;
      align-items: center;
      text-align: center;
      margin: 4px 0;
      padding: 0 4px;
      width: 100%;
      box-sizing: border-box;
      
      .el-icon {
        margin-right: 0;
      }
      
      &.is-active {
        background: var(--el-color-primary) !important;
        color: white !important;
        margin: 4px 0 !important;
        padding: 0 4px !important;
      }
      
      &:hover {
        background: var(--el-color-primary-light-9) !important;
        color: var(--el-color-primary) !important;
      }
    }
  }
}

// 暗色主题适配
.dark {
  .sidebar {
    background: var(--el-bg-color);
    border-right-color: var(--el-border-color);
    
    &-logo {
      border-bottom-color: var(--el-border-color);
    }
  }
}
</style>