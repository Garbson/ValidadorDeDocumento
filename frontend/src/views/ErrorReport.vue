<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Relatório de Erros Detalhado</h1>
      <p class="text-gray-600">Visualize todos os erros encontrados na validação com detalhes completos</p>
    </div>

    <!-- No validation message -->
    <div v-if="!validationStore.hasValidation" class="card">
      <div class="card-body text-center py-12">
        <AlertCircle class="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">Nenhuma validação encontrada</h3>
        <p class="text-gray-500 mb-4">Execute uma validação primeiro para visualizar o relatório de erros.</p>
        <router-link to="/visualizador" class="btn-primary">
          <Eye class="w-4 h-4 mr-2" />
          Ir para Visualizador
        </router-link>
      </div>
    </div>

    <!-- Error Report Content -->
    <div v-else>
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="card">
          <div class="card-body text-center">
            <div class="text-2xl font-bold text-error-600">{{ validationStore.totalErrors }}</div>
            <div class="text-sm text-gray-500">Total de Erros</div>
          </div>
        </div>
        <div class="card">
          <div class="card-body text-center">
            <div class="text-2xl font-bold text-warning-600">{{ linhasComErro }}</div>
            <div class="text-sm text-gray-500">Linhas com Erro</div>
          </div>
        </div>
        <div class="card">
          <div class="card-body text-center">
            <div class="text-2xl font-bold text-primary-600">{{ tiposDeErroUnicos.length }}</div>
            <div class="text-sm text-gray-500">Tipos de Erro</div>
          </div>
        </div>
        <div class="card">
          <div class="card-body text-center">
            <div class="text-2xl font-bold" :class="getSuccessRateColorClass(validationStore.successRate)">
              {{ validationStore.successRate.toFixed(1) }}%
            </div>
            <div class="text-sm text-gray-500">Taxa de Sucesso</div>
          </div>
        </div>
      </div>

      <!-- Error Type Breakdown -->
      <div class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold flex items-center">
            <PieChart class="w-5 h-5 mr-2" />
            Distribuição por Tipo de Erro
          </h2>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="tipo in estatisticasTiposErro"
              :key="tipo.nome"
              class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div class="flex items-center justify-between">
                <div>
                  <div class="font-medium text-gray-900">{{ formatErrorType(tipo.nome) }}</div>
                  <div class="text-sm text-gray-500">{{ tipo.quantidade }} ocorrências</div>
                </div>
                <div class="text-right">
                  <div class="text-lg font-bold text-error-600">{{ tipo.percentual.toFixed(1) }}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold flex items-center">
            <Filter class="w-5 h-5 mr-2" />
            Filtros
          </h2>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Tipo de Erro</label>
              <select v-model="filtroTipoErro" class="input">
                <option value="">Todos os tipos</option>
                <option v-for="tipo in tiposDeErroUnicos" :key="tipo" :value="tipo">
                  {{ formatErrorType(tipo) }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Campo</label>
              <select v-model="filtroCampo" class="input">
                <option value="">Todos os campos</option>
                <option v-for="campo in camposComErro" :key="campo" :value="campo">
                  {{ campo }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Buscar na Descrição</label>
              <input
                v-model="filtroDescricao"
                type="text"
                placeholder="Digite para buscar..."
                class="input"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Error List -->
      <div class="card">
        <div class="card-header">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold flex items-center">
              <List class="w-5 h-5 mr-2" />
              Lista de Erros Detalhada
              <span class="ml-2 text-sm font-normal text-gray-500">({{ errosFiltrados.length }} de {{ validationStore.totalErrors }})</span>
            </h2>
            <div class="flex space-x-2">
              <button @click="exportarErrosFiltrados" class="btn-secondary">
                <Download class="w-4 h-4 mr-2" />
                Exportar Filtrados
              </button>
              <button @click="limparFiltros" class="btn-secondary">
                <RotateCcw class="w-4 h-4 mr-2" />
                Limpar Filtros
              </button>
            </div>
          </div>
        </div>
        <div class="card-body">
          <!-- Pagination controls -->
          <div v-if="totalPaginas > 1" class="flex justify-between items-center mb-4">
            <div class="text-sm text-gray-500">
              Mostrando {{ (paginaAtual - 1) * itensPorPagina + 1 }} - {{ Math.min(paginaAtual * itensPorPagina, errosFiltrados.length) }} de {{ errosFiltrados.length }} erros
            </div>
            <div class="flex space-x-2">
              <button
                @click="paginaAtual = Math.max(1, paginaAtual - 1)"
                :disabled="paginaAtual === 1"
                class="btn-secondary disabled:opacity-50"
              >
                <ChevronLeft class="w-4 h-4" />
              </button>
              <span class="px-3 py-2 text-sm text-gray-700">
                Página {{ paginaAtual }} de {{ totalPaginas }}
              </span>
              <button
                @click="paginaAtual = Math.min(totalPaginas, paginaAtual + 1)"
                :disabled="paginaAtual === totalPaginas"
                class="btn-secondary disabled:opacity-50"
              >
                <ChevronRight class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Error table -->
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Linha
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campo
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tipo de Erro
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Valor Encontrado
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Descrição
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fatura/NF
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr
                  v-for="erro in errosPaginados"
                  :key="`${erro.linha}-${erro.campo}-${Math.random()}`"
                  class="hover:bg-gray-50 transition-colors"
                >
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ erro.linha }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <code class="bg-gray-100 px-2 py-1 rounded text-xs">{{ erro.campo }}</code>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="getTipoErroColorClass(erro.erro_tipo)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                      {{ formatErrorType(erro.erro_tipo) }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" :title="erro.valor_encontrado">
                    {{ erro.valor_encontrado || '-' }}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-900 max-w-md">
                    {{ erro.descricao }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ extrairFaturaNF(erro) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Empty state -->
          <div v-if="errosFiltrados.length === 0" class="text-center py-8">
            <Search class="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 class="text-lg font-medium text-gray-900 mb-2">Nenhum erro encontrado</h3>
            <p class="text-gray-500">Nenhum erro corresponde aos filtros aplicados.</p>
          </div>
        </div>
      </div>

      <!-- Enhanced Statistics for Tax Validation -->
      <div v-if="validationStore.currentValidation?.resultado?.totais_acumulados" class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold flex items-center">
            <Calculator class="w-5 h-5 mr-2" />
            Totais de Impostos Acumulados
          </h2>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="(valor, campo) in validationStore.currentValidation.resultado.totais_acumulados"
              :key="campo"
              class="border border-gray-200 rounded-lg p-4"
            >
              <div class="text-sm text-gray-500">{{ formatTaxFieldName(campo) }}</div>
              <div class="text-lg font-bold text-primary-600">
                {{ formatCurrency(valor) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Invoice Statistics -->
      <div v-if="validationStore.currentValidation?.resultado?.estatisticas_faturas" class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold flex items-center">
            <FileText class="w-5 h-5 mr-2" />
            Estatísticas de Faturas
          </h2>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600">
                {{ validationStore.currentValidation.resultado.estatisticas_faturas.total_faturas }}
              </div>
              <div class="text-sm text-gray-500">Total de Faturas</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-success-600">
                {{ validationStore.currentValidation.resultado.estatisticas_faturas.total_notas_fiscais }}
              </div>
              <div class="text-sm text-gray-500">Total de Notas Fiscais</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-warning-600">
                {{ calcularMediaNotasPorFatura() }}
              </div>
              <div class="text-sm text-gray-500">Média NF/Fatura</div>
            </div>
          </div>

          <!-- Detailed invoice breakdown -->
          <div class="space-y-2">
            <h4 class="font-medium text-gray-900">Detalhamento por Fatura:</h4>
            <div class="max-h-64 overflow-y-auto space-y-2">
              <div
                v-for="(detalhes, fatura) in validationStore.currentValidation.resultado.estatisticas_faturas.faturas_detalhes"
                :key="fatura"
                class="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <span class="font-medium">Fatura {{ fatura }}</span>
                </div>
                <div class="text-sm text-gray-600">
                  {{ detalhes.quantidade_notas }} nota{{ detalhes.quantidade_notas !== 1 ? 's' : '' }} fiscal{{ detalhes.quantidade_notas !== 1 ? 'is' : '' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useValidationStore } from '@/stores/validation'
import {
  AlertCircle, CheckSquare, PieChart, Filter, List, Download, RotateCcw,
  ChevronLeft, ChevronRight, Search, Calculator, FileText
} from 'lucide-vue-next'

const validationStore = useValidationStore()

// Reactive filters
const filtroTipoErro = ref('')
const filtroCampo = ref('')
const filtroDescricao = ref('')

// Pagination
const paginaAtual = ref(1)
const itensPorPagina = ref(50)

// Computed properties
const linhasComErro = computed(() => {
  if (!validationStore.hasValidation) return 0
  return validationStore.currentValidation.resultado.linhas_com_erro
})

const tiposDeErroUnicos = computed(() => {
  if (!validationStore.hasValidation) return []
  const tipos = new Set()
  validationStore.currentValidation.resultado.erros.forEach(erro => {
    tipos.add(erro.erro_tipo)
  })
  return Array.from(tipos).sort()
})

const camposComErro = computed(() => {
  if (!validationStore.hasValidation) return []
  const campos = new Set()
  validationStore.currentValidation.resultado.erros.forEach(erro => {
    campos.add(erro.campo)
  })
  return Array.from(campos).sort()
})

const estatisticasTiposErro = computed(() => {
  if (!validationStore.hasValidation) return []

  const contadores = {}
  const totalErros = validationStore.totalErrors

  validationStore.currentValidation.resultado.erros.forEach(erro => {
    contadores[erro.erro_tipo] = (contadores[erro.erro_tipo] || 0) + 1
  })

  return Object.entries(contadores)
    .map(([nome, quantidade]) => ({
      nome,
      quantidade,
      percentual: (quantidade / totalErros) * 100
    }))
    .sort((a, b) => b.quantidade - a.quantidade)
})

const errosFiltrados = computed(() => {
  if (!validationStore.hasValidation) return []

  let erros = validationStore.currentValidation.resultado.erros

  // Filtro por tipo de erro
  if (filtroTipoErro.value) {
    erros = erros.filter(erro => erro.erro_tipo === filtroTipoErro.value)
  }

  // Filtro por campo
  if (filtroCampo.value) {
    erros = erros.filter(erro => erro.campo === filtroCampo.value)
  }

  // Filtro por descrição
  if (filtroDescricao.value) {
    const termoBusca = filtroDescricao.value.toLowerCase()
    erros = erros.filter(erro =>
      erro.descricao.toLowerCase().includes(termoBusca) ||
      erro.valor_encontrado.toLowerCase().includes(termoBusca)
    )
  }

  return erros
})

const totalPaginas = computed(() => {
  return Math.ceil(errosFiltrados.value.length / itensPorPagina.value)
})

const errosPaginados = computed(() => {
  const inicio = (paginaAtual.value - 1) * itensPorPagina.value
  const fim = inicio + itensPorPagina.value
  return errosFiltrados.value.slice(inicio, fim)
})

// Watch for filter changes to reset pagination
watch([filtroTipoErro, filtroCampo, filtroDescricao], () => {
  paginaAtual.value = 1
})

// Methods
const getSuccessRateColorClass = (rate) => {
  if (rate >= 95) return 'text-success-600'
  if (rate >= 80) return 'text-warning-600'
  return 'text-error-600'
}

const getTipoErroColorClass = (tipo) => {
  const colorMap = {
    'CAMPO_OBRIGATORIO': 'bg-error-100 text-error-800',
    'FORMATO_INVALIDO': 'bg-warning-100 text-warning-800',
    'TAMANHO_INVALIDO': 'bg-orange-100 text-orange-800',
    'ESTRUTURA_DUPLICADA': 'bg-purple-100 text-purple-800',
    'COMBINACAO_DUPLICADA': 'bg-pink-100 text-pink-800',
    'TOTAL_BC': 'bg-blue-100 text-blue-800',
    'TOTAL_ICMS': 'bg-blue-100 text-blue-800',
    'TOTAL_PIS': 'bg-blue-100 text-blue-800',
    'TOTAL_COFINS': 'bg-blue-100 text-blue-800',
    'TOTAL_FUST': 'bg-blue-100 text-blue-800',
    'TOTAL_FUNTEL': 'bg-blue-100 text-blue-800',
    'TOTAL_FCP': 'bg-blue-100 text-blue-800',
    'CALCULO_ERRO_ICMS': 'bg-red-100 text-red-800',
    'CALCULO_ERRO_FCP': 'bg-red-100 text-red-800'
  }
  return colorMap[tipo] || 'bg-gray-100 text-gray-800'
}

const formatErrorType = (tipo) => {
  const formatMap = {
    'CAMPO_OBRIGATORIO': 'Campo Obrigatório',
    'FORMATO_INVALIDO': 'Formato Inválido',
    'TAMANHO_INVALIDO': 'Tamanho Inválido',
    'ESTRUTURA_DUPLICADA': 'Estrutura Duplicada',
    'COMBINACAO_DUPLICADA': 'Combinação Duplicada',
    'TOTAL_BC': 'Total Base de Cálculo',
    'TOTAL_ICMS': 'Total ICMS',
    'TOTAL_PIS': 'Total PIS',
    'TOTAL_COFINS': 'Total COFINS',
    'TOTAL_FUST': 'Total FUST',
    'TOTAL_FUNTEL': 'Total FUNTEL',
    'TOTAL_FCP': 'Total FCP',
    'CALCULO_ERRO_ICMS': 'Erro Cálculo ICMS',
    'CALCULO_ERRO_FCP': 'Erro Cálculo FCP'
  }
  return formatMap[tipo] || tipo
}

const formatTaxFieldName = (campo) => {
  const formatMap = {
    'NFE56-TOT-VLR-PIS': 'Total PIS',
    'NFE56-TOT-VLR-COFINS': 'Total COFINS',
    'NFE56-TOT-VLR-FUST': 'Total FUST',
    'NFE56-TOT-VLR-FUNTEL': 'Total FUNTEL',
    'NFE56-TOT-VLR-ICMS': 'Total ICMS',
    'NFE56-TOT-VLR-FCP': 'Total FCP',
    'NFE56-TOT-VLR-BC': 'Total Base de Cálculo'
  }
  return formatMap[campo] || campo
}

const formatCurrency = (valor) => {
  return `R$ ${(valor / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const extrairFaturaNF = (erro) => {
  // Extrair fatura e NF da descrição do erro quando possível
  if (erro.erro_tipo === 'COMBINACAO_DUPLICADA' && erro.valor_encontrado.includes('Fatura:')) {
    return erro.valor_encontrado.replace('Fatura: ', '').replace(', NF: ', ' / NF: ')
  }

  // Para erros de linha, tentar extrair informações do contexto
  if (erro.campo.includes('NFE01')) {
    return `Linha ${erro.linha}`
  }

  return '-'
}

const calcularMediaNotasPorFatura = () => {
  if (!validationStore.currentValidation?.resultado?.estatisticas_faturas) return 0

  const stats = validationStore.currentValidation.resultado.estatisticas_faturas
  if (stats.total_faturas === 0) return 0

  return (stats.total_notas_fiscais / stats.total_faturas).toFixed(1)
}

const limparFiltros = () => {
  filtroTipoErro.value = ''
  filtroCampo.value = ''
  filtroDescricao.value = ''
  paginaAtual.value = 1
}

const exportarErrosFiltrados = () => {
  // Create CSV content
  const headers = ['Linha', 'Campo', 'Tipo de Erro', 'Valor Encontrado', 'Descrição', 'Fatura/NF']
  const csvContent = [
    headers.join(','),
    ...errosFiltrados.value.map(erro => [
      erro.linha,
      `"${erro.campo}"`,
      `"${formatErrorType(erro.erro_tipo)}"`,
      `"${erro.valor_encontrado || ''}"`,
      `"${erro.descricao.replace(/"/g, '""')}"`,
      `"${extrairFaturaNF(erro)}"`
    ].join(','))
  ].join('\n')

  // Download CSV file
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `relatorio_erros_filtrado_${new Date().toISOString().slice(0, 10)}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>