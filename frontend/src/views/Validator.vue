<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">
        Validador de Arquivos
      </h1>
      <p class="text-gray-600">Envie seus arquivos para validação automática</p>
    </div>

    <!-- Upload Form / Mapeamento -->
    <div class="card max-w-4xl mx-auto" v-show="!validationStore.hasValidation">
      <div class="card-header">
        <h2 class="text-lg font-semibold flex items-center">
          <Upload class="w-5 h-5 mr-2" />
          Upload de Arquivos
        </h2>
      </div>
      <div class="card-body space-y-6">
        <form
          v-if="!showMapper && !mappingConfirmed"
          @submit.prevent="handleValidation"
          class="space-y-6"
        >
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

          <!-- Data File Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Arquivo de Dados (TXT)
              <span class="text-red-500">*</span>
            </label>
            <div class="mt-1">
              <input
                ref="dataFileInput"
                type="file"
                accept=".txt"
                @change="handleDataFileChange"
                class="file-input"
                required
              />
            </div>
            <p class="text-sm text-gray-500 mt-1">
              Arquivo TXT sequencial para validação
            </p>
          </div>

          <!-- Options -->
          <div class="grid md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Limite de Erros
              </label>
              <input
                v-model.number="maxErrors"
                type="number"
                min="1"
                max="10000"
                class="input"
                placeholder="100"
              />
              <p class="text-sm text-gray-500 mt-1">
                Padrão: 100 erros. Aumente conforme necessário (valores altos
                podem travar o navegador)
              </p>
            </div>

            <div class="flex items-center">
              <input
                id="previewLayout"
                v-model="previewLayout"
                type="checkbox"
                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label
                for="previewLayout"
                class="ml-2 block text-sm text-gray-700"
              >
                Visualizar layout antes da validação
              </label>
            </div>
          </div>

          <!-- Ações -->
          <div class="flex justify-center gap-4 flex-wrap">
            <button
              type="button"
              v-if="layoutFile"
              class="btn-secondary px-6 py-3"
              @click="abrirMapper"
            >
              Mapear / Ajustar Layout
            </button>
            <button
              type="submit"
              :disabled="!layoutFile || !dataFile || validationStore.isLoading"
              class="btn-primary px-8 py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div v-if="validationStore.isLoading" class="flex items-center">
                <div class="loading-spinner w-5 h-5 mr-2"></div>
                Validando...
              </div>
              <div v-else class="flex items-center">
                <CheckSquare class="w-5 h-5 mr-2" />
                Iniciar Validação
              </div>
            </button>
          </div>
        </form>

        <!-- Etapa 2: Mapeamento -->
        <div v-if="showMapper && layoutFile" class="space-y-4">
          <div class="p-3 bg-blue-50 text-blue-700 text-sm rounded">
            Revise e confirme o mapeamento antes de validar os dados.
          </div>
          <LayoutMapper
            :file="layoutFile"
            @cancel="cancelarMapper"
            @confirmed="onMappingConfirmed"
          />
        </div>

        <!-- Error Message -->
        <div
          v-if="validationStore.error"
          class="bg-error-50 border border-error-200 rounded-md p-4"
        >
          <div class="flex">
            <AlertCircle class="w-5 h-5 text-error-400 mr-2 mt-0.5" />
            <div>
              <h3 class="text-sm font-medium text-error-800">
                Erro na Validação
              </h3>
              <p class="text-sm text-error-700 mt-1">
                {{ validationStore.error }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Layout Preview -->
    <div v-if="layoutPreview && previewLayout" class="card max-w-6xl mx-auto">
      <div class="card-header flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <h3 class="text-lg font-semibold flex items-center">
          <FileSpreadsheet class="w-5 h-5 mr-2" />
          Preview do Layout: {{ layoutPreview.nome }}
        </h3>
        <div class="flex items-center flex-wrap gap-2 text-sm">
          <!-- Paginação de Campos no Preview do Layout -->
          <div class="flex items-center gap-2">
            <button
              class="btn-secondary px-2 py-1"
              @click="paginaAnteriorCampos"
              :disabled="paginaAtualCampos === 1"
              title="Página anterior"
            >
              «P
            </button>
            <span class="text-xs text-gray-600">
              Campos:
              <strong>{{ paginaAtualCampos }}/{{ totalPaginasCampos }}</strong>
              <span v-if="allVisibleCampos.length > 0">({{ allVisibleCampos.length }} total)</span>
            </span>
            <button
              class="btn-secondary px-2 py-1"
              @click="proximaPaginaCampos"
              :disabled="paginaAtualCampos >= totalPaginasCampos"
              title="Próxima página"
            >
              P»
            </button>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="overflow-x-auto">
          <table class="table">
            <thead class="table-header">
              <tr>
                <th class="table-header-cell">Campo</th>
                <th class="table-header-cell">Posição</th>
                <th class="table-header-cell">Tamanho</th>
                <th class="table-header-cell">Tipo</th>
                <th class="table-header-cell">Obrigatório</th>
                <th class="table-header-cell">Formato</th>
              </tr>
            </thead>
            <tbody class="table-body">
              <tr v-for="campo in visibleCampos" :key="campo.nome">
                <td class="table-cell font-medium">{{ campo.nome }}</td>
                <td class="table-cell">
                  {{ campo.posicao_inicio }}-{{ campo.posicao_fim }}
                </td>
                <td class="table-cell">{{ campo.tamanho }}</td>
                <td class="table-cell">
                  <span class="badge badge-info">{{ campo.tipo }}</span>
                </td>
                <td class="table-cell">
                  <span v-if="campo.obrigatorio" class="badge badge-error"
                    >Sim</span
                  >
                  <span v-else class="badge badge-success">Não</span>
                </td>
                <td class="table-cell">{{ campo.formato || "-" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="mt-4 text-sm text-gray-600">
          <p>
            <strong>Tamanho da linha:</strong>
            {{ layoutPreview.tamanho_linha }} caracteres
          </p>
        </div>
      </div>
    </div>

    <!-- Preview Paginado de Registros -->
    <div
      v-if="layoutPreview && fileLines.length"
      class="card max-w-6xl mx-auto"
    >
      <div
        class="card-header flex flex-col gap-2 md:flex-row md:items-center md:justify-between"
      >
        <h3 class="text-lg font-semibold flex items-center">
          <FileSpreadsheet class="w-5 h-5 mr-2" />
          Registros do Arquivo (Preview)
        </h3>
        <div class="flex items-center flex-wrap gap-2 text-sm">
          <!-- Paginação de Campos -->
          <div class="flex items-center gap-2 mr-4">
            <button
              class="btn-secondary px-2 py-1"
              @click="paginaAnteriorCampos"
              :disabled="paginaAtualCampos === 1"
              title="Página anterior"
            >
              «P
            </button>
            <span class="text-xs text-gray-600">
              Campos:
              <strong>{{ paginaAtualCampos }}/{{ totalPaginasCampos }}</strong>
              <span v-if="allVisibleCampos.length > 0">({{ allVisibleCampos.length }} total)</span>
            </span>
            <button
              class="btn-secondary px-2 py-1"
              @click="proximaPaginaCampos"
              :disabled="paginaAtualCampos >= totalPaginasCampos"
              title="Próxima página"
            >
              P»
            </button>
          </div>
          <button
            class="btn-secondary px-2 py-1"
            @click="firstRecord"
            :disabled="currentLineIndex === 0"
          >
            «
          </button>
          <button
            class="btn-secondary px-2 py-1"
            @click="prevRecord"
            :disabled="currentLineIndex === 0"
          >
            ‹
          </button>
          <div class="flex items-center gap-1">
            <span>Linha</span>
            <input
              type="number"
              class="input w-24"
              :min="1"
              :max="totalLines"
              v-model.number="jumpLine"
              @change="jumpToLine"
            />
            <span>/ {{ totalLines }}</span>
          </div>
          <button
            class="btn-secondary px-2 py-1"
            @click="nextRecord"
            :disabled="currentLineIndex === totalLines - 1"
          >
            ›
          </button>
          <button
            class="btn-secondary px-2 py-1"
            @click="lastRecord"
            :disabled="currentLineIndex === totalLines - 1"
          >
            »
          </button>
          <span class="ml-2 text-gray-500" v-if="truncated"
            >(Mostrando primeiras {{ fileLines.length }} linhas de
            {{ fullLineCount }} - arquivo truncado)</span
          >
        </div>
      </div>
      <div class="card-body">
        <div class="mb-3 text-xs text-gray-500">
          Comprimento da linha atual: {{ currentRawLine.length }} /
          Tamanho esperado layout: {{ layoutPreview.tamanho_linha }} |
          Tipo detectado da linha: <strong>{{ currentLineKey || '-' }}</strong> |
          Mostrando campos {{ (paginaAtualCampos - 1) * camposPorPagina + 1 }}-{{ Math.min(paginaAtualCampos * camposPorPagina, allVisibleCampos.length) }} de {{ allVisibleCampos.length }}<br>
          <strong>Valores:</strong>
          {{ currentFields.filter(f => f.valor && f.valor.trim()).length }} preenchidos,
          {{ currentFields.filter(f => !f.valor || !f.valor.trim()).length }} vazios
          (apenas campos tipo {{ currentLineKey?.slice(0, 2) || '??' }} têm valores)
        </div>
        <div class="overflow-x-auto">
          <table class="table">
            <thead class="table-header">
              <tr>
                <th class="table-header-cell">#</th>
                <th class="table-header-cell">Campo</th>
                <th class="table-header-cell">Posição</th>
                <th class="table-header-cell">Tam</th>
                <th class="table-header-cell">Valor</th>
                <th class="table-header-cell">Erro</th>
              </tr>
            </thead>
            <tbody class="table-body">
              <tr
                v-for="f in currentFields"
                :key="f.nome"
                :class="{
                  'bg-error-50': f.erro,
                  'bg-gray-50': !f.valor || !f.valor.trim(),
                  'bg-green-50': f.valor && f.valor.trim() && !f.erro
                }"
              >
                <td class="table-cell text-xs">{{ currentLineIndex + 1 }}</td>
                <td class="table-cell font-medium">
                  <span v-if="f.valor && f.valor.trim()" class="text-blue-600 font-bold">{{ f.nome }}</span>
                  <span v-else class="text-gray-400">{{ f.nome }}</span>
                </td>
                <td class="table-cell text-xs">
                  {{ f.pos_inicio }}-{{ f.pos_fim }}
                </td>
                <td class="table-cell text-xs">{{ f.tamanho }}</td>
                <td class="table-cell">
                  <code
                    class="text-xs break-all"
                    :class="{ 'text-error-600': f.erro }"
                    >{{ f.display }}</code
                  >
                </td>
                <td class="table-cell text-xs">
                  <span v-if="f.erro" class="text-error-600">{{ f.erro }}</span>
                  <span v-else class="text-success-600">OK</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-4 text-xs text-gray-500">
          Valores com tamanho divergente destacados. Espaços mostrados como '·'.<br>
          <strong>Dica:</strong> Use os botões «P / P» para navegar entre todas as {{ totalPaginasCampos }} páginas de campos ({{ camposPorPagina }} campos por página).<br>
          <strong>Comportamento:</strong> Mostra TODOS os campos de TODOS os tipos, mas apenas os campos do tipo da linha atual têm valores preenchidos.
        </p>
      </div>
    </div>

    <!-- Validation Results -->
    <div v-if="validationStore.hasValidation">
      <div class="mb-4 p-4 bg-green-100 text-green-800 rounded">
        🎉 CONDIÇÃO ATENDIDA: Dados de validação carregados!
      </div>
      <ValidationResults />
    </div>

  </div>
</template>

<script setup>
import LayoutMapper from "@/components/LayoutMapper.vue";
import ValidationResults from "@/components/ValidationResults.vue";
import { useValidationStore } from "@/stores/validation";
import {
  AlertCircle,
  CheckSquare,
  FileSpreadsheet,
  Upload,
} from "lucide-vue-next";
import { computed, ref, watch, onMounted } from "vue";
import { useTempStore } from '@/stores/temp'

const validationStore = useValidationStore();

// Mostrar painel de debug apenas em modo desenvolvimento
const isDev = !!import.meta.env.DEV;

// Reactive data
const layoutFile = ref(null);
const dataFile = ref(null);
const maxErrors = ref(100); // Valor padrão balanceado para performance
const previewLayout = ref(false);
const layoutPreview = ref(null);
const layoutLoading = ref(false);
const showMapper = ref(false);
const mappingConfirmed = ref(false);
const mappingData = ref(null);
const organizarLayout = ref(null); // legado: não mais usado para renderização

// Refs para os inputs
const layoutFileInput = ref(null);
const dataFileInput = ref(null);
const armazenaLayout = ref(null);

// Handle file changes
const handleLayoutFileChange = async (event) => {
  const file = event?.target?.files?.[0] || event?.dataTransfer?.files?.[0];
  if (!file) return;

  // Manter o arquivo selecionado
  layoutFile.value = file;
  showMapper.value = false;
  mappingConfirmed.value = false;
  mappingData.value = null;
  layoutPreview.value = null;
  organizarLayout.value = null;

  if (previewLayout.value) {
    layoutLoading.value = true;
    try {
      armazenaLayout.value = await validationStore.validateLayout(file);
      // mantenha o objeto completo no layoutPreview
      layoutPreview.value = armazenaLayout.value;
  // organizarLayout (legado) não é mais necessário; filtragem é feita por grupo
      console.log("Layout preview carregado:", layoutPreview.value);
    } catch (_) {
      layoutPreview.value = null;
    } finally {
      layoutLoading.value = false;
    }
  }
};

// Handle data file (TXT) change
const handleDataFileChange = async (event) => {
  const file = event?.target?.files?.[0] || event?.dataTransfer?.files?.[0];
  if (!file) return;

  dataFile.value = file;
  // Recarrega o preview paginado de registros
  try {
    await loadFileLines();
  } catch (e) {
    console.error('Falha ao carregar linhas do arquivo de dados:', e);
    fileLines.value = [];
    fullLineCount.value = 0;
  }
};

// Handle validation
const handleValidation = async () => {
  // Verificar se os arquivos ainda estão disponíveis
  if (!layoutFile.value || !dataFile.value) {
    console.error("Arquivos não disponíveis:", {
      layout: !!layoutFile.value,
      data: !!dataFile.value,
    });
    return;
  }

  // Se usuário já abriu mapper exige confirmação
  if (showMapper.value && !mappingConfirmed.value) {
    console.warn("Mapper aberto mas não confirmado");
    return;
  }

  console.log("Iniciando validação com arquivos:", {
    layoutFile: layoutFile.value.name,
    dataFile: dataFile.value.name,
  });

  try {
    await validationStore.validateFile(
      layoutFile.value,
      dataFile.value,
      maxErrors.value || 100
    );
    setTimeout(() => {
      const el = document.querySelector("[data-validation-results]");
      if (el) el.scrollIntoView({ behavior: "smooth" });
    }, 100);
  } catch (error) {
    console.error("Erro na validação:", error);
  }
};

const abrirMapper = () => {
  showMapper.value = true;
};
const cancelarMapper = () => {
  showMapper.value = false;
};
const onMappingConfirmed = async (payload) => {
  mappingData.value = payload;
  mappingConfirmed.value = true;
  showMapper.value = false;
  if (payload && payload.layout && payload.layout.campos) {
    // mantenha o objeto completo
    layoutPreview.value = payload.layout;
  // filtragem é dinâmica pelos grupos
  }
};

// Watch para limpar preview quando previewLayout é desabilitado
watch(previewLayout, (newValue) => {
  if (!newValue) {
    layoutPreview.value = null;
  } else if (
    (console.log("Habilitando previewLayout novamente"), layoutFile.value)
  ) {
    // Recarregar preview se habilitado novamente
    validationStore
      .validateLayout(layoutFile.value)
      .then((result) => {
        console.log(
          "Recarregando preview do layout após reabilitar previewLayout"
        );
        console.log(
          "Recarregando preview do layout após reabilitar previewLayout"
        );
        armazenaLayout.value = result;
        layoutPreview.value = armazenaLayout.value;
        console.log("Layout preview recarregado:", layoutPreview.value);
      })
      .catch(() => {
        console.error("Erro ao recarregar preview do layout");
        layoutPreview.value = null;
      });
  }
});

// Watch para debug da reatividade
// Removido watch de debug

// Removido clearValidation ao montar para não apagar resultados recém-gerados ao voltar para a tela
// Limpa apenas erros residuais (ex: mensagem de erro anterior)
validationStore.clearError();
// Montagem concluída

// Ao montar, verificar se o Mapeamento deixou algo no temp store (arquivo ou filename)
onMounted(async () => {
  try {
    const temp = useTempStore()
    if (temp.layoutFile) {
      const lf = temp.layoutFile
      layoutFile.value = lf
      try { const dt = new DataTransfer(); dt.items.add(lf); if (layoutFileInput.value) layoutFileInput.value.files = dt.files } catch (e) { /* ignore */ }
      if (temp.layoutData) layoutPreview.value = temp.layoutData
      temp.clear()
      return
    }

    if (temp.layoutFilename && !temp.layoutFile) {
      const filename = temp.layoutFilename
      let downloadUrl = `/api/layout-export/download/${filename}`
      try {
        let resp = await fetch(downloadUrl)
        if (!resp.ok) {
          // tentar backend direto
          const backendUrl = `http://localhost:8000${downloadUrl}`
          resp = await fetch(backendUrl)
          if (!resp.ok) throw new Error('Falha ao baixar layout: ' + resp.status)
          downloadUrl = backendUrl
        }
        const blob = await resp.blob()
        const file = new File([blob], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        layoutFile.value = file
        try { const dt = new DataTransfer(); dt.items.add(file); if (layoutFileInput.value) layoutFileInput.value.files = dt.files } catch (e) {}
        if (temp.layoutData) layoutPreview.value = temp.layoutData
        temp.clear()
        return
      } catch (err) {
        console.warn('Não foi possível baixar layout indicado pelo Mapeamento:', err)
        // continuar fallback para history.state
      }
    }

    // fallback: verificar history.state (compatibilidade antiga)
    const st = window.history.state || {}
    if (st.layoutFile) {
      const lf = st.layoutFile
      if (lf instanceof File) {
        layoutFile.value = lf
        try { const dt = new DataTransfer(); dt.items.add(lf); if (layoutFileInput.value) layoutFileInput.value.files = dt.files } catch (e) {}
        if (st.layoutData) layoutPreview.value = st.layoutData
      }
    }
  } catch (err) {
    console.warn('Erro ao processar layout pré-carregado:', err)
  }
})

// Preview paginado de registros
const fileLines = ref([]);
const fullLineCount = ref(0);
const currentLineIndex = ref(0);
const jumpLine = ref(1);
const MAX_PREVIEW_LINES = 500;
const truncated = ref(false);

const loadFileLines = async () => {
  fileLines.value = [];
  fullLineCount.value = 0;
  currentLineIndex.value = 0;
  jumpLine.value = 1;
  truncated.value = false;
  if (!dataFile.value) return;
  const text = await dataFile.value.text();
  const lines = text.split(/\r?\n/);
  fullLineCount.value = lines.length;
  if (lines.length > MAX_PREVIEW_LINES) {
    fileLines.value = lines.slice(0, MAX_PREVIEW_LINES);
    truncated.value = true;
  } else {
    fileLines.value = lines;
  }
};

watch(dataFile, () => {
  loadFileLines();
});
watch(layoutPreview, () => {
  /* re-render fields */
});

const currentRawLine = computed(
  () => fileLines.value[currentLineIndex.value] || ""
);

// Utilidades para agrupamento
const normalizeName = (s) => String(s || "").trim().toUpperCase();
const prefix5 = (s) => normalizeName(s).slice(0, 5);
// Prefixo da linha atual (sem trim do conteúdo total para não afetar posições; apenas detecção do tipo)
const currentLineKey = computed(() => (currentRawLine.value || "").slice(0, 5).toUpperCase());

// Lista completa de campos (ou vazia)
const allCampos = computed(() => layoutPreview.value?.campos ?? []);

// Função removida - não mais necessária com paginação

// Resetar para a primeira página quando mudar o layout
watch(allCampos, () => {
  paginaAtualCampos.value = 1;
});

// Todos os campos sem filtro (será paginado)
const allVisibleCampos = computed(() => {
  return allCampos.value;
});

// Paginação de campos
const camposPorPagina = ref(50); // Mostrar 50 campos por página
const paginaAtualCampos = ref(1);

const totalPaginasCampos = computed(() => {
  return Math.ceil(allVisibleCampos.value.length / camposPorPagina.value);
});

const visibleCampos = computed(() => {
  const inicio = (paginaAtualCampos.value - 1) * camposPorPagina.value;
  const fim = inicio + camposPorPagina.value;
  return allVisibleCampos.value.slice(inicio, fim);
});

// Funções de navegação da paginação
const proximaPaginaCampos = () => {
  if (paginaAtualCampos.value < totalPaginasCampos.value) {
    paginaAtualCampos.value++;
  }
};

const paginaAnteriorCampos = () => {
  if (paginaAtualCampos.value > 1) {
    paginaAtualCampos.value--;
  }
};

// Função de navegação direta removida - usando apenas botões anterior/próximo

// Navegação removida - agora usamos paginação de campos

const parseLine = (raw) => {
  if (!layoutPreview.value || !raw) return [];
  const campos = visibleCampos.value;

  // Detectar tipo de registro da linha atual
  const lineType = raw.slice(0, 2); // Primeiros 2 chars
  const tipoPrefix = `NFE${lineType}-`;

  // Sanear linha: remover CR final e garantir comprimento mínimo com padding
  let line = raw;
  if (line.endsWith("\r")) line = line.slice(0, -1);
  // Tabs não devem deslocar colunas; se existirem, trate como espaços
  line = line.replace(/\t/g, " ");
  const expected = layoutPreview.value?.tamanho_linha || line.length;
  if (line.length < expected) {
    line = line.padEnd(expected, " ");
  }

  return campos.map((c) => {
    let valor = "";
    let erro = null;

    // LÓGICA PRINCIPAL: só extrair valor se o campo pertence ao tipo da linha
    if (c.nome.startsWith(tipoPrefix)) {
      // Campo pertence ao tipo da linha atual - extrair valor
      const startIdx = Math.max(0, (c.posicao_inicio || 1) - 1);
      const endExclusive = c.posicao_fim
        ? c.posicao_fim
        : startIdx + (c.tamanho || 0);
      valor = line.slice(startIdx, endExclusive);

      // Validar apenas campos que têm valor
      const trimmed = valor.trim();
      const tipo = (c.tipo || "").toUpperCase();
      const overflow = c.tamanho ? valor.length > c.tamanho : false;
      const invalidNumero = tipo === "NUMERO" && valor && /[^0-9 ]/.test(valor);
      const invalidData = tipo === "DATA" && valor && !/^\d{8}$/.test(valor);
      const invalidDecimal = tipo === "DECIMAL" && valor && /[^0-9 ]/.test(valor);

      if (c.obrigatorio && trimmed.length === 0) {
        erro = "Vazio obrigatório";
      } else if (invalidNumero) {
        erro = "Caracter inválido (NUMERO)";
      } else if (invalidData) {
        erro = "Data inválida (AAAAmmdd)";
      } else if (invalidDecimal) {
        erro = "Decimal inválido (somente dígitos)";
      } else if (overflow) {
        erro = `Excede (${valor.length}/${c.tamanho})`;
      }
    }
    // Caso contrário, campo fica vazio (é de outro tipo)

    return {
      nome: c.nome,
      pos_inicio: c.posicao_inicio,
      pos_fim: c.posicao_fim || (c.posicao_inicio + c.tamanho - 1),
      tamanho: c.tamanho,
      valor,
      display: (valor || "").replace(/ /g, "·") || "(vazio)",
      erro,
    };
  });
};

const currentFields = computed(() => parseLine(currentRawLine.value));
const totalLines = computed(() => fileLines.value.length);

const nextRecord = () => {
  if (currentLineIndex.value < totalLines.value - 1) {
    currentLineIndex.value++;
    jumpLine.value = currentLineIndex.value + 1;
  }
};
const prevRecord = () => {
  if (currentLineIndex.value > 0) {
    currentLineIndex.value--;
    jumpLine.value = currentLineIndex.value + 1;
  }
};
const firstRecord = () => {
  currentLineIndex.value = 0;
  jumpLine.value = 1;
};
const lastRecord = () => {
  currentLineIndex.value = totalLines.value - 1;
  jumpLine.value = totalLines.value;
};
const jumpToLine = () => {
  if (!jumpLine.value) return;
  let idx = jumpLine.value - 1;
  if (idx < 0) idx = 0;
  if (idx > totalLines.value - 1) idx = totalLines.value - 1;
  currentLineIndex.value = idx;
  jumpLine.value = idx + 1;
};
</script>
