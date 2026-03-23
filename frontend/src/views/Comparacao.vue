<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">
        Comparação Estrutural de Arquivos
      </h1>
      <p class="text-gray-600">Compare dois arquivos TXT linha por linha usando um layout como referência</p>
    </div>

    <!-- Upload Form -->
    <div class="card max-w-4xl mx-auto" v-show="!hasResults">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <GitCompare class="w-5 h-5 mr-2" />
          Upload de Arquivos para Comparação
        </h2>
      </div>
      <div class="card-body space-y-6">
        <form @submit.prevent="handleComparison" class="space-y-6">
          <!-- Layout File Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Arquivo de Layout (Excel)
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="layoutFileInput"
                type="file"
                accept=".xlsx,.xls"
                @change="handleLayoutFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo Excel com as especificações dos campos (.xlsx ou .xls)
            </p>
          </div>

          <!-- Base File Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Arquivo Base (TXT) - Referência
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="baseFileInput"
                type="file"
                accept=".txt"
                @change="handleBaseFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo TXT que será usado como referência (base) para comparação
            </p>
          </div>

          <!-- Validation File Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Arquivo a ser Comparado (TXT)
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="validationFileInput"
                type="file"
                accept=".txt"
                @change="handleValidationFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo TXT que será comparado com o arquivo base
            </p>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-end">
            <button
              type="submit"
              :disabled="isLoading || !canSubmit"
              class="btn-primary"
            >
              <template v-if="isLoading">
                <Loader2 class="w-4 h-4 mr-2 animate-spin" />
                Comparando...
              </template>
              <template v-else>
                <GitCompare class="w-4 h-4 mr-2" />
                Comparar Arquivos
              </template>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center items-center py-12">
      <div class="text-center">
        <Loader2 class="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
        <p class="text-gray-600">Comparando arquivos estruturalmente...</p>
      </div>
    </div>

    <!-- Results -->
    <div v-if="hasResults && !isLoading" class="space-y-6">
      <!-- Header de Resultados -->
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-900">Resultado da Comparação</h2>
        <div class="flex gap-3">
          <button @click="downloadReport" class="btn-secondary">
            <Download class="w-4 h-4 mr-2" />
            Baixar Relatório
          </button>
          <button @click="resetComparison" class="btn-outline">
            <RotateCcw class="w-4 h-4 mr-2" />
            Nova Comparação
          </button>
        </div>
      </div>

      <!-- Estatísticas -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="stat-card">
          <div class="stat-value">{{ comparisonResult?.total_linhas_comparadas || 0 }}</div>
          <div class="stat-label">Total de Linhas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-green-600">{{ comparisonResult?.linhas_identicas || 0 }}</div>
          <div class="stat-label">Linhas Idênticas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-red-600">{{ comparisonResult?.linhas_com_diferencas || 0 }}</div>
          <div class="stat-label">Linhas com Diferenças</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" :class="taxaIdentidadeClass">
            {{ (comparisonResult?.taxa_identidade || 0).toFixed(2) }}%
          </div>
          <div class="stat-label">Taxa de Identidade</div>
        </div>
      </div>

      <!-- Diferenças Detalhadas -->
      <div v-if="comparisonResult?.diferencas_por_linha?.length > 0" class="card">
        <div class="card-header flex justify-between items-center">
          <h3 class="text-lg font-semibold">Diferenças Encontradas</h3>
          <div class="flex items-center gap-3">
            <span class="text-sm text-gray-500">
              {{ errosSelecionados.size }} de {{ comparisonResult.diferencas_por_linha.length }} selecionados para o relatório
            </span>
            <button
              @click="toggleTodosErros"
              class="text-sm px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              {{ errosSelecionados.size === comparisonResult.diferencas_por_linha.length ? 'Desmarcar Todos' : 'Selecionar Todos' }}
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="space-y-6">
            <div
              v-for="(diferenca, index) in comparisonResult.diferencas_por_linha"
              :key="index"
              :class="[
                'border rounded-lg p-4 transition-all',
                errosSelecionados.has(index) ? 'border-gray-200' : 'border-dashed border-gray-300 opacity-50'
              ]"
            >
              <div class="flex justify-between items-center mb-3">
                <div class="flex items-center gap-3">
                  <label class="flex items-center cursor-pointer" @click.stop>
                    <input
                      type="checkbox"
                      :checked="errosSelecionados.has(index)"
                      @change="toggleErroSelecionado(index)"
                      class="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
                    />
                  </label>
                  <h4 class="font-semibold text-gray-900">
                    Linha {{ diferenca.numero_linha }} - {{ diferenca.tipo_registro }}
                  </h4>
                </div>
                <span class="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                  {{ diferenca.total_diferencas }} diferença(s)
                </span>
              </div>

              <!-- Visualização das Linhas -->
              <div class="space-y-1 mb-4 text-sm font-mono">
                <!-- Linha de Numeração -->
                <div v-if="diferenca.linha_numeracao">
                  <span class="text-gray-600">Campos:</span>
                  <div
                    :data-ref="`numeracao-linha-${index}`"
                    class="bg-blue-50 p-2 rounded border overflow-x-auto text-blue-800 font-semibold relative"
                    style="white-space: pre;"
                  ><span v-if="campoDestacado?.linhaIndex === index" class="campo-highlight-overlay" :style="getHighlightStyle(`numeracao-linha-${index}`, diferenca.linha_numeracao)"></span>{{ diferenca.linha_numeracao }}</div>
                </div>

                <div>
                  <span class="text-gray-600">Base:</span>
                  <div
                    :data-ref="`base-linha-${index}`"
                    class="bg-gray-50 p-2 rounded border overflow-x-auto cursor-help hover:bg-blue-50 transition-colors relative"
                    style="white-space: pre;"
                    @scroll="sincronizarScroll($event, `validado-linha-${index}`, `numeracao-linha-${index}`)"
                    @mousemove="mostrarTooltipThrottled($event, diferenca, diferenca.arquivo_base_linha, 'base')"
                    @mouseleave="esconderTooltip"
                    title="Clique para ver detalhes dos campos"
                  ><span v-if="campoDestacado?.linhaIndex === index" class="campo-highlight-overlay" :style="getHighlightStyle(`base-linha-${index}`, diferenca.arquivo_base_linha)"></span>{{ diferenca.arquivo_base_linha }}</div>
                </div>
                <div>
                  <span class="text-gray-600">Comparado:</span>
                  <div
                    :data-ref="`validado-linha-${index}`"
                    class="bg-gray-50 p-2 rounded border overflow-x-auto cursor-help hover:bg-blue-50 transition-colors relative"
                    style="white-space: pre;"
                    @scroll="sincronizarScroll($event, `base-linha-${index}`, `numeracao-linha-${index}`)"
                    @mousemove="mostrarTooltipThrottled($event, diferenca, diferenca.arquivo_validado_linha, 'validado')"
                    @mouseleave="esconderTooltip"
                    title="Clique para ver detalhes dos campos"
                  ><span v-if="campoDestacado?.linhaIndex === index" class="campo-highlight-overlay" :style="getHighlightStyle(`validado-linha-${index}`, diferenca.arquivo_validado_linha)"></span>{{ diferenca.arquivo_validado_linha }}</div>
                </div>
              </div>

              <!-- Diferenças por Campo -->
              <div class="space-y-2">
                <h5 class="font-medium text-gray-700">Campos com Diferenças:</h5>
                <div class="grid gap-2">
                  <div
                    v-for="(campo, campIndex) in diferenca.diferencas_campos"
                    :key="campIndex"
                    :class="[
                      'p-3 rounded-lg border-l-4',
                      campo.tipo_diferenca && campo.tipo_diferenca.startsWith('CALCULO_')
                        ? 'bg-orange-50 border-orange-400'
                        : 'bg-red-50 border-red-400'
                    ]"
                  >
                    <div class="flex justify-between items-start">
                      <div class="flex-1">
                        <div class="flex items-center">
                          <span
                            class="font-medium cursor-pointer relative group hover:text-blue-700 hover:underline transition-colors"
                            :title="`Clique para destacar na linha`"
                            @click="destacarCampoNaLinha(index, campo)"
                          >
                            Campo {{ (campo.sequencia_campo || 0).toString().padStart(2, '0') }} - {{ campo.nome_campo }}
                            <!-- Tooltip customizado -->
                            <div class="absolute bottom-full left-0 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                              <div>📋 Campo: {{ campo.nome_campo }}</div>
                              <div>📍 Posição: {{ campo.posicao_inicio }}-{{ campo.posicao_fim }}</div>
                              <div>🔢 Sequência: {{ (campo.sequencia_campo || 0).toString().padStart(2, '0') }}</div>
                              <div class="text-blue-300 mt-1">Clique para destacar na linha</div>
                              <!-- Seta do tooltip -->
                              <div class="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                            </div>
                          </span>
                          <span v-if="campo.tipo_diferenca && campo.tipo_diferenca.startsWith('CALCULO_')"
                                class="ml-2 px-2 py-1 text-xs bg-orange-200 text-orange-800 rounded-full">
                            🧮 Calculo do imposto
                          </span>
                          <span v-else-if="campo.tipo_diferenca"
                                class="ml-2 px-2 py-1 text-xs bg-red-200 text-red-800 rounded-full">
                            {{ campo.tipo_diferenca }}
                          </span>
                        </div>
                        <span class="text-sm text-gray-600">
                          (Pos {{ campo.posicao_inicio }}-{{ campo.posicao_fim }})
                        </span>
                      </div>
                    </div>

                    <!-- Descrição detalhada para cálculos de impostos -->
                    <div v-if="campo.tipo_diferenca && campo.tipo_diferenca.startsWith('CALCULO_')"
                         class="mt-3 p-3 bg-orange-100 rounded">
                      <h6 class="font-semibold text-orange-800 mb-2">📊 Detalhes do Cálculo:</h6>
                      <div class="text-sm text-orange-900 font-mono">
                        {{ campo.descricao }}
                      </div>
                    </div>

                    <!-- Descrição genérica para outros tipos de diferença -->
                    <div v-else-if="campo.descricao"
                         class="mt-2 p-2 bg-gray-100 rounded">
                      <div class="text-sm text-gray-700">
                        {{ campo.descricao }}
                      </div>
                    </div>

                    <!-- Valores comparados (apenas quando não é cálculo) -->
                    <div v-if="!campo.tipo_diferenca || !campo.tipo_diferenca.startsWith('CALCULO_')"
                         class="mt-2 text-sm">
                      <div class="grid grid-cols-2 gap-2">
                        <div class="text-gray-600">
                          Base: <span class="font-mono bg-white px-1 rounded">{{ campo.valor_base }}</span>
                        </div>
                        <div class="text-gray-600">
                          Comp: <span class="font-mono bg-white px-1 rounded">{{ campo.valor_validado }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Error State -->
    <div v-if="error" class="card border-red-200 bg-red-50">
      <div class="card-body">
        <div class="flex items-start">
          <AlertCircle class="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 class="text-red-800 font-medium">Erro na Comparação</h3>
            <p class="text-red-700 mt-1">{{ error }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Tooltip Flutuante para Campos - Melhorado -->
    <div
      v-if="tooltipInfo.visible && tooltipInfo.campo"
      class="fixed z-50 px-4 py-3 bg-gray-900 text-white text-sm rounded-lg shadow-xl pointer-events-none border border-gray-700"
      :style="{
        left: tooltipInfo.x + 'px',
        top: tooltipInfo.y + 'px',
        maxWidth: '320px',
        minWidth: '280px'
      }"
    >
      <div class="space-y-2">
        <div class="font-bold text-blue-300 border-b border-gray-700 pb-1 flex items-center justify-between">
          <span>📋 {{ tooltipInfo.campo.nome }}</span>
          <span
            :class="tooltipInfo.tipoLinha === 'base' ? 'bg-green-700 text-green-200' : 'bg-orange-700 text-orange-200'"
            class="px-2 py-1 rounded text-xs font-mono"
          >
            {{ tooltipInfo.tipoLinha === 'base' ? '📊 BASE' : '🔍 VALIDADO' }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span class="text-gray-400">📍 Posição:</span>
            <span class="text-white font-mono">{{ tooltipInfo.campo.posicao_inicio }}-{{ tooltipInfo.campo.posicao_fim }}</span>
          </div>
          <div>
            <span class="text-gray-400">🔢 Campo:</span>
            <span class="text-yellow-300 font-mono">{{ tooltipInfo.indice.toString().padStart(2, '0') }}</span>
          </div>
          <div>
            <span class="text-gray-400">📄 Tipo:</span>
            <span class="text-green-300">{{ tooltipInfo.campo.tipo }}</span>
          </div>
          <div v-if="tooltipInfo.campo.obrigatorio">
            <span class="text-gray-400">⚠️ Status:</span>
            <span class="text-red-300">Obrigatório</span>
          </div>
        </div>

        <div v-if="tooltipInfo.valor.trim()" class="border-t border-gray-700 pt-2">
          <div class="text-gray-400 text-xs mb-1">💾 Valor atual:</div>
          <div class="bg-gray-800 p-2 rounded font-mono text-xs break-all text-cyan-300">
            "{{ tooltipInfo.valor.trim() }}"
          </div>
        </div>

        <div class="text-xs text-gray-500 border-t border-gray-700 pt-1">
          🎯 Precisão melhorada - Posição {{ Math.round(tooltipInfo.posicaoExata || 0) }}px
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { AlertCircle, Download, GitCompare, Loader2, RotateCcw } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import api from '../services/api'
import localStorageService from '../services/localStorage'

// Reactive data
const tooltipInfo = ref({
  visible: false,
  x: 0,
  y: 0,
  campo: null,
  valor: '',
  indice: 0,
  posicaoExata: 0,
  tipoLinha: 'base'
})
const layoutData = ref({ campos: [] })
const layoutFile = ref(null)
const baseFile = ref(null)
const validationFile = ref(null)
const isLoading = ref(false)
const error = ref('')
const comparisonResult = ref(null)
const reportText = ref('')
const timestamp = ref('')

// Estado para destaque de campo na linha
const campoDestacado = ref(null)
let highlightTimeout = null

// Estado para seleção de erros no relatório
const errosSelecionados = ref(new Set())

// Computed properties
const hasResults = computed(() => comparisonResult.value !== null)
const canSubmit = computed(() => layoutFile.value && baseFile.value && validationFile.value)

const taxaIdentidadeClass = computed(() => {
  const taxa = comparisonResult.value?.taxa_identidade || 0
  if (taxa >= 95) return 'text-green-600'
  if (taxa >= 80) return 'text-yellow-600'
  return 'text-red-600'
})

// Computed para todos os cálculos de impostos (corretos e incorretos)
const calculationResults = computed(() => {
  if (!comparisonResult.value?.diferencas_por_linha) return { errors: [], correct: [], total: [] }

  const errors = []
  const correct = []
  const total = []

  comparisonResult.value.diferencas_por_linha.forEach(linha => {
    if (linha.diferencas_campos) {
      linha.diferencas_campos.forEach(campo => {
        if (campo.tipo_diferenca && (campo.tipo_diferenca.startsWith('CALCULO_'))) {
          const item = {
            ...campo,
            linha: linha.numero_linha,
            tipo_registro: linha.tipo_registro
          }

          total.push(item)

          if (campo.tipo_diferenca.includes('_OK_')) {
            correct.push(item)
          } else if (campo.tipo_diferenca.includes('_ERRO_')) {
            errors.push(item)
          }
        }
      })
    }
  })

  return { errors, correct, total }
})

// Manter compatibilidade com código existente
const calculationErrors = computed(() => calculationResults.value.errors)

// File handlers
function handleLayoutFileChange(event) {
  layoutFile.value = event.target.files[0]
  clearError()
}

function handleBaseFileChange(event) {
  baseFile.value = event.target.files[0]
  clearError()
}

function handleValidationFileChange(event) {
  validationFile.value = event.target.files[0]
  clearError()
}

function clearError() {
  error.value = ''
}

// Main comparison function
async function handleComparison() {
  if (!canSubmit.value) return

  isLoading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('layout_file', layoutFile.value)
    formData.append('arquivo_base', baseFile.value)
    formData.append('arquivo_validado', validationFile.value)

    const response = await api.post('/comparar-estrutural', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    comparisonResult.value = response.data.resultado_comparacao
    reportText.value = response.data.relatorio_texto
    timestamp.value = response.data.timestamp
    layoutData.value = response.data.layout // Salvar dados do layout

    // Inicializar todos os erros como selecionados
    inicializarSelecaoErros()

  } catch (err) {
    console.error('Erro na comparação:', err)
    error.value = err.response?.data?.detail || 'Erro interno do servidor'
  } finally {
    isLoading.value = false
  }
}

// Download report - filtra apenas erros selecionados
async function downloadReport() {
  if (!timestamp.value) return

  try {
    if (!comparisonResult.value?.diferencas_por_linha) {
      throw new Error('Dados da comparação não encontrados')
    }

    // Filtrar diferenças selecionadas
    const diferencasFiltradas = comparisonResult.value.diferencas_por_linha.filter(
      (_, index) => errosSelecionados.value.has(index)
    )

    // Gerar relatório em texto com os erros filtrados
    let content = `=== RELATÓRIO DE COMPARAÇÃO ESTRUTURAL ===\n`
    content += `Data/Hora: ${new Date().toLocaleString('pt-BR')}\n`
    content += `\n=== ESTATÍSTICAS ===\n`
    content += `Total de Linhas Comparadas: ${comparisonResult.value.total_linhas_comparadas}\n`
    content += `Linhas Idênticas: ${comparisonResult.value.linhas_identicas}\n`
    content += `Linhas com Diferenças (total): ${comparisonResult.value.linhas_com_diferencas}\n`
    content += `Linhas incluídas neste relatório: ${diferencasFiltradas.length}\n`
    content += `Taxa de Identidade: ${(comparisonResult.value.taxa_identidade || 0).toFixed(2)}%\n`

    if (diferencasFiltradas.length === 0) {
      content += `\nNenhuma diferença selecionada para o relatório.\n`
    } else {
      content += `\n${'='.repeat(60)}\n`
      content += `DIFERENÇAS DETALHADAS\n`
      content += `${'='.repeat(60)}\n`

      diferencasFiltradas.forEach(dif => {
        content += `\n--- Linha ${dif.numero_linha} - ${dif.tipo_registro} (${dif.total_diferencas} diferença(s)) ---\n`

        if (dif.arquivo_base_linha) {
          content += `  Base:      ${dif.arquivo_base_linha}\n`
        }
        if (dif.arquivo_validado_linha) {
          content += `  Comparado: ${dif.arquivo_validado_linha}\n`
        }

        if (dif.diferencas_campos?.length > 0) {
          content += `  Campos com diferenças:\n`
          dif.diferencas_campos.forEach(campo => {
            content += `    - Campo ${(campo.sequencia_campo || 0).toString().padStart(2, '0')} | ${campo.nome_campo} (Pos ${campo.posicao_inicio}-${campo.posicao_fim})\n`
            if (campo.tipo_diferenca?.startsWith('CALCULO_')) {
              content += `      Tipo: ${campo.tipo_diferenca}\n`
              if (campo.descricao) content += `      Detalhe: ${campo.descricao}\n`
            } else {
              content += `      Base: "${campo.valor_base}" | Comparado: "${campo.valor_validado}"\n`
              if (campo.descricao) content += `      Descrição: ${campo.descricao}\n`
            }
          })
        }
      })
    }

    content += `\n${'='.repeat(60)}\n`
    content += `Fim do Relatório\n`

    const filename = `comparacao_estrutural_${timestamp.value}.txt`
    localStorageService.downloadText(content, filename)
  } catch (err) {
    console.error('Erro ao baixar relatório:', err)
    error.value = 'Erro ao baixar relatório: ' + err.message
  }
}

// Função para extrair NUM-NF da descrição
function extractNumNF(descricao) {
  if (!descricao) return null
  const match = descricao.match(/NUM-NF:\s*(\d+)/)
  return match ? `NUM-NF: ${match[1]}` : null
}

// Função para obter campos de um tipo de registro
function getCamposDoTipo(tipoRegistro) {
  if (!layoutData.value?.campos) return []

  return layoutData.value.campos.filter(campo => {
    const nomeCampo = campo.nome || ''
    return nomeCampo.includes(`NFE${tipoRegistro}-`) || nomeCampo.includes(`NFCOM${tipoRegistro}-`) ||
           (!nomeCampo.startsWith('NFE') && !nomeCampo.startsWith('NFCOM'))
  })
}

// Função para encontrar campo pela posição do mouse na linha com precisão melhorada
function getCampoNaPosicaoMelhorada(event, tipoRegistro, linhaComBarras) {
  const campos = getCamposDoTipo(tipoRegistro)
  if (!campos.length || !linhaComBarras) return null

  // Obter elemento e suas medidas
  const elemento = event.target
  const rect = elemento.getBoundingClientRect()
  const style = window.getComputedStyle(elemento)

  // Calcular posição real considerando scroll
  const scrollLeft = elemento.scrollLeft
  const posicaoMouseReal = event.offsetX + scrollLeft

  // Criar um elemento temporário para medir texto
  const medidor = document.createElement('span')
  medidor.style.font = style.font
  medidor.style.fontSize = style.fontSize
  medidor.style.fontFamily = style.fontFamily
  medidor.style.visibility = 'hidden'
  medidor.style.position = 'absolute'
  medidor.style.whiteSpace = 'pre'
  document.body.appendChild(medidor)

  try {
    // Dividir linha pelas barras |
    const segments = linhaComBarras.split('|')
    let posicaoAcumulada = 0

    for (let i = 0; i < segments.length - 1 && i < campos.length; i++) { // -1 porque o último segmento após a última | pode estar vazio
      const segmento = segments[i]

      // Medir largura real do segmento
      medidor.textContent = segmento
      const larguraSegmento = medidor.offsetWidth

      // Medir largura da barra |
      medidor.textContent = '|'
      const larguraBarra = medidor.offsetWidth

      const inicioSegmento = posicaoAcumulada
      const fimSegmento = posicaoAcumulada + larguraSegmento

      if (posicaoMouseReal >= inicioSegmento && posicaoMouseReal <= fimSegmento) {
        return {
          campo: campos[i],
          valor: segmento,
          indice: i + 1,
          posicaoExata: posicaoMouseReal - inicioSegmento
        }
      }

      posicaoAcumulada = fimSegmento + larguraBarra
    }
  } finally {
    document.body.removeChild(medidor)
  }

  return null
}

// Funções para controlar tooltip com precisão melhorada
function mostrarTooltip(event, diferenca, linha, tipoLinha = 'base') {
  // Usar função melhorada de detecção
  const campoInfo = getCampoNaPosicaoMelhorada(event, diferenca.tipo_registro, linha)

  if (campoInfo) {
    // Posição do tooltip na tela (fixo)
    const tooltipX = event.clientX
    const tooltipY = event.clientY

    // Ajustar posição para não sair da tela
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const tooltipWidth = 320 // Largura estimada do tooltip
    const tooltipHeight = 200 // Altura estimada do tooltip (aumentada)

    let finalX = tooltipX
    let finalY = tooltipY

    // Ajustar X se sair da tela
    if (finalX + tooltipWidth > viewportWidth) {
      finalX = viewportWidth - tooltipWidth - 10
    }
    if (finalX < 10) {
      finalX = 10
    }

    // Posicionamento baseado no tipo de linha:
    // BASE: tooltip muito acima (bem distante)
    // VALIDADO/COMPARADO: tooltip abaixo
    if (tipoLinha === 'base') {
      finalY = tooltipY - tooltipHeight - 80 // Muito acima da linha (bem distante)
      // Se não couber acima, forçar bem abaixo
      if (finalY < 10) {
        finalY = tooltipY + 60 // Bem distante quando for abaixo
      }
    } else {
      finalY = tooltipY + 40 // Sempre abaixo da linha (aumentado para mais distância)
      // Se não couber abaixo, mover para cima mas ainda tentar ficar abaixo
      if (finalY + tooltipHeight > viewportHeight) {
        finalY = viewportHeight - tooltipHeight - 20 // Forçar a ficar dentro da tela na parte inferior
        // Só se realmente não couber, aí sim ir para cima
        if (finalY < tooltipY + 10) {
          finalY = tooltipY - tooltipHeight - 80
        }
      }
    }

    tooltipInfo.value = {
      visible: true,
      x: finalX,
      y: finalY,
      campo: campoInfo.campo,
      valor: campoInfo.valor,
      indice: campoInfo.indice,
      posicaoExata: campoInfo.posicaoExata,
      tipoLinha: tipoLinha
    }
  }
}

function esconderTooltip() {
  // Limpar qualquer throttle pendente
  if (tooltipThrottle) {
    clearTimeout(tooltipThrottle)
    tooltipThrottle = null
  }
  // Esconder imediatamente
  tooltipInfo.value.visible = false
}

// Throttle para melhorar performance do mousemove
let tooltipThrottle = null
function mostrarTooltipThrottled(event, diferenca, linha, tipoLinha) {
  if (tooltipThrottle) {
    clearTimeout(tooltipThrottle)
  }

  tooltipThrottle = setTimeout(() => {
    mostrarTooltip(event, diferenca, linha, tipoLinha)
    tooltipThrottle = null
  }, 50) // 50ms de throttle
}

// === Funções de destaque de campo na linha ===

function destacarCampoNaLinha(linhaIndex, campo) {
  // Limpar timeout anterior
  if (highlightTimeout) {
    clearTimeout(highlightTimeout)
  }

  // Definir campo destacado
  campoDestacado.value = {
    linhaIndex,
    posicao_inicio: campo.posicao_inicio,
    posicao_fim: campo.posicao_fim,
    nome_campo: campo.nome_campo
  }

  // Scroll para a área das linhas
  const baseEl = document.querySelector(`[data-ref="base-linha-${linhaIndex}"]`)
  if (baseEl) {
    // Calcular posição de scroll baseada na posição do campo
    const style = window.getComputedStyle(baseEl)
    const medidor = document.createElement('span')
    medidor.style.font = style.font
    medidor.style.fontSize = style.fontSize
    medidor.style.fontFamily = style.fontFamily
    medidor.style.visibility = 'hidden'
    medidor.style.position = 'absolute'
    medidor.style.whiteSpace = 'pre'
    document.body.appendChild(medidor)

    // Medir posição do campo na linha usando pipes
    const linhaTexto = baseEl.textContent
    const segments = linhaTexto.split('|')
    let charPos = 0
    const seq = campo.sequencia_campo || 0

    for (let i = 0; i < seq - 1 && i < segments.length; i++) {
      charPos += segments[i].length + 1 // +1 pelo pipe
    }

    medidor.textContent = linhaTexto.substring(0, charPos)
    const scrollTarget = medidor.offsetWidth - 100 // 100px de margem
    document.body.removeChild(medidor)

    // Scroll suave para o campo
    baseEl.scrollLeft = Math.max(0, scrollTarget)

    // Sincronizar scroll nas outras linhas
    const validadoEl = document.querySelector(`[data-ref="validado-linha-${linhaIndex}"]`)
    const numeracaoEl = document.querySelector(`[data-ref="numeracao-linha-${linhaIndex}"]`)
    if (validadoEl) validadoEl.scrollLeft = baseEl.scrollLeft
    if (numeracaoEl) numeracaoEl.scrollLeft = baseEl.scrollLeft

    // Scroll a página para mostrar as linhas
    baseEl.closest('.border')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // Remover destaque após 4 segundos
  highlightTimeout = setTimeout(() => {
    campoDestacado.value = null
  }, 4000)
}

function getHighlightStyle(refName, linhaTexto) {
  if (!campoDestacado.value || !linhaTexto) return { display: 'none' }

  const campo = campoDestacado.value
  const el = document.querySelector(`[data-ref="${refName}"]`)
  if (!el) return { display: 'none' }

  const style = window.getComputedStyle(el)
  const medidor = document.createElement('span')
  medidor.style.font = style.font
  medidor.style.fontSize = style.fontSize
  medidor.style.fontFamily = style.fontFamily
  medidor.style.visibility = 'hidden'
  medidor.style.position = 'absolute'
  medidor.style.whiteSpace = 'pre'
  document.body.appendChild(medidor)

  // Calcular posição visual usando posições de caractere
  const posInicio = campo.posicao_inicio - 1 // Converter para 0-based
  const posFim = campo.posicao_fim

  medidor.textContent = linhaTexto.substring(0, posInicio)
  const left = medidor.offsetWidth

  medidor.textContent = linhaTexto.substring(posInicio, posFim)
  const width = medidor.offsetWidth

  document.body.removeChild(medidor)

  return {
    position: 'absolute',
    left: left + 'px',
    top: '0',
    width: width + 'px',
    height: '100%',
    backgroundColor: 'rgba(59, 130, 246, 0.25)',
    borderLeft: '2px solid rgb(59, 130, 246)',
    borderRight: '2px solid rgb(59, 130, 246)',
    pointerEvents: 'none',
    zIndex: '10',
    transition: 'all 0.3s ease',
    animation: 'highlight-pulse 1.5s ease-in-out infinite'
  }
}

// === Funções de seleção de erros para o relatório ===

function toggleErroSelecionado(index) {
  const newSet = new Set(errosSelecionados.value)
  if (newSet.has(index)) {
    newSet.delete(index)
  } else {
    newSet.add(index)
  }
  errosSelecionados.value = newSet
}

function toggleTodosErros() {
  if (!comparisonResult.value?.diferencas_por_linha) return

  if (errosSelecionados.value.size === comparisonResult.value.diferencas_por_linha.length) {
    errosSelecionados.value = new Set()
  } else {
    const allIndexes = new Set()
    for (let i = 0; i < comparisonResult.value.diferencas_por_linha.length; i++) {
      allIndexes.add(i)
    }
    errosSelecionados.value = allIndexes
  }
}

function inicializarSelecaoErros() {
  if (!comparisonResult.value?.diferencas_por_linha) return
  const allIndexes = new Set()
  for (let i = 0; i < comparisonResult.value.diferencas_por_linha.length; i++) {
    allIndexes.add(i)
  }
  errosSelecionados.value = allIndexes
}

// Reset comparison
function resetComparison() {
  comparisonResult.value = null
  reportText.value = ''
  timestamp.value = ''
  layoutFile.value = null
  baseFile.value = null
  validationFile.value = null
  error.value = ''
  campoDestacado.value = null
  errosSelecionados.value = new Set()

  // Reset file inputs
  if (layoutFileInput.value) layoutFileInput.value.value = ''
  if (baseFileInput.value) baseFileInput.value.value = ''
  if (validationFileInput.value) validationFileInput.value.value = ''
}

// Sincronização de scroll
let scrollSyncing = false
function sincronizarScroll(event, targetRefName, numeracaoRefName = null) {
  if (scrollSyncing) return

  const target = document.querySelector(`[data-ref="${targetRefName}"]`)
  const numeracao = numeracaoRefName ? document.querySelector(`[data-ref="${numeracaoRefName}"]`) : null

  if (target && target !== event.target) {
    scrollSyncing = true
    target.scrollLeft = event.target.scrollLeft

    // Sincronizar também a linha de numeração se existir
    if (numeracao) {
      numeracao.scrollLeft = event.target.scrollLeft
    }

    setTimeout(() => { scrollSyncing = false }, 10)
  }
}

// Template refs
const layoutFileInput = ref(null)
const baseFileInput = ref(null)
const validationFileInput = ref(null)
</script>

<style scoped>
.file-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500;
}

.btn-primary {
  @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}

.btn-outline {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}

.card {
  @apply bg-white shadow rounded-lg;
}

.card-header {
  @apply px-6 py-4 border-b border-gray-200;
}

.card-body {
  @apply px-6 py-4;
}

.stat-card {
  @apply bg-white p-4 rounded-lg shadow border border-gray-200;
}

.stat-value {
  @apply text-2xl font-bold;
}

.stat-label {
  @apply text-sm text-gray-600 mt-1;
}

/* Tooltips customizados */
.cursor-help {
  cursor: help;
}

.cursor-help:hover {
  @apply text-blue-600 transition-colors duration-200;
}

/* Garantir que tooltips customizados apareçam */
.group:hover .group-hover\:opacity-100 {
  opacity: 1 !important;
}

/* Melhorar aparência dos tooltips nativos */
[title] {
  position: relative;
  white-space: pre-line;
}

/* Força exibição de tooltips nativos */
[title]:hover {
  position: relative;
}

/* Ajustar z-index para tooltips */
.z-50 {
  z-index: 9999 !important;
}

/* Overlay de destaque do campo */
.campo-highlight-overlay {
  display: block;
  border-radius: 2px;
}

@keyframes highlight-pulse {
  0%, 100% {
    background-color: rgba(59, 130, 246, 0.25);
  }
  50% {
    background-color: rgba(59, 130, 246, 0.45);
  }
}
</style>