import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import NProgress from 'nprogress'

// 创建axios实例
const service = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    NProgress.start()
    
    // 在这里可以添加token等认证信息
    // const token = getToken()
    // if (token) {
    //   config.headers['Authorization'] = `Bearer ${token}`
    // }
    
    return config
  },
  error => {
    NProgress.done()
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    NProgress.done()
    
    const res = response.data
    
    // 如果是文件下载等特殊情况，直接返回
    if (response.config.responseType === 'blob') {
      return response
    }
    
    // 正常响应
    return res
  },
  error => {
    NProgress.done()
    
    let message = '请求失败'
    
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          message = data.detail || '请求参数错误'
          break
        case 401:
          message = '未授权，请重新登录'
          // 可以在这里处理登录跳转
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 422:
          message = data.detail || '数据验证失败'
          break
        case 500:
          message = '服务器内部错误'
          break
        case 502:
          message = '网关错误'
          break
        case 503:
          message = '服务不可用'
          break
        case 504:
          message = '网关超时'
          break
        default:
          message = data.detail || `连接错误${status}`
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络'
    } else {
      message = error.message || '请求配置错误'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 封装常用的请求方法
export const request = {
  get(url, params = {}) {
    return service.get(url, { params })
  },
  
  post(url, data = {}) {
    return service.post(url, data)
  },
  
  put(url, data = {}) {
    return service.put(url, data)
  },
  
  delete(url, params = {}) {
    return service.delete(url, { params })
  },
  
  patch(url, data = {}) {
    return service.patch(url, data)
  }
}

// 文件上传
export const uploadFile = (url, file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return service.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: onProgress
  })
}

// 文件下载
export const downloadFile = async (url, filename, params = {}) => {
  try {
    const response = await service.get(url, {
      params,
      responseType: 'blob'
    })
    
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
    
    return response
  } catch (error) {
    console.error('文件下载失败:', error)
    throw error
  }
}

export default service