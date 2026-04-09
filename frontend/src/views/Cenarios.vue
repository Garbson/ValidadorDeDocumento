<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">
        Identificação de Cenários
      </h1>
      <p class="text-gray-600">
        Faça upload de um arquivo TXT para identificar os cenários de cada
        fatura
      </p>
    </div>

    <!-- Upload Form -->
    <div class="card max-w-4xl mx-auto" v-show="!hasResults">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <Search class="w-5 h-5 mr-2" />
          Upload de Arquivo
        </h2>
      </div>
      <div class="card-body space-y-6">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Arquivo de Faturas (TXT)
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="fileInput"
                type="file"
                accept=".txt"
                @change="handleFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo TXT com faturas (não necessita de layout Excel)
            </p>
          </div>

          <div class="flex justify-end">
            <button
              type="submit"
              :disabled="isLoading || !arquivo"
              class="btn-primary"
            >
              <template v-if="isLoading">
                <Loader2 class="w-4 h-4 mr-2 animate-spin" />
                Identificando...
              </template>
              <template v-else>
                <Search class="w-4 h-4 mr-2" />
                Identificar Cenários
              </template>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex justify-center items-center py-12">
      <div class="text-center">
        <Loader2 class="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
        <p class="text-gray-600">
          Analisando faturas e identificando cenários...
        </p>
      </div>
    </div>

    <!-- Results -->
    <div v-if="hasResults && !isLoading" class="space-y-6">
      <!-- Header de Resultados -->
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-900">Cenários Identificados</h2>
        <button @click="resetForm" class="btn-secondary">
          <RotateCcw class="w-4 h-4 mr-2" />
          Nova Análise
        </button>
      </div>

      <!-- Estatísticas Gerais -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-blue-600">
            {{ resultado.total_faturas }}
          </p>
          <p class="text-sm text-gray-600">Total de Faturas</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-cyan-600">
            {{ totalClientesUnicos }}
          </p>
          <p class="text-sm text-gray-600">Clientes Únicos</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-green-600">
            {{ resultado.cenarios_encontrados.length }}
          </p>
          <p class="text-sm text-gray-600">Cenários Encontrados</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-purple-600">
            {{ faturasFiltradas.length }}
          </p>
          <p class="text-sm text-gray-600">Faturas Filtradas</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-orange-600">
            {{ cenariosSelecionados.length || "Todos" }}
          </p>
          <p class="text-sm text-gray-600">Filtros Ativos</p>
        </div>
      </div>

      <!-- Cards de Cenários (filtros clicáveis - multi-seleção) -->
      <div class="card">
        <div class="card-header flex justify-between items-center">
          <h3 class="text-lg font-semibold">
            Selecione os Cenários para Filtrar
          </h3>
          <span
            v-if="cenariosSelecionados.length > 0"
            class="text-xs text-gray-500"
          >
            Mostrando faturas que contenham <strong>todos</strong> os cenários
            selecionados
          </span>
        </div>
        <div class="card-body">
          <div class="flex flex-wrap gap-3">
            <!-- Botão "Todos" (limpar filtros) -->
            <button
              @click="cenariosSelecionados = []"
              class="px-4 py-3 rounded-lg border-2 transition-all duration-200 text-sm font-medium"
              :class="
                cenariosSelecionados.length === 0
                  ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-md'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:bg-blue-50'
              "
            >
              <span class="block text-lg font-bold">{{
                resultado.total_faturas
              }}</span>
              Todos
            </button>

            <!-- Botão por cenário (toggle) -->
            <button
              v-for="cenario in resultado.cenarios_encontrados"
              :key="cenario"
              @click="toggleCenario(cenario)"
              class="px-4 py-3 rounded-lg border-2 transition-all duration-200 text-sm font-medium"
              :class="
                cenariosSelecionados.includes(cenario)
                  ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-md'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:bg-blue-50'
              "
            >
              <span class="block text-lg font-bold">{{
                resultado.contagem_por_cenario[cenario]
              }}</span>
              {{ cenario }}
            </button>
          </div>
        </div>
      </div>

      <!-- Busca por Campo -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold flex items-center">
            <Filter class="w-5 h-5 mr-2" />
            Busca por Campo do Layout
          </h3>
        </div>
        <div class="card-body space-y-4">
          <p class="text-sm text-gray-500">
            Digite o código do campo (ex:
            <code class="bg-gray-100 px-1 rounded">01.02</code>) para buscar
            faturas por valor específico.
          </p>

          <div class="flex flex-col md:flex-row gap-4">
            <!-- Input do código do campo -->
            <div class="flex-1">
              <label class="block text-sm font-medium text-gray-700 mb-1"
                >Código do Campo</label
              >
              <input
                v-model="campoBusca"
                type="text"
                placeholder="Ex: 01.02"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
                @input="onCampoInput"
              />
            </div>

            <!-- Info do campo encontrado -->
            <div
              v-if="campoEncontrado"
              class="flex-[2] bg-blue-50 border border-blue-200 rounded-lg p-3"
            >
              <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div>
                  <span class="text-gray-500">Nome:</span>
                  <span class="font-semibold text-blue-800 ml-1">{{
                    campoEncontrado.nome
                  }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Tipo:</span>
                  <span
                    class="font-mono ml-1"
                    :class="{
                      'text-green-700': campoEncontrado.tipo === 'TEXTO',
                      'text-blue-700': campoEncontrado.tipo === 'NUMERO',
                      'text-orange-700': campoEncontrado.tipo === 'DECIMAL',
                    }"
                    >{{ campoEncontrado.tipo }}</span
                  >
                </div>
                <div>
                  <span class="text-gray-500">Tamanho:</span>
                  <span class="font-mono ml-1">{{
                    campoEncontrado.tamanho
                  }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Posição:</span>
                  <span class="font-mono ml-1"
                    >{{ campoEncontrado.posicao_de }}-{{
                      campoEncontrado.posicao_ate
                    }}</span
                  >
                </div>
              </div>
            </div>
            <div
              v-else-if="campoBusca.length >= 4 && !campoEncontrado"
              class="flex-[2] bg-red-50 border border-red-200 rounded-lg p-3 flex items-center"
            >
              <span class="text-sm text-red-600"
                >Campo não encontrado no layout.</span
              >
            </div>
          </div>

          <!-- Valor para buscar -->
          <div
            v-if="campoEncontrado"
            class="flex flex-col md:flex-row gap-4 items-end"
          >
            <div class="flex-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Valor para Buscar
                <span class="text-gray-400 text-xs ml-1">(busca parcial)</span>
              </label>
              <input
                v-model="valorBusca"
                type="text"
                :placeholder="`Buscar no campo ${campoEncontrado.nome}...`"
                :maxlength="campoEncontrado.tamanho"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
                @keyup.enter="executarBuscaCampo"
              />
            </div>
            <button
              @click="executarBuscaCampo"
              :disabled="!valorBusca || isBuscandoCampo"
              class="btn-primary whitespace-nowrap"
            >
              <template v-if="isBuscandoCampo">
                <Loader2 class="w-4 h-4 mr-2 animate-spin" />
                Buscando...
              </template>
              <template v-else>
                <Search class="w-4 h-4 mr-2" />
                Buscar Faturas
              </template>
            </button>
            <button
              v-if="resultadoBuscaCampo"
              @click="limparBuscaCampo"
              class="btn-secondary whitespace-nowrap"
            >
              <X class="w-4 h-4 mr-2" />
              Limpar Busca
            </button>
          </div>

          <!-- Resultado da busca por campo -->
          <div v-if="resultadoBuscaCampo" class="mt-4">
            <div
              class="bg-green-50 border border-green-200 rounded-lg p-3 mb-3 flex items-center justify-between"
            >
              <span class="text-sm text-green-800">
                <strong>{{ resultadoBuscaCampo.total_encontradas }}</strong>
                fatura(s) encontrada(s) com
                <code class="bg-green-100 px-1 rounded">{{ campoBusca }}</code>
                =
                <code class="bg-green-100 px-1 rounded"
                  >"{{ valorBusca }}"</code
                >
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabela de Faturas -->
      <div class="card">
        <div class="card-header flex justify-between items-center">
          <h3 class="text-lg font-semibold">
            Faturas
            <span v-if="cenariosSelecionados.length" class="text-blue-600"
              >({{ cenariosSelecionados.join(" + ") }})</span
            >
            <span v-if="resultadoBuscaCampo" class="text-green-600 ml-2">
              | Campo {{ campoBusca }} = "{{ valorBusca }}"
            </span>
          </h3>
          <span class="text-sm text-gray-500"
            >{{ faturasFiltradas.length }} faturas</span
          >
        </div>
        <div class="card-body p-0">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    #
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Conta Cliente
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    CPS/Fatura
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    <div class="flex flex-col items-center gap-1">
                      <div>Sites</div>
                      <div>
                        <input
                          v-model="sitesFilter"
                          type="number"
                          class="rounded-xl w-20 h-8"
                        />
                      </div>
                    </div>
                  </th>
                  <th
                    v-if="resultadoBuscaCampo"
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-green-50"
                  >
                    {{ campoEncontrado?.nome || campoBusca }}
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Serviços
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Cenários
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Alíq. ICMS
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Isenção
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Retenção
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Débito Auto.
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Tipos Registro
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Linha Início
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Total Linhas
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr
                  v-for="(fatura, index) in faturasPaginadas"
                  :key="index"
                  class="hover:bg-gray-50"
                >
                  <td class="px-4 py-3 text-sm text-gray-500">
                    {{ (paginaAtual - 1) * itensPorPagina + index + 1 }}
                  </td>
                  <td class="px-4 py-3 text-sm font-mono text-gray-900">
                    {{ fatura.conta_cliente }}
                  </td>
                  <td class="px-4 py-3 text-sm font-mono text-gray-900">
                    {{ fatura.cps_fatura }}
                  </td>
                  <td class="px-4 py-3 text-sm text-center">
                    <span
                      class="inline-block px-2 py-1 rounded-full text-xs font-bold"
                      :class="
                        fatura.quantidade_sites > 1
                          ? 'bg-cyan-100 text-cyan-800'
                          : 'bg-gray-100 text-gray-600'
                      "
                    >
                      {{ fatura.quantidade_sites }}
                    </span>
                  </td>
                  <td
                    v-if="resultadoBuscaCampo"
                    class="px-4 py-3 text-sm font-mono text-green-700 bg-green-50 font-bold"
                  >
                    {{ fatura.valor_campo || "-" }}
                  </td>
                  <td class="px-4 py-3 text-sm">
                    <div
                      v-if="fatura.servicos && fatura.servicos.length"
                      class="space-y-1"
                    >
                      <div
                        v-for="servico in fatura.servicos"
                        :key="servico.sigla"
                        class="flex items-center gap-1"
                      >
                        <span
                          class="inline-block px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 font-mono"
                        >
                          {{ servico.sigla }}
                        </span>
                        <span
                          class="text-xs text-gray-700 truncate max-w-[150px]"
                          :title="servico.descricao"
                        >
                          {{ servico.descricao }}
                        </span>
                        <span
                          v-if="servico.valor"
                          class="text-[10px] font-mono text-emerald-700 font-semibold whitespace-nowrap"
                        >
                          {{ servico.valor }}
                        </span>
                      </div>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                  </td>
                  <td class="px-4 py-3 text-sm">
                    <span
                      v-for="cenario in fatura.cenarios"
                      :key="cenario"
                      class="inline-block px-2 py-1 mr-1 mb-1 rounded-full text-xs font-medium"
                      :class="cenarioClass(cenario)"
                    >
                      {{ cenario }}
                    </span>
                  </td>
                  <!-- Alíquota ICMS -->
                  <td class="px-4 py-3 text-sm font-mono">
                    <span
                      v-if="fatura.aliquota_icms"
                      class="inline-block px-2 py-1 rounded-full text-xs font-bold"
                      :class="
                        fatura.aliquota_icms === '0,00%'
                          ? 'bg-teal-100 text-teal-800'
                          : 'bg-blue-100 text-blue-800'
                      "
                    >
                      {{ fatura.aliquota_icms }}
                    </span>
                    <span v-else class="text-gray-400">—</span>
                  </td>
                  <!-- Isenção -->
                  <td class="px-4 py-3 text-sm">
                    <div v-if="fatura.isencao" class="space-y-1">
                      <span
                        class="inline-block px-2 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-800"
                      >
                        Isenta
                      </span>
                      <span
                        v-if="fatura.valor_isentos"
                        class="block text-xs font-mono text-teal-700 font-semibold"
                      >
                        {{ fatura.valor_isentos }}
                      </span>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                  </td>
                  <!-- Retenção -->
                  <td class="px-4 py-3 text-sm">
                    <div v-if="fatura.retencao" class="space-y-1">
                      <span
                        class="inline-block px-2 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800"
                      >
                        {{ fatura.retencao.percentual }}
                      </span>
                      <span class="block text-xs text-red-600">{{
                        fatura.retencao.tipo
                      }}</span>
                      <span
                        class="block text-xs font-mono text-red-700 font-semibold"
                      >
                        {{ fatura.retencao.valor }}
                      </span>
                      <!-- Detalhes PIS/CSSL/COFINS -->
                      <div
                        v-if="fatura.retencao.detalhes"
                        class="text-[10px] text-red-500 space-y-0.5 mt-1 border-t border-red-200 pt-1"
                      >
                        <div
                          v-for="(info, nome) in fatura.retencao.detalhes"
                          :key="nome"
                        >
                          {{ nome }}: {{ info.percentual }} = {{ info.valor }}
                        </div>
                      </div>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                  </td>
                  <td class="px-4 py-3 text-sm">
                    <span
                      v-if="fatura.debito_automatico"
                      class="inline-block px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"
                    >
                      Sim
                    </span>
                    <span v-else class="text-gray-400">Não</span>
                  </td>
                  <td class="px-4 py-3 text-sm font-mono text-gray-600">
                    {{ fatura.tipos_registro.join(", ") }}
                  </td>
                  <td class="px-4 py-3 text-sm text-gray-600">
                    {{ fatura.linha_inicio }}
                  </td>
                  <td class="px-4 py-3 text-sm text-gray-600">
                    {{ fatura.total_linhas }}
                  </td>
                </tr>
                <tr v-if="faturasFiltradas.length === 0">
                  <td
                    :colspan="resultadoBuscaCampo ? 15 : 14"
                    class="px-4 py-8 text-center text-gray-500"
                  >
                    Nenhuma fatura encontrada para os filtros selecionados.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Paginação -->
          <div
            v-if="totalPaginas > 1"
            class="flex items-center justify-between px-4 py-3 border-t border-gray-200"
          >
            <div class="text-sm text-gray-500">
              Mostrando {{ (paginaAtual - 1) * itensPorPagina + 1 }} a
              {{
                Math.min(paginaAtual * itensPorPagina, faturasFiltradas.length)
              }}
              de {{ faturasFiltradas.length }}
            </div>
            <div class="flex gap-2">
              <button
                @click="paginaAtual = Math.max(1, paginaAtual - 1)"
                :disabled="paginaAtual === 1"
                class="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
              >
                Anterior
              </button>
              <span class="px-3 py-1 text-sm text-gray-600">
                {{ paginaAtual }} / {{ totalPaginas }}
              </span>
              <button
                @click="paginaAtual = Math.min(totalPaginas, paginaAtual + 1)"
                :disabled="paginaAtual === totalPaginas"
                class="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
              >
                Próximo
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="card border-red-200 bg-red-50 max-w-4xl mx-auto">
      <div class="card-body">
        <p class="text-red-700">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Filter, Loader2, RotateCcw, Search, X } from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import {
  buscarPorCampo,
  getCamposLayout,
  identificarCenarios,
} from "../services/api";

const arquivo = ref(null);
const isLoading = ref(false);
const error = ref("");
const resultado = ref(null);
const cenariosSelecionados = ref([]);
const paginaAtual = ref(1);
const itensPorPagina = 50;
const sitesFilter = ref(null);

// Busca por campo
const camposLayout = ref([]);
const campoBusca = ref("");
const campoEncontrado = ref(null);
const valorBusca = ref("");
const isBuscandoCampo = ref(false);
const resultadoBuscaCampo = ref(null);

const hasResults = computed(() => resultado.value !== null);

const totalClientesUnicos = computed(() => {
  if (!resultado.value) return 0;
  const clientes = new Set(resultado.value.faturas.map((f) => f.conta_cliente));
  return clientes.size;
});

const faturasFiltradas = computed(() => {
  if (!resultado.value) return [];

  // Se tem busca por campo ativa, usar os resultados dela
  if (resultadoBuscaCampo.value) {
    let faturas = resultadoBuscaCampo.value.faturas;
    // Aplicar também o filtro de cenários
    if (cenariosSelecionados.value.length > 0) {
      faturas = faturas.filter((f) =>
        cenariosSelecionados.value.every((c) => f.cenarios.includes(c)),
      );
    }
    // ADICIONADO: filtro mínimo de sites (mostra faturas com quantidade_sites >= sitesFilter)
    if (sitesFilter.value !== null && sitesFilter.value !== "") {
      const minSites = Number(sitesFilter.value);
      if (!Number.isNaN(minSites)) {
        faturas = faturas.filter((f) => Number(f.quantidade_sites) >= minSites);
      }
    }
    return faturas;
  }

  let faturas = resultado.value.faturas;
  if (cenariosSelecionados.value.length > 0) {
    faturas = faturas.filter((f) =>
      cenariosSelecionados.value.every((c) => f.cenarios.includes(c)),
    );
  }
  // ADICIONADO: filtro mínimo de sites (mostra faturas com quantidade_sites >= sitesFilter)
  if (sitesFilter.value !== null && sitesFilter.value !== "") {
    const minSites = Number(sitesFilter.value);
    if (!Number.isNaN(minSites)) {
      faturas = faturas.filter((f) => Number(f.quantidade_sites) >= minSites);
    }
  }
  return faturas;
});

const totalPaginas = computed(() =>
  Math.max(1, Math.ceil(faturasFiltradas.value.length / itensPorPagina)),
);

const faturasPaginadas = computed(() => {
  const inicio = (paginaAtual.value - 1) * itensPorPagina;
  return faturasFiltradas.value.slice(inicio, inicio + itensPorPagina);
});

// Reset página ao mudar filtro
watch(
  [cenariosSelecionados, sitesFilter],
  () => {
    // ADICIONADO: sempre volta para a página 1 quando o filtro de sites muda
    paginaAtual.value = 1;
  },
  { deep: true },
);

// Carregar campos do layout ao montar
onMounted(async () => {
  try {
    const response = await getCamposLayout();
    camposLayout.value = response.data.campos;
  } catch (e) {
    // Layout não disponível, não é erro crítico
    console.warn(
      "Layout PrintCenter não disponível para busca por campo:",
      e.message,
    );
  }
});

function onCampoInput() {
  const codigo = campoBusca.value.trim();
  campoEncontrado.value =
    camposLayout.value.find((c) => c.codigo === codigo) || null;
  // Limpar resultado anterior se mudar o campo
  if (resultadoBuscaCampo.value) {
    resultadoBuscaCampo.value = null;
    valorBusca.value = "";
  }
}

async function executarBuscaCampo() {
  if (!campoEncontrado.value || !valorBusca.value || !arquivo.value) return;

  isBuscandoCampo.value = true;
  try {
    const response = await buscarPorCampo(
      arquivo.value,
      campoEncontrado.value.tipo_registro,
      campoEncontrado.value.posicao_de,
      campoEncontrado.value.posicao_ate,
      valorBusca.value,
    );
    resultadoBuscaCampo.value = response.data;
    paginaAtual.value = 1;
  } catch (e) {
    error.value =
      e.response?.data?.detail || e.message || "Erro na busca por campo";
  } finally {
    isBuscandoCampo.value = false;
  }
}

function limparBuscaCampo() {
  resultadoBuscaCampo.value = null;
  campoBusca.value = "";
  campoEncontrado.value = null;
  valorBusca.value = "";
  paginaAtual.value = 1;
}

function toggleCenario(cenario) {
  const idx = cenariosSelecionados.value.indexOf(cenario);
  if (idx >= 0) {
    cenariosSelecionados.value.splice(idx, 1);
  } else {
    cenariosSelecionados.value.push(cenario);
  }
}

function handleFileChange(event) {
  arquivo.value = event.target.files[0] || null;
}

async function handleSubmit() {
  if (!arquivo.value) return;
  isLoading.value = true;
  error.value = "";
  resultado.value = null;

  try {
    const response = await identificarCenarios(arquivo.value);
    resultado.value = response.data;
  } catch (e) {
    error.value =
      e.response?.data?.detail || e.message || "Erro ao identificar cenários";
  } finally {
    isLoading.value = false;
  }
}

function resetForm() {
  resultado.value = null;
  cenariosSelecionados.value = [];
  // ADICIONADO: limpa o filtro de sites no reset geral
  sitesFilter.value = null;
  arquivo.value = null;
  error.value = "";
  paginaAtual.value = 1;
  limparBuscaCampo();
}

function cenarioClass(cenario) {
  const classes = {
    "ICMS (Modelo 22)": "bg-blue-100 text-blue-800",
    "ICMS (Modelo 62)": "bg-indigo-100 text-indigo-800",
    ISS: "bg-green-100 text-green-800",
    Cobilling: "bg-purple-100 text-purple-800",
    "Débito Automático": "bg-yellow-100 text-yellow-800",
    Recibo: "bg-orange-100 text-orange-800",
    "Dupla Convivência": "bg-pink-100 text-pink-800",
    Isenção: "bg-teal-100 text-teal-800",
  };
  // Cenários de Retenção (dinâmicos: "Retenção 9,45%", "Retenção 4,8%", etc.)
  if (cenario.startsWith("Retenção")) {
    return "bg-red-100 text-red-800";
  }
  return classes[cenario] || "bg-gray-100 text-gray-800";
}
</script>
