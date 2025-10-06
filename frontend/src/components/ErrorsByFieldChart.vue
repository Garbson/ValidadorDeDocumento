<template>
  <div class="card">
    <div class="card-header">
      <h3 class="text-lg font-semibold flex items-center">
        <BarChart3 class="w-5 h-5 mr-2" />
        Top Campos com Erros
      </h3>
    </div>
    <div class="card-body">
      <div class="relative">
        <canvas ref="chartCanvas" class="max-h-64"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Chart, BarElement, CategoryScale, LinearScale, Tooltip, Legend, BarController } from 'chart.js'
import { BarChart3 } from 'lucide-vue-next'

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, BarController)

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

const chartCanvas = ref(null)
let chartInstance = null

const createChart = () => {
  if (!chartCanvas.value || !props.data) return

  const ctx = chartCanvas.value.getContext('2d')

  // Pegar apenas os top 10 campos com mais erros
  const sortedEntries = Object.entries(props.data)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 10)

  const labels = sortedEntries.map(([field]) => field)
  const values = sortedEntries.map(([,count]) => count)

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Quantidade de Erros',
        data: values,
        backgroundColor: 'rgba(239, 68, 68, 0.8)', // red-500 with opacity
        borderColor: 'rgb(239, 68, 68)', // red-500
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
        },
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 0
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `Erros: ${context.parsed.y.toLocaleString('pt-BR')}`
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