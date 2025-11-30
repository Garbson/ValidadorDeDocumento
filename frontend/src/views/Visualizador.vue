<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Visualizador de Registros</h1>
      <p class="text-gray-600">Carregue o layout (Excel) e o arquivo sequencial (TXT) para visualizar cada registro com campos e tooltips</p>
    </div>

    <!-- Uploads -->
    <div class="card max-w-4xl mx-auto">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <Upload class="w-5 h-5 mr-2" />
          Arquivos de Entrada
        </h2>
      </div>
      <div class="card-body space-y-5">
        <div class="grid md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Layout (Excel) <span class="text-red-500">*</span></label>
            <input type="file" accept=".xlsx,.xls" class="file-input" @change="onLayoutChange" />
            <p class="text-xs text-gray-500 mt-1">Use a mesma planilha de layout do Comparação/Calculadora</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Arquivo TXT <span class="text-red-500">*</span></label>
            <input type="file" accept=".txt" class="file-input" @change="onDataChange" />
            <p class="text-xs text-gray-500 mt-1">Arquivo sequencial de linhas de tamanho fixo</p>
          </div>
        </div>
        <div class="grid md:grid-cols-3 gap-4 items-end">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Aba do Excel (opcional)</label>
            <input v-model.number="sheetIndex" type="number" min="0" class="input" placeholder="0" />
          </div>
          <div class="flex items-center gap-2">
            <input id="showDots" v-model="showDots" type="checkbox" class="h-4 w-4 text-primary-600 border-gray-300 rounded" />
            <label for="showDots" class="text-sm text-gray-700">Mostrar espaços como ·</label>
          </div>
          <div class="flex justify-end">
            <button class="btn-primary px-6 py-3" :disabled="!layoutFile || !dataFile || loading" @click="carregar">
              <span v-if="loading" class="flex items-center"><div class="loading-spinner w-5 h-5 mr-2"></div>Processando…</span>
              <span v-else class="flex items-center"><Eye class="w-5 h-5 mr-2" />Visualizar</span>
            </button>
          </div>
        </div>
        <div v-if="error" class="bg-error-50 border border-error-200 rounded p-3 text-sm text-error-700">{{ error }}</div>
      </div>
    </div>

    <!-- Layout resumo -->
    <div v-if="layout" class="card max-w-6xl mx-auto">
      <div class="card-header">
        <h3 class="text-lg font-semibold flex items-center">
          <FileSpreadsheet class="w-5 h-5 mr-2" />
          Layout: {{ layout.nome }}
        </h3>
      </div>
      <div class="card-body text-sm text-gray-600">
        Tamanho da linha: <span class="font-mono">{{ layout.tamanho_linha }}</span>. Campos: {{ camposOrdenados.length }}
      </div>
    </div>

    <!-- Visualização por Nota Fiscal: inclui header (00) e trailer (90/99) -->
    <div v-if="layout && linhas.length" class="card max-w-6xl mx-auto">
      <div class="card-header">
        <h3 class="text-lg font-semibold flex items-center mb-3">
          <FileText class="w-5 h-5 mr-2" />
          Visualização de Registros
        </h3>
        
        <!-- Abas -->
        <div class="flex gap-2 border-b border-gray-200">
          <button
            @click="modoVisualizacao = 'agrupado'"
            :class="[
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              modoVisualizacao === 'agrupado' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            ]"
          >
            Agrupado por NF
          </button>
          <button
            @click="modoVisualizacao = 'completo'"
            :class="[
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              modoVisualizacao === 'completo' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            ]"
          >
            Arquivo Completo
          </button>
        </div>
      </div>

      <!-- Modo: Agrupado por NF -->
      <div v-if="modoVisualizacao === 'agrupado'" class="card-header flex items-center justify-between border-t">
    <div class="flex items-center gap-2">
          <div class="text-xs text-gray-500" v-if="paginas.length">
            Página {{ paginaAtualIndex + 1 }} de {{ paginas.length }}
          </div>
          <button
      class="inline-flex items-center px-2 py-1 border border-gray-300 text-sm rounded-md bg-white hover:bg-gray-50 disabled:opacity-50"
            :disabled="!podeVoltar100"
            @click="voltar100()"
            title="Voltar -100 notas"
          >
            <ChevronsLeft class="w-4 h-4" />
          </button>
          <button
      class="inline-flex items-center px-2 py-1 border border-gray-300 text-sm rounded-md bg-white hover:bg-gray-50 disabled:opacity-50"
            :disabled="!temPaginaAnterior"
            @click="goAnterior()"
            title="Nota anterior"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <button
      class="inline-flex items-center px-2 py-1 border border-gray-300 text-sm rounded-md bg-white hover:bg-gray-50 disabled:opacity-50"
            :disabled="!temProximaPagina"
            @click="goProxima()"
            title="Próxima nota"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
          <button
      class="inline-flex items-center px-2 py-1 border border-gray-300 text-sm rounded-md bg-white hover:bg-gray-50 disabled:opacity-50"
            :disabled="!podePular100"
            @click="pular100()"
            title="Pular +100 notas"
          >
            <ChevronsRight class="w-4 h-4" />
          </button>
        </div>
      </div>
      <div v-if="modoVisualizacao === 'agrupado'" class="card-body">
        <div v-if="paginaAtual" class="border rounded">
          <div class="px-3 py-2 bg-gray-100 text-sm font-medium flex items-center justify-between">
            <div>
              <span v-if="paginaAtual.tipo==='file-header'">HEADER DO ARQUIVO (00)</span>
              <span v-else-if="paginaAtual.tipo==='file-trailer'">TRAILER DO ARQUIVO (90/99)</span>
              <span v-else-if="paginaAtual.tipo==='solto'">BLOCO EXTRA</span>
              <span v-else>
                NF: {{ paginaAtual.meta?.nf || '—' }}
                <span class="text-gray-400"> | </span>
                Fatura: {{ paginaAtual.meta?.fatura || '—' }}
              </span>
            </div>
            <div class="text-xs text-gray-500">linhas {{ paginaAtual.linha_inicio }}–{{ paginaAtual.linha_fim }} ({{ paginaAtual.linhas.length }})</div>
          </div>
          <div class="p-2 space-y-2">
            <div
              v-for="(linha, idxLocal) in paginaAtual.linhas"
              :key="idxLocal + '-' + paginaAtualIndex"
              class="font-mono text-sm overflow-x-auto whitespace-pre p-2 bg-gray-50 rounded border border-gray-200"
            >
              <span class="text-gray-500 mr-2">{{ linha.num }}.</span>
              <span
                class="inline-block"
                @mousemove="mostrarTooltipThrottled($event, linha.raw, linhaComBarras(linha.raw))"
                @mouseleave="esconderTooltip"
              >
                <template v-for="(campo, i) in camposParaLinha(linha.raw)" :key="campo.nome + '-' + i">
                  <span class="inline-block px-1 hover:bg-yellow-100 rounded cursor-default">{{ valorCampoLinha(linha.raw, campo) }}</span>
                  <span v-if="i < camposParaLinha(linha.raw).length - 1" class="text-gray-400"> | </span>
                </template>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Modo: Arquivo Completo -->
      <div v-if="modoVisualizacao === 'completo'" class="card-body">
        <div class="mb-4 flex items-center gap-4">
          <label class="flex items-center gap-2 text-sm">
            <input type="checkbox" v-model="showDots" class="rounded" />
            Mostrar espaços como pontos (·)
          </label>
          <div class="text-xs text-gray-500">
            Total de linhas: {{ linhas.length }}
          </div>
        </div>
        
        <div class="border rounded bg-gray-50 p-4 max-h-[600px] overflow-y-auto">
          <div
            v-for="(linha, idx) in linhas"
            :key="idx"
            class="font-mono text-xs mb-1 flex hover:bg-yellow-50 transition-colors"
          >
            <span class="text-gray-400 mr-3 select-none w-12 text-right flex-shrink-0">{{ idx + 1 }}</span>
            <span class="whitespace-pre">{{ formatarLinhaCompleta(linha) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tooltip flutuante avançado -->
    <div
      v-if="tooltipInfo.visible && tooltipInfo.campo"
      class="fixed z-50 px-4 py-3 bg-gray-900 text-white text-sm rounded-lg shadow-xl pointer-events-none border border-gray-700"
      :style="{ left: tooltipInfo.x + 'px', top: tooltipInfo.y + 'px', maxWidth: '320px', minWidth: '280px' }"
    >
      <div class="space-y-2">
        <div class="font-bold text-blue-300 border-b border-gray-700 pb-1 flex items-center justify-between">
          <span>📋 {{ tooltipInfo.campo.nome }}</span>
          <span class="px-2 py-1 rounded text-xs font-mono bg-purple-700 text-purple-200">VIS</span>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div><span class="text-gray-400">📍 Posição:</span> <span class="text-white font-mono">{{ tooltipInfo.campo.posicao_inicio }}-{{ tooltipInfo.campo.posicao_fim }}</span></div>
          <div><span class="text-gray-400">🔢 Campo:</span> <span class="text-yellow-300 font-mono">{{ (tooltipInfo.indice || 0).toString().padStart(2, '0') }}</span></div>
          <div><span class="text-gray-400">📏 Tamanho:</span> <span class="text-green-300">{{ tooltipInfo.campo.tamanho }}</span></div>
          <div><span class="text-gray-400">📄 Tipo:</span> <span class="text-green-300">{{ tooltipInfo.campo.tipo }}</span></div>
          <div v-if="tooltipInfo.campo.obrigatorio" class="col-span-2"><span class="text-gray-400">⚠️ Status:</span> <span class="text-red-300">Obrigatório</span></div>
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
import api from '@/services/api'
import { Upload, Eye, FileSpreadsheet, FileText, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-vue-next'

const layoutFile = ref(null)
const dataFile = ref(null)
const sheetIndex = ref(0)
const loading = ref(false)
const error = ref('')

const layout = ref(null)
const linhas = ref([])
const idx = ref(0)
const jump = ref(1)
const showDots = ref(true)
const MAX_MOSTRAR = 500
const paginaAtualIndex = ref(0)
const modoVisualizacao = ref('agrupado') // 'agrupado' ou 'completo'

const onLayoutChange = (e) => {
  layoutFile.value = e.target.files?.[0] || null
}
const onDataChange = async (e) => {
  dataFile.value = e.target.files?.[0] || null
  if (dataFile.value) {
    const text = await dataFile.value.text()
    // manter quebras de linha originais
    linhas.value = text.split(/\r?\n/).filter(l => l !== '')
    idx.value = 0
    jump.value = 1
  paginaAtualIndex.value = 0
  }
}

const carregar = async () => {
  error.value = ''
  if (!layoutFile.value || !dataFile.value) {
    error.value = 'Selecione o layout e o arquivo TXT.'
    return
  }
  loading.value = true
  try {
    const form = new FormData()
    form.append('layout_file', layoutFile.value)
    if (sheetIndex.value !== null && sheetIndex.value !== undefined) {
      form.append('sheet_name', String(sheetIndex.value))
    }
    const resp = await api.post('/validar-layout', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    layout.value = resp.data
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Erro ao carregar layout'
  } finally {
    loading.value = false
  }
}

const camposOrdenados = computed(() => {
  if (!layout.value?.campos) return []
  return [...layout.value.campos].sort((a, b) => a.posicao_inicio - b.posicao_inicio)
})

// Seleciona campos por tipo de registro, alinhado ao Comparacao.vue
const getCamposDoTipo = (tipo) => {
  if (!layout.value?.campos) return []
  const campos = layout.value.campos.filter(c => {
    const nome = c.nome || ''
    return nome.includes(`NFE${tipo}-`) || nome.includes(`NFCOM${tipo}-`)
  })
  // Fallback: se nada encontrado, usar todos ordenados (evita linha vazia caso layout não use prefixos)
  return (campos.length ? campos : camposOrdenados.value).slice().sort((a, b) => a.posicao_inicio - b.posicao_inicio)
}

const camposParaLinha = (raw) => {
  const tipo = tipoRegistro(raw)
  if (!tipo) return camposOrdenados.value
  return getCamposDoTipo(tipo)
}

const truncado = computed(() => false) // paginação usa todas as linhas para permitir ver o trailer
const linhasExibidas = computed(() => linhas.value)

// Helpers para identificar tipo da linha
const tipoRegistro = (raw) => (raw && raw.length >= 2 ? raw.slice(0, 2) : '')
const isHeader = (raw) => tipoRegistro(raw) === '00'
const isTrailer = (raw) => ['90', '99'].includes(tipoRegistro(raw))
const isInicioNF = (raw) => tipoRegistro(raw) === '20'
const isFimNF = (raw) => tipoRegistro(raw) === '56'

// Extrair metadados (fatura/nf) usando campos específicos do tipo 20, alinhado ao dicionário/comparador
const metaFromLinha = (raw) => {
  try {
    if (!layout.value?.campos) return { fatura: null, nf: null }
    // Apenas tenta extrair dos campos do tipo 20 (início de NF)
    const tipo = tipoRegistro(raw)
    const campos20 = getCamposDoTipo('20')
    const base = padToLayout(raw)

    // Preferências conhecidas (SEFAZ): NUM_NFCOM e TRANSACTION_ID_CLARO
    const matchCampo = (campos, patterns) => campos.find(c => patterns.some(p => p.test(c.nome || '')))

    const nfCampo = matchCampo(campos20, [
      /NUM[_-]?NFCOM/i,
      /NUM[_-]?NF(?!COM)/i,
      /NUMERO[_-]?NF/i,
      /NRO[_-]?NF/i,
      /NFE20-.*NF/i,
      /NFCOM20-.*NF/i
    ])
    const faturaCampo = matchCampo(campos20, [
      /TRANSACTION[_-]?ID[_-]?CLARO/i,
      /FATURA/i,
      /ID[_-]?FAT/i,
      /FAT[_-]?ID/i
    ])

    const getVal = (c) => c ? base.slice((c.posicao_inicio || 1) - 1, c.posicao_fim || ((c.posicao_inicio - 1) + c.tamanho)).trim() : null
    return {
      fatura: getVal(faturaCampo),
      nf: getVal(nfCampo)
    }
  } catch {
    return { fatura: null, nf: null }
  }
}

// Agrupar linhas por NF, incluindo header e trailer do arquivo
const grupos = computed(() => {
  const result = []
  const fonte = linhas.value
  if (!fonte.length) return result

  // Adicionar header (todas as linhas 00 iniciais consecutivas)
  let i = 0
  const headerLines = []
  while (i < fonte.length && isHeader(fonte[i])) {
    headerLines.push({ num: i + 1, raw: fonte[i] })
    i++
  }
  if (headerLines.length) {
    result.push({ tipo: 'file-header', linhas: headerLines, linha_inicio: headerLines[0].num, linha_fim: headerLines[headerLines.length-1].num, meta: null })
  }

  // Grupos por NF (20 ... 56), mantendo quaisquer linhas intermediárias pertencentes
  let grupoAtual = null
  for (; i < fonte.length; i++) {
    const raw = fonte[i]
    const num = i + 1
    if (isTrailer(raw)) {
      // Ao encontrar trailer, fecha grupo atual se existir e empilha trailer depois
      if (grupoAtual) {
        grupoAtual.linha_fim = grupoAtual.linhas[grupoAtual.linhas.length-1].num
        result.push(grupoAtual)
        grupoAtual = null
      }
      // Trailer(s) podem ser múltiplos no final
      const trailerLines = [{ num, raw }]
      let j = i + 1
      while (j < fonte.length && isTrailer(fonte[j])) {
        trailerLines.push({ num: j + 1, raw: fonte[j] })
        j++
      }
      result.push({ tipo: 'file-trailer', linhas: trailerLines, linha_inicio: trailerLines[0].num, linha_fim: trailerLines[trailerLines.length-1].num, meta: null })
      break
    }

  if (isInicioNF(raw)) {
      // fechar anterior
      if (grupoAtual) {
        grupoAtual.linha_fim = grupoAtual.linhas[grupoAtual.linhas.length-1].num
        result.push(grupoAtual)
      }
      grupoAtual = {
        tipo: 'nf',
        meta: metaFromLinha(raw),
        linhas: [{ num, raw }],
        linha_inicio: num,
        linha_fim: num
      }
      continue
    }

  if (grupoAtual) {
      grupoAtual.linhas.push({ num, raw })
      if (isFimNF(raw)) {
        grupoAtual.linha_fim = num
        result.push(grupoAtual)
        grupoAtual = null
      }
    } else {
      // Linhas fora de grupos: agrupar como blocos soltos (ex.: 01, 02 antes do primeiro 20)
      // Empilhar em um grupo "solto" por praticidade
      const bloco = { tipo: 'solto', meta: null, linhas: [{ num, raw }], linha_inicio: num, linha_fim: num }
      // Agregar próximas não 20/90/99 até encontrar início de NF ou trailer
      let j = i + 1
      while (j < fonte.length && !isInicioNF(fonte[j]) && !isTrailer(fonte[j])) {
        bloco.linhas.push({ num: j + 1, raw: fonte[j] })
        bloco.linha_fim = j + 1
        j++
      }
      result.push(bloco)
      i = j - 1
    }
  }

  // Se restou um grupo aberto sem 56 até o limite, empilha mesmo assim
  if (grupoAtual) {
    grupoAtual.linha_fim = grupoAtual.linhas[grupoAtual.linhas.length-1].num
    result.push(grupoAtual)
  }

  return result
})

const totalLinhasExibidas = computed(() => grupos.value.reduce((acc, g) => acc + g.linhas.length, 0))

// Páginas de navegação: HEADER, NFs agregadas por (nf,fatura), BLOCOS EXTRAS (soltos), TRAILER
const paginas = computed(() => {
  const gs = grupos.value
  if (!gs.length) return []

  const pages = []
  // Header (se existir)
  const header = gs.find(g => g.tipo === 'file-header')
  if (header) pages.push({ ...header })

  // Mapear NFs agregadas mantendo ordem de primeira ocorrência
  const nfMap = new Map()
  const nfOrder = []

  gs.forEach((g, idx) => {
    if (g.tipo === 'nf') {
      const key = `${g.meta?.nf || ''}|${g.meta?.fatura || ''}`
      if (!nfMap.has(key)) {
        nfMap.set(key, {
          tipo: 'nf',
          meta: { nf: g.meta?.nf || null, fatura: g.meta?.fatura || null },
          linhas: [],
          linha_inicio: Number.POSITIVE_INFINITY,
          linha_fim: 0,
          _firstIdx: idx
        })
        nfOrder.push(key)
      }
      const agg = nfMap.get(key)
      // anexar linhas e atualizar range
      g.linhas.forEach(l => {
        agg.linhas.push(l)
        if (l.num < agg.linha_inicio) agg.linha_inicio = l.num
        if (l.num > agg.linha_fim) agg.linha_fim = l.num
      })
    }
  })

  // Empilhar NF pages pela ordem de primeira ocorrência
  nfOrder
    .sort((a, b) => (nfMap.get(a)._firstIdx - nfMap.get(b)._firstIdx))
    .forEach(key => {
      const { _firstIdx, ...rest } = nfMap.get(key)
      // se não houve linhas, evitar push
      if (rest.linhas && rest.linhas.length) pages.push(rest)
    })

  // Blocos soltos agregados (opcional): agrupar todos em uma página
  const soltos = gs.filter(g => g.tipo === 'solto')
  if (soltos.length) {
    const linhas = []
    let min = Number.POSITIVE_INFINITY
    let max = 0
    soltos.forEach(g => {
      g.linhas.forEach(l => {
        linhas.push(l)
        if (l.num < min) min = l.num
        if (l.num > max) max = l.num
      })
    })
    pages.push({ tipo: 'solto', meta: null, linhas, linha_inicio: isFinite(min) ? min : 0, linha_fim: max })
  }

  // Trailer no final (pode haver um bloco já agregado pelo agrupador)
  const trailer = gs.find(g => g.tipo === 'file-trailer')
  if (trailer) pages.push({ ...trailer })

  return pages
})
const paginaAtual = computed(() => paginas.value[paginaAtualIndex.value] || null)

// Índices apenas de NFs para pular 100
const nfIndices = computed(() => paginas.value
  .map((p, i) => (p.tipo === 'nf' ? i : null))
  .filter(i => i !== null))

const temProximaPagina = computed(() => (paginaAtualIndex.value + 1) < paginas.value.length)
const temPaginaAnterior = computed(() => paginaAtualIndex.value > 0)

const podePular100 = computed(() => nfIndices.value.length > 0 && (function(){
  const pos = nfIndices.value.findIndex(i => i >= paginaAtualIndex.value)
  return pos !== -1 && (pos + 100) < nfIndices.value.length
})())

const podeVoltar100 = computed(() => nfIndices.value.length > 0 && (function(){
  const pos = nfIndices.value.findIndex(i => i >= paginaAtualIndex.value)
  return pos > 100 || (pos === -1 && nfIndices.value.length > 100)
})())

function goAnterior() {
  if (temPaginaAnterior.value) paginaAtualIndex.value -= 1
}

function goProxima() {
  if (temProximaPagina.value) paginaAtualIndex.value += 1
}

function voltar100() {
  if (!nfIndices.value.length) return
  // posição NF atual ou próxima NF antes da página atual
  const pos = nfIndices.value.findIndex(i => i >= paginaAtualIndex.value)
  const alvo = pos <= 0 ? nfIndices.value[0]
    : nfIndices.value[Math.max(pos - 100, 0)]
  paginaAtualIndex.value = alvo
}

function pular100() {
  if (!nfIndices.value.length) return
  // posição NF atual ou próxima NF após a página atual
  const pos = nfIndices.value.findIndex(i => i >= paginaAtualIndex.value)
  const alvo = pos === -1 ? nfIndices.value[nfIndices.value.length - 1]
    : nfIndices.value[Math.min(pos + 100, nfIndices.value.length - 1)]
  paginaAtualIndex.value = alvo
}

const padToLayout = (raw) => {
  if (!layout.value?.tamanho_linha) return raw || ''
  return (raw || '').length < layout.value.tamanho_linha
    ? (raw || '').padEnd(layout.value.tamanho_linha, ' ')
    : raw
}

const valorCampoLinha = (linhaRaw, c) => {
  const base = padToLayout(linhaRaw)
  const start = (c.posicao_inicio || 1) - 1
  const end = c.posicao_fim || (c.posicao_inicio - 1 + c.tamanho)
  let val = base.slice(start, end)
  if (showDots.value) val = (val || '').replace(/ /g, '·')
  return val || ''
}

const tooltipCampo = (c) => `${c.nome} | ${c.posicao_inicio}-${c.posicao_fim} (tam ${c.tamanho}) | ${c.tipo}`

// Tooltip avançado
const tooltipInfo = ref({ visible: false, x: 0, y: 0, campo: null, valor: '', indice: 0, posicaoExata: 0 })
let tooltipThrottle = null

function linhaComBarras(raw) {
  const campos = camposParaLinha(raw)
  return campos.map(c => valorCampoLinha(raw, c)).join('|')
}

function getCampoNaPosicaoMelhorada(event, raw, linhaComBarrasStr) {
  const campos = camposParaLinha(raw)
  if (!campos.length || !linhaComBarrasStr) return null

  const elemento = event.target
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
      medidor.textContent = ' | '
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

function mostrarTooltip(event, raw, linhaComBarrasStr) {
  const campoInfo = getCampoNaPosicaoMelhorada(event, raw, linhaComBarrasStr)
  if (campoInfo) {
    let finalX = event.clientX
    let finalY = event.clientY + 40
    const vw = window.innerWidth, vh = window.innerHeight
    const tw = 320, th = 200
    if (finalX + tw > vw) finalX = vw - tw - 10
    if (finalY + th > vh) finalY = vh - th - 10
    tooltipInfo.value = { 
      visible: true, 
      x: finalX, 
      y: finalY, 
      campo: campoInfo.campo, 
      valor: campoInfo.valor, 
      indice: campoInfo.indice, 
      posicaoExata: campoInfo.posicaoExata 
    }
  }
}

function mostrarTooltipThrottled(event, raw, linhaComBarrasStr) {
  if (tooltipThrottle) clearTimeout(tooltipThrottle)
  tooltipThrottle = setTimeout(() => mostrarTooltip(event, raw, linhaComBarrasStr), 50)
}

function esconderTooltip() {
  if (tooltipThrottle) { clearTimeout(tooltipThrottle); tooltipThrottle = null }
  tooltipInfo.value.visible = false
}

const formatarLinhaCompleta = (linha) => {
  if (!linha) return ''
  return showDots.value ? linha.replace(/ /g, '·') : linha
}

// Navegação desabilitada no modo empilhado (mantida aqui se quiser reativar)
</script>

<style scoped>
.file-input {
  @apply block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none;
}
</style>
