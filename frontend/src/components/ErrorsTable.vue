<template>
  <div class="card">
    <div class="card-header">
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-semibold flex items-center">
          <AlertCircle class="w-5 h-5 mr-2" />
          Detalhes dos Erros ({{ filteredErrors.length }} de {{ errors.length }})
        </h3>
        <div class="flex items-center space-x-4">
          <!-- Filtros -->
          <div class="flex items-center space-x-2">
            <label class="text-sm text-gray-600">Filtrar por tipo:</label>
            <select v-model="selectedErrorType" class="input text-sm w-auto">
              <option value="">Todos</option>
              <option v-for="type in errorTypes" :key="type" :value="type">
                {{ formatErrorType(type) }}
              </option>
            </select>
          </div>
          <div class="flex items-center space-x-2">
            <label class="text-sm text-gray-600">Por página:</label>
            <select v-model="itemsPerPage" class="input text-sm w-auto">
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
              <option :value="9999">Todos</option>
            </select>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body p-0">
      <div class="overflow-x-auto">
        <table class="table">
          <thead class="table-header">
            <tr>
              <th class="table-header-cell cursor-pointer" @click="sortBy('linha')">
                Linha
                <ChevronUp v-if="sortField === 'linha' && sortDirection === 'asc'" class="w-4 h-4 inline ml-1" />
                <ChevronDown v-else-if="sortField === 'linha' && sortDirection === 'desc'" class="w-4 h-4 inline ml-1" />
              </th>
              <th class="table-header-cell cursor-pointer" @click="sortBy('campo')">
                Campo
                <ChevronUp v-if="sortField === 'campo' && sortDirection === 'asc'" class="w-4 h-4 inline ml-1" />
                <ChevronDown v-else-if="sortField === 'campo' && sortDirection === 'desc'" class="w-4 h-4 inline ml-1" />
              </th>
              <th class="table-header-cell cursor-pointer" @click="sortBy('erro_tipo')">
                Tipo de Erro
                <ChevronUp v-if="sortField === 'erro_tipo' && sortDirection === 'asc'" class="w-4 h-4 inline ml-1" />
                <ChevronDown v-else-if="sortField === 'erro_tipo' && sortDirection === 'desc'" class="w-4 h-4 inline ml-1" />
              </th>
              <th class="table-header-cell">Valor Encontrado</th>
              <th class="table-header-cell">Descrição</th>
            </tr>
          </thead>
          <tbody class="table-body">
            <tr v-for="error in paginatedErrors" :key="`${error.linha}-${error.campo}`" class="hover:bg-gray-50">
              <td class="table-cell font-mono">{{ error.linha }}</td>
              <td class="table-cell font-medium">{{ error.campo }}</td>
              <td class="table-cell">
                <span :class="getErrorTypeBadgeClass(error.erro_tipo)">
                  {{ formatErrorType(error.erro_tipo) }}
                </span>
              </td>
              <td class="table-cell">
                <code class="text-xs bg-gray-100 px-2 py-1 rounded max-w-xs truncate block">
                  {{ error.valor_encontrado }}
                </code>
              </td>
              <td class="table-cell text-sm">{{ error.descricao }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Paginação -->
      <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-700">
            Mostrando {{ startItem }} a {{ endItem }} de {{ filteredErrors.length }} erros
          </div>
          <div class="flex items-center space-x-2">
            <button
              @click="currentPage = Math.max(1, currentPage - 1)"
              :disabled="currentPage === 1"
              class="btn-secondary text-sm disabled:opacity-50"
            >
              <ChevronLeft class="w-4 h-4" />
              Anterior
            </button>

            <div class="flex space-x-1">
              <button
                v-for="page in visiblePages"
                :key="page"
                @click="currentPage = page"
                :class="[
                  'px-3 py-1 text-sm rounded-md',
                  page === currentPage
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                ]"
              >
                {{ page }}
              </button>
            </div>

            <button
              @click="currentPage = Math.min(totalPages, currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="btn-secondary text-sm disabled:opacity-50"
            >
              Próximo
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { AlertCircle, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  errors: {
    type: Array,
    required: true
  }
})

// Estado da tabela
const currentPage = ref(1)
const itemsPerPage = ref(25)
const sortField = ref('linha')
const sortDirection = ref('asc')
const selectedErrorType = ref('')

// Computed properties
const errorTypes = computed(() => {
  const types = new Set(props.errors.map(error => error.erro_tipo))
  return Array.from(types).sort()
})

const filteredErrors = computed(() => {
  let filtered = props.errors

  if (selectedErrorType.value) {
    filtered = filtered.filter(error => error.erro_tipo === selectedErrorType.value)
  }

  // Ordenação
  filtered.sort((a, b) => {
    let aValue = a[sortField.value]
    let bValue = b[sortField.value]

    if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    }

    if (sortDirection.value === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })

  return filtered
})

const totalPages = computed(() => {
  if (itemsPerPage.value >= 9999) return 1
  return Math.ceil(filteredErrors.value.length / itemsPerPage.value)
})

const paginatedErrors = computed(() => {
  if (itemsPerPage.value >= 9999) return filteredErrors.value
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredErrors.value.slice(start, end)
})

const startItem = computed(() => {
  if (itemsPerPage.value >= 9999) return 1
  return (currentPage.value - 1) * itemsPerPage.value + 1
})

const endItem = computed(() => {
  if (itemsPerPage.value >= 9999) return filteredErrors.value.length
  return Math.min(currentPage.value * itemsPerPage.value, filteredErrors.value.length)
})

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

// Methods
const sortBy = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  currentPage.value = 1
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

const getErrorTypeBadgeClass = (type) => {
  const classes = {
    'CAMPO_OBRIGATORIO': 'badge badge-error',
    'TAMANHO_CAMPO': 'badge badge-warning',
    'TIPO_INVALIDO': 'badge badge-error',
    'FORMATO_INVALIDO': 'badge badge-warning',
    'TAMANHO_LINHA': 'badge badge-info',
    'ERRO_GENERICO': 'badge badge-info'
  }
  return classes[type] || 'badge badge-info'
}

// Watchers
watch([selectedErrorType, itemsPerPage], () => {
  currentPage.value = 1
})
</script>