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
      <div class="card-header">
        <h3 class="text-lg font-semibold flex items-center">
          <FileSpreadsheet class="w-5 h-5 mr-2" />
          Preview do Layout: {{ layoutPreview.nome }}
        </h3>
      </div>
      <div class="card-body">
        <!-- Paginação por Tipo de Registro para Layout -->
        <div v-if="layoutTipos.length > 1" class="mb-3 flex items-center gap-2 text-sm">
          <button class="btn-secondary px-2 py-1" @click="layoutTipoFirst" :disabled="layoutTipoIndex === 0">«</button>
          <button class="btn-secondary px-2 py-1" @click="layoutTipoPrev" :disabled="layoutTipoIndex === 0">‹</button>
          <div class="flex items-center gap-2">
            <span>Registro:</span>
            <span class="font-mono px-2 py-0.5 rounded bg-gray-100">{{ layoutTipoAtual }}</span>
            <span class="text-gray-500">( {{ layoutTipoIndex + 1 }} / {{ layoutTipos.length }} )</span>
          </div>
          <button class="btn-secondary px-2 py-1" @click="layoutTipoNext" :disabled="layoutTipoIndex === layoutTipos.length - 1">›</button>
          <button class="btn-secondary px-2 py-1" @click="layoutTipoLast" :disabled="layoutTipoIndex === layoutTipos.length - 1">»</button>
        </div>
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
              <tr v-for="campo in layoutCamposFiltrados" :key="campo.nome">
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
              <span>Registro</span>
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
              >(Mostrando primeiros {{ fileLines.length }} registros de
              {{ fullLineCount }} - arquivo truncado)</span>
        </div>
      </div>
      
      <!-- Botões para navegação entre tipos de registro -->
      <div v-if="false" class="px-6 py-3 bg-gray-50 border-b border-gray-200">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-sm font-medium text-gray-700">Tipo de Registro:</span>
          <button
            v-for="tipo in tiposRegistro"
            :key="tipo"
            @click="selecionarTipoRegistro(tipo)"
            :class="[
              'px-3 py-1 rounded text-sm font-medium transition-colors',
              tipoRegistroSelecionado === tipo
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-100'
            ]"
          >
            Tipo {{ tipo }}
          </button>
          <button
            @click="selecionarTipoRegistro(null)"
            :class="[
              'px-3 py-1 rounded text-sm font-medium transition-colors',
              tipoRegistroSelecionado === null
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-100'
            ]"
          >
            Todos
          </button>
        </div>
      </div>
      <div class="card-body">
        <div class="mb-3 text-xs text-gray-500">
          Comprimento da linha atual: {{ currentRawLine.length }} / Tamanho
          esperado layout: {{ layoutPreview.tamanho_linha }}
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
          <strong v-if="tiposRegistro.length > 1">Multi-Registro:</strong> 
          <span v-if="tiposRegistro.length > 1">Use os botões de tipo de registro acima para filtrar campos específicos ou visualizar todos.</span>
          <span v-else>Navegue entre as linhas usando os controles de paginação.</span>
        </p>
      </div>
    </div>

    <!-- Validation Results -->
    <div v-if="validationStore.hasValidation">
      <div class="mb-4 p-4 bg-green-100 text-green-800 rounded">
        🎉 CONDIÇÃO ATENDIDA: Dados de validação carregados! hasValidation =
        {{ validationStore.hasValidation }}
      </div>
      <ValidationResults />
    </div>

    <!-- Debug do estado -->
    <div class="mt-4 p-4 bg-gray-100 text-sm rounded">
      <strong>Debug Estado:</strong><br />
      hasValidation: {{ validationStore.hasValidation }}<br />
      isLoading: {{ validationStore.isLoading }}<br />
      currentValidation existe: {{ !!validationStore.currentValidation }}
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
import { computed, ref, watch } from "vue";

const validationStore = useValidationStore();

// Reactive data
const layoutFile = ref(null);
const dataFile = ref(null);
const maxErrors = ref(100); // Valor padrão balanceado para performance
const previewLayout = ref(true);
const layoutPreview = ref(null);
const layoutLoading = ref(false);
const showMapper = ref(false);
const mappingConfirmed = ref(false);
const mappingData = ref(null);
const organizarLayout = ref(null);

// Refs para os inputs
const layoutFileInput = ref(null);
const dataFileInput = ref(null);
const armazenaLayout = ref(null);

// Handle file changes
const handleLayoutFileChange = async (event) => {
  const file = event.target.files[0];
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
      // Inicializar com o primeiro tipo de registro ou mostrar todos
      const tipos = new Set();
      layoutPreview.value?.campos?.forEach(campo => {
        const match = campo.nome.match(/^NFE(\d+)-/);
        if (match) tipos.add(match[1]);
      });
      
  // Ajustar layout automaticamente ao registro atual
  syncLayoutToCurrentLine();
      
      console.log("Layout preview carregado:", layoutPreview.value);
      console.log("Tipos detectados:", Array.from(tipos));
    } catch (_) {
      layoutPreview.value = null;
    } finally {
      layoutLoading.value = false;
    }
  }

  // NÃO limpar o input - manter arquivo selecionado para validação
};

const handleDataFileChange = (event) => {
  const file = event.target.files[0];
  if (file) {
    dataFile.value = file;
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
    // Detectar tipos e selecionar o primeiro
    const tipos = new Set();
    layoutPreview.value.campos.forEach(campo => {
      const match = campo.nome.match(/^NFE(\d+)-/);
      if (match) tipos.add(match[1]);
    });
    
  // Ajustar layout automaticamente ao registro atual
  syncLayoutToCurrentLine();
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
        console.log("Recarregando preview do layout após reabilitar previewLayout");
        armazenaLayout.value = result;
        layoutPreview.value = armazenaLayout.value;
        
        // Detectar tipos e selecionar o primeiro
        const tipos = new Set();
        layoutPreview.value?.campos?.forEach(campo => {
          const match = campo.nome.match(/^NFE(\d+)-/);
          if (match) tipos.add(match[1]);
        });
        
  // Ajustar layout automaticamente ao registro atual
  syncLayoutToCurrentLine();
        
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

// Preview paginado de registros
const fileLines = ref([]);
const fullLineCount = ref(0);
const currentLineIndex = ref(0);
const jumpLine = ref(1);
const MAX_PREVIEW_LINES = 500;
const truncated = ref(false);

// Dados de preview parseados (vindos do backend para multi-registro)
const previewRegistros = ref([]);
const tiposRegistroEncontrados = ref([]);

// Layout preview: paginação por tipo de registro
const layoutTipos = computed(() => {
  if (!layoutPreview.value?.campos) return [];
  const setTipos = new Set();
  layoutPreview.value.campos.forEach(c => {
    const m = String(c.nome).match(/^NFE(\d+)-/);
    if (m) setTipos.add(m[1]);
  });
  return Array.from(setTipos).sort();
});
const layoutTipoIndex = ref(0);
const layoutTipoAtual = computed(() => layoutTipos.value[layoutTipoIndex.value] || null);
const layoutCamposFiltrados = computed(() => {
  if (!layoutPreview.value?.campos) return [];
  if (!layoutTipoAtual.value) return layoutPreview.value.campos;
  return layoutPreview.value.campos.filter(c => String(c.nome).startsWith(`NFE${layoutTipoAtual.value}-`) || String(c.nome).includes(` NFE${layoutTipoAtual.value}-`));
});
const layoutTipoFirst = () => { layoutTipoIndex.value = 0; };
const layoutTipoPrev = () => { if (layoutTipoIndex.value > 0) layoutTipoIndex.value--; };
const layoutTipoNext = () => { if (layoutTipoIndex.value < layoutTipos.value.length - 1) layoutTipoIndex.value++; };
const layoutTipoLast = () => { layoutTipoIndex.value = Math.max(0, layoutTipos.value.length - 1); };

// Ajustar layoutTipoIndex ao carregar um novo layout
watch(layoutPreview, () => {
  layoutTipoIndex.value = 0;
});

// Detectar tipos de registro disponíveis (somente informativo)
const tiposRegistro = computed(() => {
  if (tiposRegistroEncontrados.value && tiposRegistroEncontrados.value.length > 0) {
    return tiposRegistroEncontrados.value;
  }
  if (!layoutPreview.value?.campos) return [];
  const tipos = new Set();
  layoutPreview.value.campos.forEach(campo => {
    const match = campo.nome.match(/^NFE(\d+)-/);
    if (match) tipos.add(match[1]);
  });
  return Array.from(tipos).sort();
});

// Sincroniza o layout exibido com o tipo do registro atual
const syncLayoutToCurrentLine = () => {
  if (!layoutPreview.value) return;
  let tipo = null;
  if (previewRegistros.value && previewRegistros.value.length > 0) {
    const reg = previewRegistros.value[currentLineIndex.value];
    tipo = reg?.tipo_registro || null;
  } else {
    const raw = currentRawLine.value || '';
    if (raw.length >= 2) tipo = raw.slice(0, 2);
  }
  if (tipo) {
    organizarLayout.value = (layoutPreview.value?.campos || []).filter(c => c.nome.startsWith(`NFE${tipo}-`));
  } else {
    organizarLayout.value = layoutPreview.value?.campos || [];
  }
};

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
  syncLayoutToCurrentLine();
});

// Watch para quando a validação for concluída
watch(() => validationStore.currentValidation, (newValidation) => {
  if (newValidation) {
    // Atualizar preview de registros se disponível
    if (newValidation.preview_registros) {
      previewRegistros.value = newValidation.preview_registros;
    }
    
    // Atualizar tipos de registro encontrados
    if (newValidation.tipos_registro_encontrados) {
      tiposRegistroEncontrados.value = newValidation.tipos_registro_encontrados;
      
  // Sincronizar com o registro atual
  syncLayoutToCurrentLine();
    }
  }
});

const currentRawLine = computed(
  () => fileLines.value[currentLineIndex.value] || ""
);

const parseLine = (raw) => {
  if (!layoutPreview.value || !raw) return [];
  
  // Se temos preview de registros do backend, usar eles
  if (previewRegistros.value && previewRegistros.value.length > 0) {
    const registro = previewRegistros.value[currentLineIndex.value];
    if (registro && registro.campos) {
      const tipoRegistro = registro.tipo_registro;
      // Converter campos do objeto para array no formato esperado
      return Object.entries(registro.campos).map(([nomeCampo, valorCampo]) => {
        // Encontrar informações do campo no layout (com ou sem prefixo [Tipo X])
        let campoInfo = layoutPreview.value.campos.find(c => c.nome === nomeCampo);
        if (!campoInfo) {
          campoInfo = layoutPreview.value.campos.find(c => c.nome.endsWith(nomeCampo) || c.nome.includes(` ${nomeCampo}`));
        }
        
        const valor = valorCampo || '';
        const tamanho = campoInfo?.tamanho || valor.length;
        const tipo = (campoInfo?.tipo || 'TEXTO').toUpperCase();
        const obrigatorio = campoInfo?.obrigatorio || false;
        
        // Validação básica
        const trimmed = valor.trim();
        const overflow = valor.length > tamanho;
        const invalidNumero = tipo === "NUMERO" && valor && /[^0-9 ]/.test(valor);
        const invalidData = tipo === "DATA" && valor && !/^\d{8}$/.test(trimmed);
        const invalidDecimal = tipo === "DECIMAL" && valor && /[^0-9., ]/.test(valor);
        
        let erro = null;
        if (obrigatorio && trimmed.length === 0) {
          erro = "Vazio obrigatório";
        } else if (invalidNumero) {
          erro = "Caracter inválido (NUMERO)";
        } else if (invalidData) {
          erro = "Data inválida (AAAAmmdd)";
        } else if (invalidDecimal) {
          erro = "Decimal inválido";
        } else if (overflow) {
          erro = `Excede (${valor.length}/${tamanho})`;
        }
        
        return {
          nome: nomeCampo,
          pos_inicio: campoInfo?.posicao_inicio || 0,
          pos_fim: campoInfo?.posicao_fim || (campoInfo?.posicao_inicio || 0) + tamanho,
          tamanho: tamanho,
          valor: valor,
          display: (valor || "").replace(/ /g, "·") || "(vazio)",
          erro: erro
        };
      });
    }
  }
  
  // Método antigo: parsear manualmente da linha raw
  const campos =
    (organizarLayout.value && organizarLayout.value.length
      ? organizarLayout.value
      : layoutPreview.value?.campos) || [];
  return campos.map((c) => {
    const startIdx = c.posicao_inicio - 1;
    const endIdx = c.posicao_fim
      ? c.posicao_fim
      : c.posicao_inicio - 1 + c.tamanho;
    let valor = raw.slice(startIdx, endIdx);
    const trimmed = valor.trim();
    const tipo = (c.tipo || "").toUpperCase();
    // Apenas erro se exceder o tamanho; valores menores (preenchimento parcial) são permitidos
    const overflow = valor.length > c.tamanho;
    const invalidNumero = tipo === "NUMERO" && valor && /[^0-9 ]/.test(valor);
    const invalidData = tipo === "DATA" && valor && !/^\d{8}$/.test(valor);
    const invalidDecimal = tipo === "DECIMAL" && valor && /[^0-9 ]/.test(valor);
    let erro = null;
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
    return {
      nome: c.nome,
      pos_inicio: c.posicao_inicio,
      pos_fim: c.posicao_fim || endIdx,
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
    syncLayoutToCurrentLine();
  }
};
const prevRecord = () => {
  if (currentLineIndex.value > 0) {
    currentLineIndex.value--;
    jumpLine.value = currentLineIndex.value + 1;
    syncLayoutToCurrentLine();
  }
};
const firstRecord = () => {
  currentLineIndex.value = 0;
  jumpLine.value = 1;
  syncLayoutToCurrentLine();
};
const lastRecord = () => {
  currentLineIndex.value = totalLines.value - 1;
  jumpLine.value = totalLines.value;
  syncLayoutToCurrentLine();
};
const jumpToLine = () => {
  if (!jumpLine.value) return;
  let idx = jumpLine.value - 1;
  if (idx < 0) idx = 0;
  if (idx > totalLines.value - 1) idx = totalLines.value - 1;
  currentLineIndex.value = idx;
  jumpLine.value = idx + 1;
  syncLayoutToCurrentLine();
};
</script>
