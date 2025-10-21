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

    <div v-if="layoutFile" class="card max-w-3xl mx-auto" v-show="!mappingLoaded">
      <div class="card-body flex items-center justify-between flex-wrap gap-4">
        <div class="text-sm text-gray-600 truncate">Selecionado: <strong>{{ layoutFile.name }}</strong></div>
        <div class="flex gap-2">
          <button class="btn-secondary" @click="resetAll">Trocar Arquivo</button>
          <button class="btn-primary" :disabled="loading" @click="carregarMapping">
            <span v-if="loading" class="flex items-center"><span class="loading-spinner w-5 h-5 mr-2"></span>Processando...</span>
            <span v-else>Mapear</span>
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
        <LayoutMapper :file="layoutFile" @confirmed="onConfirmed" @cancel="resetAll" />
        <div v-if="confirmedLayout" class="border rounded p-4 bg-gray-50 text-sm">
          <p class="font-medium mb-2">Layout Confirmado (preview campos):</p>
          <div v-if="downloadUrl" class="mb-3 flex flex-wrap items-center gap-3">
            <a :href="downloadUrl" target="_blank" class="btn-primary">Download Layout Excel</a>
            <button @click="usarNoValidador" class="btn-success">Usar no Validador</button>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Upload } from 'lucide-vue-next'
import LayoutMapper from '@/components/LayoutMapper.vue'
import { useTempStore } from '@/stores/temp'

const router = useRouter()
const tempStore = useTempStore()
const layoutFile = ref(null)
const loading = ref(false)
const showMapper = ref(false)
const mappingLoaded = ref(false)
const confirmedLayout = ref(null)
const downloadUrl = ref(null)
const downloadFilename = ref(null)

function onFileChange(e){
  const f = e.target.files[0]
  if(!f) return
  layoutFile.value = f
  mappingLoaded.value = false
  confirmedLayout.value = null
  showMapper.value = false
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
  downloadUrl.value = payload.download || null
  downloadFilename.value = payload.filename || null
}

async function usarNoValidador(){
  if(!downloadUrl.value) return
  const fullUrl = downloadUrl.value.startsWith('http') ? downloadUrl.value : `http://localhost:8000${downloadUrl.value}`
  try{
    loading.value = true
    const res = await fetch(fullUrl)
    if(!res.ok) throw new Error('Falha no download: ' + res.status)
    const blob = await res.blob()
    const filename = downloadFilename.value || 'layout.xlsx'
    const file = new File([blob], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    // Salvar no store temporário e navegar para o Validador
    tempStore.setLayout(file, confirmedLayout.value)
    router.push({ name: 'Validator' })
  }catch(e){
    console.error('Erro ao preparar layout para validador:', e)
    alert('Erro ao carregar layout. Por favor, faça o download manualmente e carregue no validador.')
  }finally{
    loading.value = false
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
}

async function downloadMapping(){
  if(!downloadUrl.value) return
  try{
    loading.value = true
    const fullUrl = downloadUrl.value.startsWith('http') ? downloadUrl.value : `http://localhost:8000${downloadUrl.value}`
    const res = await fetch(fullUrl)
    if(!res.ok) throw new Error('Erro ao baixar arquivo')
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = downloadFilename.value || 'layout.xlsx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  }catch(e){
    console.error('Erro ao salvar mapeamento:', e)
    alert('Falha ao baixar o arquivo. Por favor, tente novamente.')
  }finally{
    loading.value = false
  }
}

</script>
