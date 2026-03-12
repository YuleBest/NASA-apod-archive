<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAllAvailableDates, fetchEntry } from '@/composables/useApod'

const router = useRouter()

onMounted(async () => {
  try {
    const dates = await fetchAllAvailableDates()
    if (dates.length > 0) {
      const latest = dates[dates.length - 1]!
      const entry = await fetchEntry(latest)

      if (entry) {
        const url = entry.hdurl || entry.url
        if (url) {
          window.location.replace(url)
          return
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
