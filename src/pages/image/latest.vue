<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMonth } from '@/composables/useApod'

const router = useRouter()

onMounted(async () => {
  try {
    const res = await fetch('/database/update.json')
    if (res.ok) {
      const data = await res.json()
      if (data.dates && data.dates.length > 0) {
        const latest = data.dates[data.dates.length - 1]
        const ym = latest.slice(0, 7)
        const entries = await fetchMonth(ym)
        const entry = entries.find((e) => e.date === latest)

        if (entry) {
          const url = entry.hdurl || entry.url
          if (url) {
            window.location.replace(url)
            return
          }
        }
      }
    }
  } catch (err) {
    console.error('Failed to redirect to latest image:', err)
  }
  // Fallback to latest page if something goes wrong
  router.replace('/latest')
})
</script>

<template>
  <div class="image-redirect">
    <div class="spinner"></div>
    <p>Redirecting to the latest original image...</p>
  </div>
</template>

<style scoped>
.latest-redirect,
.image-redirect {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #0d141f;
  color: #63b3ff;
  font-family: 'Inter', sans-serif;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(99, 179, 255, 0.1);
  border-top-color: #63b3ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
