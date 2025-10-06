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

    <!-- Gráficos de Estatísticas -->
    <div
      class="grid grid-cols-1 lg:grid-cols-2 gap-6"
      v-if="validationStore.hasErrors"
    >
      <ErrorsByTypeChart :data="validationStore.errorsByType" />
      <ErrorsByFieldChart :data="validationStore.errorsByField" />
    </div>

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

        <!-- Progress Bar -->
        <div class="mt-4">
          <div class="progress-bar">
            <div
              class="progress-fill"
              :class="getProgressBarColor(validationStore.successRate)"
              :style="{ width: `${validationStore.successRate}%` }"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Detalhes dos Erros -->
    <ErrorsTable
      v-if="validationStore.hasErrors"
      :errors="validationStore.currentValidation.resultado.erros"
    />

    <!-- Mensagem de Sucesso -->
    <div v-else class="card bg-success-50 border-success-200">
      <div class="card-body text-center">
        <CheckCircle class="w-16 h-16 text-success-500 mx-auto mb-4" />
        <h3 class="text-lg font-semibold text-success-800 mb-2">
          🎉 Validação 100% Bem-sucedida!
        </h3>
        <p class="text-success-700">
          Nenhum erro foi encontrado no arquivo. Todos os
          {{
            validationStore.currentValidation.resultado.total_linhas
          }}
          registros estão válidos.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import ErrorsByFieldChart from "@/components/ErrorsByFieldChart.vue";
import ErrorsByTypeChart from "@/components/ErrorsByTypeChart.vue";
import ErrorsTable from "@/components/ErrorsTable.vue";
import StatCard from "@/components/StatCard.vue";
import { useValidationStore } from "@/stores/validation";
import {
  AlertTriangle,
  CheckCircle,
  Download,
  RefreshCw,
  XCircle,
} from "lucide-vue-next";
import { onMounted } from "vue";

onMounted(() => {});

const validationStore = useValidationStore();

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
</script>
