<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import NavBar from '@/components/NavBar.vue'

const router = useRouter()
const route = useRoute()

// Hide NavBar on the detail page (/:date)
const showNavBar = computed(() => route.name !== '/[date]')

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
    e.preventDefault()
    router.push('/search')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <NavBar v-if="showNavBar" />
  <router-view />
</template>

<style scoped></style>
