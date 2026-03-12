<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isScrolled = ref(false)

function handleScroll() {
  isScrolled.value = window.scrollY > 20
}

function goToSearch() {
  router.push('/search')
}

function goToHome() {
  router.push('/')
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  // Check initial state
  handleScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <nav class="navbar" :class="{ scrolled: isScrolled }">
    <div class="container">
      <div class="nav-brand" @click="goToHome">
        <span class="brand-text">NASA <span class="accent">APOD</span> <span>Archive</span></span>
      </div>

      <div class="nav-actions">
        <div class="search-trigger" @click="goToSearch">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="search-icon"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <span class="search-placeholder">Search...</span>
          <span class="search-shortcut">/</span>
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  width: 100%;
  height: 64px;
  background: transparent;
  border-bottom: 1px solid transparent;
  z-index: 1000;
  display: flex;
  align-items: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.navbar.scrolled {
  background: rgba(6, 12, 23, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  height: 64px;
}

.container {
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.logo {
  font-size: 20px;
}

.brand-text {
  font-weight: 800;
  font-size: 18px;
  letter-spacing: -0.01em;
}

.accent {
  color: #63b3ff;
}

.nav-actions {
  display: flex;
  align-items: center;
}

.search-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  padding: 6px 12px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-muted);
}

.search-trigger:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(99, 179, 255, 0.4);
}

.search-placeholder {
  font-size: 14px;
  font-weight: 500;
}

.search-icon {
  color: #63b3ff;
}

.search-shortcut {
  font-size: 11px;
  font-family: monospace;
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

@media (max-width: 640px) {
  .search-placeholder,
  .search-shortcut {
    display: none;
  }
  .search-trigger {
    padding: 8px;
  }
}
</style>
