<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navbar -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="flex items-center space-x-2">
              <div class="w-8 h-8 bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg flex items-center justify-center">
                <FileText class="w-5 h-5 text-white" />
              </div>
              <span class="text-xl font-bold text-gradient">Validador de Documentos</span>
            </router-link>
          </div>

          <!-- Navigation Links -->
          <div class="hidden md:flex items-center space-x-8">
            <router-link
              v-for="link in navLinks"
              :key="link.name"
              :to="link.path"
              class="nav-link"
              :class="{ 'nav-link-active': $route.name === link.name }"
            >
              <component :is="link.icon" class="w-4 h-4" />
              {{ link.label }}
            </router-link>
          </div>

          <!-- Mobile menu button -->
          <div class="md:hidden flex items-center">
            <button
              @click="mobileMenuOpen = !mobileMenuOpen"
              class="text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700"
            >
              <Menu class="w-6 h-6" v-if="!mobileMenuOpen" />
              <X class="w-6 h-6" v-else />
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile menu -->
      <div v-show="mobileMenuOpen" class="md:hidden bg-white border-t border-gray-200">
        <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
          <router-link
            v-for="link in navLinks"
            :key="link.name"
            :to="link.path"
            class="mobile-nav-link"
            :class="{ 'mobile-nav-link-active': $route.name === link.name }"
            @click="mobileMenuOpen = false"
          >
            <component :is="link.icon" class="w-4 h-4" />
            {{ link.label }}
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-12">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div class="text-center text-gray-500 text-sm">
          <p>&copy; 2024 Validador de Documentos Sequenciais - Claro/Embratel</p>
          <p class="mt-1">Desenvolvido para otimizar a análise de arquivos sequenciais</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { BarChart3, CheckSquare, FileSpreadsheet, FileText, Home, Menu, X } from 'lucide-vue-next'
import { ref } from 'vue'

const mobileMenuOpen = ref(false)

const navLinks = [
  { name: 'Home', path: '/', label: 'Início', icon: Home },
  { name: 'Validator', path: '/validador', label: 'Validador', icon: CheckSquare },
  { name: 'Mapeamento', path: '/mapeamento', label: 'Mapeamento', icon: FileText },
  { name: 'Layout', path: '/layout', label: 'Layout', icon: FileSpreadsheet },
  { name: 'Reports', path: '/relatorios', label: 'Relatórios', icon: BarChart3 },
]
</script>

<style>
.nav-link {
  @apply flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-blue-700 hover:bg-blue-50 transition-colors duration-200;
}

.nav-link-active {
  @apply text-blue-700 bg-blue-50;
}

.mobile-nav-link {
  @apply flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-700 hover:bg-blue-50 transition-colors duration-200;
}

.mobile-nav-link-active {
  @apply text-blue-700 bg-blue-50;
}
</style>