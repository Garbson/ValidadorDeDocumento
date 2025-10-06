<template>
  <div class="card">
    <div class="card-header">
      <h3 class="text-lg font-semibold flex items-center">
        <TrendingUp class="w-5 h-5 mr-2" />
        Evolução da Taxa de Sucesso
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
import { Chart, LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend, LineController } from 'chart.js'
import { TrendingUp } from 'lucide-vue-next'

Chart.register(LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend, LineController)

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

  const labels = props.data.map((_, index) => `Validação ${index + 1}`)
  const values = props.data.map(item => item.y)

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Taxa de Sucesso (%)',
        data: values,
        borderColor: 'rgb(59, 130, 246)', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
        pointBackgroundColor: values.map(value => {
          if (value >= 95) return 'rgb(34, 197, 94)' // green-500
          if (value >= 80) return 'rgb(251, 191, 36)' // yellow-500
          return 'rgb(239, 68, 68)' // red-500
        }),
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value) {
              return value + '%'
            }
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
              return `Taxa de Sucesso: ${context.parsed.y.toFixed(1)}%`
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