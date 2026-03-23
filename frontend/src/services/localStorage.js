/**
 * Serviço para gerenciar dados no localStorage
 * Substitui o salvamento físico de arquivos
 */

const STORAGE_KEYS = {
  VALIDATIONS: 'validador_validations',
  COMPARISONS: 'validador_comparisons',
  LAYOUTS: 'validador_layouts'
}

class LocalStorageService {
  // =============== VALIDAÇÕES ===============

  /**
   * Salva resultado de validação no localStorage
   */
  saveValidation(timestamp, data) {
    const validations = this.getValidations()
    validations[timestamp] = {
      ...data,
      savedAt: new Date().toISOString()
    }
    localStorage.setItem(STORAGE_KEYS.VALIDATIONS, JSON.stringify(validations))
    console.log('✅ Validação salva no localStorage:', timestamp)
  }

  /**
   * Obtém todas as validações salvas
   */
  getValidations() {
    const data = localStorage.getItem(STORAGE_KEYS.VALIDATIONS)
    return data ? JSON.parse(data) : {}
  }

  /**
   * Obtém validação específica
   */
  getValidation(timestamp) {
    const validations = this.getValidations()
    return validations[timestamp] || null
  }

  /**
   * Remove validação específica
   */
  removeValidation(timestamp) {
    const validations = this.getValidations()
    delete validations[timestamp]
    localStorage.setItem(STORAGE_KEYS.VALIDATIONS, JSON.stringify(validations))
    console.log('🗑️ Validação removida:', timestamp)
  }

  // =============== COMPARAÇÕES ===============

  /**
   * Salva resultado de comparação no localStorage
   */
  saveComparison(timestamp, data) {
    const comparisons = this.getComparisons()
    comparisons[timestamp] = {
      ...data,
      savedAt: new Date().toISOString()
    }
    localStorage.setItem(STORAGE_KEYS.COMPARISONS, JSON.stringify(comparisons))
    console.log('✅ Comparação salva no localStorage:', timestamp)
  }

  /**
   * Obtém todas as comparações salvas
   */
  getComparisons() {
    const data = localStorage.getItem(STORAGE_KEYS.COMPARISONS)
    return data ? JSON.parse(data) : {}
  }

  /**
   * Obtém comparação específica
   */
  getComparison(timestamp) {
    const comparisons = this.getComparisons()
    return comparisons[timestamp] || null
  }

  /**
   * Remove comparação específica
   */
  removeComparison(timestamp) {
    const comparisons = this.getComparisons()
    delete comparisons[timestamp]
    localStorage.setItem(STORAGE_KEYS.COMPARISONS, JSON.stringify(comparisons))
    console.log('🗑️ Comparação removida:', timestamp)
  }

  // =============== LAYOUTS ===============

  /**
   * Salva layout exportado no localStorage
   */
  saveLayout(timestamp, data) {
    const layouts = this.getLayouts()
    layouts[timestamp] = {
      ...data,
      savedAt: new Date().toISOString()
    }
    localStorage.setItem(STORAGE_KEYS.LAYOUTS, JSON.stringify(layouts))
    console.log('✅ Layout salvo no localStorage:', timestamp)
  }

  /**
   * Obtém todos os layouts salvos
   */
  getLayouts() {
    const data = localStorage.getItem(STORAGE_KEYS.LAYOUTS)
    return data ? JSON.parse(data) : {}
  }

  /**
   * Obtém layout específico
   */
  getLayout(timestamp) {
    const layouts = this.getLayouts()
    return layouts[timestamp] || null
  }

  // =============== DOWNLOADS ===============

  /**
   * Gera download de arquivo Excel a partir de base64
   */
  downloadExcel(data, filename) {
    try {
      // Converter base64 para blob
      const byteCharacters = atob(data)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })

      // Criar download
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      console.log('📥 Download Excel realizado:', filename)
    } catch (error) {
      console.error('❌ Erro no download Excel:', error)
      throw new Error('Falha ao baixar arquivo Excel')
    }
  }

  /**
   * Gera download de arquivo de texto
   */
  downloadText(content, filename) {
    try {
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      console.log('📥 Download texto realizado:', filename)
    } catch (error) {
      console.error('❌ Erro no download texto:', error)
      throw new Error('Falha ao baixar arquivo de texto')
    }
  }

  /**
   * Gera download de arquivo PDF a partir de base64
   */
  downloadPDF(data, filename) {
    try {
      const byteCharacters = atob(data)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: 'application/pdf' })

      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      console.log('Download PDF realizado:', filename)
    } catch (error) {
      console.error('Erro no download PDF:', error)
      throw new Error('Falha ao baixar arquivo PDF')
    }
  }

  /**
   * Gera download de CSV
   */
  downloadCSV(content, filename) {
    try {
      const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      console.log('📥 Download CSV realizado:', filename)
    } catch (error) {
      console.error('❌ Erro no download CSV:', error)
      throw new Error('Falha ao baixar arquivo CSV')
    }
  }

  // =============== UTILIDADES ===============

  /**
   * Obtém estatísticas de uso do localStorage
   */
  getStorageStats() {
    const validations = Object.keys(this.getValidations()).length
    const comparisons = Object.keys(this.getComparisons()).length
    const layouts = Object.keys(this.getLayouts()).length

    return {
      validations,
      comparisons,
      layouts,
      total: validations + comparisons + layouts
    }
  }

  /**
   * Limpa todos os dados (uso apenas para desenvolvimento)
   */
  clearAll() {
    localStorage.removeItem(STORAGE_KEYS.VALIDATIONS)
    localStorage.removeItem(STORAGE_KEYS.COMPARISONS)
    localStorage.removeItem(STORAGE_KEYS.LAYOUTS)
    console.log('🧹 localStorage limpo completamente')
  }

  /**
   * Limpa dados antigos (mais de X dias)
   */
  cleanOldData(maxDays = 30) {
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - maxDays)

    // Limpar validações antigas
    const validations = this.getValidations()
    Object.keys(validations).forEach(timestamp => {
      const savedAt = new Date(validations[timestamp].savedAt)
      if (savedAt < cutoffDate) {
        delete validations[timestamp]
      }
    })
    localStorage.setItem(STORAGE_KEYS.VALIDATIONS, JSON.stringify(validations))

    // Limpar comparações antigas
    const comparisons = this.getComparisons()
    Object.keys(comparisons).forEach(timestamp => {
      const savedAt = new Date(comparisons[timestamp].savedAt)
      if (savedAt < cutoffDate) {
        delete comparisons[timestamp]
      }
    })
    localStorage.setItem(STORAGE_KEYS.COMPARISONS, JSON.stringify(comparisons))

    console.log(`🧹 Dados mais antigos que ${maxDays} dias foram removidos`)
  }
}

// Exportar instância única
export default new LocalStorageService()