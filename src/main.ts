import './style.css'
import { createApp } from 'vue'
import { createHead } from '@unhead/vue/client'
import { createRouter, createWebHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'
import App from './App.vue'

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const head = createHead()
createApp(App).use(router).use(head).mount('#app')
