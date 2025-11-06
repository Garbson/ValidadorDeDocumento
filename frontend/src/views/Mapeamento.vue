
<template>
  <div class="space-y-6">
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Mapeamento de Layout</h1>
      <p class="text-gray-600 max-w-2xl mx-auto">Carregue um arquivo Excel com colunas variadas (ex: CAMPO, TAM, TIPO, PREENCH, DOMINIO) e gere um layout padronizado automaticamente com posições calculadas.</p>
    </div>

    <div class="card max-w-3xl mx-auto" v-if="!layoutFile && !mappingLoaded">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <Upload class="w-5 h-5 mr-2" />
          Upload do Arquivo de Layout
        </h2>
      </div>
      <div class="card-body space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Arquivo Excel <span class="text-red-500">*</span></label>
          <input type="file" accept=".xlsx,.xls" class="file-input" @change="onFileChange" />
          <p class="text-xs text-gray-500 mt-1">Extensões suportadas: .xlsx, .xls</p>
        </div>
      </div>
    </div>

    <!-- Seleção de aba -->
    <div v-if="layoutFile && !sheetsLoaded" class="card max-w-3xl mx-auto">
      <div class="card-body flex items-center justify-between flex-wrap gap-4">
        <div class="text-sm text-gray-600 truncate">Selecionado: <strong>{{ layoutFile.name }}</strong></div>
        <div class="flex gap-2">
          <button class="btn-secondary" @click="resetAll">Trocar Arquivo</button>
          <button class="btn-primary" :disabled="loading" @click="carregarAbas">
            <span v-if="loading" class="flex items-center"><span class="loading-spinner w-5 h-5 mr-2"></span>Carregando abas...</span>
            <span v-else>Próximo</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Seleção de aba do Excel -->
    <div v-if="sheetsLoaded && !mappingLoaded" class="card max-w-3xl mx-auto">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <FileSpreadsheet class="w-5 h-5 mr-2" />
          Selecionar Aba do Excel
        </h2>
      </div>
      <div class="card-body space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Abas disponíveis <span class="text-red-500">*</span>
          </label>
          <select v-model="selectedSheet" class="input w-full">
            <option v-for="(sheet, index) in sheets" :key="index" :value="index">
              {{ index + 1 }}. {{ sheet }}
            </option>
          </select>
          <p class="text-xs text-gray-500 mt-1">
            Encontradas {{ sheets.length }} aba(s). Selecione a que contém o layout.
          </p>
        </div>
        <div class="flex gap-2 justify-end">
          <button class="btn-secondary" @click="voltarParaArquivo">Voltar</button>
          <button class="btn-primary" :disabled="selectedSheet === null || loading" @click="carregarMapping">
            <span v-if="loading" class="flex items-center"><span class="loading-spinner w-5 h-5 mr-2"></span>Processando...</span>
            <span v-else>Mapear Aba Selecionada</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showMapper" class="card max-w-7xl mx-auto">
      <div class="card-header flex items-center justify-between">
        <h2 class="text-lg font-semibold">Resultado do Mapeamento</h2>
        <button class="btn-secondary" @click="resetAll">Novo Arquivo</button>
      </div>
      <div class="card-body space-y-6">
        <LayoutMapper :file="layoutFile" :selected-sheet="selectedSheet" @confirmed="onConfirmed" @cancel="resetAll" />
        <div v-if="confirmedLayout" class="border rounded p-4 bg-gray-50 text-sm">
          <p class="font-medium mb-2">Layout Confirmado (preview campos):</p>
          <div v-if="downloadUrl" class="mb-3 flex flex-wrap items-center gap-3">
            <button @click="downloadLayout" class="btn-primary">Download Layout Excel</button>
            <button @click="usarNoValidador" class="btn-success">Usar no Visualizador</button>
            <span class="text-xs text-gray-500 truncate" :title="downloadFilename">{{ downloadFilename }}</span>
          </div>
          <div class="overflow-x-auto">
            <table class="table">
              <thead class="table-header">
                <tr>
                  <th class="table-header-cell">Campo</th>
                  <th class="table-header-cell">Início</th>
                  <th class="table-header-cell">Tamanho</th>
                  <th class="table-header-cell">Tipo</th>
                  <th class="table-header-cell">Obrigatório</th>
                </tr>
              </thead>
              <tbody class="table-body">
                <tr v-for="c in confirmedLayout.campos.slice(0,25)" :key="c.nome">
                  <td class="table-cell font-medium">{{ c.nome }}</td>
                  <td class="table-cell text-xs">{{ c.posicao_inicio }}</td>
                  <td class="table-cell text-xs">{{ c.tamanho }}</td>
                  <td class="table-cell text-xs">{{ c.tipo }}</td>
                  <td class="table-cell text-xs">{{ c.obrigatorio ? 'S' : 'N' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="mt-2 text-xs text-gray-500">Mostrando primeiros 25 campos (se existirem).</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutMapper from '@/components/LayoutMapper.vue'
import localStorageService from '@/services/localStorage'
import { useTempStore } from '@/stores/temp'
import { useValidationStore } from '@/stores/validation'
import { FileSpreadsheet, Upload } from 'lucide-vue-next'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const validationStore = useValidationStore()
const tempStore = useTempStore()
const layoutFile = ref(null)
const loading = ref(false)
const showMapper = ref(false)
const mappingLoaded = ref(false)
const confirmedLayout = ref(null)
const downloadUrl = ref(null)
const downloadFilename = ref(null)

// Novas variáveis para seleção de abas
const sheetsLoaded = ref(false)
const sheets = ref([])
const selectedSheet = ref(null)

function onFileChange(e){
  const f = e.target.files[0]
  if(!f) return
  layoutFile.value = f
  mappingLoaded.value = false
  confirmedLayout.value = null
  showMapper.value = false
  sheetsLoaded.value = false
  sheets.value = []
  selectedSheet.value = null
}

async function carregarAbas(){
  if(!layoutFile.value) return
  loading.value = true
  try {
    const result = await validationStore.listExcelSheets(layoutFile.value)
    sheets.value = result.sheets
    selectedSheet.value = result.default_sheet
    sheetsLoaded.value = true
  } catch (error) {
    console.error('Erro ao carregar abas:', error)
    alert('Erro ao carregar abas do Excel: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

function voltarParaArquivo(){
  sheetsLoaded.value = false
  sheets.value = []
  selectedSheet.value = null
}

async function carregarMapping(){
  if(!layoutFile.value) return
  loading.value = true
  try {
    // Apenas exibe o componente LayoutMapper que já faz chamada /mapear-layout
    showMapper.value = true
    mappingLoaded.value = true
  } finally {
    loading.value = false
  }
}

function onConfirmed(payload){
  confirmedLayout.value = payload.layout || null

  // Se temos dados do Excel, criar URL para download
  if (payload.excel_data && payload.filename) {
    // Criar download temporário via localStorage
    downloadUrl.value = 'localStorage'  // Flag para indicar que está no localStorage
    downloadFilename.value = payload.filename

    // Salvar dados para uso posterior
    window._currentLayoutData = {
      excel_data: payload.excel_data,
      filename: payload.filename
    }
  } else {
    downloadUrl.value = payload.download || null
    downloadFilename.value = payload.filename || null
  }
}

async function usarNoValidador(){
  if(!downloadUrl.value) return
  // Save server filename in temp store so Visualizador can fetch it reliably
  try {
    const filename = downloadFilename.value || (downloadUrl.value || '').split('/').pop()
    if (!filename) throw new Error('Nome do arquivo desconhecido')
    tempStore.setLayoutFromFilename(filename, confirmedLayout.value)
  // Navegar para Visualizador (usar nome de rota consistente)
  router.push({ name: 'Visualizador' })
  } catch (e) {
  console.error('Erro ao preparar layout para visualizador (fallback):', e)
  alert('Erro ao preparar layout para o Visualizador. Por favor, baixe manualmente e carregue o arquivo.')
  }
}

function downloadLayout(){
  try {
    // Usar dados salvos temporariamente
    if (window._currentLayoutData) {
      const { excel_data, filename } = window._currentLayoutData
      localStorageService.downloadExcel(excel_data, filename)
    } else {
      console.error('Dados do layout não encontrados')
      alert('Erro: Dados do layout não disponíveis para download')
    }
  } catch (error) {
    console.error('Erro no download do layout:', error)
    alert('Erro ao fazer download do layout: ' + error.message)
  }
}

function resetAll(){
  layoutFile.value = null
  loading.value = false
  showMapper.value = false
  mappingLoaded.value = false
  confirmedLayout.value = null
  downloadUrl.value = null
  downloadFilename.value = null
  sheetsLoaded.value = false
  sheets.value = []
  selectedSheet.value = null
}
</script>
