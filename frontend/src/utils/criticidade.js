/**
 * Classificação de criticidade de erros para envio à SEFAZ
 *
 * CRÍTICO = impede envio à SEFAZ (deve ser corrigido obrigatoriamente)
 * ADVERTÊNCIA = não impede envio, mas deve ser analisado
 */

// Tipos de erro que são CRÍTICOS para envio à SEFAZ
const TIPOS_CRITICOS = new Set([
  // Erros de cálculo de impostos
  'CALCULO_ERRO_ICMS',
  'CALCULO_ERRO_PIS',
  'CALCULO_ERRO_COFINS',
  'CALCULO_ERRO_FUST',
  'CALCULO_ERRO_FUNTEL',
  'CALCULO_ERRO_FCP',
  // Totais inconsistentes
  'TOTAL_ICMS',
  'TOTAL_PIS',
  'TOTAL_COFINS',
  'TOTAL_FUST',
  'TOTAL_FUNTEL',
  'TOTAL_FCP',
  'TOTAL_BC',
  // Problemas estruturais graves
  'CAMPO_OBRIGATORIO',
  'FORMATO_INVALIDO',
  'TIPO_INVALIDO',
  'TIPO_REGISTRO_NAO_RECONHECIDO',
  'TAMANHO_LINHA',
])

// Padrões parciais que indicam criticidade
const PADROES_CRITICOS = [
  'CALCULO_ERRO_',
  'TOTAL_',
]

/**
 * Determina se um tipo de erro é crítico para envio à SEFAZ
 * @param {string} tipoErro - O tipo do erro (erro_tipo ou tipo_diferenca)
 * @returns {'CRITICO' | 'ADVERTENCIA'}
 */
export function classificarCriticidade(tipoErro) {
  if (!tipoErro) return 'ADVERTENCIA'

  // Verificação exata
  if (TIPOS_CRITICOS.has(tipoErro)) return 'CRITICO'

  // Verificação por padrão
  for (const padrao of PADROES_CRITICOS) {
    if (tipoErro.includes(padrao)) return 'CRITICO'
  }

  return 'ADVERTENCIA'
}

/**
 * Determina a criticidade de um campo de diferença
 * @param {object} campo - Objeto de campo com tipo_diferenca e/ou nome_campo
 * @returns {'CRITICO' | 'ADVERTENCIA'}
 */
export function classificarCampo(campo) {
  if (!campo) return 'ADVERTENCIA'

  // Verificar tipo_diferenca
  if (campo.tipo_diferenca) {
    return classificarCriticidade(campo.tipo_diferenca)
  }

  // Verificar erro_tipo
  if (campo.erro_tipo) {
    return classificarCriticidade(campo.erro_tipo)
  }

  return 'ADVERTENCIA'
}

/**
 * Conta críticos e advertências de uma lista de erros
 * @param {Array} erros - Array de objetos de erro
 * @returns {{ criticos: number, advertencias: number }}
 */
export function contarCriticidades(erros) {
  if (!erros?.length) return { criticos: 0, advertencias: 0 }

  let criticos = 0
  let advertencias = 0

  erros.forEach(erro => {
    const tipo = erro.erro_tipo || erro.tipo_diferenca || ''
    if (classificarCriticidade(tipo) === 'CRITICO') {
      criticos++
    } else {
      advertencias++
    }
  })

  return { criticos, advertencias }
}

/**
 * Determina se uma linha de diferença tem algum campo crítico
 * @param {object} diferenca - Linha de diferença com diferencas_campos
 * @returns {boolean}
 */
export function linhaTemCritico(diferenca) {
  if (!diferenca?.diferencas_campos?.length) return false
  return diferenca.diferencas_campos.some(
    campo => classificarCampo(campo) === 'CRITICO'
  )
}

/**
 * Retorna classes CSS para o badge de criticidade
 * @param {'CRITICO' | 'ADVERTENCIA'} nivel
 * @returns {string}
 */
export function badgeClasses(nivel) {
  if (nivel === 'CRITICO') {
    return 'bg-red-600 text-white'
  }
  return 'bg-yellow-100 text-yellow-800'
}

/**
 * Retorna texto legível para o nível de criticidade
 * @param {'CRITICO' | 'ADVERTENCIA'} nivel
 * @returns {string}
 */
export function badgeTexto(nivel) {
  if (nivel === 'CRITICO') return 'CRÍTICO'
  return 'ADVERTÊNCIA'
}
