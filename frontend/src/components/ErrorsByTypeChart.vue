<template>
  <div class="card">
    <div class="card-header">
      <h3 class="text-lg font-semibold flex items-center">
        <PieChart class="w-5 h-5 mr-2" />
        Erros por Tipo
      </h3>
    </div>
    <div class="card-body">
      <div class="relative">
        <canvas ref="chartCanvas" class="max-h-64"></canvas>
      </div>
      <div class="mt-4 space-y-2">
        <div v-for="(value, key) in data" :key="key" class="flex justify-between items-center text-sm">
          <span class="flex items-center">
            <div
              class="w-3 h-3 rounded-full mr-2"
              :style="{ backgroundColor: getColorForIndex(Object.keys(data).indexOf(key)) }"
            ></div>
            {{ formatErrorType(key) }}
          </span>
          <span class="font-medium">{{ value.toLocaleString('pt-BR') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Chart, ArcElement, Tooltip, Legend, PieController } from 'chart.js'
import { PieChart } from 'lucide-vue-next'

Chart.register(ArcElement, Tooltip, Legend, PieController)

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

const chartCanvas = ref(null)
let chartInstance = null

const colors = [
  '#ef4444', // red
  '#f97316', // orange
  '#eab308', // yellow
  '#22c55e', // green
  '#3b82f6', // blue
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#6b7280', // gray
]

const getColorForIndex = (index) => {
  return colors[index % colors.length]
}

const formatErrorType = (type) => {
  const translations = {
    'CAMPO_OBRIGATORIO': 'Campo Obrigatório',
    'TAMANHO_CAMPO': 'Tamanho Inválido',
    'TIPO_INVALIDO': 'Tipo Inválido',
    'FORMATO_INVALIDO': 'Formato Inválido',
    'TAMANHO_LINHA': 'Tamanho da Linha',
    'ERRO_GENERICO': 'Erro Genérico'
  }
  return translations[type] || type
}

const createChart = () => {
  if (!chartCanvas.value || !props.data) return

  const ctx = chartCanvas.value.getContext('2d')

  const labels = Object.keys(props.data).map(formatErrorType)
  const values = Object.values(props.data)
  const backgroundColors = Object.keys(props.data).map((_, index) => getColorForIndex(index))

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: backgroundColors,
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false // Legenda customizada abaixo
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || ''
              const value = context.parsed
              const total = context.dataset.data.reduce((a, b) => a + b, 0)
              const percentage = ((value / total) * 100).toFixed(1)
              return `${label}: ${value.toLocaleString('pt-BR')} (${percentage}%)`
            }
          }
        }
      }
    }
  })
}

onMounted(() => {
  createChart()
})

watch(() => props.data, () => {
  createChart()
}, { deep: true })
</script>