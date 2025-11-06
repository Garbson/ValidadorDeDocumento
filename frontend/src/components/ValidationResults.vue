<template>
  <div data-validation-results class="space-y-6 animate-fade-in">
    <!-- Header com ações -->
    <div class="flex justify-between items-center">
      <h2 class="text-2xl font-bold text-gray-900">Resultados da Validação</h2>
      <div class="flex space-x-3">
        <button @click="downloadReport('excel')" class="btn-primary">
          <Download class="w-4 h-4 mr-2" />
          Excel
        </button>
        <button @click="downloadReport('csv')" class="btn-secondary">
          <Download class="w-4 h-4 mr-2" />
          CSV
        </button>
        <button
          @click="validationStore.clearValidation()"
          class="btn-secondary"
        >
          <RefreshCw class="w-4 h-4 mr-2" />
          Nova Validação
        </button>
      </div>
    </div>

    <!-- Tabs Navigation -->
    <div class="border-b border-gray-200">
      <nav class="-mb-px flex space-x-8" aria-label="Tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            activeTab === tab.id
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
            'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center'
          ]"
        >
          <component :is="tab.icon" class="w-4 h-4 mr-2" />
          {{ tab.label }}
          <span v-if="tab.count > 0" class="ml-2 bg-red-100 text-red-600 px-2 py-0.5 text-xs rounded-full">
            {{ tab.count }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Cards de Estatísticas -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <StatCard
        title="Total de Linhas"
        :value="validationStore.currentValidation.resultado.total_linhas"
        icon="FileText"
        color="blue"
      />
      <StatCard
        title="Linhas Válidas"
        :value="validationStore.currentValidation.resultado.linhas_validas"
        icon="CheckCircle"
        color="green"
      />
      <StatCard
        title="Linhas com Erro"
        :value="validationStore.currentValidation.resultado.linhas_com_erro"
        icon="AlertCircle"
        color="red"
      />
      <StatCard
        title="Taxa de Sucesso"
        :value="`${validationStore.successRate.toFixed(1)}%`"
        icon="TrendingUp"
        :color="getSuccessRateColor(validationStore.successRate)"
      />
    </div>

    <!-- Tab Content -->
    <div class="mt-6">
      <!-- Aba: Visão Geral -->
      <div v-if="activeTab === 'geral'">
        <!-- Status Geral -->
        <div class="card">
          <div class="card-body">
            <div class="flex items-center space-x-4">
              <div class="flex-shrink-0">
                <CheckCircle
                  v-if="validationStore.successRate >= 95"
                  class="w-12 h-12 text-success-500"
                />
                <AlertTriangle
                  v-else-if="validationStore.successRate >= 80"
                  class="w-12 h-12 text-warning-500"
                />
                <XCircle v-else class="w-12 h-12 text-error-500" />
              </div>
              <div class="flex-1">
                <h3
                  class="text-lg font-semibold"
                  :class="getStatusColor(validationStore.successRate)"
                >
                  {{ getStatusMessage(validationStore.successRate) }}
                </h3>
                <p class="text-gray-600 mt-1">
                  {{ getStatusDescription(validationStore.successRate) }}
                </p>
              </div>
              <div class="flex-shrink-0">
                <div class="text-right">
                  <div
                    class="text-2xl font-bold"
                    :class="getStatusColor(validationStore.successRate)"
                  >
                    {{ validationStore.successRate.toFixed(1) }}%
                  </div>
                  <div class="text-sm text-gray-500">Taxa de Sucesso</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Aba: Cálculos de Impostos -->
      <div v-if="activeTab === 'calculos'">
        <div class="space-y-6">
          <!-- Totais Acumulados -->
          <div v-if="validationStore.currentValidation?.resultado?.totais_acumulados" class="card">
            <div class="card-header">
              <h3 class="text-lg font-semibold flex items-center">
                <Calculator class="w-5 h-5 mr-2" />
                Totais de Impostos Acumulados
              </h3>
            </div>
            <div class="card-body">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div
                  v-for="(valor, campo) in validationStore.currentValidation.resultado.totais_acumulados"
                  :key="campo"
                  class="border border-gray-200 rounded-lg p-4"
                >
                  <div class="text-sm text-gray-500">{{ formatTaxFieldName(campo) }}</div>
                  <div class="text-lg font-bold text-primary-600">
                    {{ formatCurrency(valor) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Erros de Cálculo -->
          <div class="card">
            <div class="card-header">
              <h3 class="text-lg font-semibold flex items-center">
                <AlertTriangle class="w-5 h-5 mr-2" />
                Erros de Cálculos
              </h3>
            </div>
            <div class="card-body">
              <div v-if="errosCalculos.length === 0" class="text-center py-8">
                <CheckCircle class="w-16 h-16 text-green-300 mx-auto mb-4" />
                <h4 class="text-lg font-medium text-gray-900 mb-2">Nenhum erro de cálculo encontrado!</h4>
                <p class="text-gray-500">Todos os cálculos de impostos estão corretos.</p>
              </div>
              <div v-else class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Linha</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Campo</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Erro</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descrição</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="erro in errosCalculos" :key="`${erro.linha}-${erro.campo}`" class="hover:bg-gray-50">
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ erro.linha }}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <code class="bg-gray-100 px-2 py-1 rounded text-xs">{{ erro.campo }}</code>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {{ formatErrorType(erro.erro_tipo) }}
                        </span>
                      </td>
                      <td class="px-6 py-4 text-sm text-gray-900">{{ erro.descricao }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Aba: Estrutura -->
      <div v-if="activeTab === 'estrutura'">
        <div class="card">
          <div class="card-header">
            <h3 class="text-lg font-semibold flex items-center">
              <Layers class="w-5 h-5 mr-2" />
              Erros de Estrutura
            </h3>
          </div>
          <div class="card-body">
            <div v-if="errosEstrutura.length === 0" class="text-center py-8">
              <CheckCircle class="w-16 h-16 text-green-300 mx-auto mb-4" />
              <h4 class="text-lg font-medium text-gray-900 mb-2">Estrutura perfeita!</h4>
              <p class="text-gray-500">Nenhum registro duplicado consecutivo encontrado.</p>
            </div>
            <div v-else class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Linha</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo Registro</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Problema</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descrição</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="erro in errosEstrutura" :key="`${erro.linha}-${erro.campo}`" class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ erro.linha }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        {{ erro.valor_encontrado }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Duplicação
                      </span>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-900">{{ erro.descricao }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Aba: Faturas -->
      <div v-if="activeTab === 'faturas'">
        <div class="space-y-6">
          <!-- Estatísticas -->
          <div v-if="validationStore.currentValidation?.resultado?.estatisticas_faturas" class="card">
            <div class="card-header">
              <h3 class="text-lg font-semibold flex items-center">
                <BarChart3 class="w-5 h-5 mr-2" />
                Estatísticas de Faturas
              </h3>
            </div>
            <div class="card-body">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="text-center">
                  <div class="text-2xl font-bold text-primary-600">
                    {{ validationStore.currentValidation.resultado.estatisticas_faturas.total_faturas }}
                  </div>
                  <div class="text-sm text-gray-500">Total de Faturas</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-success-600">
                    {{ validationStore.currentValidation.resultado.estatisticas_faturas.total_notas_fiscais }}
                  </div>
                  <div class="text-sm text-gray-500">Total de Notas Fiscais</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-warning-600">
                    {{ calcularMediaNotasPorFatura() }}
                  </div>
                  <div class="text-sm text-gray-500">Média NF/Fatura</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Erros de Unicidade -->
          <div class="card">
            <div class="card-header">
              <h3 class="text-lg font-semibold flex items-center">
                <AlertTriangle class="w-5 h-5 mr-2" />
                Erros de Unicidade (Fatura + NF)
              </h3>
            </div>
            <div class="card-body">
              <div v-if="errosUnicidade.length === 0" class="text-center py-8">
                <CheckCircle class="w-16 h-16 text-green-300 mx-auto mb-4" />
                <h4 class="text-lg font-medium text-gray-900 mb-2">Todas as combinações são únicas!</h4>
                <p class="text-gray-500">Nenhuma fatura + nota fiscal duplicada encontrada.</p>
              </div>
              <div v-else class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Linha</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fatura</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nota Fiscal</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Problema</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="erro in errosUnicidade" :key="`${erro.linha}-${erro.campo}`" class="hover:bg-gray-50">
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ erro.linha }}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {{ extrairFatura(erro.valor_encontrado) }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {{ extrairNF(erro.valor_encontrado) }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Combinação Duplicada
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import StatCard from "@/components/StatCard.vue";
import { useValidationStore } from "@/stores/validation";
import {
  AlertTriangle,
  CheckCircle,
  Download,
  FileText,
  RefreshCw,
  XCircle,
  Calculator,
  Layers,
  BarChart3,
  Users
} from "lucide-vue-next";
import { computed, ref, onMounted } from "vue";

const validationStore = useValidationStore();

// Active tab state
const activeTab = ref('geral');

// Tabs configuration
const tabs = computed(() => [
  {
    id: 'geral',
    label: 'Visão Geral',
    icon: 'BarChart3',
    count: 0
  },
  {
    id: 'calculos',
    label: 'Cálculos de Impostos',
    icon: 'Calculator',
    count: errosCalculos.value.length
  },
  {
    id: 'estrutura',
    label: 'Estrutura',
    icon: 'Layers',
    count: errosEstrutura.value.length
  },
  {
    id: 'faturas',
    label: 'Faturas & Unicidade',
    icon: 'Users',
    count: errosUnicidade.value.length
  }
]);

// Computed filters for specific error types
const errosCalculos = computed(() => {
  if (!validationStore.currentValidation?.resultado?.erros) return [];
  return validationStore.currentValidation.resultado.erros.filter(erro =>
    erro.erro_tipo.includes('TOTAL_') ||
    erro.erro_tipo.includes('CALCULO_ERRO') ||
    erro.erro_tipo.includes('VALOR_ZERADO')
  );
});

const errosEstrutura = computed(() => {
  if (!validationStore.currentValidation?.resultado?.erros) return [];
  return validationStore.currentValidation.resultado.erros.filter(erro =>
    erro.erro_tipo === 'ESTRUTURA_DUPLICADA' ||
    erro.erro_tipo === 'CAMPO_OBRIGATORIO' ||
    erro.erro_tipo === 'TAMANHO_LINHA' ||
    erro.erro_tipo === 'FORMATO_INVALIDO' ||
    erro.erro_tipo === 'TIPO_INVALIDO'
  );
});

const errosUnicidade = computed(() => {
  if (!validationStore.currentValidation?.resultado?.erros) return [];
  return validationStore.currentValidation.resultado.erros.filter(erro =>
    erro.erro_tipo === 'COMBINACAO_DUPLICADA'
  );
});

onMounted(() => {});

const downloadReport = async (format) => {
  if (!validationStore.currentValidation?.timestamp) return;

  try {
    await validationStore.downloadReport(
      validationStore.currentValidation.timestamp,
      format
    );
  } catch (error) {
    // Erro no download
  }
};

const getSuccessRateColor = (rate) => {
  if (rate >= 95) return "green";
  if (rate >= 80) return "yellow";
  return "red";
};

const getStatusColor = (rate) => {
  if (rate >= 95) return "text-success-600";
  if (rate >= 80) return "text-warning-600";
  return "text-error-600";
};

const getProgressBarColor = (rate) => {
  if (rate >= 95) return "bg-success-500";
  if (rate >= 80) return "bg-warning-500";
  return "bg-error-500";
};

const getStatusMessage = (rate) => {
  if (rate >= 95) return "Excelente Qualidade";
  if (rate >= 80) return "Boa Qualidade com Atenções";
  return "Muitos Erros Encontrados";
};

const getStatusDescription = (rate) => {
  if (rate >= 95)
    return "O arquivo apresenta alta qualidade com poucos ou nenhum erro.";
  if (rate >= 80)
    return "O arquivo tem boa qualidade, mas requer algumas correções.";
  return "O arquivo apresenta muitos erros e necessita revisão completa.";
};

const getTipoBadgeColor = (nomeComTipo) => {
  const tipo = nomeComTipo.match(/\[Tipo (\w+)\]/)?.[1];
  const colors = {
    '00': 'bg-blue-100 text-blue-800',
    '01': 'bg-green-100 text-green-800',
    '02': 'bg-yellow-100 text-yellow-800',
    '04': 'bg-red-100 text-red-800',
    '06': 'bg-purple-100 text-purple-800',
    '08': 'bg-pink-100 text-pink-800',
    '10': 'bg-indigo-100 text-indigo-800',
    '20': 'bg-orange-100 text-orange-800',
    '22': 'bg-teal-100 text-teal-800',
    '90': 'bg-gray-100 text-gray-800',
  };
  return colors[tipo] || 'bg-gray-100 text-gray-800';
};

const formatTaxFieldName = (campo) => {
  const formatMap = {
    'NFE56-TOT-VLR-PIS': 'Total PIS',
    'NFE56-TOT-VLR-COFINS': 'Total COFINS',
    'NFE56-TOT-VLR-FUST': 'Total FUST',
    'NFE56-TOT-VLR-FUNTEL': 'Total FUNTEL',
    'NFE56-TOT-VLR-ICMS': 'Total ICMS',
    'NFE56-TOT-VLR-FCP': 'Total FCP',
    'NFE56-TOT-VLR-BC': 'Total Base de Cálculo'
  };
  return formatMap[campo] || campo;
};

const formatCurrency = (valor) => {
  return `R$ ${(valor / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const formatErrorType = (tipo) => {
  const formatMap = {
    'TOTAL_BC': 'Total Base de Cálculo',
    'TOTAL_ICMS': 'Total ICMS',
    'TOTAL_PIS': 'Total PIS',
    'TOTAL_COFINS': 'Total COFINS',
    'TOTAL_FUST': 'Total FUST',
    'TOTAL_FUNTEL': 'Total FUNTEL',
    'TOTAL_FCP': 'Total FCP',
    'CALCULO_ERRO_ICMS': 'Erro Cálculo ICMS',
    'CALCULO_ERRO_FCP': 'Erro Cálculo FCP',
    'CALCULO_ERRO_PIS': 'Erro Cálculo PIS',
    'CALCULO_ERRO_COFINS': 'Erro Cálculo COFINS',
    'CALCULO_ERRO_FUST': 'Erro Cálculo FUST',
    'CALCULO_ERRO_FUNTEL': 'Erro Cálculo FUNTEL',
    'VALOR_ZERADO_FCP': 'Valor FCP Zerado',
    'VALOR_ZERADO_ICMS': 'Valor ICMS Zerado',
    'VALOR_ZERADO_PIS': 'Valor PIS Zerado',
    'VALOR_ZERADO_COFINS': 'Valor COFINS Zerado',
    'VALOR_ZERADO_FUST': 'Valor FUST Zerado',
    'VALOR_ZERADO_FUNTEL': 'Valor FUNTEL Zerado',
    'ESTRUTURA_DUPLICADA': 'Estrutura Duplicada',
    'COMBINACAO_DUPLICADA': 'Combinação Duplicada',
    'TRAILER_QTD_NF': 'Erro Quantidade NF no Trailer',
    'CAMPO_OBRIGATORIO': 'Campo Obrigatório Vazio',
    'TAMANHO_LINHA': 'Tamanho de Linha Incorreto',
    'FORMATO_INVALIDO': 'Formato Inválido',
    'TIPO_INVALIDO': 'Tipo de Dados Inválido'
  };
  return formatMap[tipo] || tipo;
};

const extrairFatura = (valor) => {
  const match = valor.match(/Fatura:\s*(\w+)/);
  return match ? match[1] : '-';
};

const extrairNF = (valor) => {
  const match = valor.match(/NF:\s*(\w+)/);
  return match ? match[1] : '-';
};

const calcularMediaNotasPorFatura = () => {
  if (!validationStore.currentValidation?.resultado?.estatisticas_faturas) return '0.0';
  const stats = validationStore.currentValidation.resultado.estatisticas_faturas;
  if (stats.total_faturas === 0) return '0.0';
  return (stats.total_notas_fiscais / stats.total_faturas).toFixed(1);
};

const getTipoCampoClass = (tipo) => {
  const classes = {
    'TEXTO': 'badge badge-info',
    'NUMERO': 'badge badge-success',
    'DATA': 'badge badge-warning',
    'DECIMAL': 'badge badge-error'
  };
  return classes[tipo] || 'badge badge-info';
};
</script>
