<template>
  <div class="card">
    <div class="card-header">
      <h3 class="text-lg font-semibold flex items-center">
        <TrendingDown class="w-5 h-5 mr-2" />
        Tendência de Erros
      </h3>
    </div>
    <div class="card-body">
      <div class="relative">
        <canvas ref="chartCanvas" class="max-h-64"></canvas>
      </div>
      <div v-if="data.length === 0" class="text-center py-8 text-gray-500">
        Dados insuficientes para gerar gráfico
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Chart, BarElement, CategoryScale, LinearScale, Tooltip, Legend, BarController } from 'chart.js'
import { TrendingDown } from 'lucide-vue-next'

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, BarController)

const props = defineProps({
  data: {
    type: Array,
    required: true
  }
})

const chartCanvas = ref(null)
let chartInstance = null

const createChart = () => {
  if (!chartCanvas.value || !props.data.length) return

  const ctx = chartCanvas.value.getContext('2d')

  if (chartInstance) {
    chartInstance.destroy()
  }

  const labels = props.data.map((_, index) => `Val. ${index + 1}`)
  const values = props.data.map(item => item.y)

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Quantidade de Erros',
        data: values,
        backgroundColor: values.map(value => {
          if (value === 0) return 'rgba(34, 197, 94, 0.8)' // green-500
          if (value <= 10) return 'rgba(251, 191, 36, 0.8)' // yellow-500
          if (value <= 100) return 'rgba(249, 115, 22, 0.8)' // orange-500
          return 'rgba(239, 68, 68, 0.8)' // red-500
        }),
        borderColor: values.map(value => {
          if (value === 0) return 'rgb(34, 197, 94)' // green-500
          if (value <= 10) return 'rgb(251, 191, 36)' // yellow-500
          if (value <= 100) return 'rgb(249, 115, 22)' // orange-500
          return 'rgb(239, 68, 68)' // red-500
        }),
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            title: function(context) {
              const index = context[0].dataIndex
              return props.data[index]?.label || context[0].label
            },
            label: function(context) {
              return `Erros encontrados: ${context.parsed.y.toLocaleString('pt-BR')}`
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