<template>
  <div class="dashboard">
    <!-- 核心指标卡片 -->
    <div class="metrics-section">
      <div class="metric-card primary">
        <div class="metric-icon">
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ overview.services?.total || 0 }}</div>
          <div class="metric-label">总服务数</div>
        </div>
      </div>
      
      <div class="metric-card success">
        <div class="metric-icon">
          <el-icon><CircleCheckFilled /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ overview.services?.healthy || 0 }}</div>
          <div class="metric-label">健康服务</div>
        </div>
      </div>
      
      <div class="metric-card danger">
        <div class="metric-icon">
          <el-icon><CircleCloseFilled /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ overview.services?.unhealthy || 0 }}</div>
          <div class="metric-label">异常服务</div>
        </div>
      </div>
      
      <div class="metric-card warning">
        <div class="metric-icon">
          <el-icon><BellFilled /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ overview.alerts?.today_alerts || 0 }}</div>
          <div class="metric-label">今日告警</div>
        </div>
      </div>
    </div>

    <!-- 主要图表区域 -->
    <div class="charts-section">
      <!-- 监控趋势 -->
      <div class="chart-container large">
        <div class="chart-header">
          <div class="chart-title">
            <h3>监控趋势分析</h3>
            <p>服务健康状态和响应时间趋势</p>
          </div>
          <div class="chart-controls">
            <el-radio-group v-model="trendPeriod" size="small" @change="loadTrendData">
              <el-radio-button label="24h">24小时</el-radio-button>
              <el-radio-button label="7d">7天</el-radio-button>
              <el-radio-button label="30d">30天</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="chart-body">
          <v-chart 
            class="chart" 
            :option="trendChartOption" 
            :loading="trendLoading"
            autoresize
          />
        </div>
      </div>
      
      <!-- 响应时间分布 -->
      <div class="chart-container medium">
        <div class="chart-header">
          <div class="chart-title">
            <h3>响应时间分布</h3>
            <p>过去7天的响应时间统计</p>
          </div>
        </div>
        <div class="chart-body">
          <v-chart 
            class="chart" 
            :option="responseTimeChartOption" 
            :loading="responseTimeLoading"
            autoresize
          />
        </div>
      </div>
    </div>

    <!-- 高可用统计区域 -->
    <div class="availability-section">
      <div class="section-header">
        <div class="section-title">
          <h3>应用高可用统计</h3>
          <p>基于过去{{ availabilityPeriod }}天的监控数据分析</p>
        </div>
        <div class="section-controls">
          <el-radio-group v-model="availabilityPeriod" size="small" @change="loadAvailabilityData">
            <el-radio-button label="7">7天</el-radio-button>
            <el-radio-button label="30">30天</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <div class="availability-content">
        <!-- 统计概览 -->
        <div class="availability-overview">
          <div class="overview-card high">
            <div class="overview-header">
              <div class="overview-icon">
                <el-icon><SuccessFilled /></el-icon>
              </div>
              <div class="overview-badge">优秀</div>
            </div>
            <div class="overview-body">
              <div class="overview-value">{{ availabilitySummary.high_availability }}</div>
              <div class="overview-label">高可用</div>
              <div class="overview-desc">可用性 ≥ 99%</div>
            </div>
            <div class="overview-footer">
              <div class="progress-bar">
                <div class="progress-fill high" :style="{ width: getProgressWidth('high') }"></div>
              </div>
            </div>
          </div>
          
          <div class="overview-card medium">
            <div class="overview-header">
              <div class="overview-icon">
                <el-icon><WarningFilled /></el-icon>
              </div>
              <div class="overview-badge">良好</div>
            </div>
            <div class="overview-body">
              <div class="overview-value">{{ availabilitySummary.medium_availability }}</div>
              <div class="overview-label">中等可用</div>
              <div class="overview-desc">95% ≤ 可用性 < 99%</div>
            </div>
            <div class="overview-footer">
              <div class="progress-bar">
                <div class="progress-fill medium" :style="{ width: getProgressWidth('medium') }"></div>
              </div>
            </div>
          </div>
          
          <div class="overview-card low">
            <div class="overview-header">
              <div class="overview-icon">
                <el-icon><CircleCloseFilled /></el-icon>
              </div>
              <div class="overview-badge">需改进</div>
            </div>
            <div class="overview-body">
              <div class="overview-value">{{ availabilitySummary.low_availability }}</div>
              <div class="overview-label">较低可用</div>
              <div class="overview-desc">可用性 < 95%</div>
            </div>
            <div class="overview-footer">
              <div class="progress-bar">
                <div class="progress-fill low" :style="{ width: getProgressWidth('low') }"></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 详细图表 -->
        <div class="availability-charts">
          <!-- 应用可用性图表 -->
          <div class="chart-container">
            <div class="chart-header">
              <div class="chart-title">
                <div class="chart-title-with-icon">
                  <el-icon class="chart-icon"><TrendCharts /></el-icon>
                  <h3>应用可用性分析</h3>
                </div>
                <p>各应用的可用性百分比统计</p>
              </div>
            </div>
            <div class="chart-body">
              <v-chart 
                class="chart" 
                :option="availabilityOnlyChartOption" 
                :loading="availabilityLoading"
                autoresize
              />
            </div>
          </div>
          
          <!-- 应用响应时间图表 -->
          <div class="chart-container">
            <div class="chart-header">
              <div class="chart-title">
                <div class="chart-title-with-icon">
                  <el-icon class="chart-icon"><Timer /></el-icon>
                  <h3>应用响应时间分析</h3>
                </div>
                <p>各应用的平均响应时间对比</p>
              </div>
            </div>
            <div class="chart-body">
              <v-chart 
                class="chart" 
                :option="responseTimeByServiceChartOption" 
                :loading="availabilityLoading"
                autoresize
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细数据区域 -->
    <div class="details-section">
      <!-- 服务状态 -->
      <div class="detail-container">
        <div class="detail-header">
          <div class="detail-title">
            <h3>服务状态监控</h3>
            <p>实时服务健康状态</p>
          </div>
          <el-button 
            type="primary" 
            size="small" 
            @click="$router.push('/services')"
          >
            查看全部
          </el-button>
        </div>
        <div class="detail-body">
          <el-table 
            :data="servicesStatus" 
            v-loading="servicesLoading"
            :height="320"
            :show-header="true"
          >
            <el-table-column prop="name" label="服务名称" min-width="120" />
            <el-table-column prop="url" label="服务地址" min-width="180" show-overflow-tooltip />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <div class="status-badge" :class="`status-${getStatusType(row.status)}`">
                  <div class="status-dot"></div>
                  <span>{{ getStatusText(row.status) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="响应时间" width="100">
              <template #default="{ row }">
                <span class="response-time">
                  {{ row.response_time ? `${row.response_time}ms` : '-' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="最后检查" width="140">
              <template #default="{ row }">
                <span class="check-time">{{ formatTime(row.last_check_time) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      
      <!-- 今天的告警记录 -->
      <div class="detail-container">
        <div class="detail-header">
          <div class="detail-title">
            <h3>今天的告警记录</h3>
            <p>今日系统异常告警信息</p>
          </div>
          <el-button 
            type="primary" 
            size="small" 
            @click="$router.push('/logs')"
          >
            查看全部
          </el-button>
        </div>
        <div class="detail-body">
          <el-table 
            :data="recentAlerts" 
            v-loading="alertsLoading"
            :height="320"
            :show-header="true"
          >
            <el-table-column prop="service_name" label="服务名称" min-width="120" />
            <el-table-column label="告警级别" width="100">
              <template #default="{ row }">
                <div class="alert-level danger">
                  <el-icon><WarningFilled /></el-icon>
                  <span>严重</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" min-width="180" show-overflow-tooltip />
            <el-table-column label="告警时间" width="140">
              <template #default="{ row }">
                <span class="alert-time">{{ formatTime(row.check_time) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { dashboardApi } from '@/api/services'
import dayjs from 'dayjs'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

// 数据状态
const overview = ref({})
const servicesStatus = ref([])
const recentAlerts = ref([])
const trendPeriod = ref('24h')
const availabilityPeriod = ref('7')
const availabilityData = ref([])
const availabilitySummary = ref({
  high_availability: 0,
  medium_availability: 0,
  low_availability: 0
})

// 加载状态
const servicesLoading = ref(false)
const alertsLoading = ref(false)
const trendLoading = ref(false)
const responseTimeLoading = ref(false)
const availabilityLoading = ref(false)

// 图表配置
const trendChartOption = ref({})
const responseTimeChartOption = ref({})
const availabilityOnlyChartOption = ref({})
const responseTimeByServiceChartOption = ref({})

// 定时器
let refreshTimer = null

// 计算进度条宽度
const getProgressWidth = (type) => {
  const total = availabilitySummary.value.high_availability + 
                availabilitySummary.value.medium_availability + 
                availabilitySummary.value.low_availability
  if (total === 0) return '0%'
  
  const value = availabilitySummary.value[`${type}_availability`]
  return `${(value / total * 100)}%`
}

// 获取概览数据
const loadOverview = async () => {
  try {
    const data = await dashboardApi.getOverview()
    overview.value = data
  } catch (error) {
    console.error('获取概览数据失败:', error)
  }
}

// 获取服务状态
const loadServicesStatus = async () => {
  servicesLoading.value = true
  try {
    const data = await dashboardApi.getServicesStatus()
    servicesStatus.value = data.services.slice(0, 10)
  } catch (error) {
    console.error('获取服务状态失败:', error)
  } finally {
    servicesLoading.value = false
  }
}

// 获取今天的告警记录
const loadRecentAlerts = async () => {
  alertsLoading.value = true
  try {
    const data = await dashboardApi.getRecentAlerts({ limit: 10, today_only: true })
    recentAlerts.value = data.alerts
  } catch (error) {
    console.error('获取今天告警失败:', error)
  } finally {
    alertsLoading.value = false
  }
}

// 获取趋势数据
const loadTrendData = async () => {
  trendLoading.value = true
  try {
    const hours = trendPeriod.value === '24h' ? 24 : trendPeriod.value === '7d' ? 168 : 720
    const data = await dashboardApi.getHourlyStats({ hours })
    
    const times = []
    const successRates = []
    const totalChecks = []
    
    data.hourly_stats.forEach(item => {
      times.push(dayjs(item.hour).format('MM-DD HH:mm'))
      successRates.push(item.success_rate)
      totalChecks.push(item.total_checks)
    })
    
    trendChartOption.value = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['成功率', '检查次数']
      },
      xAxis: {
        type: 'category',
        data: times
      },
      yAxis: [
        {
          type: 'value',
          name: '成功率(%)',
          min: 0,
          max: 100
        },
        {
          type: 'value',
          name: '检查次数'
        }
      ],
      series: [
        {
          name: '成功率',
          type: 'line',
          data: successRates,
          smooth: true,
          lineStyle: {
            color: '#67C23A',
            width: 3
          },
          itemStyle: {
            color: '#67C23A'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0, color: 'rgba(103, 194, 58, 0.3)'
              }, {
                offset: 1, color: 'rgba(103, 194, 58, 0.05)'
              }]
            }
          }
        },
        {
          name: '检查次数',
          type: 'line',
          yAxisIndex: 1,
          data: totalChecks,
          smooth: true,
          lineStyle: {
            color: '#409EFF',
            width: 2
          },
          itemStyle: {
            color: '#409EFF'
          }
        }
      ]
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
  } finally {
    trendLoading.value = false
  }
}

// 获取响应时间分布
const loadResponseTimeData = async () => {
  responseTimeLoading.value = true
  try {
    const data = await dashboardApi.getResponseTimeStats({ days: 7 })
    
    const pieData = data.distribution.map(item => ({
      name: item.range,
      value: item.count
    }))
    
    responseTimeChartOption.value = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '响应时间分布',
          type: 'pie',
          radius: ['40%', '70%'],
          data: pieData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.2)'
            }
          }
        }
      ]
    }
  } catch (error) {
    console.error('获取响应时间数据失败:', error)
  } finally {
    responseTimeLoading.value = false
  }
}

// 获取高可用统计数据
const loadAvailabilityData = async () => {
  availabilityLoading.value = true
  try {
    const data = await dashboardApi.getAvailabilityStats({ days: parseInt(availabilityPeriod.value) })
    availabilityData.value = data.services
    availabilitySummary.value = data.summary
    
    const serviceNames = data.services.map(item => item.service_name)
    const availabilityValues = data.services.map(item => item.availability)
    const responseTimeValues = data.services.map(item => item.avg_response_time)
    
    // 可用性图表配置
    availabilityOnlyChartOption.value = {
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          return `${params[0].name}<br/>可用性: ${params[0].value}%`
        }
      },
      xAxis: {
        type: 'category',
        data: serviceNames,
        axisLabel: {
          rotate: 45,
          interval: 0
        }
      },
      yAxis: {
        type: 'value',
        name: '可用性(%)',
        min: 0,
        max: 100
      },
      series: [
        {
          name: '可用性',
          type: 'bar',
          data: availabilityValues,
          itemStyle: {
            color: function(params) {
              const value = params.value
              if (value >= 99) return '#67C23A'
              if (value >= 95) return '#E6A23C'
              return '#F56C6C'
            }
          }
        }
      ]
    }
    
    // 响应时间图表配置
    responseTimeByServiceChartOption.value = {
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          return `${params[0].name}<br/>平均响应时间: ${params[0].value}ms`
        }
      },
      xAxis: {
        type: 'category',
        data: serviceNames,
        axisLabel: {
          rotate: 45,
          interval: 0
        }
      },
      yAxis: {
        type: 'value',
        name: '响应时间(ms)'
      },
      series: [
        {
          name: '平均响应时间',
          type: 'line',
          data: responseTimeValues,
          smooth: true,
          lineStyle: {
            color: '#409EFF',
            width: 3
          },
          itemStyle: {
            color: '#409EFF'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0, color: 'rgba(64, 158, 255, 0.3)'
              }, {
                offset: 1, color: 'rgba(64, 158, 255, 0.05)'
              }]
            }
          }
        }
      ]
    }
  } catch (error) {
    console.error('获取高可用统计失败:', error)
  } finally {
    availabilityLoading.value = false
  }
}

// 工具函数
const getStatusType = (status) => {
  const statusMap = {
    'success': 'success',
    'healthy': 'success',
    'failed': 'danger',
    'timeout': 'warning',
    'unhealthy': 'danger',
    'unknown': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'success': '正常',
    'healthy': '正常',
    'failed': '异常',
    'timeout': '超时',
    'unhealthy': '异常',
    'unknown': '未知'
  }
  return statusMap[status] || '未知'
}

const formatTime = (time) => {
  return time ? dayjs(time).format('MM-DD HH:mm') : '-'
}

// 初始化数据
const initData = async () => {
  await Promise.all([
    loadOverview(),
    loadServicesStatus(),
    loadRecentAlerts(),
    loadTrendData(),
    loadResponseTimeData(),
    loadAvailabilityData()
  ])
}

onMounted(() => {
  initData()
  refreshTimer = setInterval(() => {
    loadOverview()
    loadServicesStatus()
    loadRecentAlerts()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 100%;
  overflow-x: hidden;
  padding: 0;
}

.metrics-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.metric-card {
  background: var(--custom-bg-color);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent-color);
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.metric-card.primary {
  --accent-color: var(--el-color-primary);
}

.metric-card.success {
  --accent-color: var(--el-color-success);
}

.metric-card.danger {
  --accent-color: var(--el-color-danger);
}

.metric-card.warning {
  --accent-color: var(--el-color-warning);
}

.metric-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--accent-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--custom-text-color-primary);
  margin-bottom: 2px;
  font-family: var(--custom-font-family);
}

.metric-label {
  font-size: 13px;
  color: var(--custom-text-color-regular);
  font-family: var(--custom-font-family);
}

.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

@media (max-width: 1200px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
}

.chart-container {
  background: var(--custom-bg-color);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  height: 400px;
  display: flex;
  flex-direction: column;
}

.chart-header {
  padding: 24px 24px 16px;
  border-bottom: 1px solid var(--custom-border-color-lighter);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.chart-title h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--custom-text-color-primary);
  margin: 0 0 4px 0;
  font-family: var(--custom-font-family);
}

.chart-title p {
  font-size: 14px;
  color: var(--custom-text-color-secondary);
  margin: 0;
  font-family: var(--custom-font-family);
}

.chart-title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-title-with-icon h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--custom-text-color-primary);
  margin: 0 0 4px 0;
  font-family: var(--custom-font-family);
}

.chart-icon {
  font-size: 16px;
  color: var(--el-color-primary);
}

.chart-controls {
  flex-shrink: 0;
}

.chart-body {
  padding: 12px;
  flex: 1;
  min-height: 0;
}

.chart {
  width: 100%;
  height: 100%;
}

.availability-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.section-title h3 {
  font-size: 24px;
  font-weight: 600;
  color: var(--custom-text-color-primary);
  margin: 0 0 4px 0;
  font-family: var(--custom-font-family);
}

.section-title p {
  font-size: 14px;
  color: var(--custom-text-color-secondary);
  margin: 0;
  font-family: var(--custom-font-family);
}

.section-controls {
  flex-shrink: 0;
}

.availability-content {
  display: grid;
  gap: 24px;
}

.availability-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.availability-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 1200px) {
  .availability-charts {
    grid-template-columns: 1fr;
  }
}

.overview-card {
  background: var(--custom-bg-color);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.overview-card.high {
  border-color
: var(--el-color-success);
}

.overview-card.medium {
  border-color: var(--el-color-warning);
}

.overview-card.low {
  border-color: var(--el-color-danger);
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.overview-icon {
  width: 24px;
  height: 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
}

.overview-card.high .overview-icon {
  background: var(--el-color-success);
}

.overview-card.medium .overview-icon {
  background: var(--el-color-warning);
}

.overview-card.low .overview-icon {
  background: var(--el-color-danger);
}

.overview-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  font-family: var(--custom-font-family);
}

.overview-card.high .overview-badge {
  color: var(--el-color-success);
  background: var(--el-color-success-light-9);
}

.overview-card.medium .overview-badge {
  color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
}

.overview-card.low .overview-badge {
  color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
}

.overview-body {
  margin-bottom: 8px;
}

.overview-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--custom-text-color-primary);
  margin-bottom: 2px;
  font-family: var(--custom-font-family);
}

.overview-label {
  font-size: 16px;
  color: var(--custom-text-color-regular);
  margin-bottom: 2px;
  font-family: var(--custom-font-family);
}

.overview-desc {
  font-size: 10px;
  color: var(--custom-text-color-placeholder);
  font-family: var(--custom-font-family);
}

.overview-footer {
  margin-top: 8px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: var(--custom-border-color-lighter);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-fill.high {
  background: var(--el-color-success);
}

.progress-fill.medium {
  background: var(--el-color-warning);
}

.progress-fill.low {
  background: var(--el-color-danger);
}

.details-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 1200px) {
  .details-section {
    grid-template-columns: 1fr;
  }
}

.detail-container {
  background: var(--custom-bg-color);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.detail-header {
  padding: 24px 24px 16px;
  border-bottom: 1px solid var(--custom-border-color-lighter);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.detail-title h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--custom-text-color-primary);
  margin: 0 0 4px 0;
  font-family: var(--custom-font-family);
}

.detail-title p {
  font-size: 14px;
  color: var(--custom-text-color-secondary);
  margin: 0;
  font-family: var(--custom-font-family);
}

.detail-body {
  padding: 0;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--custom-font-family);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-badge.status-success {
  color: var(--el-color-success);
}

.status-badge.status-success .status-dot {
  background: var(--el-color-success);
}

.status-badge.status-danger {
  color: var(--el-color-danger);
}

.status-badge.status-danger .status-dot {
  background: var(--el-color-danger);
}

.status-badge.status-warning {
  color: var(--el-color-warning);
}

.status-badge.status-warning .status-dot {
  background: var(--el-color-warning);
}

.status-badge.status-info {
  color: var(--el-color-info);
}

.status-badge.status-info .status-dot {
  background: var(--el-color-info);
}

.response-time {
  font-size: 12px;
  color: var(--custom-text-color-regular);
  font-family: var(--custom-font-family);
}

.check-time {
  font-size: 12px;
  color: var(--custom-text-color-secondary);
  font-family: var(--custom-font-family);
}

.alert-level {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--custom-font-family);
}

.alert-level.danger {
  color: var(--el-color-danger);
}

.alert-time {
  font-size: 12px;
  color: var(--custom-text-color-secondary);
  font-family: var(--custom-font-family);
}

:deep(.el-table) {
  font-family: var(--custom-font-family);
}

:deep(.el-table th) {
  background: var(--custom-bg-color-page);
  color: var(--custom-text-color-primary);
  font-weight: 600;
  font-family: var(--custom-font-family);
}

:deep(.el-table td) {
  color: var(--custom-text-color-regular);
  font-family: var(--custom-font-family);
}

:deep(.el-table--border) {
  border-color: var(--custom-border-color-lighter);
}

:deep(.el-table td),
:deep(.el-table th.is-leaf) {
  border-bottom-color: var(--custom-border-color-lighter);
}

:deep(.el-table--border th),
:deep(.el-table--border td) {
  border-right-color: var(--custom-border-color-lighter);
}
</style>