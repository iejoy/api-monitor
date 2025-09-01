<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <div 
      class="layout-sidebar"
      :class="{ collapsed: themeStore.sidebarCollapsed }"
    >
      <Sidebar />
    </div>
    
    <!-- 主内容区 -->
    <div class="layout-main">
      <!-- 顶部导航 -->
      <div class="layout-header">
        <Header />
      </div>
      
      <!-- 内容区域 -->
      <div class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
    
    <!-- 移动端遮罩 -->
    <div 
      v-if="isMobile && !themeStore.sidebarCollapsed"
      class="mobile-overlay"
      @click="themeStore.toggleSidebar"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useThemeStore } from '@/stores/theme'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const themeStore = useThemeStore()
const isMobile = ref(false)

// 检测移动端
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value && !themeStore.sidebarCollapsed) {
    themeStore.toggleSidebar()
  }
}

onMounted(() => {
  themeStore.initSidebar()
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style lang="scss" scoped>
.layout {
  display: flex;
  height: 100vh;
  
  &-sidebar {
    width: var(--sidebar-width);
    transition: var(--transition);
    position: relative;
    z-index: 100;
    
    &.collapsed {
      width: var(--sidebar-collapsed-width);
    }
    
    @media (max-width: 768px) {
      position: fixed;
      left: 0;
      top: 0;
      height: 100vh;
      z-index: 1000;
      transform: translateX(-100%);
      
      &:not(.collapsed) {
        transform: translateX(0);
      }
    }
  }
  
  &-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    
    @media (max-width: 768px) {
      margin-left: 0;
    }
  }
  
  &-header {
    height: var(--header-height);
    border-bottom: 1px solid var(--el-border-color-light);
    background: var(--el-bg-color);
    position: relative;
    z-index: 99;
  }
  
  &-content {
    flex: 1;
    padding: 12px;
    overflow-y: auto;
    background: var(--el-bg-color-page);
    
    @media (max-width: 768px) {
      padding: 8px;
    }
  }
}

.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--custom-box-shadow);
  z-index: 999;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>