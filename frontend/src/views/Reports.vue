<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Relatórios e Histórico</h1>
      <p class="text-gray-600">Visualize e gerencie seus relatórios de validação</p>
    </div>

    <!-- Quick Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="card">
        <div class="card-body text-center">
          <div class="text-2xl font-bold text-primary-600">{{ validationStore.validationHistory.length }}</div>
          <div class="text-sm text-gray-500">Validações Realizadas</div>
        </div>
      </div>
      <div class="card">
        <div class="card-body text-center">
          <div class="text-2xl font-bold text-success-600">{{ validacoesComSucesso }}</div>
          <div class="text-sm text-gray-500">Com Taxa > 95%</div>
        </div>
      </div>
      <div class="card">
        <div class="card-body text-center">
          <div class="text-2xl font-bold text-warning-600">{{ validacoesComAtencao }}</div>
          <div class="text-sm text-gray-500">Com Taxa 80-95%</div>
        </div>
      </div>
      <div class="card">
        <div class="card-body text-center">
          <div class="text-2xl font-bold text-error-600">{{ validacoesComErros }}</div>
          <div class="text-sm text-gray-500">Com Taxa < 80%</div>
        </div>
      </div>
    </div>

    <!-- Current Validation -->
    <div v-if="validationStore.hasValidation" class="card">
      <div class="card-header">
        <div class="flex justify-between items-center">
          <h2 class="text-lg font-semibold flex items-center">
            <Clock class="w-5 h-5 mr-2" />
            Validação Atual
          </h2>
          <div class="flex space-x-2">
            <button @click="downloadCurrentReport('excel')" class="btn-primary">
              <Download class="w-4 h-4 mr-2" />
              Excel
            </button>
            <button @click="downloadCurrentReport('csv')" class="btn-secondary">
              <Download class="w-4 h-4 mr-2" />
              CSV
            </button>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div class="text-sm text-gray-500">Taxa de Sucesso</div>
            <div :class="getSuccessRateColorClass(validationStore.successRate)" class="text-xl font-bold">
              {{ validationStore.successRate.toFixed(1) }}%
            </div>
          </div>
          <div>
            <div class="text-sm text-gray-500">Total de Linhas</div>
            <div class="text-xl font-bold text-gray-900">
              {{ validationStore.currentValidation.resultado.total_linhas.toLocaleString('pt-BR') }}
            </div>
          </div>
          <div>
            <div class="text-sm text-gray-500">Total de Erros</div>
            <div class="text-xl font-bold text-error-600">
              {{ validationStore.totalErrors.toLocaleString('pt-BR') }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Validation History -->
    <div class="card">
      <div class="card-header">
        <div class="flex justify-between items-center">
          <h2 class="text-lg font-semibold flex items-center">
            <History class="w-5 h-5 mr-2" />
            Histórico de Validações
          </h2>
          <button v-if="validationStore.validationHistory.length > 0" @click="clearHistory" class="btn-secondary">
            <Trash2 class="w-4 h-4 mr-2" />
            Limpar Histórico
          </button>
        </div>
      </div>
      <div class="card-body">
        <div v-if="validationStore.validationHistory.length === 0" class="text-center py-8">
          <FileX class="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900 mb-2">Nenhuma validação realizada</h3>
          <p class="text-gray-500 mb-4">Comece fazendo uma validação para ver o histórico aqui.</p>
          <router-link to="/validador" class="btn-primary">
            <CheckSquare class="w-4 h-4 mr-2" />
            Iniciar Validação
          </router-link>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="validation in validationStore.validationHistory"
            :key="validation.id"
            class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="flex items-center space-x-4">
                  <div class="flex-shrink-0">
                    <div
                      :class="getStatusIconClass(validation.resultado.taxa_sucesso)"
                      class="w-10 h-10 rounded-full flex items-center justify-center"
                    >
                      <CheckCircle v-if="validation.resultado.taxa_sucesso >= 95" class="w-5 h-5" />
                      <AlertTriangle v-else-if="validation.resultado.taxa_sucesso >= 80" class="w-5 h-5" />
                      <XCircle v-else class="w-5 h-5" />
                    </div>
                  </div>

                  <div class="flex-1">
                    <div class="flex items-center space-x-4">
                      <div>
                        <h3 class="font-medium text-gray-900">{{ validation.layoutFileName }}</h3>
                        <p class="text-sm text-gray-500">{{ validation.dataFileName }}</p>
                      </div>
                      <div class="text-center">
                        <div :class="getSuccessRateColorClass(validation.resultado.taxa_sucesso)" class="font-semibold">
                          {{ validation.resultado.taxa_sucesso.toFixed(1) }}%
                        </div>
                        <div class="text-xs text-gray-500">Taxa de Sucesso</div>
                      </div>
                      <div class="text-center">
                        <div class="font-semibold text-gray-900">
                          {{ validation.resultado.total_linhas.toLocaleString('pt-BR') }}
                        </div>
                        <div class="text-xs text-gray-500">Linhas</div>
                      </div>
                      <div class="text-center">
                        <div class="font-semibold text-error-600">
                          {{ validation.resultado.erros.length.toLocaleString('pt-BR') }}
                        </div>
                        <div class="text-xs text-gray-500">Erros</div>
                      </div>
                      <div class="text-right">
                        <div class="text-sm text-gray-900">
                          {{ formatDate(validation.createdAt) }}
                        </div>
                        <div class="text-xs text-gray-500">
                          {{ formatTime(validation.createdAt) }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="flex items-center space-x-2 ml-4">
                <button
                  @click="viewValidation(validation)"
                  class="btn-secondary"
                  title="Ver Detalhes"
                >
                  <Eye class="w-4 h-4" />
                </button>
                <button
                  @click="downloadHistoryReport(validation.timestamp, 'excel')"
                  class="btn-secondary"
                  title="Download Excel"
                >
                  <Download class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Section -->
    <div v-if="validationStore.validationHistory.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <SuccessRateChart :data="historyChartData" />
      <ErrorTrendsChart :data="errorTrendsData" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useValidationStore } from '@/stores/validation'
import { useRouter } from 'vue-router'
import {
  Clock, Download, History, Trash2, FileX, CheckSquare, CheckCircle,
  AlertTriangle, XCircle, Eye
} from 'lucide-vue-next'
import SuccessRateChart from '@/components/SuccessRateChart.vue'
import ErrorTrendsChart from '@/components/ErrorTrendsChart.vue'

const validationStore = useValidationStore()
const router = useRouter()

// Computed properties
const validacoesComSucesso = computed(() => {
  return validationStore.validationHistory.filter(v => v.resultado.taxa_sucesso >= 95).length
})

const validacoesComAtencao = computed(() => {
  return validationStore.validationHistory.filter(v =>
    v.resultado.taxa_sucesso >= 80 && v.resultado.taxa_sucesso < 95
  ).length
})

const validacoesComErros = computed(() => {
  return validationStore.validationHistory.filter(v => v.resultado.taxa_sucesso < 80).length
})

const historyChartData = computed(() => {
  return validationStore.validationHistory
    .slice()
    .reverse()
    .map((validation, index) => ({
      x: index + 1,
      y: validation.resultado.taxa_sucesso,
      label: `${validation.layoutFileName} - ${formatDate(validation.createdAt)}`
    }))
})

const errorTrendsData = computed(() => {
  return validationStore.validationHistory
    .slice()
    .reverse()
    .map((validation, index) => ({
      x: index + 1,
      y: validation.resultado.erros.length,
      label: `${validation.layoutFileName} - ${formatDate(validation.createdAt)}`
    }))
})

// Methods
const downloadCurrentReport = async (format) => {
  if (!validationStore.currentValidation?.timestamp) return

  try {
    await validationStore.downloadReport(validationStore.currentValidation.timestamp, format)
  } catch (error) {
    console.error('Erro no download:', error)
  }
}

const downloadHistoryReport = async (timestamp, format) => {
  try {
    await validationStore.downloadReport(timestamp, format)
  } catch (error) {
    console.error('Erro no download:', error)
  }
}

const viewValidation = (validation) => {
  validationStore.setCurrentValidation(validation)
  router.push('/validador')
}

const clearHistory = () => {
  if (confirm('Tem certeza que deseja limpar todo o histórico de validações?')) {
    validationStore.validationHistory.splice(0)
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('pt-BR')
}

const formatTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getSuccessRateColorClass = (rate) => {
  if (rate >= 95) return 'text-success-600'
  if (rate >= 80) return 'text-warning-600'
  return 'text-error-600'
}

const getStatusIconClass = (rate) => {
  if (rate >= 95) return 'bg-success-100 text-success-600'
  if (rate >= 80) return 'bg-warning-100 text-warning-600'
  return 'bg-error-100 text-error-600'
}
</script>