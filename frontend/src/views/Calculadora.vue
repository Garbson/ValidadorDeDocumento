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
      <!-- Aviso para arquivos grandes -->
      <div v-if="result?.resultado_basico?.total_linhas > 10000" class="card bg-yellow-50 border-yellow-300">
        <div class="card-body">
          <div class="flex items-start gap-3">
            <span class="text-3xl">⚠️</span>
            <div>
              <h3 class="font-bold text-yellow-800 text-lg">Arquivo Grande Detectado</h3>
              <p class="text-yellow-700 mt-2">
                Este arquivo tem <strong>{{ result.resultado_basico.total_linhas.toLocaleString() }} linhas</strong> e 
                <strong>{{ result.resultado_basico.erros.length.toLocaleString() }} erros</strong>.
              </p>
              <p class="text-yellow-700 mt-1">
                Para evitar travamento do navegador, apenas os <strong>primeiros 1.000 erros</strong> são mostrados com detalhes completos.
              </p>
              <p class="text-yellow-600 text-sm mt-2">
                💡 <strong>Dica:</strong> Corrija os erros principais e revalide o arquivo para ver mais detalhes.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Botão Nova Validação no topo -->
      <div class="flex justify-end">
        <button class="btn-primary" @click="reset">
          🔄 Nova Validação
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-7 gap-4">
        <div class="stat-card">
          <div class="stat-value">{{ result?.estatisticas_faturas?.total_notas_fiscais || 0 }}</div>
          <div class="stat-label">Total NFCOMs (igual SEFAZ)</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-purple-600">{{ (result?.resultado_basico?.total_linhas || 0).toLocaleString() }}</div>
          <div class="stat-label">Total de Linhas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-blue-600">{{ result?.estatisticas_faturas?.total_combinacoes_unicas || 0 }}</div>
          <div class="stat-label">Combinações Únicas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-orange-600">{{ result?.estatisticas_faturas?.total_duplicatas || 0 }}</div>
          <div class="stat-label">Duplicadas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-green-600">{{ result?.estatisticas_faturas?.total_nfs_validas || 0 }}</div>
          <div class="stat-label">NFCOMs Validadas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-red-600">{{ result?.estatisticas_faturas?.total_nfs_com_erro || 0 }}</div>
          <div class="stat-label">NFCOMs com Erro</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ (result?.estatisticas_faturas?.taxa_sucesso_nf || 0).toFixed(2) }}%</div>
          <div class="stat-label">Taxa de Sucesso</div>
        </div>
      </div>

      <!-- Botão para mostrar duplicatas -->
      <div v-if="result?.estatisticas_faturas?.total_duplicatas > 0" class="flex justify-center">
        <button @click="mostrarDuplicatas = !mostrarDuplicatas" class="btn-outline">
          <span v-if="!mostrarDuplicatas">Mostrar {{ result.estatisticas_faturas.total_duplicatas }} Duplicadas</span>
          <span v-else>Ocultar Duplicadas</span>
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


      <!-- Nova seção: Validação Detalhada com Regras e Cálculos -->
      <div v-if="result?.resultado_basico?.erros?.length" class="card">
        <div class="card-header flex items-center justify-between">
          <h3 class="text-lg font-semibold">📋 Erros Detalhados com Regras de Validação</h3>
          <button 
            v-if="result?.resultado_basico?.total_linhas < 10000"
            @click="modoDetalhado = !modoDetalhado" 
            class="btn-outline text-sm">
            {{ modoDetalhado ? 'Ocultar Detalhes' : 'Mostrar Regras e Cálculos' }}
          </button>
          <div v-else class="text-sm text-gray-500 italic">
            ⚠️ Arquivo muito grande ({{ result.resultado_basico.total_linhas.toLocaleString() }} linhas). Detalhes desabilitados para evitar travamento.
          </div>
        </div>
        <div v-if="modoDetalhado" class="card-body space-y-6">
          <div v-for="(erro, idx) in result.resultado_basico.erros" :key="idx" 
               class="border-2 border-red-300 rounded-lg p-4 bg-red-50">
            
            <!-- Cabeçalho do Erro -->
            <div class="flex items-start justify-between mb-3">
              <div>
                <div class="text-lg font-bold text-red-700 flex items-center gap-2">
                  <span class="text-2xl">❌</span>
                  <span>Linha {{ erro.linha.toString().padStart(6, '0') }}</span>
                </div>
                <div class="text-sm text-gray-600 mt-1">
                  <span class="font-mono bg-white px-2 py-1 rounded">{{ erro.campo }}</span>
                  <span class="mx-2">•</span>
                  <span class="font-semibold">{{ erro.erro_tipo }}</span>
                </div>
              </div>
              <div class="text-right">
                <div class="text-xs text-gray-500">NF/Fatura</div>
                <div class="font-mono text-sm">{{ grupoKey(erro) || '—' }}</div>
              </div>
            </div>

            <!-- Regra Aplicada -->
            <div v-if="getRegraErro(erro)" class="mb-3 p-3 bg-blue-100 border border-blue-300 rounded">
              <div class="text-xs font-semibold text-blue-800 mb-1">📐 REGRA:</div>
              <div class="font-mono text-sm text-blue-900">{{ getRegraErro(erro).regra }}</div>
            </div>

            <!-- Cálculo Detalhado -->
            <div v-if="getRegraErro(erro)" class="mb-3 p-3 bg-yellow-50 border border-yellow-300 rounded">
              <div class="text-xs font-semibold text-yellow-800 mb-2">🧮 CÁLCULO:</div>
              <div class="font-mono text-sm text-yellow-900 whitespace-pre-line">{{ getRegraErro(erro).calculo }}</div>
            </div>

            <!-- Descrição do Erro -->
            <div class="mb-3 p-3 bg-white border border-red-200 rounded">
              <div class="text-xs font-semibold text-red-800 mb-1">⚠️ PROBLEMA:</div>
              <div class="text-sm text-red-700">{{ erro.descricao }}</div>
            </div>

            <!-- Valores Comparados -->
            <div class="grid grid-cols-2 gap-3">
              <div class="p-3 bg-white border border-gray-300 rounded">
                <div class="text-xs text-gray-600 mb-1">Valor Encontrado</div>
                <div class="font-mono font-bold text-lg text-red-600">{{ erro.valor_encontrado || '—' }}</div>
              </div>
              <div class="p-3 bg-white border border-gray-300 rounded">
                <div class="text-xs text-gray-600 mb-1">Valor Esperado</div>
                <div class="font-mono font-bold text-lg text-green-600">{{ erro.valor_esperado || '—' }}</div>
              </div>
            </div>

            <!-- Linha Completa -->
            <details class="mt-3">
              <summary class="cursor-pointer text-sm text-gray-700 hover:text-gray-900 font-semibold">
                📄 Ver linha completa
              </summary>
              <pre class="mt-2 p-3 bg-gray-800 text-gray-100 rounded text-xs font-mono overflow-x-auto">{{ result.linhas_completas_com_erro[erro.linha] || '(indisponível)' }}</pre>
            </details>
          </div>
        </div>
      </div>

      <div v-if="result?.resultado_basico?.erros?.length" class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold">Ocorrências Encontradas (Lista Resumida)</h3>
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
import { computed, ref } from 'vue'
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
const modoDetalhado = ref(false)

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

// ====== Função para exibir campos com validação ======
function camposExibidosLinha(chaveGrupo, numeroLinha) {
  if (!layoutData.value?.campos || !result.value?.linhas_completas_com_erro) return []
  
  const linhaContent = conteudoLinha(chaveGrupo, numeroLinha)
  if (!linhaContent) return []
  
  const tipo = tipoRegistroDoConteudo(linhaContent)
  const campos = getCamposDoTipo(tipo)
  
  // Pegar erros desta linha
  const errosDaLinha = (result.value?.resultado_basico?.erros || []).filter(e => e.linha === numeroLinha)
  
  // Extrair todos os valores da linha para cálculos
  const valoresLinha = {}
  campos.forEach(c => {
    valoresLinha[c.nome] = extrairValorCampoNumerico(linhaContent, c)
  })
  
  return campos.map(campo => {
    const valor = extrairValorCampo(linhaContent, campo)
    const valorNum = valoresLinha[campo.nome]
    const errocampo = errosDaLinha.find(e => e.campo === campo.nome)
    
    // Detectar regra e calcular
    const regraCalculo = detectarRegraCalculo(tipo, campo.nome, valoresLinha, linhaContent)
    
    // Debug
    if (campo.nome.includes('VLR') || campo.nome.includes('PCT') || campo.nome.includes('BC')) {
      console.log('Campo:', campo.nome, 'Tipo:', tipo, 'Regra:', regraCalculo.regra)
    }
    
    return {
      nome: campo.nome,
      valor: valor || '(vazio)',
      erro: !!errocampo,
      mensagem: errocampo?.descricao || '',
      regra: regraCalculo.regra,
      calculo: regraCalculo.calculo
    }
  })
}

// Função para obter regra e cálculo de um erro
const getRegraErro = (erro) => {
  console.log('getRegraErro chamado para:', erro.campo, 'Linha:', erro.linha)
  
  const linhaContent = result.value?.linhas_completas_com_erro?.[erro.linha]
  if (!linhaContent) {
    console.log('❌ Linha não encontrada')
    return null
  }

  const tipo = linhaContent.slice(0, 2)
  console.log('✅ Tipo detectado:', tipo)

  // Extrair todos os valores da linha
  const valores = {}
  if (result.value?.layout?.campos) {
    const camposDoTipo = result.value.layout.campos.filter(c => 
      c.nome.startsWith(`NFE${tipo}-`) || c.nome.startsWith(`NFCOM${tipo}-`)
    )
    
    camposDoTipo.forEach(campo => {
      const valor = extrairValorCampoNumerico(linhaContent, campo)
      if (valor !== null) {
        valores[campo.nome] = valor
      }
    })
    console.log('📊 Valores extraídos:', Object.keys(valores).length, 'campos')
  }

  // Detectar regra baseada no campo do erro
  return detectarRegraCalculo(tipo, erro.campo, valores, linhaContent)
}

function detectarRegraCalculo(tipo, nomeCampo, valores, linhaContent) {
  console.log('detectarRegraCalculo - Tipo:', tipo, 'Campo:', nomeCampo, 'Valores disponíveis:', Object.keys(valores).length)
  
  // ====== REGISTRO 23 - PIS/COFINS ======
  if (tipo === '23') {
    // BC PIS
    if (nomeCampo === 'NFE23-PIS-VLR-BC') {
      const bc = valores[nomeCampo] || 0
      return {
        regra: 'Base de Cálculo do PIS',
        calculo: `BC = ${(bc/100).toFixed(2)}`
      }
    }
    // Alíquota PIS
    if (nomeCampo === 'NFE23-PIS-PCT-ALIQUOTA') {
      const aliq = valores[nomeCampo] || 0
      return {
        regra: 'Alíquota do PIS (em %)',
        calculo: `Alíquota = ${(aliq/100).toFixed(2)}%`
      }
    }
    // Valor PIS
    if (nomeCampo === 'NFE23-PIS-VLR-TRIBUTO') {
      const bc = valores['NFE23-PIS-VLR-BC'] || 0
      const aliq = valores['NFE23-PIS-PCT-ALIQUOTA'] || 0
      const valor = valores[nomeCampo] || 0
      const calc = Math.floor((bc * aliq) / 10000)
      const status = valor === calc ? '✅' : '❌'
      return {
        regra: 'Valor PIS = BC × Alíquota ÷ 10000',
        calculo: `${(bc/100).toFixed(2)} × ${(aliq/100).toFixed(2)}% ÷ 10000 = ${(calc/100).toFixed(2)} ${status}`
      }
    }
    
    // BC COFINS
    if (nomeCampo === 'NFE23-COFINS-VLR-BC') {
      const bc = valores[nomeCampo] || 0
      return {
        regra: 'Base de Cálculo do COFINS',
        calculo: `BC = ${(bc/100).toFixed(2)}`
      }
    }
    // Alíquota COFINS
    if (nomeCampo === 'NFE23-COFINS-PCT-ALIQUOTA') {
      const aliq = valores[nomeCampo] || 0
      return {
        regra: 'Alíquota do COFINS (em %)',
        calculo: `Alíquota = ${(aliq/100).toFixed(2)}%`
      }
    }
    // Valor COFINS
    if (nomeCampo === 'NFE23-COFINS-VLR-TRIBUTO') {
      const bc = valores['NFE23-COFINS-VLR-BC'] || 0
      const aliq = valores['NFE23-COFINS-PCT-ALIQUOTA'] || 0
      const valor = valores[nomeCampo] || 0
      const calc = Math.floor((bc * aliq) / 10000)
      const status = valor === calc ? '✅' : '❌'
      return {
        regra: 'Valor COFINS = BC × Alíquota ÷ 10000',
        calculo: `${(bc/100).toFixed(2)} × ${(aliq/100).toFixed(2)}% ÷ 10000 = ${(calc/100).toFixed(2)} ${status}`
      }
    }
  }
  
  // ====== REGISTRO 25 - ICMS ======
  if (tipo === '25') {
    if (nomeCampo === 'NFE25-ICMS-VLR-BC') {
      const bc = valores[nomeCampo] || 0
      return {
        regra: 'Base de Cálculo do ICMS',
        calculo: `BC = ${(bc/100).toFixed(2)}`
      }
    }
    if (nomeCampo === 'NFE25-ICMS-PCT-ALIQUOTA') {
      const aliq = valores[nomeCampo] || 0
      return {
        regra: 'Alíquota do ICMS (em %)',
        calculo: `Alíquota = ${(aliq/100).toFixed(2)}%`
      }
    }
    if (nomeCampo === 'NFE25-ICMS-VLR-TRIBUTO') {
      const bc = valores['NFE25-ICMS-VLR-BC'] || 0
      const aliq = valores['NFE25-ICMS-PCT-ALIQUOTA'] || 0
      const valor = valores[nomeCampo] || 0
      const calc = Math.floor((bc * aliq) / 10000)
      const status = valor === calc ? '✅' : '❌'
      return {
        regra: 'Valor ICMS = BC × Alíquota ÷ 10000',
        calculo: `${(bc/100).toFixed(2)} × ${(aliq/100).toFixed(2)}% ÷ 10000 = ${(calc/100).toFixed(2)} ${status}`
      }
    }
  }
  
  // ====== REGISTRO 44 - FUST ======
  if (tipo === '44') {
    if (nomeCampo === 'NFE44-FUST-VLR-BC') {
      const bc = valores[nomeCampo] || 0
      return {
        regra: 'Base de Cálculo do FUST',
        calculo: `BC = ${(bc/100).toFixed(2)}`
      }
    }
    if (nomeCampo === 'NFE44-FUST-PCT-ALIQUOTA') {
      const aliq = valores[nomeCampo] || 0
      return {
        regra: 'Alíquota do FUST (em %)',
        calculo: `Alíquota = ${(aliq/100).toFixed(2)}%`
      }
    }
    if (nomeCampo === 'NFE44-FUST-VLR-TRIBUTO') {
      const bc = valores['NFE44-FUST-VLR-BC'] || 0
      const aliq = valores['NFE44-FUST-PCT-ALIQUOTA'] || 0
      const valor = valores[nomeCampo] || 0
      const calc = Math.floor((bc * aliq) / 10000)
      const status = valor === calc ? '✅' : '❌'
      return {
        regra: 'Valor FUST = BC × Alíquota ÷ 10000',
        calculo: `${(bc/100).toFixed(2)} × ${(aliq/100).toFixed(2)}% ÷ 10000 = ${(calc/100).toFixed(2)} ${status}`
      }
    }
  }
  
  // ====== REGISTRO 46 - FUNTEL ======
  if (tipo === '46') {
    if (nomeCampo === 'NFE46-FUNTEL-VLR-BC') {
      const bc = valores[nomeCampo] || 0
      return {
        regra: 'Base de Cálculo do FUNTEL',
        calculo: `BC = ${(bc/100).toFixed(2)}`
      }
    }
    if (nomeCampo === 'NFE46-FUNTEL-PCT-ALIQUOTA') {
      const aliq = valores[nomeCampo] || 0
      return {
        regra: 'Alíquota do FUNTEL (em %)',
        calculo: `Alíquota = ${(aliq/100).toFixed(2)}%`
      }
    }
    if (nomeCampo === 'NFE46-FUNTEL-VLR-TRIBUTO') {
      const bc = valores['NFE46-FUNTEL-VLR-BC'] || 0
      const aliq = valores['NFE46-FUNTEL-PCT-ALIQUOTA'] || 0
      const valor = valores[nomeCampo] || 0
      const calc = Math.floor((bc * aliq) / 10000)
      const status = valor === calc ? '✅' : '❌'
      return {
        regra: 'Valor FUNTEL = BC × Alíquota ÷ 10000',
        calculo: `${(bc/100).toFixed(2)} × ${(aliq/100).toFixed(2)}% ÷ 10000 = ${(calc/100).toFixed(2)} ${status}`
      }
    }
  }
  
  // ====== REGISTRO 56 - TOTALIZADOR ======
  if (tipo === '56') {
    // Totais de impostos
    const totalizadores = {
      'NFE56-VLR-PIS-TOTAL': { nome: 'PIS', origem: 'NFE23-PIS-VLR-TRIBUTO' },
      'NFE56-VLR-COFINS-TOTAL': { nome: 'COFINS', origem: 'NFE23-COFINS-VLR-TRIBUTO' },
      'NFE56-VLR-ICMS-TOTAL': { nome: 'ICMS', origem: 'NFE25-ICMS-VLR-TRIBUTO' },
      'NFE56-VLR-FUST-TOTAL': { nome: 'FUST', origem: 'NFE44-FUST-VLR-TRIBUTO' },
      'NFE56-VLR-FUNTEL-TOTAL': { nome: 'FUNTEL', origem: 'NFE46-FUNTEL-VLR-TRIBUTO' }
    }
    
    if (totalizadores[nomeCampo]) {
      const info = totalizadores[nomeCampo]
      const valor = valores[nomeCampo] || 0
      return {
        regra: `Total ${info.nome} = Soma de todos ${info.nome} da NF`,
        calculo: `Total declarado = ${(valor/100).toFixed(2)}`
      }
    }
    
    if (nomeCampo === 'NFE56-VLR-TOTAL') {
      const total = valores[nomeCampo] || 0
      return {
        regra: 'Valor Total = Soma de todos os impostos',
        calculo: `Total = ${(total/100).toFixed(2)}`
      }
    }
  }
  
  return { regra: null, calculo: null }
}

function extrairValorCampoNumerico(linha, campo) {
  const valor = extrairValorCampo(linha, campo)
  // Remove tudo exceto dígitos e converte para inteiro
  const numStr = (valor || '').replace(/[^0-9]/g, '')
  return numStr ? parseInt(numStr, 10) : 0
}

function extrairValorCampo(linha, campo) {
  if (!linha || !campo) return ''
  const start = (campo.posicao_inicio || 1) - 1
  const end = campo.posicao_fim || (start + campo.tamanho)
  return linha.slice(start, end).trim()
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
