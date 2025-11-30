import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../services/api'
import localStorageService from '../services/localStorage'

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
  const listExcelSheets = async (layoutFile) => {
    isLoading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('layout_file', layoutFile)

      const response = await api.post('/listar-abas-excel', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao listar abas do Excel'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const validateLayout = async (layoutFile, sheetName = null) => {
    isLoading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('layout_file', layoutFile)
      if (sheetName !== null) {
        formData.append('sheet_name', sheetName.toString())
      }

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

  const validateFile = async (layoutFile, dataFile, maxErrors = 100, sheetName = null) => {
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

      // Adicionar sheet_name se especificado
      if (sheetName !== null) {
        formData.append('sheet_name', sheetName.toString())
      }

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

      // Salvar no localStorage para acesso posterior
      if (response.data.dados_relatorio) {
        localStorageService.saveValidation(response.data.timestamp, response.data.dados_relatorio)
      }

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
      // Buscar dados do localStorage
      let validationData = localStorageService.getValidation(timestamp)
      if (!validationData) {
        // Se não estiver no localStorage, usar dados da validação atual
        if (currentValidation.value?.timestamp === timestamp && currentValidation.value?.dados_relatorio) {
          validationData = currentValidation.value.dados_relatorio
        } else {
          throw new Error('Dados da validação não encontrados')
        }
      }

      // Gerar nome do arquivo
      const layoutNome = validationData.layout_nome || 'layout'
      const extensions = { excel: 'xlsx', texto: 'txt', csv: 'csv' }
      const filename = `relatorio_validacao_${layoutNome}_${timestamp}.${extensions[format]}`

      // Download baseado no formato
      if (format === 'excel') {
        // Para Excel, precisamos gerar o arquivo a partir dos dados
        // Por enquanto, usar o método de download de texto com resumo
        const content = validationData.resumo_texto || 'Relatório não disponível'
        localStorageService.downloadText(content, `relatorio_validacao_${layoutNome}_${timestamp}.txt`)
      } else if (format === 'texto') {
        const content = validationData.resumo_texto || 'Relatório não disponível'
        localStorageService.downloadText(content, filename)
      } else if (format === 'csv') {
        // Gerar CSV simples dos erros
        let csvContent = 'Linha,Campo,Tipo_Erro,Valor_Encontrado,Descricao\n'
        if (validationData.erros && validationData.erros.length > 0) {
          validationData.erros.forEach(erro => {
            csvContent += `${erro.linha},"${erro.campo}","${erro.tipo_erro}","${erro.valor_encontrado}","${erro.descricao}"\n`
          })
        } else {
          csvContent += 'Nenhum erro encontrado,,,,'
        }
        localStorageService.downloadCSV(csvContent, filename)
      }

      return true
    } catch (err) {
      console.error('Erro no download:', err)
      error.value = 'Erro ao fazer download do relatório: ' + err.message
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
    listExcelSheets,
    validateLayout,
    validateFile,
    downloadReport,
    clearValidation,
    clearError,
    getValidationById,
    setCurrentValidation
  }
})