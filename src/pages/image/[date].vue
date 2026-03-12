<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchMonth } from '@/composables/useApod'

const route = useRoute()
const router = useRouter()
const date = (route.params as any).date as string

onMounted(async () => {
  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    router.replace('/')
    return
  }

  try {
    const ym = date.slice(0, 7)
    const entries = await fetchMonth(ym)
    const entry = entries.find((e) => e.date === date)

    if (entry) {
      const url = entry.hdurl || entry.url
      if (typeof url === 'string' && url) {
        // Ensure url is a non-empty string
        window.location.replace(url)
        return
      }
    }
    router.replace(`/${date}`) // Fallback to detail page if image not found
  } catch (err) {
    console.error('Failed to redirect to image:', err)
    router.replace(`/${date}`)
  }
})
</script>

<template>
  <div class="image-redirect">
    <div class="spinner"></div>
    <p>Redirecting to original image for {{ date }}...</p>
  </div>
</template>

<style scoped>
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
