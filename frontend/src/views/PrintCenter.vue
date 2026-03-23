<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">PrintCenter</h1>
      <p class="text-gray-600">
        Compare seu arquivo com o arquivo de produção do lote selecionado
      </p>
    </div>

    <!-- Aviso: layout não configurado -->
    <div
      v-if="configLoaded && !config.layout_exists"
      class="card border-yellow-200 bg-yellow-50 max-w-4xl mx-auto"
    >
      <div class="card-body">
        <div class="flex items-start">
          <AlertCircle
            class="w-5 h-5 text-yellow-500 mt-0.5 mr-3 flex-shrink-0"
          />
          <div>
            <h3 class="text-yellow-800 font-medium">Layout não configurado</h3>
            <p class="text-yellow-700 mt-1">
              Coloque o arquivo de layout Excel na pasta
              <code class="bg-yellow-100 px-1 rounded"
                >printcenter/layout/</code
              >
              e atualize o campo
              <code class="bg-yellow-100 px-1 rounded">layout_file</code> no
              arquivo
              <code class="bg-yellow-100 px-1 rounded"
                >printcenter/config.json</code
              >.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload Form -->
    <div class="card max-w-4xl mx-auto" v-show="!hasResults && configLoaded">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <Printer class="w-5 h-5 mr-2" />
          Comparação PrintCenter
        </h2>
      </div>
      <div class="card-body space-y-6">
        <form @submit.prevent="handleComparison" class="space-y-6">
          <!-- Modo de seleção do arquivo de produção -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-3">
              Arquivo de Produção (Referência)
              <span class="text-red-500">*</span>
            </label>
            <div class="flex gap-3 mb-4">
              <button
                type="button"
                @click="modoProducao = 'lote'"
                :class="[
                  'flex-1 py-2 px-4 rounded-lg border-2 text-sm font-medium transition-colors',
                  modoProducao === 'lote'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300',
                ]"
              >
                📁 Selecionar Lote
              </button>
              <button
                type="button"
                @click="modoProducao = 'upload'"
                :class="[
                  'flex-1 py-2 px-4 rounded-lg border-2 text-sm font-medium transition-colors',
                  modoProducao === 'upload'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300',
                ]"
              >
                ⬆️ Enviar Novo Lote
              </button>
            </div>

            <!-- Seleção de Lote -->
            <div v-if="modoProducao === 'lote'">
              <select v-model="selectedLote" class="select-input">
                <option value="" disabled>Selecione um lote...</option>
                <option
                  v-for="lote in config.lotes"
                  :key="lote.arquivo"
                  :value="lote.arquivo"
                >
                  {{ lote.nome }}
                </option>
              </select>
              <p class="text-sm text-gray-500 mt-1">
                Arquivo de produção pré-configurado na pasta lotes/
              </p>
              <p
                v-if="config.lotes.length === 0"
                class="text-sm text-yellow-600 mt-1"
              >
                Nenhum lote encontrado. Use o botão abaixo para enviar um arquivo de produção.
              </p>
            </div>

            <!-- Upload de Arquivo de Produção (salva no servidor) -->
            <div v-if="modoProducao === 'upload'">
              <div class="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center"
                :class="{ 'border-blue-400 bg-blue-50': uploadingLote }">
                <input
                  ref="loteUploadInput"
                  type="file"
                  accept=".txt,*"
                  @change="handleLoteUpload"
                  class="hidden"
                  :disabled="uploadingLote"
                />
                <div v-if="!uploadingLote && !loteUploadResult">
                  <Upload class="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <button
                    type="button"
                    @click="$refs.loteUploadInput.click()"
                    class="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Selecionar arquivo de produção
                  </button>
                  <p class="text-sm text-gray-500 mt-1">
                    O arquivo será salvo no servidor e ficará disponível no dropdown de lotes
                  </p>
                </div>
                <div v-if="uploadingLote" class="py-2">
                  <Loader2 class="w-6 h-6 text-blue-500 animate-spin mx-auto mb-2" />
                  <p class="text-sm text-blue-600">Enviando arquivo... ({{ loteUploadProgress }})</p>
                  <p class="text-xs text-gray-500 mt-1">Arquivos grandes podem demorar alguns minutos</p>
                </div>
                <div v-if="loteUploadResult" class="py-2">
                  <CheckCircle2 class="w-6 h-6 text-green-500 mx-auto mb-2" />
                  <p class="text-sm text-green-700 font-medium">{{ loteUploadResult.mensagem }}</p>
                  <p class="text-xs text-gray-500 mt-1">
                    {{ loteUploadResult.tamanho_mb }}MB · {{ loteUploadResult.total_linhas }} linhas · {{ loteUploadResult.total_faturas }} faturas
                  </p>
                  <button
                    type="button"
                    @click="loteUploadResult = null; loadConfig()"
                    class="mt-2 text-sm text-blue-600 hover:text-blue-800"
                  >
                    ✓ Arquivo disponível no dropdown — clique para atualizar lista
                  </button>
                </div>
              </div>
              <p v-if="loteUploadError" class="text-sm text-red-600 mt-1">{{ loteUploadError }}</p>
            </div>
          </div>

          <!-- Upload do Arquivo do Usuário -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Seu Arquivo
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="userFileInput"
                type="file"
                accept=".txt,*"
                @change="handleUserFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo sequencial que será comparado com o arquivo de produção do
              lote
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
                <Printer class="w-4 h-4 mr-2" />
                Comparar
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
        <p class="text-gray-600">Comparando arquivos...</p>
      </div>
    </div>

    <!-- Results -->
    <div v-if="hasResults && !isLoading" class="space-y-6">
      <!-- Header de Resultados -->
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-900">
          Resultado da Comparação
        </h2>
        <div class="flex gap-3">
          <button @click="downloadReportPDF" class="btn-primary bg-red-600 hover:bg-red-700">
            <Download class="w-4 h-4 mr-2" />
            Baixar PDF
          </button>
          <button @click="downloadReport" class="btn-secondary">
            <Download class="w-4 h-4 mr-2" />
            Baixar TXT
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
          <div class="stat-value">
            {{ comparisonResult?.total_linhas_comparadas || 0 }}
          </div>
          <div class="stat-label">Total de Linhas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-green-600">
            {{ comparisonResult?.linhas_identicas || 0 }}
          </div>
          <div class="stat-label">Linhas Idênticas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-red-600">
            {{ comparisonResult?.linhas_com_diferencas || 0 }}
          </div>
          <div class="stat-label">Linhas com Diferenças</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" :class="taxaIdentidadeClass">
            {{ (comparisonResult?.taxa_identidade || 0).toFixed(2) }}%
          </div>
          <div class="stat-label">Taxa de Identidade</div>
        </div>
      </div>

      <!-- Contas Não Encontradas -->
      <div
        v-if="comparisonResult?.contas_nao_encontradas?.length > 0"
        class="card border-yellow-200 bg-yellow-50 mb-4"
      >
        <div class="card-body">
          <div class="flex items-start">
            <AlertCircle
              class="w-5 h-5 text-yellow-500 mt-0.5 mr-3 flex-shrink-0"
            />
            <div>
              <h3 class="text-yellow-800 font-medium">
                Contas Nao Encontradas no Arquivo de Producao
              </h3>
              <p class="text-yellow-700 mt-2">
                Infelizmente {{ comparisonResult.contas_nao_encontradas.length }}
                conta(s) nao foi/foram encontrada(s) no arquivo de producao:
              </p>
              <ul class="text-yellow-700 mt-2 ml-4">
                <li
                  v-for="(conta, index) in comparisonResult.contas_nao_encontradas"
                  :key="index"
                  class="list-disc font-mono"
                >
                  {{ conta }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Paginação por Fatura -->
      <div
        v-if="faturasComparadas.length > 0 && faturaAtual"
        class="card"
      >
        <!-- Navegação entre faturas -->
        <div class="card-header">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold">
                <span v-if="faturaAtual.conta_cliente === 'HEADER'">Header (Tipo 00)</span>
                <span v-else>
                  Fatura: CPS {{ faturaAtual.cps_fatura }} | Conta {{ faturaAtual.conta_cliente }}
                </span>
              </h3>
              <p class="text-sm text-gray-500 mt-1">
                {{ faturaAtual.total_linhas }} linhas |
                <span class="text-red-600">{{ faturaAtual.linhas_com_diferencas }} com diferenças</span> |
                <span class="text-green-600">{{ faturaAtual.linhas_identicas }} idênticas</span>
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button
                class="px-3 py-1 rounded border text-sm"
                :class="paginaFaturaAtual > 0 ? 'bg-white hover:bg-gray-50 cursor-pointer' : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
                :disabled="paginaFaturaAtual <= 0"
                @click="faturaAnterior"
              >
                Anterior
              </button>
              <span class="text-sm font-medium px-2">
                {{ paginaFaturaAtual + 1 }} / {{ totalFaturas }}
              </span>
              <button
                class="px-3 py-1 rounded border text-sm"
                :class="paginaFaturaAtual < totalFaturas - 1 ? 'bg-white hover:bg-gray-50 cursor-pointer' : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
                :disabled="paginaFaturaAtual >= totalFaturas - 1"
                @click="proximaFatura"
              >
                Próxima
              </button>
            </div>
          </div>
        </div>
        <div class="card-body">
          <!-- Controles de Seleção -->
          <div class="flex justify-between items-center mb-4 pb-3 border-b border-gray-200">
            <span class="text-sm text-gray-500">
              {{ totalErrosSelecionados }} de {{ totalErrosDisponiveis }} diferenças selecionadas para o relatório
            </span>
            <div class="flex gap-2">
              <button
                @click="toggleTodosDaFatura"
                class="text-xs px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                {{ todosDaFaturaSelecionados ? 'Desmarcar Fatura' : 'Selecionar Fatura' }}
              </button>
              <button
                @click="toggleTodosErros"
                class="text-xs px-3 py-1 rounded border border-blue-300 text-blue-700 hover:bg-blue-50 transition-colors"
              >
                {{ todosErrosSelecionados ? 'Desmarcar Todos' : 'Selecionar Todos' }}
              </button>
            </div>
          </div>

          <div class="space-y-6">
            <div
              v-for="(
                diferenca, index
              ) in faturaAtual.diferencas_por_linha"
              :key="index"
              :class="[
                'border rounded-lg p-4 transition-all',
                isErroSelecionado(paginaFaturaAtual, index)
                  ? 'border-gray-200'
                  : 'border-dashed border-gray-300 opacity-50'
              ]"
            >
              <div class="flex justify-between items-center mb-3">
                <div class="flex items-center gap-3">
                  <label class="flex items-center cursor-pointer" @click.stop>
                    <input
                      type="checkbox"
                      :checked="isErroSelecionado(paginaFaturaAtual, index)"
                      @change="toggleErroSelecionado(paginaFaturaAtual, index)"
                      class="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
                    />
                  </label>
                  <h4 class="font-semibold text-gray-900">
                    Linha {{ diferenca.numero_linha }} -
                    {{ diferenca.tipo_registro }}
                  </h4>
                  <!-- Badge de criticidade -->
                  <span
                    v-if="linhaTemCritico(diferenca)"
                    :class="['px-2 py-0.5 text-xs font-bold rounded-full ml-2', badgeClasses('CRITICO')]"
                  >
                    {{ badgeTexto('CRITICO') }}
                  </span>
                  <span
                    v-else
                    :class="['px-2 py-0.5 text-xs font-medium rounded-full ml-2', badgeClasses('ADVERTENCIA')]"
                  >
                    {{ badgeTexto('ADVERTENCIA') }}
                  </span>
                </div>
                <span
                  class="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full"
                >
                  {{ diferenca.total_diferencas }} diferença(s)
                </span>
              </div>

              <!-- Toggle de diff colorido -->
              <div class="flex items-center justify-end mb-1">
                <label class="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer select-none">
                  <input type="checkbox" v-model="diffColoridoAtivo" class="w-3 h-3 rounded" />
                  Diff colorido
                </label>
              </div>

              <!-- Visualização das Linhas -->
              <div class="space-y-1 mb-4 text-sm">
                <div v-if="diferenca.linha_numeracao">
                  <span class="text-gray-600 text-xs">Campos:</span>
                  <div
                    :data-ref="`pc-numeracao-linha-${paginaFaturaAtual}-${index}`"
                    class="bg-blue-50 p-2 rounded border overflow-x-auto text-blue-800 font-semibold font-mono relative"
                    style="white-space: pre"
                  >
                    <span v-if="campoDestacado?.linhaIndex === index" class="campo-highlight-overlay" :style="getHighlightStyle(`pc-numeracao-linha-${paginaFaturaAtual}-${index}`, diferenca.linha_numeracao)"></span>
                    {{ diferenca.linha_numeracao }}
                  </div>
                </div>

                <div>
                  <span class="text-gray-600 text-xs">Produção (Lote):</span>
                  <DiffLinha
                    :linha="diferenca.arquivo_base_linha"
                    :outra-linha="diferenca.arquivo_validado_linha"
                    tipo="base"
                    :diff-ativo="diffColoridoAtivo"
                    :data-ref="`pc-base-linha-${paginaFaturaAtual}-${index}`"
                    bg-class="bg-gray-50 cursor-help hover:bg-blue-50 transition-colors relative"
                    :highlight-overlay="campoDestacado?.linhaIndex === index"
                    :highlight-style="getHighlightStyle(`pc-base-linha-${paginaFaturaAtual}-${index}`, diferenca.arquivo_base_linha)"
                    @scroll="sincronizarScroll($event, `pc-validado-linha-${paginaFaturaAtual}-${index}`, `pc-numeracao-linha-${paginaFaturaAtual}-${index}`)"
                    @mousemove="mostrarTooltipThrottled($event, diferenca, diferenca.arquivo_base_linha, 'base')"
                    @mouseleave="esconderTooltip"
                  />
                </div>
                <div>
                  <span class="text-gray-600 text-xs">Seu Arquivo:</span>
                  <DiffLinha
                    :linha="diferenca.arquivo_validado_linha"
                    :outra-linha="diferenca.arquivo_base_linha"
                    tipo="comparado"
                    :diff-ativo="diffColoridoAtivo"
                    :data-ref="`pc-validado-linha-${paginaFaturaAtual}-${index}`"
                    bg-class="bg-gray-50 cursor-help hover:bg-blue-50 transition-colors relative"
                    :highlight-overlay="campoDestacado?.linhaIndex === index"
                    :highlight-style="getHighlightStyle(`pc-validado-linha-${paginaFaturaAtual}-${index}`, diferenca.arquivo_validado_linha)"
                    @scroll="sincronizarScroll($event, `pc-base-linha-${paginaFaturaAtual}-${index}`, `pc-numeracao-linha-${paginaFaturaAtual}-${index}`)"
                    @mousemove="mostrarTooltipThrottled($event, diferenca, diferenca.arquivo_validado_linha, 'validado')"
                    @mouseleave="esconderTooltip"
                  />
                </div>
              </div>

              <!-- Diferenças por Campo -->
              <div class="space-y-2">
                <h5 class="font-medium text-gray-700">
                  Campos com Diferenças:
                </h5>
                <div class="grid gap-2">
                  <div
                    v-for="(campo, campIndex) in diferenca.diferencas_campos"
                    :key="campIndex"
                    :class="[
                      'p-3 rounded-lg border-l-4',
                      campo.tipo_diferenca &&
                      campo.tipo_diferenca.startsWith('CALCULO_')
                        ? 'bg-orange-50 border-orange-400'
                        : 'bg-red-50 border-red-400',
                    ]"
                  >
                    <div class="flex justify-between items-start">
                      <div class="flex-1">
                        <div class="flex items-center">
                          <span
                            class="font-medium cursor-pointer hover:text-blue-700 hover:underline transition-colors"
                            title="Clique para destacar na linha"
                            @click="destacarCampoNaLinha(index, campo)"
                          >
                            Campo
                            {{
                              (campo.sequencia_campo || 0)
                                .toString()
                                .padStart(2, "0")
                            }}
                            - {{ campo.nome_campo }}
                          </span>
                          <span
                            v-if="
                              campo.tipo_diferenca &&
                              campo.tipo_diferenca.startsWith('CALCULO_')
                            "
                            class="ml-2 px-2 py-1 text-xs bg-orange-200 text-orange-800 rounded-full"
                          >
                            Calculo do imposto
                          </span>
                          <span
                            v-else-if="campo.tipo_diferenca"
                            class="ml-2 px-2 py-1 text-xs bg-red-200 text-red-800 rounded-full"
                          >
                            {{ campo.tipo_diferenca }}
                          </span>
                          <!-- Badge SEFAZ -->
                          <span
                            :class="['ml-2 px-2 py-0.5 text-xs font-semibold rounded-full', badgeClasses(classificarCampo(campo))]"
                          >
                            {{ badgeTexto(classificarCampo(campo)) }}
                          </span>
                        </div>
                        <span class="text-sm text-gray-600">
                          (Pos {{ campo.posicao_inicio }}-{{
                            campo.posicao_fim
                          }})
                        </span>
                      </div>
                    </div>

                    <div
                      v-if="
                        campo.tipo_diferenca &&
                        campo.tipo_diferenca.startsWith('CALCULO_')
                      "
                      class="mt-3 p-3 bg-orange-100 rounded"
                    >
                      <h6 class="font-semibold text-orange-800 mb-2">
                        Detalhes do Calculo:
                      </h6>
                      <div class="text-sm text-orange-900 font-mono">
                        {{ campo.descricao }}
                      </div>
                    </div>

                    <div
                      v-else-if="campo.descricao"
                      class="mt-2 p-2 bg-gray-100 rounded"
                    >
                      <div class="text-sm text-gray-700">
                        {{ campo.descricao }}
                      </div>
                    </div>

                    <div
                      v-if="
                        !campo.tipo_diferenca ||
                        !campo.tipo_diferenca.startsWith('CALCULO_')
                      "
                      class="mt-2 text-sm"
                    >
                      <div class="grid grid-cols-2 gap-2">
                        <div class="text-gray-600">
                          Produção:
                          <span class="font-mono bg-white px-1 rounded">{{
                            campo.valor_base
                          }}</span>
                        </div>
                        <div class="text-gray-600">
                          Seu arquivo:
                          <span class="font-mono bg-white px-1 rounded">{{
                            campo.valor_validado
                          }}</span>
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

      <!-- Sem diferenças -->
      <div v-else class="card border-green-200 bg-green-50">
        <div class="card-body text-center py-8">
          <CheckCircle class="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h3 class="text-green-800 font-medium text-lg">
            Arquivos idênticos!
          </h3>
          <p class="text-green-700 mt-1">
            Nenhuma diferença encontrada entre os arquivos.
          </p>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="card border-red-200 bg-red-50 max-w-4xl mx-auto">
      <div class="card-body">
        <div class="flex items-start">
          <AlertCircle class="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 class="text-red-800 font-medium">Erro</h3>
            <p class="text-red-700 mt-1">{{ error }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Tooltip Flutuante -->
    <div
      v-if="tooltipInfo.visible && tooltipInfo.campo"
      class="fixed z-50 px-4 py-3 bg-gray-900 text-white text-sm rounded-lg shadow-xl pointer-events-none border border-gray-700"
      :style="{
        left: tooltipInfo.x + 'px',
        top: tooltipInfo.y + 'px',
        maxWidth: '320px',
        minWidth: '280px',
      }"
    >
      <div class="space-y-2">
        <div
          class="font-bold text-blue-300 border-b border-gray-700 pb-1 flex items-center justify-between"
        >
          <span>{{ tooltipInfo.campo.nome }}</span>
          <span
            :class="
              tooltipInfo.tipoLinha === 'base'
                ? 'bg-green-700 text-green-200'
                : 'bg-orange-700 text-orange-200'
            "
            class="px-2 py-1 rounded text-xs font-mono"
          >
            {{ tooltipInfo.tipoLinha === "base" ? "PRODUÇÃO" : "SEU ARQUIVO" }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span class="text-gray-400">Posição:</span>
            <span class="text-white font-mono"
              >{{ tooltipInfo.campo.posicao_inicio }}-{{
                tooltipInfo.campo.posicao_fim
              }}</span
            >
          </div>
          <div>
            <span class="text-gray-400">Campo:</span>
            <span class="text-yellow-300 font-mono">{{
              tooltipInfo.indice.toString().padStart(2, "0")
            }}</span>
          </div>
          <div>
            <span class="text-gray-400">Tipo:</span>
            <span class="text-green-300">{{ tooltipInfo.campo.tipo }}</span>
          </div>
          <div v-if="tooltipInfo.campo.obrigatorio">
            <span class="text-gray-400">Status:</span>
            <span class="text-red-300">Obrigatório</span>
          </div>
        </div>

        <div
          v-if="tooltipInfo.valor.trim()"
          class="border-t border-gray-700 pt-2"
        >
          <div class="text-gray-400 text-xs mb-1">Valor atual:</div>
          <div
            class="bg-gray-800 p-2 rounded font-mono text-xs break-all text-cyan-300"
          >
            "{{ tooltipInfo.valor.trim() }}"
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  AlertCircle,
  CheckCircle,
  CheckCircle2,
  Download,
  Loader2,
  Printer,
  RotateCcw,
  Upload,
} from "lucide-vue-next";
import { computed, onMounted, ref, nextTick } from "vue";
import api from "../services/api";
import localStorageService from "../services/localStorage";
import DiffLinha from "../components/DiffLinha.vue";
import { classificarCampo, linhaTemCritico, badgeClasses, badgeTexto } from "../utils/criticidade";
import jsPDF from "jspdf";
import "jspdf-autotable";

// Config
const config = ref({
  lotes: [],
  layout_file: "",
  layout_exists: false,
  sheet_index: 0,
});
const configLoaded = ref(false);

// Form
const selectedLote = ref("");
const userFile = ref(null);
const userFileInput = ref(null);
const modoProducao = ref("lote");
const producaoFile = ref(null); // mantido para reset

// Upload de lote
const loteUploadInput = ref(null);
const uploadingLote = ref(false);
const loteUploadProgress = ref("");
const loteUploadResult = ref(null);
const loteUploadError = ref("");

// State
const isLoading = ref(false);
const error = ref("");
const comparisonResult = ref(null);
const reportText = ref("");
const timestamp = ref("");
const layoutData = ref({ campos: [] });
const paginaFaturaAtual = ref(0);

// Estado para destaque de campo na linha
const campoDestacado = ref(null);
let highlightTimeout = null;

// Diff colorido
const diffColoridoAtivo = ref(true);

// Estado para seleção de erros no relatório
// Map: "faturaIndex-diffIndex" => true
const errosSelecionados = ref(new Set());

// Tooltip
const tooltipInfo = ref({
  visible: false,
  x: 0,
  y: 0,
  campo: null,
  valor: "",
  indice: 0,
  posicaoExata: 0,
  tipoLinha: "base",
});

// Computed
const hasResults = computed(() => comparisonResult.value !== null);
const canSubmit = computed(() => {
  const temArquivoUsuario = !!userFile.value;
  const temLayoutConfigurado = config.value.layout_exists;
  const temLoteSelecionado = !!selectedLote.value;
  return temArquivoUsuario && temLayoutConfigurado && temLoteSelecionado;
});

const taxaIdentidadeClass = computed(() => {
  const taxa = comparisonResult.value?.taxa_identidade || 0;
  if (taxa >= 95) return "text-green-600";
  if (taxa >= 80) return "text-yellow-600";
  return "text-red-600";
});

// Paginação por fatura
const faturasComparadas = computed(() => comparisonResult.value?.faturas_comparadas || []);
const totalFaturas = computed(() => faturasComparadas.value.length);
const faturaAtual = computed(() => faturasComparadas.value[paginaFaturaAtual.value] || null);

function irParaFatura(index) {
  if (index >= 0 && index < totalFaturas.value) {
    paginaFaturaAtual.value = index;
  }
}
function faturaAnterior() { irParaFatura(paginaFaturaAtual.value - 1); }
function proximaFatura() { irParaFatura(paginaFaturaAtual.value + 1); }

/**
 * Retorna todas as linhas da fatura selecionada (para visualização completa).
 * Filtra todas_linhas pelo range de linhas da fatura atual.
 */
const linhasFaturaCompleta = computed(() => {
  const fatura = faturaAtual.value;
  if (!fatura || !todasLinhas.value?.length) return [];
  return todasLinhas.value.filter(
    (l) =>
      l.numero_linha >= fatura.linhaInicio && l.numero_linha <= fatura.linhaFim,
  );
});

// Load config
async function loadConfig() {
  try {
    const response = await api.get("/printcenter/config");
    config.value = response.data;
    // Se tem lotes disponíveis, default para modo lote
    if (config.value.lotes.length > 0) {
      modoProducao.value = "lote";
    }
  } catch (err) {
    console.error("Erro ao carregar configuração PrintCenter:", err);
    error.value =
      "Erro ao carregar configuração do PrintCenter. Verifique se a pasta printcenter/ existe.";
  } finally {
    configLoaded.value = true;
  }
}

onMounted(loadConfig);

// File handler
function handleUserFileChange(event) {
  userFile.value = event.target.files[0];
  error.value = "";
}

// Upload de lote (salva no servidor)
async function handleLoteUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  uploadingLote.value = true;
  loteUploadError.value = "";
  loteUploadResult.value = null;
  loteUploadProgress.value = `${(file.size / (1024 * 1024)).toFixed(1)}MB`;

  try {
    const formData = new FormData();
    formData.append("arquivo", file);

    const response = await api.post("/printcenter/upload-lote", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 600000, // 10 minutos para arquivos muito grandes
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
          loteUploadProgress.value = `${percent}% de ${(progressEvent.total / (1024 * 1024)).toFixed(1)}MB`;
        }
      },
    });

    loteUploadResult.value = response.data;

    // Recarregar config para atualizar lista de lotes
    await loadConfig();

    // Selecionar automaticamente o lote que acabou de ser enviado
    if (response.data.arquivo) {
      selectedLote.value = response.data.arquivo;
      modoProducao.value = "lote";
    }
  } catch (err) {
    console.error("Erro no upload do lote:", err);
    if (err.response?.status === 504 || err.code === 'ECONNABORTED') {
      loteUploadError.value = "Timeout no upload. Tente novamente ou coloque o arquivo diretamente na pasta printcenter/lotes/ no servidor.";
    } else {
      loteUploadError.value = err.response?.data?.detail || err.message || "Erro ao enviar arquivo";
    }
  } finally {
    uploadingLote.value = false;
    // Limpar o input para permitir re-upload do mesmo arquivo
    if (loteUploadInput.value) loteUploadInput.value.value = "";
  }
}

// Main comparison
async function handleComparison() {
  if (!canSubmit.value) return;

  isLoading.value = true;
  error.value = "";

  try {
    const formData = new FormData();
    formData.append("arquivo_usuario", userFile.value);
    formData.append("lote_arquivo", selectedLote.value);

    const response = await api.post("/printcenter/comparar", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    comparisonResult.value = response.data.resultado_comparacao;
    reportText.value = response.data.relatorio_texto;
    timestamp.value = response.data.timestamp;
    layoutData.value = response.data.layout;
    paginaFaturaAtual.value = 0;

    // Inicializar todos os erros como selecionados
    nextTick(() => inicializarSelecaoErros());
  } catch (err) {
    console.error("Erro na comparação:", err);
    if (err.response?.status === 504 || err.code === 'ECONNABORTED') {
      error.value = "Timeout: o servidor demorou demais para responder. Tente novamente.";
    } else {
      error.value = err.response?.data?.detail || err.message || "Erro interno do servidor";
    }
  } finally {
    isLoading.value = false;
  }
}

// === Funções de destaque de campo na linha ===

function destacarCampoNaLinha(linhaIndex, campo) {
  if (highlightTimeout) clearTimeout(highlightTimeout);

  campoDestacado.value = {
    linhaIndex,
    posicao_inicio: campo.posicao_inicio,
    posicao_fim: campo.posicao_fim,
    nome_campo: campo.nome_campo,
  };

  const prefixo = `pc-base-linha-${paginaFaturaAtual.value}-${linhaIndex}`;
  const baseEl = document.querySelector(`[data-ref="${prefixo}"]`);
  if (baseEl) {
    const style = window.getComputedStyle(baseEl);
    const medidor = document.createElement("span");
    medidor.style.font = style.font;
    medidor.style.fontSize = style.fontSize;
    medidor.style.fontFamily = style.fontFamily;
    medidor.style.visibility = "hidden";
    medidor.style.position = "absolute";
    medidor.style.whiteSpace = "pre";
    document.body.appendChild(medidor);

    const linhaTexto = baseEl.textContent;
    const segments = linhaTexto.split("|");
    let charPos = 0;
    const seq = campo.sequencia_campo || 0;
    for (let i = 0; i < seq - 1 && i < segments.length; i++) {
      charPos += segments[i].length + 1;
    }
    medidor.textContent = linhaTexto.substring(0, charPos);
    const scrollTarget = medidor.offsetWidth - 100;
    document.body.removeChild(medidor);

    baseEl.scrollLeft = Math.max(0, scrollTarget);

    const validadoEl = document.querySelector(`[data-ref="pc-validado-linha-${paginaFaturaAtual.value}-${linhaIndex}"]`);
    const numeracaoEl = document.querySelector(`[data-ref="pc-numeracao-linha-${paginaFaturaAtual.value}-${linhaIndex}"]`);
    if (validadoEl) validadoEl.scrollLeft = baseEl.scrollLeft;
    if (numeracaoEl) numeracaoEl.scrollLeft = baseEl.scrollLeft;

    baseEl.closest(".border")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  highlightTimeout = setTimeout(() => {
    campoDestacado.value = null;
  }, 4000);
}

function getHighlightStyle(refName, linhaTexto) {
  if (!campoDestacado.value || !linhaTexto) return { display: "none" };

  const campo = campoDestacado.value;
  const el = document.querySelector(`[data-ref="${refName}"]`);
  if (!el) return { display: "none" };

  const style = window.getComputedStyle(el);
  const medidor = document.createElement("span");
  medidor.style.font = style.font;
  medidor.style.fontSize = style.fontSize;
  medidor.style.fontFamily = style.fontFamily;
  medidor.style.visibility = "hidden";
  medidor.style.position = "absolute";
  medidor.style.whiteSpace = "pre";
  document.body.appendChild(medidor);

  const posInicio = campo.posicao_inicio - 1;
  const posFim = campo.posicao_fim;

  medidor.textContent = linhaTexto.substring(0, posInicio);
  const left = medidor.offsetWidth;
  medidor.textContent = linhaTexto.substring(posInicio, posFim);
  const width = medidor.offsetWidth;
  document.body.removeChild(medidor);

  return {
    position: "absolute",
    left: left + "px",
    top: "0",
    width: width + "px",
    height: "100%",
    backgroundColor: "rgba(59, 130, 246, 0.25)",
    borderLeft: "2px solid rgb(59, 130, 246)",
    borderRight: "2px solid rgb(59, 130, 246)",
    pointerEvents: "none",
    zIndex: "10",
    transition: "all 0.3s ease",
    animation: "highlight-pulse 1.5s ease-in-out infinite",
  };
}

// === Funções de seleção de erros para o relatório ===

function getErroKey(faturaIndex, diffIndex) {
  return `${faturaIndex}-${diffIndex}`;
}

function isErroSelecionado(faturaIndex, diffIndex) {
  return errosSelecionados.value.has(getErroKey(faturaIndex, diffIndex));
}

function toggleErroSelecionado(faturaIndex, diffIndex) {
  const key = getErroKey(faturaIndex, diffIndex);
  const newSet = new Set(errosSelecionados.value);
  if (newSet.has(key)) {
    newSet.delete(key);
  } else {
    newSet.add(key);
  }
  errosSelecionados.value = newSet;
}

function toggleTodosDaFatura() {
  if (!faturaAtual.value?.diferencas_por_linha) return;
  const newSet = new Set(errosSelecionados.value);
  const allSelected = todosDaFaturaSelecionados.value;

  faturaAtual.value.diferencas_por_linha.forEach((_, idx) => {
    const key = getErroKey(paginaFaturaAtual.value, idx);
    if (allSelected) {
      newSet.delete(key);
    } else {
      newSet.add(key);
    }
  });
  errosSelecionados.value = newSet;
}

function toggleTodosErros() {
  if (!faturasComparadas.value?.length) return;
  const newSet = new Set(errosSelecionados.value);
  const allSelected = todosErrosSelecionados.value;

  faturasComparadas.value.forEach((fatura, fatIdx) => {
    if (fatura.diferencas_por_linha) {
      fatura.diferencas_por_linha.forEach((_, diffIdx) => {
        const key = getErroKey(fatIdx, diffIdx);
        if (allSelected) {
          newSet.delete(key);
        } else {
          newSet.add(key);
        }
      });
    }
  });
  errosSelecionados.value = newSet;
}

const todosDaFaturaSelecionados = computed(() => {
  if (!faturaAtual.value?.diferencas_por_linha) return false;
  return faturaAtual.value.diferencas_por_linha.every((_, idx) =>
    isErroSelecionado(paginaFaturaAtual.value, idx)
  );
});

const todosErrosSelecionados = computed(() => {
  if (!faturasComparadas.value?.length) return false;
  return errosSelecionados.value.size === totalErrosDisponiveis.value;
});

const totalErrosSelecionados = computed(() => errosSelecionados.value.size);

const totalErrosDisponiveis = computed(() => {
  if (!faturasComparadas.value?.length) return 0;
  let total = 0;
  faturasComparadas.value.forEach((fatura) => {
    total += fatura.diferencas_por_linha?.length || 0;
  });
  return total;
});

function inicializarSelecaoErros() {
  const allKeys = new Set();
  faturasComparadas.value.forEach((fatura, fatIdx) => {
    if (fatura.diferencas_por_linha) {
      fatura.diferencas_por_linha.forEach((_, diffIdx) => {
        allKeys.add(getErroKey(fatIdx, diffIdx));
      });
    }
  });
  errosSelecionados.value = allKeys;
}

// === Download de relatório em PDF bonito ===

function downloadReportPDF() {
  if (!comparisonResult.value) return;

  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 14;
  let y = 20;

  // === CAPA / HEADER ===
  doc.setFillColor(30, 58, 138); // blue-900
  doc.rect(0, 0, pageWidth, 45, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(22);
  doc.setFont("helvetica", "bold");
  doc.text("Relatório de Comparação", pageWidth / 2, 18, { align: "center" });

  doc.setFontSize(11);
  doc.setFont("helvetica", "normal");
  doc.text("PrintCenter - Validador de Documentos", pageWidth / 2, 28, { align: "center" });

  doc.setFontSize(9);
  doc.text(`Gerado em: ${new Date().toLocaleString("pt-BR")}`, pageWidth / 2, 37, { align: "center" });

  y = 55;

  // === ESTATÍSTICAS ===
  doc.setTextColor(30, 58, 138);
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text("Resumo da Comparação", margin, y);
  y += 3;

  doc.setDrawColor(30, 58, 138);
  doc.setLineWidth(0.5);
  doc.line(margin, y, pageWidth - margin, y);
  y += 8;

  const stats = [
    ["Total de Linhas Comparadas", String(comparisonResult.value.total_linhas_comparadas || 0)],
    ["Linhas Idênticas", String(comparisonResult.value.linhas_identicas || 0)],
    ["Linhas com Diferenças", String(comparisonResult.value.linhas_com_diferencas || 0)],
    ["Taxa de Identidade", `${(comparisonResult.value.taxa_identidade || 0).toFixed(2)}%`],
    ["Diferenças incluídas neste relatório", `${totalErrosSelecionados.value} de ${totalErrosDisponiveis.value}`],
  ];

  doc.autoTable({
    startY: y,
    head: [["Métrica", "Valor"]],
    body: stats,
    margin: { left: margin, right: margin },
    theme: "grid",
    headStyles: {
      fillColor: [30, 58, 138],
      textColor: 255,
      fontStyle: "bold",
      fontSize: 10,
    },
    bodyStyles: {
      fontSize: 9,
      textColor: [50, 50, 50],
    },
    alternateRowStyles: {
      fillColor: [240, 245, 255],
    },
    columnStyles: {
      0: { fontStyle: "bold", cellWidth: 100 },
      1: { halign: "center" },
    },
  });

  y = doc.lastAutoTable.finalY + 12;

  // === CONTAS NÃO ENCONTRADAS ===
  if (comparisonResult.value.contas_nao_encontradas?.length > 0) {
    if (y > 250) { doc.addPage(); y = 20; }

    doc.setTextColor(180, 83, 9);
    doc.setFontSize(12);
    doc.setFont("helvetica", "bold");
    doc.text("Contas Não Encontradas no Arquivo de Produção", margin, y);
    y += 8;

    doc.setTextColor(80, 80, 80);
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    comparisonResult.value.contas_nao_encontradas.forEach((conta) => {
      if (y > 275) { doc.addPage(); y = 20; }
      doc.text(`• ${conta}`, margin + 4, y);
      y += 5;
    });
    y += 8;
  }

  // === DIFERENÇAS POR FATURA (apenas selecionadas) ===
  faturasComparadas.value.forEach((fatura, fatIdx) => {
    const diferencasFiltradas = (fatura.diferencas_por_linha || []).filter(
      (_, diffIdx) => isErroSelecionado(fatIdx, diffIdx)
    );

    if (diferencasFiltradas.length === 0) return;

    if (y > 240) { doc.addPage(); y = 20; }

    // Header da fatura
    doc.setFillColor(239, 246, 255); // blue-50
    doc.rect(margin, y - 5, pageWidth - margin * 2, 12, "F");

    doc.setTextColor(30, 58, 138);
    doc.setFontSize(11);
    doc.setFont("helvetica", "bold");

    let tituloFatura = "";
    if (fatura.conta_cliente === "HEADER") {
      tituloFatura = "Header (Tipo 00)";
    } else {
      tituloFatura = `Fatura: CPS ${fatura.cps_fatura} | Conta ${fatura.conta_cliente}`;
    }
    doc.text(tituloFatura, margin + 2, y + 2);

    doc.setFontSize(8);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(100, 100, 100);
    doc.text(
      `${fatura.total_linhas} linhas | ${fatura.linhas_com_diferencas} com diferenças | ${diferencasFiltradas.length} no relatório`,
      pageWidth - margin - 2,
      y + 2,
      { align: "right" }
    );
    y += 14;

    // Tabela de diferenças da fatura
    const tableBody = [];

    diferencasFiltradas.forEach((dif) => {
      if (dif.diferencas_campos?.length > 0) {
        dif.diferencas_campos.forEach((campo) => {
          const seq = (campo.sequencia_campo || 0).toString().padStart(2, "0");
          const isCalculo = campo.tipo_diferenca?.startsWith("CALCULO_");

          tableBody.push([
            String(dif.numero_linha),
            dif.tipo_registro,
            `${seq} - ${campo.nome_campo}`,
            isCalculo ? (campo.tipo_diferenca || "") : (campo.valor_base || ""),
            isCalculo ? (campo.descricao || "").substring(0, 60) : (campo.valor_validado || ""),
            isCalculo ? "Cálculo" : (campo.tipo_diferenca || "Diferença"),
          ]);
        });
      }
    });

    if (tableBody.length > 0) {
      doc.autoTable({
        startY: y,
        head: [["Linha", "Tipo", "Campo", "Produção / Tipo", "Seu Arquivo / Detalhe", "Categoria"]],
        body: tableBody,
        margin: { left: margin, right: margin },
        theme: "striped",
        headStyles: {
          fillColor: [59, 130, 246],
          textColor: 255,
          fontStyle: "bold",
          fontSize: 7,
        },
        bodyStyles: {
          fontSize: 7,
          textColor: [50, 50, 50],
          cellPadding: 2,
        },
        columnStyles: {
          0: { cellWidth: 14, halign: "center" },
          1: { cellWidth: 14, halign: "center" },
          2: { cellWidth: 42 },
          3: { cellWidth: 38 },
          4: { cellWidth: 48 },
          5: { cellWidth: 20, halign: "center" },
        },
        didParseCell: function (data) {
          if (data.section === "body" && data.column.index === 5) {
            if (data.cell.raw === "Cálculo") {
              data.cell.styles.fillColor = [255, 237, 213]; // orange-100
              data.cell.styles.textColor = [154, 52, 18]; // orange-800
            } else {
              data.cell.styles.fillColor = [254, 226, 226]; // red-100
              data.cell.styles.textColor = [153, 27, 27]; // red-800
            }
          }
        },
      });

      y = doc.lastAutoTable.finalY + 10;
    }
  });

  // === RODAPÉ EM TODAS AS PÁGINAS ===
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    const pageHeight = doc.internal.pageSize.getHeight();

    doc.setDrawColor(200, 200, 200);
    doc.setLineWidth(0.3);
    doc.line(margin, pageHeight - 15, pageWidth - margin, pageHeight - 15);

    doc.setFontSize(7);
    doc.setTextColor(150, 150, 150);
    doc.setFont("helvetica", "normal");
    doc.text("Validador de Documentos - PrintCenter", margin, pageHeight - 8);
    doc.text(`Página ${i} de ${totalPages}`, pageWidth - margin, pageHeight - 8, { align: "right" });
  }

  doc.save(`printcenter_comparacao_${timestamp.value}.pdf`);
}

// Download report TXT
function downloadReport() {
  if (!reportText.value) return;
  const filename = `printcenter_comparacao_${timestamp.value}.txt`;
  localStorageService.downloadText(reportText.value, filename);
}

// Reset
function resetComparison() {
  comparisonResult.value = null;
  reportText.value = "";
  timestamp.value = "";
  userFile.value = null;
  producaoFile.value = null;
  loteUploadResult.value = null;
  loteUploadError.value = "";
  error.value = "";
  paginaFaturaAtual.value = 0;
  campoDestacado.value = null;
  errosSelecionados.value = new Set();
  if (userFileInput.value) userFileInput.value.value = "";
}

// Tooltip functions
function getCamposDoTipo(tipoRegistro) {
  if (!layoutData.value?.campos) return [];
  return layoutData.value.campos.filter((campo) => {
    const nomeCampo = campo.nome || "";
    return (
      nomeCampo.includes(`NFE${tipoRegistro}-`) ||
      nomeCampo.includes(`NFCOM${tipoRegistro}-`) ||
      (!nomeCampo.startsWith("NFE") && !nomeCampo.startsWith("NFCOM"))
    );
  });
}

function getCampoNaPosicaoMelhorada(event, tipoRegistro, linhaComBarras) {
  const campos = getCamposDoTipo(tipoRegistro);
  if (!campos.length || !linhaComBarras) return null;

  const elemento = event.target;
  const style = window.getComputedStyle(elemento);
  const scrollLeft = elemento.scrollLeft;
  const posicaoMouseReal = event.offsetX + scrollLeft;

  const medidor = document.createElement("span");
  medidor.style.font = style.font;
  medidor.style.fontSize = style.fontSize;
  medidor.style.fontFamily = style.fontFamily;
  medidor.style.visibility = "hidden";
  medidor.style.position = "absolute";
  medidor.style.whiteSpace = "pre";
  document.body.appendChild(medidor);

  try {
    const segments = linhaComBarras.split("|");
    let posicaoAcumulada = 0;

    for (let i = 0; i < segments.length - 1 && i < campos.length; i++) {
      const segmento = segments[i];
      medidor.textContent = segmento;
      const larguraSegmento = medidor.offsetWidth;
      medidor.textContent = "|";
      const larguraBarra = medidor.offsetWidth;

      const inicioSegmento = posicaoAcumulada;
      const fimSegmento = posicaoAcumulada + larguraSegmento;

      if (
        posicaoMouseReal >= inicioSegmento &&
        posicaoMouseReal <= fimSegmento
      ) {
        return {
          campo: campos[i],
          valor: segmento,
          indice: i + 1,
          posicaoExata: posicaoMouseReal - inicioSegmento,
        };
      }

      posicaoAcumulada = fimSegmento + larguraBarra;
    }
  } finally {
    document.body.removeChild(medidor);
  }

  return null;
}

function mostrarTooltip(event, diferenca, linha, tipoLinha = "base") {
  const campoInfo = getCampoNaPosicaoMelhorada(
    event,
    diferenca.tipo_registro,
    linha,
  );

  if (campoInfo) {
    const tooltipX = event.clientX;
    const tooltipY = event.clientY;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const tooltipWidth = 320;
    const tooltipHeight = 200;

    let finalX = tooltipX;
    let finalY = tooltipY;

    if (finalX + tooltipWidth > viewportWidth)
      finalX = viewportWidth - tooltipWidth - 10;
    if (finalX < 10) finalX = 10;

    if (tipoLinha === "base") {
      finalY = tooltipY - tooltipHeight - 80;
      if (finalY < 10) finalY = tooltipY + 60;
    } else {
      finalY = tooltipY + 40;
      if (finalY + tooltipHeight > viewportHeight) {
        finalY = viewportHeight - tooltipHeight - 20;
        if (finalY < tooltipY + 10) finalY = tooltipY - tooltipHeight - 80;
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
      tipoLinha: tipoLinha,
    };
  }
}

function esconderTooltip() {
  if (tooltipThrottle) {
    clearTimeout(tooltipThrottle);
    tooltipThrottle = null;
  }
  tooltipInfo.value.visible = false;
}

let tooltipThrottle = null;
function mostrarTooltipThrottled(event, diferenca, linha, tipoLinha) {
  if (tooltipThrottle) clearTimeout(tooltipThrottle);
  tooltipThrottle = setTimeout(() => {
    mostrarTooltip(event, diferenca, linha, tipoLinha);
    tooltipThrottle = null;
  }, 50);
}

// Scroll sync
let scrollSyncing = false;
function sincronizarScroll(event, targetRefName, numeracaoRefName = null) {
  if (scrollSyncing) return;
  const target = document.querySelector(`[data-ref="${targetRefName}"]`);
  const numeracao = numeracaoRefName
    ? document.querySelector(`[data-ref="${numeracaoRefName}"]`)
    : null;

  if (target && target !== event.target) {
    scrollSyncing = true;
    target.scrollLeft = event.target.scrollLeft;
    if (numeracao) numeracao.scrollLeft = event.target.scrollLeft;
    setTimeout(() => {
      scrollSyncing = false;
    }, 10);
  }
}
</script>

<style scoped>
.file-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500;
}

.select-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500;
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

.cursor-help:hover {
  @apply text-blue-600 transition-colors duration-200;
}

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
