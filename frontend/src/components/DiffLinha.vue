<template>
  <div class="font-mono text-sm overflow-x-auto rounded border p-2" :class="bgClass" style="white-space: pre;" :data-ref="dataRef" @scroll="$emit('scroll', $event)" @mousemove="$emit('mousemove', $event)" @mouseleave="$emit('mouseleave', $event)">
    <span v-if="highlightOverlay" class="campo-highlight-overlay" :style="highlightStyle"></span>
    <template v-if="diffAtivo && outraLinha">
      <span
        v-for="(seg, i) in segmentosDiff"
        :key="i"
        :class="seg.classe"
      >{{ seg.texto }}</span>
    </template>
    <template v-else>{{ linha }}</template>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  linha: { type: String, default: '' },
  outraLinha: { type: String, default: '' },
  tipo: { type: String, default: 'base' }, // 'base' ou 'comparado'
  diffAtivo: { type: Boolean, default: true },
  dataRef: { type: String, default: '' },
  bgClass: { type: String, default: 'bg-gray-50' },
  highlightOverlay: { type: Boolean, default: false },
  highlightStyle: { type: Object, default: () => ({}) },
});

defineEmits(['scroll', 'mousemove', 'mouseleave']);

const segmentosDiff = computed(() => {
  if (!props.linha || !props.outraLinha) return [{ texto: props.linha, classe: '' }];

  const linhaA = props.linha;
  const linhaB = props.outraLinha;
  const segmentos = [];
  let textoAtual = '';
  let isDiffAtual = null;

  const maxLen = Math.max(linhaA.length, linhaB.length);

  for (let i = 0; i < maxLen; i++) {
    const charA = i < linhaA.length ? linhaA[i] : '';
    const charB = i < linhaB.length ? linhaB[i] : '';

    // Só processa se tem caractere na linha atual
    if (i >= linhaA.length) break;

    const isDiff = charA !== charB;

    if (isDiff !== isDiffAtual && textoAtual.length > 0) {
      segmentos.push({
        texto: textoAtual,
        classe: getClasse(isDiffAtual),
      });
      textoAtual = '';
    }

    isDiffAtual = isDiff;
    textoAtual += charA;
  }

  // Último segmento
  if (textoAtual.length > 0) {
    segmentos.push({
      texto: textoAtual,
      classe: getClasse(isDiffAtual),
    });
  }

  return segmentos;
});

function getClasse(isDiff) {
  if (!isDiff) return '';

  if (props.tipo === 'base') {
    // Base: vermelho = foi removido/diferente
    return 'diff-removed';
  } else {
    // Comparado: verde = é diferente
    return 'diff-added';
  }
}
</script>

<style scoped>
.diff-removed {
  background-color: rgba(239, 68, 68, 0.2);
  color: #991b1b;
  border-radius: 2px;
  padding: 0 1px;
  text-decoration: underline;
  text-decoration-color: rgba(239, 68, 68, 0.5);
}

.diff-added {
  background-color: rgba(34, 197, 94, 0.2);
  color: #166534;
  border-radius: 2px;
  padding: 0 1px;
  text-decoration: underline;
  text-decoration-color: rgba(34, 197, 94, 0.5);
}

.campo-highlight-overlay {
  display: block;
  border-radius: 2px;
}
</style>
