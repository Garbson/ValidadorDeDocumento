<template>
  <div class="space-y-6" v-if="state.loaded">
    <div class="flex items-center justify-between">
      <h3 class="text-xl font-semibold">Mapeamento de Layout</h3>
      <div class="flex gap-2">
        <button class="btn-secondary" @click="$emit('cancel')" :disabled="state.saving">Cancelar</button>
        <button class="btn-primary" :disabled="!isComplete || state.saving" @click="confirmMapping">
          <span v-if="state.saving">Confirmando...</span>
          <span v-else>Confirmar Mapeamento</span>
        </button>
      </div>
    </div>

    <div v-if="response.cached" class="p-3 bg-green-50 border border-green-200 text-sm rounded">
      Mapeamento recuperado do cache (assinatura: <code>{{ response.signature }}</code>). Confirme ou ajuste.
    </div>
    <div v-else class="p-3 bg-blue-50 border border-blue-200 text-sm rounded">
      Mapeamento sugerido automaticamente (assinatura: <code>{{ response.signature }}</code>). Revise antes de confirmar.
    </div>

  <div v-if="state.message" class="text-xs" :class="state.error ? 'text-error-600' : 'text-success-600'">{{ state.message }}</div>
  <div class="overflow-x-auto">
      <table class="table">
        <thead class="table-header">
          <tr>
            <th class="table-header-cell w-40">Canônico</th>
            <th class="table-header-cell">Selecionar / Coluna Original</th>
            <th class="table-header-cell">Exemplos Originais</th>
            <th class="table-header-cell">Obrigatória</th>
            <th class="table-header-cell w-24">Ação</th>
          </tr>
        </thead>
        <tbody class="table-body">
          <tr v-for="c in canonicalColumns" :key="c" :class="rowClass(c)">
            <td class="table-cell font-medium">{{ c }}</td>
            <td class="table-cell">
              <select v-model="localMapping[c]" class="input w-full">
                <option :value="null">-- Selecionar --</option>
                <option v-for="(h, index) in allOriginalHeaders" :key="`header-${index}-${h}`" :value="h">{{ h }}</option>
                <option value="__custom__">(Nova Coluna Manual)</option>
              </select>
              <div v-if="localMapping[c] === '__custom__'" class="mt-2">
                <input v-model="customColumns[c]" placeholder="Nome da nova coluna" class="input w-full" />
              </div>
            </td>
            <td class="table-cell text-xs">
              <div v-if="localMapping[c] && localMapping[c] !== '__custom__'">
                <ul class="list-disc ml-4 space-y-0.5" v-if="originalSamples[localMapping[c]] && originalSamples[localMapping[c]].length">
                  <li v-for="s in originalSamples[localMapping[c]]" :key="s" class="truncate" :title="s">{{ s }}</li>
                </ul>
                <span v-else class="text-gray-400">(sem exemplos)</span>
              </div>
              <div v-else class="text-gray-400">—</div>
            </td>
            <td class="table-cell text-center">
              <span v-if="isRequired(c)" class="text-error-600 font-semibold">Sim</span>
              <span v-else class="text-gray-500">Não</span>
            </td>
            <td class="table-cell">
              <button v-if="localMapping[c]" class="text-xs text-red-600 hover:underline" @click="clearMapping(c)">Limpar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  <div class="grid md:grid-cols-2 gap-4" v-if="response.sample.length">
      <div class="card">
        <div class="card-header"><h4 class="font-semibold text-sm">Amostra Normalizada (Top 5)</h4></div>
        <div class="card-body overflow-x-auto">
          <table class="table text-xs">
            <thead class="table-header">
              <tr>
                <th v-for="c in canonicalColumns" :key="c" class="table-header-cell">{{ c }}</th>
              </tr>
            </thead>
            <tbody class="table-body">
              <tr v-for="(row, idx) in response.sample" :key="idx">
                <td v-for="c in canonicalColumns" :key="c" class="table-cell">{{ row[c] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="card">
        <div class="card-header"><h4 class="font-semibold text-sm">Status</h4></div>
        <div class="card-body text-sm space-y-2">
          <div>
            <strong>Completude:</strong> {{ Math.round((1 - missingRequired.length/requiredColumns.length)*100) }}%
          </div>
          <div v-if="missingRequired.length" class="text-error-600">
            <strong>Faltando:</strong> {{ missingRequired.join(', ') }}
          </div>
          <div v-if="response.warnings.length" class="text-warning-600">
            <strong>Warnings:</strong>
            <ul class="list-disc ml-5">
              <li v-for="w in response.warnings" :key="w">{{ w }}</li>
            </ul>
          </div>
          <div v-if="!missingRequired.length" class="text-success-600 font-medium">Todos os campos obrigatórios mapeados.</div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="py-8 text-center text-sm text-gray-500">Carregando mapeamento...</div>
</template>

<script setup>
import api from '@/services/api'
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  file: { type: File, required: true },
  selectedSheet: { type: Number, default: null }
})
const emits = defineEmits(['cancel', 'confirmed'])

const state = reactive({ loaded: false, saving: false, message: '', error: false })
const response = reactive({
  signature: '',
  cached: false,
  mapping: {},
  analysis: {},
  warnings: [],
  sample: [],
  canonical_columns: [],
  original_samples: {},
  normalized_rows: [],
  original_headers: []
})

const localMapping = reactive({})
const customColumns = reactive({})

const requiredColumns = ['Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio']
const canonicalColumns = computed(() => response.canonical_columns)
const originalHeaders = ref([]) // mapeadas inicialmente
const allOriginalHeaders = computed(() => response.original_headers || originalHeaders.value)
const originalSamples = computed(() => response.original_samples || {})

const missingRequired = computed(() => requiredColumns.filter(c => !resolveColumnName(c)))
const isComplete = computed(() => missingRequired.value.length === 0)

function isRequired(c){ return requiredColumns.includes(c) }
function clearMapping(c){ localMapping[c] = null; customColumns[c] = '' }
function rowClass(c){ return isRequired(c) && !resolveColumnName(c) ? 'bg-error-50' : '' }

function resolveColumnName(c){
  const sel = localMapping[c]
  if(sel === '__custom__') return customColumns[c] || null
  return sel || null
}

async function loadMapping(){
  const form = new FormData()
  form.append('layout_file', props.file)
  if (props.selectedSheet !== null) {
    form.append('sheet_name', props.selectedSheet.toString())
  }
  const { data } = await api.post('/mapear-layout', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  Object.assign(response, data)
  originalHeaders.value = Object.values(data.mapping).filter(Boolean)
  // Inicializa localMapping
  for(const k of data.canonical_columns){
    localMapping[k] = data.mapping[k] || null
  }
  state.loaded = true
}

async function confirmMapping(){
  state.saving = true
  state.message = ''
  state.error = false
  const finalMapping = {}
  for(const c of canonicalColumns.value){
    finalMapping[c] = resolveColumnName(c)
  }
  try {
    await api.post('/layout-mappings', {
      signature: response.signature,
      mapping: finalMapping,
      analysis: response.analysis,
      sample: response.sample,
      warnings: response.warnings,
      original_samples: response.original_samples,
      normalized_rows: response.normalized_rows
    })
  } catch(e){
    state.message = 'Falha ao salvar mapeamento.'
    state.error = true
    state.saving = false
    return
  }
  if(!isComplete.value){
    state.message = 'Campos obrigatórios faltando. Ajuste antes de confirmar.'
    state.error = true
    state.saving = false
    return
  }
  const campos = []
  const tiposValidos = ['TEXTO', 'NUMERO', 'DATA', 'DECIMAL']
  if (response.normalized_rows.length){
    for(const row of response.normalized_rows){
      if(!row.Campo) continue
      const nome = String(row.Campo).trim()
      const pos = Number(row.Posicao_Inicio) || null
      const tam = Number(row.Tamanho) || null
      let tipo = (row.Tipo || '').toString().toUpperCase().trim()
      
      // Normalizar tipos comuns para válidos
      if(tipo === 'VARCHAR' || tipo === 'VARCHAR2' || tipo === 'CHAR' || tipo === 'STRING') {
        tipo = 'TEXTO'
      } else if(tipo === 'INT' || tipo === 'INTEGER' || tipo === 'BIGINT') {
        tipo = 'NUMERO'
      } else if(tipo === 'FLOAT' || tipo === 'DOUBLE' || tipo === 'REAL') {
        tipo = 'DECIMAL'
      } else if(tipo === 'DATE' || tipo === 'DATETIME' || tipo === 'TIMESTAMP') {
        tipo = 'DATA'
      }
      
      // Garantir que tipo é válido
      if(!tiposValidos.includes(tipo)){
        console.warn(`Tipo inválido "${tipo}" para campo "${nome}", usando TEXTO como fallback`)
        tipo = 'TEXTO' // fallback para tipo desconhecido
      }
      const obrig = (row.Obrigatorio || '').toString().toUpperCase() === 'S'
      if(nome && pos && tam){
        campos.push({ nome, posicao_inicio: pos, tamanho: tam, tipo, obrigatorio: obrig })
      }
    }
  }
  console.log('Campos construídos:', campos)
  if (!campos.length){
    state.message = 'Nenhum campo válido para exportação.'
    state.error = true
    state.saving = false
    emits('confirmed', { signature: response.signature, mapping: finalMapping })
    return
  }
  try {
    console.log('Chamando /layout-export com', campos.length, 'campos')
    console.log('Campos enviados:', campos)
    const payload = {
      nome: `Layout Normalizado ${response.signature}`,
      campos,
      signature: response.signature
    }
    console.log('Payload completo:', payload)
    const { data: exp } = await api.post('/layout-export', payload)
    console.log('Export retornou:', exp)
    state.message = 'Layout exportado com sucesso.'
    emits('confirmed', { signature: response.signature, mapping: finalMapping, layout: exp.layout, download: exp.download_url, filename: exp.filename })
  } catch(e){
    console.error('Erro ao exportar:', e)
    console.error('Resposta do servidor:', e.response?.data)
    state.message = `Exportação falhou: ${e.response?.data?.detail || e.message}`
    state.error = true
    emits('confirmed', { signature: response.signature, mapping: finalMapping })
  } finally {
    state.saving = false
  }
}

loadMapping().catch(() => { state.loaded = true })
</script>

<style scoped>
.table { width:100%; font-size:0.875rem; }
.table-header { background:#f3f4f6; }
.table-header-cell { padding:0.5rem 0.75rem; text-align:left; font-weight:500; color:#4b5563; }
.table-cell { padding:0.25rem 0.75rem; border-top:1px solid #e5e7eb; vertical-align:top; }
</style>
