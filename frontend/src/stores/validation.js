import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../services/api'

export const useValidationStore = defineStore('validation', () => {
  // Estado
  const currentValidation = ref(null)
  const validationHistory = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const hasValidation = ref(false) // Mudança: de computed para ref direto

  // Getters computed
  const hasErrors = computed(() => {
    return currentValidation.value?.resultado?.erros?.length > 0
  })
  const successRate = computed(() => {
    return currentValidation.value?.resultado?.taxa_sucesso || 0
  })
  const totalErrors = computed(() => {
    return currentValidation.value?.resultado?.erros?.length || 0
  })
  const errorsByType = computed(() => {
    if (!currentValidation.value?.estatisticas?.tipos_erro) return {}
    return currentValidation.value.estatisticas.tipos_erro
  })
  const errorsByField = computed(() => {
    if (!currentValidation.value?.estatisticas?.campos_com_erro) return {}
    return currentValidation.value.estatisticas.campos_com_erro
  })

  // Actions
  const validateLayout = async (layoutFile) => {
    isLoading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('layout_file', layoutFile)

      const response = await api.post('/validar-layout', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao validar layout'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const validateFile = async (layoutFile, dataFile, maxErrors = 100) => {
    // Garantir que sempre temos um limite de erros balanceado para performance
    const finalMaxErrors = maxErrors || 100
    // Iniciando validação de arquivo

    isLoading.value = true
    error.value = null

    try {
      // Criando FormData
      const formData = new FormData()
      formData.append('layout_file', layoutFile)
      formData.append('data_file', dataFile)

      // Sempre enviar o limite de erros para evitar respostas muito grandes
      formData.append('max_erros', finalMaxErrors.toString())

      // Enviando requisição para /validar-arquivo
      const startTime = Date.now()

      const response = await api.post('/validar-arquivo', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000, // 5 minutos para arquivos grandes
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          // Upload progress handler
        }
      })

      const endTime = Date.now()
      // Resposta recebida e salvando dados

      // Salvar dados DIRETAMENTE no store principal
      currentValidation.value = response.data
      hasValidation.value = true // Definir explicitamente
      // Dados salvos no store principal

      // Adicionar ao histórico de forma assíncrona para não afetar a UI
      setTimeout(() => {
        try {
          validationHistory.value.unshift({
            ...response.data,
            id: Date.now(),
            layoutFileName: layoutFile.name,
            dataFileName: dataFile.name,
            createdAt: new Date().toISOString()
          })

          // Manter apenas os últimos 10 no histórico
          if (validationHistory.value.length > 10) {
            validationHistory.value = validationHistory.value.slice(0, 10)
          }
          // Dados salvos no histórico
        } catch (err) {
          // Erro ao salvar histórico
        }
      }, 100)

      // Validação concluída
      return response.data
    } catch (err) {
      // Erro durante validação

      error.value = err.response?.data?.detail || 'Erro durante a validação'
      throw err
    } finally {
      isLoading.value = false
      // Finalizando validação
    }
  }

  const downloadReport = async (timestamp, format = 'excel') => {
    try {
      const response = await api.get(`/download-relatorio/${timestamp}`, {
        params: { formato: format },
        responseType: 'blob'
      })

      // Criar URL para download
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      // Definir nome do arquivo baseado no formato
      const extensions = { excel: 'xlsx', texto: 'txt', csv: 'csv' }
      link.setAttribute('download', `relatorio_validacao_${timestamp}.${extensions[format]}`)

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      return true
    } catch (err) {
      error.value = 'Erro ao fazer download do relatório'
      throw err
    }
  }

  const clearValidation = () => {
    currentValidation.value = null
    hasValidation.value = false
    error.value = null
  }

  const clearError = () => {
    error.value = null
  }

  const getValidationById = (id) => {
    return validationHistory.value.find(v => v.id === id)
  }

  const setCurrentValidation = (validation) => {
    currentValidation.value = validation
  }

  return {
    // Estado
    currentValidation,
    validationHistory,
    isLoading,
    error,

    // Getters
    hasValidation,
    hasErrors,
    successRate,
    totalErrors,
    errorsByType,
    errorsByField,

    // Actions
    validateLayout,
    validateFile,
    downloadReport,
    clearValidation,
    clearError,
    getValidationById,
    setCurrentValidation
  }
})