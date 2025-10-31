<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">
        Comparação Estrutural de Arquivos
      </h1>
      <p class="text-gray-600">Compare dois arquivos TXT linha por linha usando um layout como referência</p>
    </div>

    <!-- Upload Form -->
    <div class="card max-w-4xl mx-auto" v-show="!hasResults">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <GitCompare class="w-5 h-5 mr-2" />
          Upload de Arquivos para Comparação
        </h2>
      </div>
      <div class="card-body space-y-6">
        <form @submit.prevent="handleComparison" class="space-y-6">
          <!-- Layout File Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Arquivo de Layout (Excel)
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="layoutFileInput"
                type="file"
                accept=".xlsx,.xls"
                @change="handleLayoutFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo Excel com as especificações dos campos (.xlsx ou .xls)
            </p>
          </div>

          <!-- Base File Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Arquivo Base (TXT) - Referência
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="baseFileInput"
                type="file"
                accept=".txt"
                @change="handleBaseFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo TXT que será usado como referência (base) para comparação
            </p>
          </div>

          <!-- Validation File Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Arquivo a ser Comparado (TXT)
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="validationFileInput"
                type="file"
                accept=".txt"
                @change="handleValidationFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo TXT que será comparado com o arquivo base
            </p>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-end">
            <button
              type="submit"
              :disabled="isLoading || !canSubmit"
              class="btn-primary"
            >
              <template v-if="isLoading">
                <Loader2 class="w-4 h-4 mr-2 animate-spin" />
                Comparando...
              </template>
              <template v-else>
                <GitCompare class="w-4 h-4 mr-2" />
                Comparar Arquivos
              </template>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center items-center py-12">
      <div class="text-center">
        <Loader2 class="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
        <p class="text-gray-600">Comparando arquivos estruturalmente...</p>
      </div>
    </div>

  <!-- Results -->
  <div v-if="hasResults && !isLoading" class="space-y-6">
      <!-- Header de Resultados -->
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-900">Resultado da Comparação</h2>
        <div class="flex gap-3">
          <button @click="downloadReport" class="btn-secondary">
            <Download class="w-4 h-4 mr-2" />
            Baixar Relatório
          </button>
          <button @click="resetComparison" class="btn-outline">
            <RotateCcw class="w-4 h-4 mr-2" />
            Nova Comparação
          </button>
        </div>
      </div>

  <!-- Estatísticas -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="stat-card">
          <div class="stat-value">{{ comparisonResult?.total_linhas_comparadas || 0 }}</div>
          <div class="stat-label">Total de Linhas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-green-600">{{ comparisonResult?.linhas_identicas || 0 }}</div>
          <div class="stat-label">Linhas Idênticas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-red-600">{{ comparisonResult?.linhas_com_diferencas || 0 }}</div>
          <div class="stat-label">Linhas com Diferenças</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" :class="taxaIdentidadeClass">
            {{ (comparisonResult?.taxa_identidade || 0).toFixed(2) }}%
          </div>
          <div class="stat-label">Taxa de Identidade</div>
        </div>
      </div>

      <!-- Paginação por Fatura (Nota) -->
      <div v-if="totalFaturas > 1" class="card">
        <div class="card-body flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div class="text-sm text-gray-700">
            Fatura <span class="font-semibold">{{ currentFatura }}</span> de <span class="font-semibold">{{ totalFaturas }}</span>
          </div>
          <div class="flex items-center gap-2">
            <button class="btn-outline" @click="prevFatura" :disabled="currentFatura <= 1">Anterior</button>
            <button class="btn-outline" @click="nextFatura" :disabled="currentFatura >= totalFaturas">Próxima</button>
          </div>
        </div>
      </div>

  <!-- Diferenças Detalhadas (paginadas por fatura) -->
  <div v-if="linhasExibidas.length > 0" class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold">Diferenças Encontradas</h3>
        </div>
        <div class="card-body">
          <div class="space-y-6">
            <div
      v-for="(diferenca, index) in linhasExibidas"
              :key="index"
              class="border border-gray-200 rounded-lg p-4"
            >
              <div class="flex justify-between items-center mb-3">
                <h4 class="font-semibold text-gray-900">
                  Linha {{ diferenca.numero_linha }} - {{ diferenca.tipo_registro }}
                </h4>
                <span class="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                  {{ diferenca.total_diferencas }} diferença(s)
                </span>
              </div>

              <!-- Visualização das Linhas -->
              <div class="space-y-1 mb-4 text-sm font-mono">
                <!-- Linha de Numeração -->
                <div v-if="diferenca.linha_numeracao">
                  <span class="text-gray-600">Campos:</span>
                  <div
                    :data-ref="`numeracao-linha-${index}`"
                    class="bg-blue-50 p-2 rounded border overflow-x-auto text-blue-800 font-semibold"
                    style="white-space: pre;"
                  >{{ diferenca.linha_numeracao }}</div>
                </div>

                <div>
                  <span class="text-gray-600">Base:</span>
                  <div
                    :data-ref="`base-linha-${index}`"
                    class="bg-gray-50 p-2 rounded border overflow-x-auto"
                    style="white-space: pre;"
                    @scroll="sincronizarScroll($event, `validado-linha-${index}`, `numeracao-linha-${index}`)"
                  >{{ diferenca.arquivo_base_linha }}</div>
                </div>
                <div>
                  <span class="text-gray-600">Comparado:</span>
                  <div
                    :data-ref="`validado-linha-${index}`"
                    class="bg-gray-50 p-2 rounded border overflow-x-auto"
                    style="white-space: pre;"
                    @scroll="sincronizarScroll($event, `base-linha-${index}`, `numeracao-linha-${index}`)"
                  >{{ diferenca.arquivo_validado_linha }}</div>
                </div>
              </div>

              <!-- Diferenças por Campo -->
              <div class="space-y-2">
                <h5 class="font-medium text-gray-700">Campos com Diferenças:</h5>
                <div class="grid gap-2">
                  <div
                    v-for="(campo, campIndex) in diferenca.diferencas_campos"
                    :key="campIndex"
                    class="flex justify-between items-center p-2 bg-red-50 rounded"
                  >
                    <div class="flex-1">
                      <span class="font-medium">Campo {{ (campo.sequencia_campo || 0).toString().padStart(2, '0') }} - {{ campo.nome_campo }}</span>
                      <span class="text-sm text-gray-600 ml-2">
                        (Pos {{ campo.posicao_inicio }}-{{ campo.posicao_fim }})
                      </span>
                    </div>
                    <div class="text-sm text-right max-w-md">
                      <div class="text-gray-600">
                        Base: <span class="font-mono bg-white px-1 rounded">{{ campo.valor_base }}</span>
                      </div>
                      <div class="text-gray-600">
                        Comp: <span class="font-mono bg-white px-1 rounded">{{ campo.valor_validado }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Totais e Componentes (apenas para tipo 56) -->
              <div v-if="diferenca.tipo_registro === '56' && (diferenca.totais_acumulados || diferenca.componentes_totais)" class="mt-4">
                <h5 class="font-medium text-gray-700">Totais calculados na fatura</h5>
                <div v-if="diferenca.totais_acumulados" class="text-sm text-gray-700 mt-2">
                  <div v-for="(val, key) in diferenca.totais_acumulados" :key="key" class="flex justify-between py-1 border-b border-gray-100">
                    <span class="font-mono">{{ key }}</span>
                    <span class="font-semibold">{{ formatCents(val) }}</span>
                  </div>
                </div>
                <div v-if="diferenca.componentes_totais" class="text-sm text-gray-700 mt-4">
                  <h6 class="font-medium">Componentes por total</h6>
                  <div v-for="(grp, gi) in diferenca.componentes_totais" :key="gi" class="mt-2">
                    <div class="font-mono text-blue-700">{{ grp.total }}</div>
                    <div v-if="grp.componentes && grp.componentes.length" class="pl-3 mt-1 space-y-1">
                      <div v-for="(comp, ci) in grp.componentes" :key="ci" class="flex justify-between">
                        <span>#{{ comp.linha }} • Tipo {{ comp.tipo }} • {{ comp.campo }}</span>
                        <span class="font-semibold">{{ formatCents(comp.valor) }}</span>
                      </div>
                    </div>
                    <div v-else class="pl-3 text-gray-500">Sem componentes (0)</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Error State -->
    <div v-if="error" class="card border-red-200 bg-red-50">
      <div class="card-body">
        <div class="flex items-start">
          <AlertCircle class="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 class="text-red-800 font-medium">Erro na Comparação</h3>
            <p class="text-red-700 mt-1">{{ error }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { AlertCircle, Download, GitCompare, Loader2, RotateCcw } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import api from '../services/api'
import localStorageService from '../services/localStorage'

// Reactive data
const layoutFile = ref(null)
const baseFile = ref(null)
const validationFile = ref(null)
const isLoading = ref(false)
const error = ref('')
const comparisonResult = ref(null)
const reportText = ref('')
const timestamp = ref('')

// Pagination by Fatura (Nota fiscal: começa em tipo 01)
const currentFatura = ref(1)
const gruposFatura = computed(() => {
  const diffs = comparisonResult.value?.diferencas_por_linha || []
  if (!diffs.length) return []

  const grupos = []
  let atual = []

  for (const d of diffs) {
    // Iniciar nova fatura ao encontrar tipo 01 (mantém a linha no novo grupo)
    if (d.tipo_registro === '01') {
      if (atual.length) grupos.push(atual)
      atual = []
    }
    atual.push(d)
  }
  if (atual.length) grupos.push(atual)

  // Se não encontrou nenhum 01, mantemos tudo como um único grupo
  return grupos.length ? grupos : [diffs]
})

const totalFaturas = computed(() => gruposFatura.value.length)
const linhasExibidas = computed(() => {
  const idx = Math.min(Math.max(currentFatura.value - 1, 0), Math.max(totalFaturas.value - 1, 0))
  return totalFaturas.value ? gruposFatura.value[idx] : (comparisonResult.value?.diferencas_por_linha || [])
})

function nextFatura() {
  if (currentFatura.value < totalFaturas.value) currentFatura.value += 1
}

function prevFatura() {
  if (currentFatura.value > 1) currentFatura.value -= 1
}

// Computed properties
const hasResults = computed(() => comparisonResult.value !== null)
const canSubmit = computed(() => layoutFile.value && baseFile.value && validationFile.value)

const taxaIdentidadeClass = computed(() => {
  const taxa = comparisonResult.value?.taxa_identidade || 0
  if (taxa >= 95) return 'text-green-600'
  if (taxa >= 80) return 'text-yellow-600'
  return 'text-red-600'
})

// File handlers
function handleLayoutFileChange(event) {
  layoutFile.value = event.target.files[0]
  clearError()
}

function handleBaseFileChange(event) {
  baseFile.value = event.target.files[0]
  clearError()
}

function handleValidationFileChange(event) {
  validationFile.value = event.target.files[0]
  clearError()
}

function clearError() {
  error.value = ''
}

// Main comparison function
async function handleComparison() {
  if (!canSubmit.value) return

  isLoading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('layout_file', layoutFile.value)
    formData.append('arquivo_base', baseFile.value)
    formData.append('arquivo_validado', validationFile.value)

    const response = await api.post('/comparar-estrutural', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

  comparisonResult.value = response.data.resultado_comparacao
    reportText.value = response.data.relatorio_texto
    timestamp.value = response.data.timestamp

    // Salvar no localStorage para download posterior
    if (response.data.dados_comparacao) {
      localStorageService.saveComparison(timestamp.value, response.data.dados_comparacao)
    }

  currentFatura.value = 1

  } catch (err) {
    console.error('Erro na comparação:', err)
    error.value = err.response?.data?.detail || 'Erro interno do servidor'
  } finally {
    isLoading.value = false
  }
}

// Download report
async function downloadReport() {
  if (!timestamp.value) return

  try {
    // Buscar dados do localStorage
    let comparisonData = localStorageService.getComparison(timestamp.value)

    // Se não estiver no localStorage, usar dados atuais
    if (!comparisonData && reportText.value) {
      comparisonData = {
        relatorio_texto: reportText.value,
        layout_nome: 'layout',
        timestamp: timestamp.value
      }
    }

    if (!comparisonData) {
      throw new Error('Dados da comparação não encontrados')
    }

    // Fazer download do relatório de texto
    const filename = `comparacao_estrutural_${timestamp.value}.txt`
    const content = comparisonData.relatorio_texto || reportText.value || 'Relatório não disponível'

    localStorageService.downloadText(content, filename)
  } catch (err) {
    console.error('Erro ao baixar relatório:', err)
    error.value = 'Erro ao baixar relatório: ' + err.message
  }
}

// Reset comparison
function resetComparison() {
  comparisonResult.value = null
  reportText.value = ''
  timestamp.value = ''
  layoutFile.value = null
  baseFile.value = null
  validationFile.value = null
  error.value = ''

  // Reset file inputs
  if (layoutFileInput.value) layoutFileInput.value.value = ''
  if (baseFileInput.value) baseFileInput.value.value = ''
  if (validationFileInput.value) validationFileInput.value.value = ''
}

// Sincronização de scroll
let scrollSyncing = false
function sincronizarScroll(event, targetRefName, numeracaoRefName = null) {
  if (scrollSyncing) return

  const target = document.querySelector(`[data-ref="${targetRefName}"]`)
  const numeracao = numeracaoRefName ? document.querySelector(`[data-ref="${numeracaoRefName}"]`) : null

  if (target && target !== event.target) {
    scrollSyncing = true
    target.scrollLeft = event.target.scrollLeft

    // Sincronizar também a linha de numeração se existir
    if (numeracao) {
      numeracao.scrollLeft = event.target.scrollLeft
    }

    setTimeout(() => { scrollSyncing = false }, 10)
  }
}

// Template refs
const layoutFileInput = ref(null)
const baseFileInput = ref(null)
const validationFileInput = ref(null)

// Helpers
function formatCents(value) {
  const n = Number(value || 0)
  const reais = n / 100
  return reais.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
</script>

<style scoped>
.file-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500;
}

.btn-primary {
  @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}

.btn-outline {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}

.card {
  @apply bg-white shadow rounded-lg;
}

.card-header {
  @apply px-6 py-4 border-b border-gray-200;
}

.card-body {
  @apply px-6 py-4;
}

.stat-card {
  @apply bg-white p-4 rounded-lg shadow border border-gray-200;
}

.stat-value {
  @apply text-2xl font-bold;
}

.stat-label {
  @apply text-sm text-gray-600 mt-1;
}
</style>