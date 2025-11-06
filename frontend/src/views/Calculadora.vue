<template>
  <div class="space-y-6">
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Validação de Cálculos e Totalizadores</h1>
      <p class="text-gray-600">Envie um layout e um TXT; verificaremos cálculos de impostos e os totais (registro 56) e mostraremos as linhas com problema.</p>
    </div>

    <div class="card max-w-4xl mx-auto" v-show="!hasResults">
      <div class="card-header">
        <h2 class="text-lg font-semibold">Upload para Validação</h2>
      </div>
      <div class="card-body space-y-6">
        <form @submit.prevent="handleValidate" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Arquivo de Layout (Excel) <span class="text-red-500">*</span></label>
            <input ref="layoutFileInput" type="file" accept=".xlsx,.xls" @change="onLayoutChange" class="file-input" required />
            <p class="text-sm text-gray-500 mt-1">Especificação dos campos (.xlsx ou .xls)</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Arquivo de Dados (TXT) <span class="text-red-500">*</span></label>
            <input ref="dataFileInput" type="file" accept=".txt" @change="onDataChange" class="file-input" required />
            <p class="text-sm text-gray-500 mt-1">Arquivo sequencial a validar</p>
          </div>
          <div class="flex justify-end">
            <button type="submit" :disabled="isLoading || !canSubmit" class="btn-primary">
              <span v-if="isLoading">Validando...</span>
              <span v-else>Validar Cálculos</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="isLoading" class="flex justify-center items-center py-12">
      <div class="text-center text-gray-600">Processando...</div>
    </div>

    <div v-if="error" class="card border-red-200 bg-red-50">
      <div class="card-body text-red-700">{{ error }}</div>
    </div>

    <div v-if="hasResults && !isLoading" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div class="stat-card">
          <div class="stat-value">{{ result?.estatisticas_faturas?.total_notas_fiscais || 0 }}</div>
          <div class="stat-label">Total NFCOMs (igual SEFAZ)</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-blue-600">{{ result?.estatisticas_faturas?.total_combinacoes_unicas || 0 }}</div>
          <div class="stat-label">Combinações Únicas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-orange-600">{{ result?.estatisticas_faturas?.total_duplicatas || 0 }}</div>
          <div class="stat-label">Duplicatas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-green-600">{{ result?.estatisticas_faturas?.total_nfs_validas || 0 }}</div>
          <div class="stat-label">NFCOMs Validadas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ (result?.estatisticas_faturas?.taxa_sucesso_nf || 0).toFixed(2) }}%</div>
          <div class="stat-label">Taxa de Sucesso</div>
        </div>
      </div>

      <!-- Botão para mostrar duplicatas -->
      <div v-if="result?.estatisticas_faturas?.total_duplicatas > 0" class="flex justify-center">
        <button @click="mostrarDuplicatas = !mostrarDuplicatas" class="btn-outline">
          <span v-if="!mostrarDuplicatas">Mostrar {{ result.estatisticas_faturas.total_duplicatas }} Duplicatas</span>
          <span v-else>Ocultar Duplicatas</span>
        </button>
      </div>

      <!-- Modal/Card de duplicatas -->
      <div v-if="mostrarDuplicatas && result?.estatisticas_faturas?.duplicatas_detalhes?.length" class="card border-orange-200 bg-orange-50">
        <div class="card-header">
          <h3 class="text-lg font-semibold text-orange-800">NFs Duplicadas Encontradas</h3>
          <p class="text-sm text-orange-600 mt-1">Estas combinações (Fatura + NF) aparecem mais de uma vez no arquivo:</p>
        </div>
        <div class="card-body">
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div v-for="(dup, i) in result.estatisticas_faturas.duplicatas_detalhes" :key="i"
                 class="flex justify-between items-center p-3 bg-white rounded border border-orange-200">
              <div class="flex-1">
                <span class="font-mono text-sm">Linha {{ dup.linha.toString().padStart(6, '0') }}:</span>
                <span class="ml-2 font-semibold">Fatura {{ dup.fatura }} | NF {{ dup.nf }}</span>
              </div>
              <div class="text-xs text-orange-600 bg-orange-100 px-2 py-1 rounded">
                DUPLICATA
              </div>
            </div>
          </div>
          <div class="mt-4 p-3 bg-orange-100 rounded text-sm text-orange-700">
            <strong>⚠️ Importante:</strong> A SEFAZ conta cada registro 01 individualmente ({{ result?.estatisticas_faturas?.total_notas_fiscais }}).
            Sua calculadora agora usa a mesma lógica, mas duplicatas podem indicar problemas na geração do arquivo.
          </div>
        </div>
      </div>

      <div v-if="result?.totais" class="card">
        <div class="card-header"><h3 class="text-lg font-semibold">Totais Acumulados (registro 56)</h3></div>
        <div class="card-body">
          <ul class="grid sm:grid-cols-2 gap-2 font-mono text-sm">
            <li v-for="(v, k) in result.totais.valores" :key="k">
              <span class="text-gray-700">{{ k }}:</span>
              <span class="ml-2">{{ formatCentavos(v) }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div v-if="result?.resultado_basico?.erros?.length" class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold">Ocorrências Encontradas</h3>
        </div>
        <div class="card-body space-y-4">
          <!-- Filtro por tipo de erro com contadores -->
          <div class="flex flex-wrap gap-2 mb-2">
            <button class="px-3 py-1 rounded-full border text-sm"
                    :class="!selectedErrorType ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300'"
                    @click="selectedErrorType = ''">
              Todos <span class="ml-1 text-xs opacity-75">({{ totalErros }})</span>
            </button>
            <button v-for="(count, tipo) in errorTypeCounts" :key="tipo" class="px-3 py-1 rounded-full border text-sm"
                    :class="selectedErrorType === tipo ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300'"
                    @click="selectedErrorType = (selectedErrorType === tipo ? '' : tipo)">
              {{ tipo }} <span class="ml-1 text-xs opacity-75">({{ count }})</span>
            </button>
          </div>

          <div v-for="(erro, i) in filteredErros" :key="i" class="border rounded p-3">
            <div class="flex justify-between items-center">
              <div class="font-semibold">Linha {{ erro.linha }} — {{ erro.erro_tipo }}</div>
              <div class="text-xs text-gray-500">Campo: {{ erro.campo }}</div>
            </div>
            <div class="text-sm text-gray-700 mt-1">{{ erro.descricao }}</div>
            <div class="mt-2">
              <div class="text-xs text-gray-500">Linha completa:</div>
              <pre class="bg-gray-50 p-2 rounded border overflow-x-auto text-sm font-mono" style="white-space: pre;">{{ result.linhas_completas_com_erro[erro.linha] || '(linha indisponível)' }}</pre>
            </div>

            <!-- Expansor por NF/Fatura: agora disponível para TODOS os erros -->
            <div class="mt-3">
              <button class="btn-outline" @click="toggleGrupoNF(i)">
                {{ expanded[i] ? 'Ocultar' : 'Ver' }} NF/Fatura relacionada
              </button>
              <div v-if="expanded[i]" class="mt-3 space-y-3">
                <template v-if="grupoKey(erro)">
                  <div v-if="(linhasContribuintes(erro) || []).length" class="text-sm text-gray-700">Linhas contribuintes para {{ erro.campo }}:</div>
                  <div v-if="(linhasContribuintes(erro) || []).length" class="font-mono text-sm bg-gray-50 p-2 rounded border overflow-x-auto" style="white-space: pre;">
                    <div v-for="ln in linhasContribuintes(erro)" :key="ln">
                      <span class="text-gray-500">[{{ ln.toString().padStart(6, '0') }}]</span>
                      <div
                        class="inline-block cursor-help hover:bg-blue-50 rounded px-1"
                        @mousemove="mostrarTooltipThrottled($event, tipoRegistroDoConteudo(conteudoLinha(grupoKey(erro), ln)), linhaComBarras(conteudoLinha(grupoKey(erro), ln)))"
                        @mouseleave="esconderTooltip"
                        style="white-space: pre;"
                      >{{ linhaComBarras(conteudoLinha(grupoKey(erro), ln)) }}</div>
                    </div>
                  </div>

                  <div class="text-sm text-gray-700">Todas as linhas da NF/Fatura:</div>
                  <div class="font-mono text-sm bg-gray-50 p-2 rounded border overflow-x-auto" style="white-space: pre;">
                    <div v-for="ln in (result.grupos_por_nf[grupoKey(erro)]?.linhas || [])" :key="'all-'+ln">
                      <span class="text-gray-500">[{{ ln.toString().padStart(6, '0') }}]</span>
                      <div
                        class="inline-block cursor-help hover:bg-blue-50 rounded px-1"
                        @mousemove="mostrarTooltipThrottled($event, tipoRegistroDoConteudo(conteudoLinha(grupoKey(erro), ln)), linhaComBarras(conteudoLinha(grupoKey(erro), ln)))"
                        @mouseleave="esconderTooltip"
                        style="white-space: pre;"
                      >{{ linhaComBarras(conteudoLinha(grupoKey(erro), ln)) }}</div>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <div class="text-sm text-gray-500 italic">NF/Fatura não identificada para este erro.</div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-end">
        <button class="btn-outline" @click="reset">Nova Validação</button>
      </div>
    </div>

    <div
      v-if="tooltipInfo.visible && tooltipInfo.campo"
      class="fixed z-50 px-4 py-3 bg-gray-900 text-white text-sm rounded-lg shadow-xl pointer-events-none border border-gray-700"
      :style="{ left: tooltipInfo.x + 'px', top: tooltipInfo.y + 'px', maxWidth: '320px', minWidth: '280px' }"
    >
      <div class="space-y-2">
        <div class="font-bold text-blue-300 border-b border-gray-700 pb-1 flex items-center justify-between">
          <span>📋 {{ tooltipInfo.campo.nome }}</span>
          <span class="px-2 py-1 rounded text-xs font-mono bg-orange-700 text-orange-200">NF</span>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div><span class="text-gray-400">📍 Posição:</span> <span class="text-white font-mono">{{ tooltipInfo.campo.posicao_inicio }}-{{ tooltipInfo.campo.posicao_fim }}</span></div>
          <div><span class="text-gray-400">🔢 Campo:</span> <span class="text-yellow-300 font-mono">{{ (tooltipInfo.indice || 0).toString().padStart(2, '0') }}</span></div>
          <div><span class="text-gray-400">📄 Tipo:</span> <span class="text-green-300">{{ tooltipInfo.campo.tipo }}</span></div>
          <div v-if="tooltipInfo.campo.obrigatorio"><span class="text-gray-400">⚠️ Status:</span> <span class="text-red-300">Obrigatório</span></div>
        </div>
        <div v-if="(tooltipInfo.valor || '').trim()" class="border-t border-gray-700 pt-2">
          <div class="text-gray-400 text-xs mb-1">💾 Valor atual:</div>
          <div class="bg-gray-800 p-2 rounded font-mono text-xs break-all text-cyan-300">"{{ (tooltipInfo.valor || '').trim() }}"</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../services/api'

const layoutFileInput = ref(null)
const dataFileInput = ref(null)
const layoutFile = ref(null)
const dataFile = ref(null)
const isLoading = ref(false)
const error = ref('')
const result = ref(null)
const layoutData = ref(null)
const expanded = ref({})
const selectedErrorType = ref('')
const mostrarDuplicatas = ref(false)

const hasResults = computed(() => !!result.value)
const canSubmit = computed(() => !!layoutFile.value && !!dataFile.value)

function formatCentavos(v) {
  if (typeof v !== 'number') return String(v)
  return (v / 100).toFixed(2).replace('.', ',')
}

function onLayoutChange(event) {
  try {
    const files = event?.target?.files
    layoutFile.value = files && files.length ? files[0] : null
  } catch (e) {
    layoutFile.value = null
  }
}

function onDataChange(event) {
  try {
    const files = event?.target?.files
    dataFile.value = files && files.length ? files[0] : null
  } catch (e) {
    dataFile.value = null
  }
}

async function handleValidate() {
  if (!canSubmit.value) return
  isLoading.value = true
  error.value = ''
  try {
    const fd = new FormData()
  fd.append('layout_file', layoutFile.value)
  fd.append('data_file', dataFile.value)
    const resp = await api.post('/validar-calculos', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    result.value = resp.data
  layoutData.value = resp.data?.layout || null
  expanded.value = {}
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.detail || 'Erro ao validar cálculos'
  } finally {
    isLoading.value = false
  }
}

function reset() {
  result.value = null
  layoutData.value = null
  error.value = ''
  mostrarDuplicatas.value = false
  if (layoutFileInput.value) layoutFileInput.value.value = ''
  if (dataFileInput.value) dataFileInput.value.value = ''
  layoutFile.value = null
  dataFile.value = null
}

// Utilidades para grupo NF/Fatura a partir da descrição do erro do 56
function grupoKey(erro) {
  // 1) Tenta extrair de "Fatura X | NF Y" na descrição
  const d = erro?.descricao || ''
  const m = d.match(/Fatura\s+(\S+)\s*\|\s*NF\s+(\S+)/)
  if (m) return `${m[1]}|${m[2]}`
  // 2) Fallback: localizar pelo número da linha em grupos_por_nf
  return grupoKeyPorLinha(erro?.linha)
}

function grupoKeyPorLinha(linha) {
  if (!linha || !result.value?.grupos_por_nf) return ''
  const grupos = result.value.grupos_por_nf
  for (const k of Object.keys(grupos)) {
    const arr = grupos[k]?.linhas || []
    if (arr.includes(linha)) return k
  }
  return ''
}

function linhasContribuintes(erro) {
  const key = grupoKey(erro)
  const campoTotal = erro?.campo
  if (!key || !campoTotal) return []
  const grp = result.value?.grupos_por_nf?.[key]
  return grp?.contribuintes_por_total?.[campoTotal] || []
}

function toggleGrupoNF(idx) {
  expanded.value[idx] = !expanded.value[idx]
}

// ====== Filtro e contadores por tipo de erro ======
const totalErros = computed(() => result.value?.resultado_basico?.erros?.length || 0)
const errorTypeCounts = computed(() => {
  const counts = {}
  const erros = result.value?.resultado_basico?.erros || []
  for (const e of erros) {
    counts[e.erro_tipo] = (counts[e.erro_tipo] || 0) + 1
  }
  return counts
})
const filteredErros = computed(() => {
  const erros = result.value?.resultado_basico?.erros || []
  if (!selectedErrorType.value) return erros
  return erros.filter(e => e.erro_tipo === selectedErrorType.value)
})

// ====== Renderização com '|' e tooltips (similar à Comparação) ======
function tipoRegistroDoConteudo(linhaStr) {
  if (!linhaStr || typeof linhaStr !== 'string') return ''
  return linhaStr.slice(0, 2)
}

function getCamposDoTipo(tipoRegistro) {
  if (!layoutData.value?.campos) return []
  return layoutData.value.campos.filter(campo => {
    const nome = campo.nome || ''
    return nome.includes(`NFE${tipoRegistro}-`) || nome.includes(`NFCOM${tipoRegistro}-`) || (!nome.startsWith('NFE') && !nome.startsWith('NFCOM'))
  })
}

function linhaComBarras(linhaStr) {
  if (!linhaStr) return ''
  const tipo = tipoRegistroDoConteudo(linhaStr)
  const campos = getCamposDoTipo(tipo)
  if (!campos.length) return linhaStr
  const partes = []
  for (let i = 0; i < campos.length; i++) {
    const c = campos[i]
    const ini = Math.max(0, (c.posicao_inicio || 1) - 1)
    const fim = Math.min(linhaStr.length, c.posicao_fim || ini)
    partes.push(linhaStr.slice(ini, fim))
  }
  return partes.join('|')
}

function conteudoLinha(grupoKey, ln) {
  return result.value?.grupos_por_nf?.[grupoKey]?.linhas_conteudo?.[ln] || ''
}

// Tooltip
const tooltipInfo = ref({ visible: false, x: 0, y: 0, campo: null, valor: '', indice: 0, posicaoExata: 0, tipoLinha: 'validado' })
let tooltipThrottle = null

function getCampoNaPosicaoMelhorada(event, tipoRegistro, linhaComBarrasStr) {
  const campos = getCamposDoTipo(tipoRegistro)
  if (!campos.length || !linhaComBarrasStr) return null

  const elemento = event.target
  const rect = elemento.getBoundingClientRect()
  const style = window.getComputedStyle(elemento)
  const scrollLeft = elemento.scrollLeft
  const posicaoMouseReal = event.offsetX + scrollLeft

  const medidor = document.createElement('span')
  medidor.style.font = style.font
  medidor.style.fontSize = style.fontSize
  medidor.style.fontFamily = style.fontFamily
  medidor.style.visibility = 'hidden'
  medidor.style.position = 'absolute'
  medidor.style.whiteSpace = 'pre'
  document.body.appendChild(medidor)

  try {
    const segments = linhaComBarrasStr.split('|')
    let posicaoAcumulada = 0
    for (let i = 0; i < segments.length && i < campos.length; i++) {
      const segmento = segments[i]
      medidor.textContent = segmento
      const larguraSegmento = medidor.offsetWidth
      medidor.textContent = '|'
      const larguraBarra = medidor.offsetWidth

      const inicioSegmento = posicaoAcumulada
      const fimSegmento = posicaoAcumulada + larguraSegmento

      if (posicaoMouseReal >= inicioSegmento && posicaoMouseReal <= fimSegmento) {
        return { campo: campos[i], valor: segmento, indice: i + 1, posicaoExata: posicaoMouseReal - inicioSegmento }
      }
      posicaoAcumulada = fimSegmento + larguraBarra
    }
  } finally {
    document.body.removeChild(medidor)
  }
  return null
}

function mostrarTooltip(event, tipoRegistro, linhaComBarrasStr) {
  const campoInfo = getCampoNaPosicaoMelhorada(event, tipoRegistro, linhaComBarrasStr)
  if (campoInfo) {
    let finalX = event.clientX
    let finalY = event.clientY + 40
    const vw = window.innerWidth, vh = window.innerHeight
    const tw = 320, th = 180
    if (finalX + tw > vw) finalX = vw - tw - 10
    if (finalY + th > vh) finalY = vh - th - 10
    tooltipInfo.value = { visible: true, x: finalX, y: finalY, campo: campoInfo.campo, valor: campoInfo.valor, indice: campoInfo.indice, posicaoExata: campoInfo.posicaoExata, tipoLinha: 'validado' }
  }
}

function mostrarTooltipThrottled(event, tipoRegistro, linhaComBarrasStr) {
  if (tooltipThrottle) clearTimeout(tooltipThrottle)
  tooltipThrottle = setTimeout(() => mostrarTooltip(event, tipoRegistro, linhaComBarrasStr), 50)
}

function esconderTooltip() {
  if (tooltipThrottle) { clearTimeout(tooltipThrottle); tooltipThrottle = null }
  tooltipInfo.value.visible = false
}
</script>

<style scoped>
.file-input { @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500; }
.btn-primary { @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed; }
.btn-outline { @apply inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500; }
.card { @apply bg-white shadow rounded-lg; }
.card-header { @apply px-6 py-4 border-b border-gray-200; }
.card-body { @apply px-6 py-4; }
.stat-card { @apply bg-white p-4 rounded-lg shadow border border-gray-200; }
.stat-value { @apply text-2xl font-bold; }
.stat-label { @apply text-sm text-gray-600 mt-1; }
</style>
