import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Comparacao from '../views/Comparacao.vue'
import Reports from '../views/Reports.vue'
import ErrorReport from '../views/ErrorReport.vue'
import Mapeamento from '../views/Mapeamento.vue'
import Calculadora from '../views/Calculadora.vue'
import PrintCenter from '../views/PrintCenter.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
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
  {
    path: '/printcenter',
    name: 'PrintCenter',
    component: PrintCenter
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router