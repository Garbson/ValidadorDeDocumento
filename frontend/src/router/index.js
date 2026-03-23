import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Comparacao from '../views/Comparacao.vue'
import ErrorReport from '../views/ErrorReport.vue'
import Calculadora from '../views/Calculadora.vue'
import PrintCenter from '../views/PrintCenter.vue'
import Cenarios from '../views/Cenarios.vue'

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
    path: '/calculadora',
    name: 'Calculadora',
    component: Calculadora
  },
  {
    path: '/printcenter',
    name: 'PrintCenter',
    component: PrintCenter
  },
  {
    path: '/cenarios',
    name: 'Cenarios',
    component: Cenarios
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router