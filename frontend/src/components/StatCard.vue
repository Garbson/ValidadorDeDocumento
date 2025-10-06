<template>
  <div class="card">
    <div class="card-body">
      <div class="flex items-center">
        <div class="flex-shrink-0">
          <div :class="iconClasses">
            <component :is="iconComponent" class="w-6 h-6" />
          </div>
        </div>
        <div class="ml-4 flex-1">
          <p class="text-sm font-medium text-gray-500">{{ title }}</p>
          <p :class="valueClasses">{{ formattedValue }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FileText, CheckCircle, AlertCircle, TrendingUp, TrendingDown } from 'lucide-vue-next'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  icon: {
    type: String,
    default: 'FileText'
  },
  color: {
    type: String,
    default: 'blue'
  }
})

const iconComponents = {
  FileText,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  TrendingDown
}

const iconComponent = computed(() => iconComponents[props.icon] || FileText)

const colorClasses = {
  blue: {
    icon: 'bg-blue-100 text-blue-600',
    value: 'text-blue-600'
  },
  green: {
    icon: 'bg-success-100 text-success-600',
    value: 'text-success-600'
  },
  red: {
    icon: 'bg-error-100 text-error-600',
    value: 'text-error-600'
  },
  yellow: {
    icon: 'bg-warning-100 text-warning-600',
    value: 'text-warning-600'
  }
}

const iconClasses = computed(() => {
  const baseClasses = 'w-12 h-12 rounded-lg flex items-center justify-center'
  const colorClass = colorClasses[props.color]?.icon || colorClasses.blue.icon
  return `${baseClasses} ${colorClass}`
})

const valueClasses = computed(() => {
  const baseClasses = 'text-2xl font-bold'
  const colorClass = colorClasses[props.color]?.value || colorClasses.blue.value
  return `${baseClasses} ${colorClass}`
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString('pt-BR')
  }
  return props.value
})
</script>