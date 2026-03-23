<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Histórico de Validações</h1>
      <p class="text-gray-600">Consulte os resultados de validações e comparações anteriores</p>
    </div>

    <!-- Estatísticas Gerais -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="stat-card">
        <div class="stat-value text-blue-600">{{ stats.total }}</div>
        <div class="stat-label">Total de Registros</div>
      </div>
      <div class="stat-card">
        <div class="stat-value text-green-600">{{ stats.validations }}</div>
        <div class="stat-label">Validações</div>
      </div>
      <div class="stat-card">
        <div class="stat-value text-purple-600">{{ stats.comparisons }}</div>
        <div class="stat-label">Comparações</div>
      </div>
      <div class="stat-card">
        <div class="stat-value text-gray-600">{{ storageUsage }}</div>
        <div class="stat-label">Uso do Storage</div>
      </div>
    </div>

    <!-- Filtros e Ações -->
    <div class="card">
      <div class="card-body">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <!-- Filtro por tipo -->
            <select v-model="filtroTipo" class="select-input text-sm">
              <option value="todos">Todos os tipos</option>
              <option value="validacoes">Validações</option>
              <option value="comparacoes">Comparações</option>
            </select>

            <!-- Busca -->
            <div class="relative">
              <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                v-model="termoBusca"
                type="text"
                placeholder="Buscar por nome do layout..."
                class="pl-9 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 w-64"
              />
            </div>
          </div>

          <div class="flex gap-2">
            <button
              @click="limparAntigos"
              class="text-sm px-3 py-2 border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50 transition-colors flex items-center gap-1"
            >
              <Trash2 class="w-3.5 h-3.5" />
              Limpar antigos (+30 dias)
            </button>
            <button
              @click="atualizarLista"
              class="text-sm px-3 py-2 border border-blue-300 rounded-md text-blue-600 hover:bg-blue-50 transition-colors flex items-center gap-1"
            >
              <RefreshCw class="w-3.5 h-3.5" />
              Atualizar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Lista de Registros -->
    <div v-if="registrosFiltrados.length === 0" class="card">
      <div class="card-body text-center py-12">
        <Clock class="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">Nenhum registro encontrado</h3>
        <p class="text-gray-500">
          {{ filtroTipo !== 'todos' || termoBusca ? 'Tente alterar os filtros.' : 'Faça uma validação ou comparação para começar.' }}
        </p>
      </div>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="registro in registrosFiltrados"
        :key="registro.id"
        class="card hover:shadow-md transition-shadow cursor-pointer"
        @click="abrirRegistro(registro)"
      >
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <!-- Ícone do tipo -->
              <div
                :class="[
                  'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                  registro.tipo === 'validacao'
                    ? 'bg-green-100 text-green-600'
                    : 'bg-purple-100 text-purple-600'
                ]"
              >
                <CheckCircle v-if="registro.tipo === 'validacao'" class="w-5 h-5" />
                <GitCompare v-else class="w-5 h-5" />
              </div>

              <!-- Info principal -->
              <div>
                <div class="flex items-center gap-2">
                  <h3 class="font-semibold text-gray-900">
                    {{ registro.titulo }}
                  </h3>
                  <span
                    :class="[
                      'px-2 py-0.5 text-xs rounded-full font-medium',
                      registro.tipo === 'validacao'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-purple-100 text-purple-700'
                    ]"
                  >
                    {{ registro.tipo === 'validacao' ? 'Validação' : 'Comparação' }}
                  </span>
                </div>
                <div class="flex items-center gap-4 mt-1 text-sm text-gray-500">
                  <span class="flex items-center gap-1">
                    <Calendar class="w-3.5 h-3.5" />
                    {{ formatarData(registro.data) }}
                  </span>
                  <span v-if="registro.layoutNome" class="flex items-center gap-1">
                    <FileText class="w-3.5 h-3.5" />
                    {{ registro.layoutNome }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Métricas -->
            <div class="flex items-center gap-6">
              <!-- Taxa de sucesso / identidade -->
              <div class="text-right">
                <div
                  :class="[
                    'text-lg font-bold',
                    getTaxaColor(registro.taxa)
                  ]"
                >
                  {{ registro.taxa.toFixed(1) }}%
                </div>
                <div class="text-xs text-gray-500">
                  {{ registro.tipo === 'validacao' ? 'Sucesso' : 'Identidade' }}
                </div>
              </div>

              <!-- Barra de progresso mini -->
              <div class="w-20 hidden sm:block">
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    :class="[
                      'rounded-full h-2 transition-all',
                      getTaxaBarColor(registro.taxa)
                    ]"
                    :style="{ width: registro.taxa + '%' }"
                  ></div>
                </div>
              </div>

              <!-- Info de erros -->
              <div class="text-right min-w-[80px]">
                <div class="text-sm font-medium text-gray-900">
                  {{ registro.totalLinhas }} linhas
                </div>
                <div v-if="registro.erros > 0" class="text-xs text-red-500">
                  {{ registro.erros }} {{ registro.tipo === 'validacao' ? 'erros' : 'diferenças' }}
                </div>
                <div v-else class="text-xs text-green-500">
                  Sem problemas
                </div>
              </div>

              <!-- Ações -->
              <div class="flex items-center gap-1">
                <button
                  @click.stop="removerRegistro(registro)"
                  class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                  title="Remover"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
                <ChevronRight class="w-5 h-5 text-gray-400" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Calendar,
  CheckCircle,
  ChevronRight,
  Clock,
  FileText,
  GitCompare,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import localStorageService from "../services/localStorage";

const router = useRouter();

// Estado
const registros = ref([]);
const filtroTipo = ref("todos");
const termoBusca = ref("");

// Estatísticas
const stats = ref({ validations: 0, comparisons: 0, layouts: 0, total: 0 });

const storageUsage = computed(() => {
  let totalBytes = 0;
  for (const key of Object.keys(localStorage)) {
    if (key.startsWith("validador_")) {
      totalBytes += (localStorage.getItem(key) || "").length * 2; // UTF-16
    }
  }
  if (totalBytes < 1024) return `${totalBytes} B`;
  if (totalBytes < 1024 * 1024) return `${(totalBytes / 1024).toFixed(1)} KB`;
  return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
});

// Carregar registros
function carregarRegistros() {
  const lista = [];

  // Carregar validações
  const validacoes = localStorageService.getValidations();
  Object.entries(validacoes).forEach(([timestamp, data]) => {
    lista.push({
      id: `val-${timestamp}`,
      tipo: "validacao",
      timestamp,
      titulo: data.layout_nome || data.dados_relatorio?.layout_nome || "Validação",
      layoutNome: data.layout_nome || data.dados_relatorio?.layout_nome || "",
      data: data.savedAt || data.dados_relatorio?.data_geracao || timestamp,
      taxa: data.resultado?.taxa_sucesso ?? data.dados_relatorio?.estatisticas?.taxa_sucesso ?? 0,
      totalLinhas: data.resultado?.total_linhas ?? data.dados_relatorio?.estatisticas?.total_linhas ?? 0,
      erros: data.resultado?.erros?.length ?? data.dados_relatorio?.estatisticas?.total_erros ?? 0,
      dados: data,
    });
  });

  // Carregar comparações
  const comparacoes = localStorageService.getComparisons();
  Object.entries(comparacoes).forEach(([timestamp, data]) => {
    lista.push({
      id: `comp-${timestamp}`,
      tipo: "comparacao",
      timestamp,
      titulo: data.layout_nome || "Comparação Estrutural",
      layoutNome: data.layout_nome || "",
      data: data.savedAt || timestamp,
      taxa: data.resultado_comparacao?.taxa_identidade ?? 0,
      totalLinhas: data.resultado_comparacao?.total_linhas_comparadas ?? 0,
      erros: data.resultado_comparacao?.linhas_com_diferencas ?? 0,
      dados: data,
    });
  });

  // Ordenar por data (mais recente primeiro)
  lista.sort((a, b) => {
    const dateA = new Date(a.data);
    const dateB = new Date(b.data);
    return dateB - dateA;
  });

  registros.value = lista;
  stats.value = localStorageService.getStorageStats();
}

// Filtros
const registrosFiltrados = computed(() => {
  let result = registros.value;

  if (filtroTipo.value === "validacoes") {
    result = result.filter((r) => r.tipo === "validacao");
  } else if (filtroTipo.value === "comparacoes") {
    result = result.filter((r) => r.tipo === "comparacao");
  }

  if (termoBusca.value.trim()) {
    const termo = termoBusca.value.toLowerCase().trim();
    result = result.filter(
      (r) =>
        r.titulo.toLowerCase().includes(termo) ||
        r.layoutNome.toLowerCase().includes(termo)
    );
  }

  return result;
});

// Ações
function abrirRegistro(registro) {
  if (registro.tipo === "validacao") {
    // Navegar para relatório de erros com os dados
    router.push({
      name: "ErrorReport",
      query: { timestamp: registro.timestamp },
    });
  } else {
    // Navegar para comparação
    router.push({
      name: "Comparacao",
      query: { timestamp: registro.timestamp },
    });
  }
}

function removerRegistro(registro) {
  if (!confirm("Tem certeza que deseja remover este registro?")) return;

  if (registro.tipo === "validacao") {
    localStorageService.removeValidation(registro.timestamp);
  } else {
    localStorageService.removeComparison(registro.timestamp);
  }
  carregarRegistros();
}

function limparAntigos() {
  if (
    !confirm("Remover registros com mais de 30 dias? Esta ação não pode ser desfeita.")
  )
    return;
  localStorageService.cleanOldData(30);
  carregarRegistros();
}

function atualizarLista() {
  carregarRegistros();
}

// Formatação
function formatarData(dateStr) {
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    return date.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function getTaxaColor(taxa) {
  if (taxa >= 95) return "text-green-600";
  if (taxa >= 80) return "text-yellow-600";
  return "text-red-600";
}

function getTaxaBarColor(taxa) {
  if (taxa >= 95) return "bg-green-500";
  if (taxa >= 80) return "bg-yellow-500";
  return "bg-red-500";
}

onMounted(carregarRegistros);
</script>

<style scoped>
.file-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm;
}
.select-input {
  @apply px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500;
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
</style>
