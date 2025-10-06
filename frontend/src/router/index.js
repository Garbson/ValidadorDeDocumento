import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Validator from '../views/Validator.vue'
import Reports from '../views/Reports.vue'
import Layout from '../views/Layout.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/validador',
    name: 'Validator',
    component: Validator
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
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router