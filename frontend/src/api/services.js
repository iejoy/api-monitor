import { request } from '@/utils/request'

// 服务管理相关API
export const servicesApi = {
  // 获取服务列表
  getServices(params = {}) {
    return request.get('/services/', params)
  },

  // 获取服务详情
  getService(id) {
    return request.get(`/services/${id}`)
  },

  // 创建服务
  createService(data) {
    return request.post('/services/', data)
  },

  // 更新服务
  updateService(id, data) {
    return request.put(`/services/${id}`, data)
  },

  // 删除服务
  deleteService(id) {
    return request.delete(`/services/${id}`)
  },

  // 切换服务状态
  toggleService(id) {
    return request.post(`/services/${id}/toggle`)
  },

  // 测试服务
  testService(id) {
    return request.post(`/services/${id}/test`)
  },

  // 获取服务统计
  getServiceStats(id) {
    return request.get(`/services/${id}/stats`)
  },

  // 获取服务监控日志
  getServiceLogs(id, params = {}) {
    return request.get(`/services/${id}/logs`, params)
  }
}

// 监控日志相关API
export const logsApi = {
  // 获取监控日志列表
  getMonitorLogs(params = {}) {
    return request.get('/logs/', params)
  },

  // 获取日志详情
  getLog(id) {
    return request.get(`/logs/${id}`)
  },

  // 删除日志
  deleteLog(id) {
    return request.delete(`/logs/${id}`)
  },

  // 批量删除日志
  batchDeleteLogs(params = {}) {
    return request.delete('/logs/', params)
  },

  // 获取监控统计
  getMonitorStats(params = {}) {
    return request.get('/logs/stats/overview', params)
  },

  // 获取时间线统计
  getTimelineStats(params = {}) {
    return request.get('/logs/stats/timeline', params)
  }
}

// 告警配置相关API
export const alertsApi = {
  // 获取告警配置列表
  getAlertConfigs(params = {}) {
    return request.get('/alerts/', params)
  },

  // 获取告警配置详情
  getAlertConfig(id) {
    return request.get(`/alerts/${id}`)
  },

  // 创建告警配置
  createAlertConfig(data) {
    return request.post('/alerts/', data)
  },

  // 更新告警配置
  updateAlertConfig(id, data) {
    return request.put(`/alerts/${id}`, data)
  },

  // 删除告警配置
  deleteAlertConfig(id) {
    return request.delete(`/alerts/${id}`)
  },

  // 切换告警配置状态
  toggleAlertConfig(id) {
    return request.post(`/alerts/${id}/toggle`)
  },

  // 测试告警配置
  testAlertConfig(id, data = null) {
    if (id) {
      return request.post(`/alerts/${id}/test`, data)
    } else {
      return request.post('/alerts/test', data)
    }
  },

  // 获取指定服务的告警配置
  getServiceAlertConfig(serviceId) {
    return request.get(`/alerts/service/${serviceId}`)
  },

  // 获取告警模板列表
  getAlertTemplates(params = {}) {
    return request.get('/settings/alert-templates/', params)
  },

  // 获取告警模板详情
  getAlertTemplate(id) {
    return request.get(`/settings/alert-templates/${id}`)
  },

  // 创建告警模板
  createAlertTemplate(data) {
    return request.post('/settings/alert-templates/', data)
  },

  // 更新告警模板
  updateAlertTemplate(id, data) {
    return request.put(`/settings/alert-templates/${id}`, data)
  },

  // 删除告警模板
  deleteAlertTemplate(id) {
    return request.delete(`/settings/alert-templates/${id}`)
  }
}

// 仪表板相关API
export const dashboardApi = {
  // 获取仪表板概览
  getOverview() {
    return request.get('/dashboard/overview')
  },

  // 获取仪表板统计数据
  getStats() {
    return request.get('/dashboard/stats')
  },

  // 获取图表数据
  getCharts(params = {}) {
    return request.get('/dashboard/charts', params)
  },

  // 获取服务状态
  getServicesStatus() {
    return request.get('/dashboard/services/status')
  },

  // 获取最近告警
  getRecentAlerts(params = {}) {
    return request.get('/dashboard/alerts/recent', params)
  },

  // 获取按小时统计的监控数据
  getHourlyStats(params = {}) {
    return request.get('/dashboard/hourly-stats', params)
  },

  // 获取响应时间分布统计
  getResponseTimeStats(params = {}) {
    return request.get('/dashboard/response-time-stats', params)
  },

  // 获取高可用统计
  getAvailabilityStats(params = {}) {
    return request.get('/dashboard/availability-stats', params)
  },

  // 获取系统健康状态
  getSystemHealth() {
    return request.get('/dashboard/health')
  }
}

// 系统设置相关API
export const settingsApi = {
  // 获取系统设置
  getSystemSettings() {
    return request.get('/settings/')
  },

  // 更新系统设置
  updateSystemSettings(data) {
    return request.put('/settings/', data)
  },

  // 测试邮件配置
  testEmailConfig(data) {
    return request.post('/settings/test/email', data)
  },

  // 测试飞书配置
  testFeishuConfig(data) {
    return request.post('/settings/test/feishu', data)
  },

  // 测试微信配置
  testWechatConfig(data) {
    return request.post('/settings/test/wechat', data)
  },

  // 获取系统信息
  getSystemInfo() {
    return request.get('/settings/system/info')
  },

  // 清理系统日志
  clearSystemLogs() {
    return request.post('/settings/system/clear-logs')
  },

  // 导出系统数据
  exportSystemData() {
    return request.get('/settings/system/export', { responseType: 'blob' })
  },

  // 获取告警模板列表
  getAlertTemplates(params = {}) {
    return request.get('/settings/alert-templates/', params)
  },

  // 获取告警模板详情
  getAlertTemplate(id) {
    return request.get(`/settings/alert-templates/${id}`)
  },

  // 创建告警模板
  createAlertTemplate(data) {
    return request.post('/settings/alert-templates/', data)
  },

  // 更新告警模板
  updateAlertTemplate(id, data) {
    return request.put(`/settings/alert-templates/${id}`, data)
  },

  // 删除告警模板
  deleteAlertTemplate(id) {
    return request.delete(`/settings/alert-templates/${id}`)
  }
}

// 导出统一的API接口，保持向后兼容
export const getServices = servicesApi.getServices
export const getService = servicesApi.getService
export const createService = servicesApi.createService
export const updateService = servicesApi.updateService
export const deleteService = servicesApi.deleteService
export const getServiceLogs = servicesApi.getServiceLogs

export const getMonitorLogs = logsApi.getMonitorLogs

export const getAlertConfigs = alertsApi.getAlertConfigs
export const getAlertConfig = alertsApi.getAlertConfig
export const createAlertConfig = alertsApi.createAlertConfig
export const updateAlertConfig = alertsApi.updateAlertConfig
export const deleteAlertConfig = alertsApi.deleteAlertConfig
export const testAlertConfig = alertsApi.testAlertConfig

export const getSystemSettings = settingsApi.getSystemSettings
export const updateSystemSettings = settingsApi.updateSystemSettings
export const testEmailConfig = settingsApi.testEmailConfig
export const testFeishuConfig = settingsApi.testFeishuConfig
export const testWechatConfig = settingsApi.testWechatConfig
export const getSystemInfo = settingsApi.getSystemInfo
export const clearSystemLogs = settingsApi.clearSystemLogs
export const exportSystemData = settingsApi.exportSystemData

// 默认导出所有API
export default {
  services: servicesApi,
  logs: logsApi,
  alerts: alertsApi,
  dashboard: dashboardApi,
  settings: settingsApi
}