import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Visualizador from '../views/Visualizador.vue'
import Comparacao from '../views/Comparacao.vue'
import Reports from '../views/Reports.vue'
import ErrorReport from '../views/ErrorReport.vue'
import Layout from '../views/Layout.vue'
import Mapeamento from '../views/Mapeamento.vue'
import Calculadora from '../views/Calculadora.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
  path: '/visualizador',
  name: 'Visualizador',
  component: Visualizador
  },
  {
    path: '/comparacao',
    name: 'Comparacao',
    component: Comparacao
  },
  {
    path: '/relatorio-erros',
    name: 'ErrorReport',
    component: ErrorReport
  },
  {
    path: '/layout',
    name: 'Layout',
    component: Layout
  },
  {
    path: '/relatorios',
    name: 'Reports',
    component: Reports
  },
  {
    path: '/mapeamento',
    name: 'Mapeamento',
    component: Mapeamento
  },
  {
    path: '/calculadora',
    name: 'Calculadora',
    component: Calculadora
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router