const STORAGE_KEY = 'ff_backend_origin'
const DEV_FRONTEND_PORTS = new Set(['4173', '5173', '5174'])
const PROBE_PATH = '/api/admin/public/system-name'
const PROBE_TIMEOUT_MS = 1500
const ACCEPTABLE_PROBE_STATUS = new Set([200, 401, 403])

let resolvedOrigin = ''
let resolvingPromise = null

const normalizeOrigin = (origin) => String(origin || '').trim().replace(/\/+$/, '')

const isAbsoluteUrl = (value) => /^(?:https?:)?\/\//i.test(String(value || ''))

const getStoredOrigin = () => {
  try {
    return normalizeOrigin(window.localStorage.getItem(STORAGE_KEY))
  } catch {
    return ''
  }
}

const saveOrigin = (origin) => {
  const normalized = normalizeOrigin(origin)
  resolvedOrigin = normalized
  try {
    window.localStorage.setItem(STORAGE_KEY, normalized)
  } catch {
    // Ignore storage failures.
  }
  return normalized
}

const clearStoredOrigin = () => {
  resolvedOrigin = ''
  try {
    window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Ignore storage failures.
  }
}

const getCandidateOrigins = () => {
  const candidates = []
  const envOrigin = normalizeOrigin(import.meta.env.VITE_BACKEND_TARGET)
  const storedOrigin = getStoredOrigin()

  if (storedOrigin) candidates.push(storedOrigin)
  if (envOrigin) candidates.push(envOrigin)

  if (typeof window !== 'undefined') {
    const currentOrigin = normalizeOrigin(window.location.origin)
    const currentPort = String(window.location.port || '')
    if (currentOrigin && !DEV_FRONTEND_PORTS.has(currentPort)) {
      candidates.push(currentOrigin)
    }
  }

  candidates.push(
    'http://localhost:8010',
    'http://127.0.0.1:8010',
    'http://localhost:8000',
    'http://127.0.0.1:8000'
  )

  return [...new Set(candidates.filter(Boolean).map(normalizeOrigin))]
}

const probeOrigin = async (origin) => {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS)

  try {
    const response = await fetch(`${origin}${PROBE_PATH}`, {
      method: 'GET',
      cache: 'no-store',
      signal: controller.signal
    })
    return ACCEPTABLE_PROBE_STATUS.has(response.status)
  } catch {
    return false
  } finally {
    clearTimeout(timer)
  }
}

export const ensureBackendOrigin = async () => {
  if (resolvedOrigin) return resolvedOrigin

  if (!resolvingPromise) {
    resolvingPromise = (async () => {
      const envOrigin = normalizeOrigin(import.meta.env.VITE_BACKEND_TARGET)
      const fallbackOrigin = envOrigin || 'http://localhost:8010'

      for (const candidate of getCandidateOrigins()) {
        if (await probeOrigin(candidate)) {
          return saveOrigin(candidate)
        }
      }

      clearStoredOrigin()
      return saveOrigin(fallbackOrigin)
    })().finally(() => {
      resolvingPromise = null
    })
  }

  return resolvingPromise
}

export const getBackendOrigin = () => {
  if (resolvedOrigin) return resolvedOrigin

  const storedOrigin = getStoredOrigin()
  if (storedOrigin) {
    resolvedOrigin = storedOrigin
    return resolvedOrigin
  }

  const envOrigin = normalizeOrigin(import.meta.env.VITE_BACKEND_TARGET)
  if (envOrigin) {
    resolvedOrigin = envOrigin
    return resolvedOrigin
  }

  return ''
}

export const buildBackendUrl = (path = '') => {
  const value = String(path || '')
  if (!value) return value
  if (isAbsoluteUrl(value) || value.startsWith('data:') || value.startsWith('blob:')) return value

  const origin = getBackendOrigin()
  if (!origin) return value

  return `${origin}${value.startsWith('/') ? value : `/${value}`}`
}

export const buildBackendWsUrl = (path = '') => buildBackendUrl(path).replace(/^http/i, 'ws')

export const normalizeAssetUrl = (path = '') => buildBackendUrl(path)
