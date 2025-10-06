<template>
  <div class="space-y-8">
    <!-- Hero Section -->
    <div class="text-center py-12">
      <h1 class="text-4xl font-bold text-gradient mb-4">
        Validador de Documentos Sequenciais
      </h1>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
        Ferramenta profissional para validação automática de arquivos sequenciais (TXT)
        baseada em layouts definidos em Excel. Economize horas de análise manual.
      </p>
      <div class="flex justify-center space-x-4">
        <router-link to="/validador" class="btn-primary px-8 py-3 text-lg">
          <CheckSquare class="w-5 h-5 mr-2" />
          Iniciar Validação
        </router-link>
        <router-link to="/layout" class="btn-secondary px-8 py-3 text-lg">
          <FileSpreadsheet class="w-5 h-5 mr-2" />
          Testar Layout
        </router-link>
      </div>
    </div>

    <!-- Features Grid -->
    <div class="grid md:grid-cols-3 gap-8">
      <div class="card">
        <div class="card-body text-center">
          <div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Zap class="w-6 h-6 text-primary-600" />
          </div>
          <h3 class="text-lg font-semibold mb-2">Validação Rápida</h3>
          <p class="text-gray-600">
            Processe arquivos de milhares de linhas em segundos.
            Detecção automática de erros de formato, tipo e campos obrigatórios.
          </p>
        </div>
      </div>

      <div class="card">
        <div class="card-body text-center">
          <div class="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <BarChart3 class="w-6 h-6 text-success-600" />
          </div>
          <h3 class="text-lg font-semibold mb-2">Relatórios Detalhados</h3>
          <p class="text-gray-600">
            Relatórios completos em Excel, CSV ou texto com estatísticas,
            gráficos e detalhes de cada erro encontrado.
          </p>
        </div>
      </div>

      <div class="card">
        <div class="card-body text-center">
          <div class="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Shield class="w-6 h-6 text-warning-600" />
          </div>
          <h3 class="text-lg font-semibold mb-2">Layouts Flexíveis</h3>
          <p class="text-gray-600">
            Suporte a múltiplos tipos de dados (texto, número, data, decimal)
            com validação de formatos específicos.
          </p>
        </div>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg text-white p-8">
      <div class="text-center mb-8">
        <h2 class="text-2xl font-bold mb-2">Impacto na Produtividade</h2>
        <p class="text-primary-100">Resultados reais de uso na Claro/Embratel</p>
      </div>

      <div class="grid md:grid-cols-4 gap-6 text-center">
        <div>
          <div class="text-3xl font-bold mb-2">95%</div>
          <div class="text-primary-100">Redução no tempo de análise</div>
        </div>
        <div>
          <div class="text-3xl font-bold mb-2">99.9%</div>
          <div class="text-primary-100">Precisão na detecção</div>
        </div>
        <div>
          <div class="text-3xl font-bold mb-2">10x</div>
          <div class="text-primary-100">Aumento na capacidade</div>
        </div>
        <div>
          <div class="text-3xl font-bold mb-2">100%</div>
          <div class="text-primary-100">Rastreabilidade</div>
        </div>
      </div>
    </div>

    <!-- How it Works -->
    <div>
      <h2 class="text-2xl font-bold text-center mb-8">Como Funciona</h2>
      <div class="grid md:grid-cols-3 gap-8">
        <div class="text-center">
          <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span class="text-2xl font-bold text-primary-600">1</span>
          </div>
          <h3 class="font-semibold mb-2">Upload do Layout</h3>
          <p class="text-gray-600 text-sm">
            Envie seu arquivo Excel com as especificações dos campos:
            posição, tamanho, tipo e se é obrigatório.
          </p>
        </div>

        <div class="text-center">
          <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span class="text-2xl font-bold text-primary-600">2</span>
          </div>
          <h3 class="font-semibold mb-2">Upload dos Dados</h3>
          <p class="text-gray-600 text-sm">
            Envie o arquivo TXT sequencial que você quer validar.
            A ferramenta processará linha por linha.
          </p>
        </div>

        <div class="text-center">
          <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span class="text-2xl font-bold text-primary-600">3</span>
          </div>
          <h3 class="font-semibold mb-2">Relatório Completo</h3>
          <p class="text-gray-600 text-sm">
            Receba relatórios detalhados com todos os erros encontrados,
            estatísticas e sugestões de correção.
          </p>
        </div>
      </div>
    </div>

    <!-- Supported Formats -->
    <div class="card">
      <div class="card-header">
        <h2 class="text-lg font-semibold">Formatos Suportados</h2>
      </div>
      <div class="card-body">
        <div class="grid md:grid-cols-2 gap-6">
          <div>
            <h3 class="font-medium mb-3 flex items-center">
              <FileSpreadsheet class="w-4 h-4 mr-2 text-green-600" />
              Layouts (Excel)
            </h3>
            <ul class="text-sm text-gray-600 space-y-1">
              <li>• Arquivos .xlsx e .xls</li>
              <li>• Colunas: Campo, Posicao_Inicio, Tamanho, Tipo, Obrigatorio</li>
              <li>• Tipos: TEXTO, NUMERO, DATA, DECIMAL</li>
              <li>• Formatos personalizados para datas</li>
            </ul>
          </div>
          <div>
            <h3 class="font-medium mb-3 flex items-center">
              <FileText class="w-4 h-4 mr-2 text-blue-600" />
              Dados (TXT)
            </h3>
            <ul class="text-sm text-gray-600 space-y-1">
              <li>• Arquivos de texto (.txt)</li>
              <li>• Codificação UTF-8 ou Latin-1</li>
              <li>• Linhas de tamanho fixo</li>
              <li>• Sem limitação de tamanho</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { CheckSquare, FileSpreadsheet, Zap, BarChart3, Shield, FileText } from 'lucide-vue-next'
</script>