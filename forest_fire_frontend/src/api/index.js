import axios from 'axios'
import { useRouter } from 'vue-router'
import { ensureBackendOrigin } from './backend'

const api = axios.create({
    timeout: 10000
})

// 请求拦截器：自动带上 token
api.interceptors.request.use(async config => {
    const backendOrigin = await ensureBackendOrigin()
    const requestUrl = String(config.url || '')

    if (!/^https?:\/\//i.test(requestUrl)) {
        const normalizedPath = requestUrl.startsWith('/api')
            ? requestUrl
            : `/api${requestUrl.startsWith('/') ? requestUrl : `/${requestUrl}`}`
        config.url = `${backendOrigin}${normalizedPath}`
    }

    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
}, error => {
    return Promise.reject(error)
})

// 响应拦截器：处理 401 未授�?
api.interceptors.response.use(
    response => response.data,
    error => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export default api
