import axios from 'axios'

// Base URL strategy:
// - In development (Vite dev server), prefer the proxy '/api' to hit backend :8000
// - Allow override with VITE_API_URL only when explicitly desired (set VITE_FORCE_API_URL=true)
// - In production, VITE_API_URL can point to the deployed API; otherwise '/api' works when served behind the same origin
const isDev = import.meta.env.DEV
const forceApi = import.meta.env.VITE_FORCE_API_URL === 'true'
let base = '/api'

if (!isDev && import.meta.env.VITE_API_URL) {
  base = import.meta.env.VITE_API_URL
}

if (isDev) {
  if (forceApi && import.meta.env.VITE_API_URL) {
    base = import.meta.env.VITE_API_URL
  } else {
    base = '/api' // use Vite proxy to http://localhost:8000
  }
}

const api = axios.create({
  baseURL: base,
  timeout: 300000, // 5 minutos para arquivos grandes da claro
})

// Interceptor para requisições
api.interceptors.request.use(
  (config) => {
    // Adicionar headers comuns se necessário
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para respostas
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Tratamento global de erros
    if (error.response?.status === 413) {
      error.message = 'Arquivo muito grande. Tente com um arquivo menor.'
    } else if (error.response?.status === 422) {
      error.message = 'Dados inválidos. Verifique os arquivos enviados.'
    } else if (error.response?.status >= 500) {
      error.message = 'Erro interno do servidor. Tente novamente mais tarde.'
    }

    return Promise.reject(error)
  }
)

export default api