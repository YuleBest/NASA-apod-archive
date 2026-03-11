<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHead } from '@unhead/vue'
import { fetchEntry, isVideo, type ApodEntry } from '@/composables/useApod'

const route = useRoute('/[date]')
const router = useRouter()

const date = computed(() => route.params.date)
const entry = ref<ApodEntry | null>(null)
const loading = ref(true)
const error = ref('')
const imgLoaded = ref(false)

useHead({
  title: computed(() => (entry.value ? `${entry.value.title} | NASA APOD` : 'NASA APOD Details')),
  meta: [
    {
      name: 'description',
      content: computed(
        () =>
          entry.value?.explanation?.slice(0, 160) || 'NASA Astronomy Picture of the Day details.',
      ),
    },
    { property: 'og:title', content: computed(() => entry.value?.title || 'NASA APOD') },
    {
      property: 'og:description',
      content: computed(() => entry.value?.explanation?.slice(0, 160) || 'NASA APOD Image'),
    },
    { property: 'og:image', content: computed(() => entry.value?.url || '') },
    { name: 'twitter:card', content: 'summary_large_image' },
  ],
})

const allAvailableDates = ref<string[]>([])

async function loadData() {
  loading.value = true
  imgLoaded.value = false
  try {
    const data = await fetchEntry(date.value)
    if (!data) {
      error.value = 'Entry not found'
    } else {
      entry.value = data
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await fetch('/database/update.json')
    if (res.ok) {
      const data: { dates: string[] } = await res.json()
      allAvailableDates.value = data.dates
    }
  } catch {}
  await loadData()
})

watch(date, () => {
  loadData()
})

// adjacent dates
function navigate(dir: -1 | 1) {
  if (!allAvailableDates.value.length) return
  const idx = allAvailableDates.value.indexOf(date.value)
  if (idx === -1) return
  const nextTarget = allAvailableDates.value[idx + dir]
  if (nextTarget) router.push(`/${nextTarget}`)
}

function formatDate(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const displayUrl = computed(() => entry.value?.hdurl || entry.value?.url || null)
const isVid = computed(() => isVideo(entry.value?.url ?? null))
</script>

<template>
  <div class="detail">
    <!-- Nav bar -->
    <nav class="topbar">
      <button class="back-btn" @click="router.push('/')">← Back</button>
      <span class="topbar-date">{{ date }}</span>
      <div class="nav-arrows">
        <button class="arrow-btn" @click="navigate(-1)" title="Newer">‹</button>
        <button class="arrow-btn" @click="navigate(1)" title="Older">›</button>
      </div>
    </nav>

    <!-- Loading / Error -->
    <div v-if="loading" class="state-msg">
      <div class="spinner"></div>
      <span>Loading…</span>
    </div>
    <div v-else-if="error || !entry" class="state-msg error">
      {{ error || 'No data for this date.' }}
    </div>

    <!-- Content -->
    <template v-else>
      <div class="layout-container split-layout">
        <!-- Media -->
        <div class="media-wrap" :class="{ loaded: imgLoaded || isVid }">
          <video
            v-if="isVid"
            :src="entry.url ?? undefined"
            controls
            autoplay
            loop
            muted
            class="media-video"
          />
          <template v-else>
            <img
              v-if="displayUrl"
              :src="displayUrl"
              :alt="entry.title ?? ''"
              class="media-img"
              @load="imgLoaded = true"
            />
          </template>
        </div>

        <!-- Info panel -->
        <div class="info" :class="{ 'info-loaded': imgLoaded || isVid }">
          <div class="info-meta">
            <span class="info-date">{{ formatDate(entry.date) }}</span>
            <span v-if="entry.copyright" class="info-copy">© {{ entry.copyright }}</span>
          </div>
          <h1 class="info-title">{{ entry.title }}</h1>
          <!-- Actions -->

          <div class="actions">
            <a
              v-if="entry.hdurl && !isVid"
              :href="entry.hdurl"
              target="_blank"
              rel="noopener"
              class="btn btn-primary"
            >
              🖼 HD Image
            </a>
            <a
              :href="`https://apod.nasa.gov/apod/ap${entry.date.replace(/-/g, '').slice(2)}.html`"
              target="_blank"
              rel="noopener"
              class="btn btn-ghost"
            >
              🔗 APOD Page
            </a>
          </div>

          <div class="explanation">
            <p>{{ entry.explanation }}</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.detail {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}

/* ─── Topbar ─────────────────────────────────────────────── */
.topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: rgba(6, 12, 23, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}
.back-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.back-btn:hover {
  border-color: #63b3ff;
  color: #63b3ff;
}
.topbar-date {
  font-size: 13px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
.nav-arrows {
  display: flex;
  gap: 4px;
}
.arrow-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border);
  color: var(--text);
  width: 34px;
  height: 34px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  transition: all 0.2s;
}
.arrow-btn:hover {
  border-color: #63b3ff;
  color: #63b3ff;
}

/* ─── State ──────────────────────────────────────────────── */
.state-msg {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  padding: 120px 0;
  color: var(--text-muted);
}
.state-msg.error {
  color: #fc8181;
}
.spinner {
  width: 22px;
  height: 22px;
  border: 2px solid rgba(99, 179, 255, 0.2);
  border-top-color: #63b3ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ─── Layouts ────────────────────────────────────────────── */
.layout-container {
  display: flex;
  flex-direction: column;
  width: 100%;
}
.split-layout {
  flex-direction: row;
  height: 100vh;
  padding-top: 57px; /* topbar height */
  overflow: hidden;
}
.split-layout .media-wrap {
  flex: 0 0 auto;
  min-width: 30%;
  max-width: 65vw;
  height: calc(100vh - 57px);
  margin-top: 0;
  border-right: 1px solid var(--border);
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
}
.split-layout .info {
  flex: 1;
  height: calc(100vh - 57px);
  overflow-y: auto;
  padding: 40px 48px 80px;
  max-width: 800px;
  margin: 0;
}

@media (max-width: 900px) {
  .split-layout {
    flex-direction: column;
    height: auto;
    overflow: visible;
  }
  .split-layout .media-wrap {
    flex: none;
    max-width: 100%;
    width: 100%;
    height: auto;
    max-height: 70vh;
    border-right: none;
  }
  .split-layout .info {
    max-width: 800px;
    margin: 0 auto;
    height: auto;
    overflow-y: visible;
    padding: 32px 24px 80px;
  }
}

/* ─── Media ──────────────────────────────────────────────── */
.media-wrap {
  position: relative;
  overflow: hidden;
  background: var(--card-bg); /* skeleton base */
  transition: background 0.5s;
}
.media-wrap:not(.loaded) {
  animation: pulse-bg 1.5s infinite alternate ease-in-out;
}
@keyframes pulse-bg {
  0% {
    background-color: #0c1525;
  }
  100% {
    background-color: #1a2744;
  }
}

.media-wrap.loaded {
  background: #060c17;
}
.media-img {
  position: relative;
  height: 100%;
  width: auto;
  max-width: 100%;
  display: block;
  object-fit: contain;
  opacity: 0;
  transition: opacity 0.5s ease;
}
.media-wrap.loaded .media-img {
  opacity: 1;
}
.media-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

/* ─── Info ───────────────────────────────────────────────── */
.info {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px 80px;
  opacity: 0;
  transform: translateY(15px);
  transition:
    opacity 0.6s ease,
    transform 0.6s ease;
}
.info-loaded {
  opacity: 1;
  transform: translateY(0);
}
.info-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.info-date {
  font-size: 13px;
  color: #63b3ff;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.info-copy {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
}
.info-title {
  font-size: clamp(1.6rem, 4vw, 2.4rem);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.02em;
  margin: 0 0 24px;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
}
.btn-primary {
  background: #63b3ff;
  color: #060c17;
}
.btn-primary:hover {
  background: #90caff;
}
.btn-ghost {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border);
  color: var(--text);
}
.btn-ghost:hover {
  border-color: #63b3ff;
  color: #63b3ff;
}

.explanation p {
  font-size: 1.05rem;
  line-height: 1.9;
  color: var(--text-muted);
  margin: 0;
}
</style>
