import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import Layout from '@/components/Layout/index.vue'

// 配置NProgress
NProgress.configure({ 
  showSpinner: false,
  minimum: 0.2,
  speed: 500
})

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard/index.vue'),
        meta: {
          title: '仪表板',
          icon: 'Odometer'
        }
      },
      {
        path: 'services',
        name: 'Services',
        component: () => import('@/views/Services/index.vue'),
        meta: {
          title: '服务管理',
          icon: 'Monitor'
        }
      },
      {
        path: 'services/create',
        name: 'ServiceCreate',
        component: () => import('@/views/Services/Create.vue'),
        meta: {
          title: '添加服务',
          icon: 'Plus',
          hidden: true
        }
      },
      {
        path: 'services/:id/edit',
        name: 'ServiceEdit',
        component: () => import('@/views/Services/Edit.vue'),
        meta: {
          title: '编辑服务',
          icon: 'Edit',
          hidden: true
        }
      },
      {
        path: 'services/:id/detail',
        name: 'ServiceDetail',
        component: () => import('@/views/Services/Detail.vue'),
        meta: {
          title: '服务详情',
          icon: 'View',
          hidden: true
        }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs/index.vue'),
        meta: {
          title: '监控日志',
          icon: 'DocumentCopy'
        }
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: () => import('@/views/Alerts/index.vue'),
        meta: {
          title: '告警配置',
          icon: 'Bell'
        }
      },
      {
        path: 'alerts/create',
        name: 'AlertCreate',
        component: () => import('@/views/Alerts/Create.vue'),
        meta: {
          title: '添加告警配置',
          icon: 'Plus',
          hidden: true
        }
      },
      {
        path: 'alerts/:id/edit',
        name: 'AlertEdit',
        component: () => import('@/views/Alerts/Edit.vue'),
        meta: {
          title: '编辑告警配置',
          icon: 'Edit',
          hidden: true
        }
      },
      {
        path: 'alerts/:id/detail',
        name: 'AlertDetail',
        component: () => import('@/views/Alerts/Detail.vue'),
        meta: {
          title: '告警配置详情',
          icon: 'View',
          hidden: true
        }
      },
      {
        path: 'templates',
        name: 'Templates',
        component: () => import('@/views/Templates/index.vue'),
        meta: {
          title: '配置模板',
          icon: 'Files'
        }
      },
      {
        path: 'templates/create',
        name: 'TemplateCreate',
        component: () => import('@/views/Templates/Create.vue'),
        meta: {
          title: '创建配置模板',
          icon: 'Plus',
          hidden: true
        }
      },
      {
        path: 'templates/:id/edit',
        name: 'TemplateEdit',
        component: () => import('@/views/Templates/Edit.vue'),
        meta: {
          title: '编辑配置模板',
          icon: 'Edit',
          hidden: true
        }
      },
      {
        path: 'templates/:id/detail',
        name: 'TemplateDetail',
        component: () => import('@/views/Templates/Detail.vue'),
        meta: {
          title: '配置模板详情',
          icon: 'View',
          hidden: true
        }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings/index.vue'),
        meta: {
          title: '系统设置',
          icon: 'Setting'
        }
      }
    ]
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/Error/404.vue'),
    meta: {
      title: '页面不存在',
      hidden: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  NProgress.start()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 业务应用监控平台`
  } else {
    document.title = '业务应用监控平台'
  }
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router