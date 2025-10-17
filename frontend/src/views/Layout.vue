<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Teste de Layout</h1>
      <p class="text-gray-600">Valide a estrutura do seu arquivo de layout Excel</p>
    </div>

    <!-- Upload Form -->
    <div class="card max-w-2xl mx-auto">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <FileSpreadsheet class="w-5 h-5 mr-2" />
          Upload de Layout
        </h2>
      </div>
      <div class="card-body space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Arquivo de Layout Excel
            <span class="text-red-500">*</span>
          </label>
          <input
            type="file"
            accept=".xlsx,.xls"
            @change="handleFileChange"
            class="file-input"
            ref="fileInput"
          />
          <p class="text-sm text-gray-500 mt-1">
            Arquivo Excel (.xlsx ou .xls) com as especificações dos campos
          </p>
        </div>

        <button
          @click="validateLayout"
          :disabled="!selectedFile || isLoading"
          class="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div v-if="isLoading" class="flex items-center justify-center">
            <div class="loading-spinner w-5 h-5 mr-2"></div>
            Validando Layout...
          </div>
          <div v-else class="flex items-center justify-center">
            <CheckSquare class="w-5 h-5 mr-2" />
            Validar Layout
          </div>
        </button>

        <!-- Error Message -->
        <div v-if="error" class="bg-error-50 border border-error-200 rounded-md p-4">
          <div class="flex">
            <AlertCircle class="w-5 h-5 text-error-400 mr-2 mt-0.5" />
            <div>
              <h3 class="text-sm font-medium text-error-800">Erro na Validação</h3>
              <p class="text-sm text-error-700 mt-1">{{ error }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Layout Results -->
    <div v-if="layoutData" class="space-y-6 animate-fade-in">
      <!-- Layout Info -->
      <div class="card max-w-6xl mx-auto">
        <div class="card-header">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold flex items-center">
              <CheckCircle class="w-5 h-5 mr-2 text-success-500" />
              Layout Válido: {{ layoutData.nome }}
            </h3>
            <button @click="clearLayout" class="btn-secondary">
              <RefreshCw class="w-4 h-4 mr-2" />
              Novo Teste
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600">{{ layoutData.campos.length }}</div>
              <div class="text-sm text-gray-500">Total de Campos</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600">{{ layoutData.tamanho_linha }}</div>
              <div class="text-sm text-gray-500">Tamanho da Linha</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600">{{ camposObrigatorios }}</div>
              <div class="text-sm text-gray-500">Campos Obrigatórios</div>
            </div>
          </div>

          <!-- Campos por Tipo -->
          <div class="mb-6">
            <h4 class="font-semibold mb-3">Distribuição por Tipo</h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div v-for="(count, type) in tiposCampos" :key="type" class="text-center">
                <div class="badge badge-info text-lg px-3 py-2">{{ count }}</div>
                <div class="text-sm text-gray-600 mt-1">{{ type }}</div>
              </div>
            </div>
          </div>

          <!-- Tabela de Campos -->
          <div class="overflow-x-auto">
            <table class="table">
              <thead class="table-header">
                <tr>
                  <th class="table-header-cell">Campo</th>
                  <th class="table-header-cell">Posição</th>
                  <th class="table-header-cell">Tamanho</th>
                  <th class="table-header-cell">Tipo</th>
                  <th class="table-header-cell">Obrigatório</th>
                  <th class="table-header-cell">Formato</th>
                </tr>
              </thead>
              <tbody class="table-body">
                <tr v-for="campo in layoutData.campos" :key="campo.nome" class="hover:bg-gray-50">
                  <td class="table-cell font-medium">{{ campo.nome }}</td>
                  <td class="table-cell font-mono">{{ campo.posicao_inicio }}-{{ campo.posicao_fim }}</td>
                  <td class="table-cell">{{ campo.tamanho }}</td>
                  <td class="table-cell">
                    <span :class="getTipoBadgeClass(campo.tipo)">{{ campo.tipo }}</span>
                  </td>
                  <td class="table-cell">
                    <span v-if="campo.obrigatorio" class="badge badge-error">Sim</span>
                    <span v-else class="badge badge-success">Não</span>
                  </td>
                  <td class="table-cell">
                    <code v-if="campo.formato" class="text-xs bg-gray-100 px-2 py-1 rounded">
                      {{ campo.formato }}
                    </code>
                    <span v-else class="text-gray-400">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Exemplo de Linha -->
      <div class="card max-w-6xl mx-auto">
        <div class="card-header">
          <h3 class="text-lg font-semibold flex items-center">
            <FileText class="w-5 h-5 mr-2" />
            Exemplo de Linha Válida
          </h3>
        </div>
        <div class="card-body">
          <div class="bg-gray-100 p-4 rounded-lg font-mono text-sm break-all">
            {{ exemploLinha }}
          </div>
          <p class="text-sm text-gray-600 mt-2">
            Exemplo de como uma linha válida deve aparecer no arquivo TXT baseado neste layout.
          </p>
        </div>
      </div>
    </div>

    <!-- Layout Guide -->
    <div class="card max-w-4xl mx-auto">
      <div class="card-header">
        <h3 class="text-lg font-semibold flex items-center">
          <BookOpen class="w-5 h-5 mr-2" />
          Guia do Layout Excel
        </h3>
      </div>
      <div class="card-body">
        <div class="space-y-4">
          <p class="text-gray-700">
            Seu arquivo Excel deve conter as seguintes colunas obrigatórias:
          </p>

          <div class="overflow-x-auto">
            <table class="table">
              <thead class="table-header">
                <tr>
                  <th class="table-header-cell">Coluna</th>
                  <th class="table-header-cell">Descrição</th>
                  <th class="table-header-cell">Valores Válidos</th>
                  <th class="table-header-cell">Exemplo</th>
                </tr>
              </thead>
              <tbody class="table-body">
                <tr>
                  <td class="table-cell font-medium">Campo</td>
                  <td class="table-cell">Nome do campo</td>
                  <td class="table-cell">Qualquer texto</td>
                  <td class="table-cell"><code>NOME_CLIENTE</code></td>
                </tr>
                <tr>
                  <td class="table-cell font-medium">Posicao_Inicio</td>
                  <td class="table-cell">Posição inicial (1-indexed)</td>
                  <td class="table-cell">Número > 0</td>
                  <td class="table-cell"><code>1</code></td>
                </tr>
                <tr>
                  <td class="table-cell font-medium">Tamanho</td>
                  <td class="table-cell">Tamanho do campo</td>
                  <td class="table-cell">Número > 0</td>
                  <td class="table-cell"><code>30</code></td>
                </tr>
                <tr>
                  <td class="table-cell font-medium">Tipo</td>
                  <td class="table-cell">Tipo de dados</td>
                  <td class="table-cell">TEXTO, NUMERO, DATA, DECIMAL</td>
                  <td class="table-cell"><code>TEXTO</code></td>
                </tr>
                <tr>
                  <td class="table-cell font-medium">Obrigatorio</td>
                  <td class="table-cell">Campo obrigatório</td>
                  <td class="table-cell">S (Sim) ou N (Não)</td>
                  <td class="table-cell"><code>S</code></td>
                </tr>
                <tr>
                  <td class="table-cell font-medium">Formato</td>
                  <td class="table-cell">Formato específico (opcional)</td>
                  <td class="table-cell">Para datas: YYYYMMDD, etc.</td>
                  <td class="table-cell"><code>YYYYMMDD</code></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FileSpreadsheet, CheckSquare, AlertCircle, CheckCircle, RefreshCw, FileText, BookOpen } from 'lucide-vue-next'
import { useValidationStore } from '@/stores/validation'

const validationStore = useValidationStore()

const selectedFile = ref(null)
const layoutData = ref(null)
const isLoading = ref(false)
const error = ref(null)
const fileInput = ref(null)

const camposObrigatorios = computed(() => {
  if (!layoutData.value) return 0
  return layoutData.value.campos.filter(campo => campo.obrigatorio).length
})

const tiposCampos = computed(() => {
  if (!layoutData.value) return {}
  const tipos = {}
  layoutData.value.campos.forEach(campo => {
    tipos[campo.tipo] = (tipos[campo.tipo] || 0) + 1
  })
  return tipos
})

const exemploLinha = computed(() => {
  if (!layoutData.value) return ''

  let linha = ''
  for (const campo of layoutData.value.campos) {
    const tamanho = campo.tamanho
    let exemplo = ''

    switch (campo.tipo) {
      case 'TEXTO':
        exemplo = 'EXEMPLO'.padEnd(tamanho, ' ')
        break
      case 'NUMERO':
        exemplo = '123'.padStart(tamanho, '0')
        break
      case 'DATA':
        exemplo = '20240101'.padEnd(tamanho, ' ')
        break
      case 'DECIMAL':
        exemplo = '12345'.padStart(tamanho, '0')
        break
      default:
        exemplo = ' '.repeat(tamanho)
    }

    linha += exemplo.substring(0, tamanho)
  }

  return linha
})

const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (!file) return
  // Se o mesmo arquivo for escolhido novamente o evento pode não disparar; resetamos o input após uso
  selectedFile.value = file
  layoutData.value = null
  error.value = null
  // Opcional: auto validar ao selecionar (descomentar abaixo)
  // validateLayout()
}

const validateLayout = async () => {
  if (!selectedFile.value || isLoading.value) return
  isLoading.value = true
  error.value = null
  try {
    layoutData.value = await validationStore.validateLayout(selectedFile.value)
    // permitir re-selecionar o mesmo arquivo posteriormente
    if (fileInput.value) fileInput.value.value = ''
  } catch (err) {
    error.value = err.response?.data?.detail || 'Erro ao validar layout'
  } finally {
    isLoading.value = false
  }
}

const clearLayout = () => {
  layoutData.value = null
  error.value = null
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const getTipoBadgeClass = (tipo) => {
  const classes = {
    'TEXTO': 'badge badge-info',
    'NUMERO': 'badge badge-success',
    'DATA': 'badge badge-warning',
    'DECIMAL': 'badge badge-error'
  }
  return classes[tipo] || 'badge badge-info'
}
</script>