import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
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