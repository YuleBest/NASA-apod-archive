<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useHead } from '@unhead/vue'
import {
  fetchAvailableMonths,
  fetchMonth,
  fetchAllAvailableDates,
  isVideo,
  transitionDate,
  type ApodEntry,
} from '@/composables/useApod'

useHead({
  title: 'NASA APOD Archive | Discover the Cosmos',
  meta: [
    {
      name: 'description',
      content:
        'A curated archive of the universes most breathtaking images from NASA Astronomy Picture of the Day.',
    },
    { property: 'og:title', content: 'NASA APOD Archive' },
    {
      property: 'og:description',
      content: 'A curated archive of the universes most breathtaking images from NASA.',
    },
  ],
})

const router = useRouter()
const route = useRoute()

const allMonths = ref<string[]>([])
const allAvailableDates = ref<string[]>([])
const validYears = ref<string[]>([])
const years = computed(() => validYears.value)

const selectedYear = ref('')
const selectedMonthPart = ref('')
const activeTransitionDate = transitionDate

const validMonthsInYear = ref<string[]>([])
const selectingYear = ref(false)

const availableMonthsForYear = computed(() => {
  return validMonthsInYear.value.map((m) => m.slice(5, 7))
})

async function checkValidMonths(year: string) {
  if (!year) {
    validMonthsInYear.value = []
    return
  }
  selectingYear.value = true
  try {
    const monthsToTest = allMonths.value.filter((m) => m.startsWith(year))
    const results = await Promise.all(
      monthsToTest.map(async (m) => {
        try {
          const entries = await fetchMonth(m)
          return entries.length > 0
        } catch {
          return false
        }
      }),
    )
    validMonthsInYear.value = monthsToTest.filter((_, i) => results[i])
  } finally {
    selectingYear.value = false
  }
}

watch(selectedYear, async (newYear: string) => {
  await checkValidMonths(newYear)
  // If current selected month is not in the valid list, reset it
  if (!validMonthsInYear.value.some((m) => m.endsWith(`-${selectedMonthPart.value}`))) {
    selectedMonthPart.value = availableMonthsForYear.value[0] ?? ''
  }
})

const entries = ref<ApodEntry[]>([])
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    allAvailableDates.value = await fetchAllAvailableDates()
    allMonths.value = await fetchAvailableMonths()

    if (allMonths.value.length) {
      const rawYears = [...new Set(allMonths.value.map((m) => m.slice(0, 4)))]
      validYears.value = rawYears.filter((y) => allMonths.value.some((m) => m.startsWith(y)))

      if (validYears.value.length) {
        const qY = route.query.y as string
        const qM = route.query.m as string

        if (qY && validYears.value.includes(qY)) {
          selectedYear.value = qY
          await checkValidMonths(qY)
          if (qM && availableMonthsForYear.value.includes(qM.padStart(2, '0'))) {
            selectedMonthPart.value = qM.padStart(2, '0')
          } else {
            selectedMonthPart.value = availableMonthsForYear.value[0] ?? ''
          }
        } else {
          selectedYear.value = validYears.value[0] ?? ''
          await checkValidMonths(selectedYear.value)
          selectedMonthPart.value = availableMonthsForYear.value[0] ?? ''
        }

        await loadMonth()
      }
    }
  } catch (e: unknown) {
    console.error('Error during initial data fetch:', e)
  }
})

// Update query params when month/year changes
watch([selectedYear, selectedMonthPart], () => {
  const query = { ...route.query }
  query.y = selectedYear.value
  query.m = selectedMonthPart.value
  // Remove d from query if it exists
  delete query.d
  router.replace({ query })
})

const todayStr = (() => {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  return formatter.format(new Date()) // Returns YYYY-MM-DD
})()

const latestDateBtn = computed(() => {
  if (!allAvailableDates.value.length) return { label: 'Latest', date: '' }
  const latest = allAvailableDates.value[allAvailableDates.value.length - 1]!
  // If latest date is today or even newer (ET vs local mismatch), call it TODAY
  const isToday = latest >= todayStr
  return {
    label: isToday ? 'TODAY' : 'YESTERDAY',
    date: latest,
  }
})

const showGoDialog = ref(false)
const goDateInput = ref('')

function goToLatest() {
  router.push('/latest')
}

function handleGo() {
  if (goDateInput.value) {
    const dateStr = goDateInput.value
    // Validate if the date exists
    if (allAvailableDates.value.includes(dateStr)) {
      router.push(`/${dateStr}`)
    } else {
      alert('This date has no data or is not downloaded yet.')
    }
  }
}

function onYearChange() {
  if (!availableMonthsForYear.value.includes(selectedMonthPart.value)) {
    selectedMonthPart.value = availableMonthsForYear.value[0] ?? ''
  }
  window.scrollTo(0, 0)
  loadMonth()
}

function onMonthChange() {
  window.scrollTo(0, 0)
  loadMonth()
}

async function loadMonth() {
  if (!selectedYear.value || !selectedMonthPart.value) return
  const ym = `${selectedYear.value}-${selectedMonthPart.value}`
  loading.value = true
  error.value = ''
  try {
    const data = await fetchMonth(ym)
    entries.value = [...data].reverse().filter((e) => !e.no_data && e.title)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function goToDate(date: string) {
  transitionDate.value = date
  const navigate = () => router.push(`/${date}`)

  if (!(document as any).startViewTransition) {
    navigate()
    return
  }

  ;(document as any).startViewTransition(() => {
    navigate()
  })
}

function formatDate(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// ── Search Logic ───────────────────────────────────────────
// Search logic moved to /search page

function getFirstSentence(text?: string | null) {
  if (!text) return ''
  // Split by first period followed by a space or end of string.
  const match = text.match(/^.*?\.(?=\s|$)/)
  return match ? match[0] : text.slice(0, 120) + '...'
}
</script>

<template>
  <div class="app">
    <header class="hero">
      <div class="hero-content">
        <div class="hero-badge">🔭 NASA</div>
        <h1 class="font-domine">
          <span class="accent">Astronomy Picture</span>
          <br />
          <span>of the Day</span>
        </h1>
        <p class="hero-sub">A curated archive of the universe's most breathtaking images</p>
      </div>
    </header>

    <main class="main">
      <div class="controls">
        <div class="controls-left">
          <select v-model="selectedYear" class="month-select" @change="onYearChange()">
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
          <select v-model="selectedMonthPart" class="month-select" @change="onMonthChange()">
            <option v-for="m in availableMonthsForYear" :key="m" :value="m">{{ m }}</option>
          </select>

          <!-- Search wrapper removed (moved to Navbar) -->
        </div>

        <div class="controls-right">
          <div class="go-wrapper">
            <button class="today-btn go-btn" @click="showGoDialog = !showGoDialog">GO</button>
            <div v-if="showGoDialog" class="go-dialog">
              <input type="date" v-model="goDateInput" class="go-input" />
              <button class="today-btn" @click="handleGo()">Let's GO!</button>
            </div>
          </div>
          <button v-if="latestDateBtn.date" class="today-btn" @click="goToLatest()">
            {{ latestDateBtn.label }}
          </button>
        </div>
      </div>

      <!-- Search results moved to /search page -->

      <div v-if="loading || selectingYear" class="state-msg">
        <div class="spinner"></div>
        <span>{{ selectingYear ? 'Checking available months...' : 'Loading...' }}</span>
      </div>
      <div v-else-if="error" class="state-msg error">{{ error }}</div>

      <!-- Grid -->
      <div v-else class="grid">
        <article
          v-for="entry in entries"
          :key="entry.date"
          class="card"
          @click="goToDate(entry.date)"
        >
          <div class="card-media">
            <div v-if="isVideo(entry.url)" class="video-badge">▶ Video</div>
            <img
              v-if="!isVideo(entry.url) && entry.url"
              :src="entry.url"
              :alt="entry.title ?? ''"
              loading="lazy"
              :style="{
                viewTransitionName: entry.date === activeTransitionDate ? 'apod-image' : 'none',
              }"
            />
            <video
              v-else-if="isVideo(entry.url) && entry.url"
              :src="entry.url"
              autoplay
              loop
              muted
              playsinline
              class="video-preview"
              :style="{
                viewTransitionName: entry.date === activeTransitionDate ? 'apod-image' : 'none',
              }"
            ></video>
          </div>
          <div class="card-body">
            <div class="card-date">{{ formatDate(entry.date) }}</div>
            <h2 class="card-title">{{ entry.title }}</h2>
            <p class="card-excerpt">{{ getFirstSentence(entry.explanation) }}</p>
            <span v-if="entry.copyright" class="card-copy">© {{ entry.copyright }}</span>
          </div>
        </article>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ─── Layout ─────────────────────────────────────────────── */
.app {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}

/* ─── Hero ───────────────────────────────────────────────── */
.hero {
  position: relative;
  padding: 100px 24px 60px;
  text-align: center;
  background: radial-gradient(ellipse at 50% 0%, rgba(99, 179, 255, 0.15) 0%, transparent 70%);
  overflow: hidden;
}
.hero-badge {
  display: inline-block;
  background: rgba(99, 179, 255, 0.15);
  border: 1px solid rgba(99, 179, 255, 0.3);
  color: #63b3ff;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 6px 16px;
  border-radius: 999px;
  margin-bottom: 20px;
}
.hero h1 {
  font-size: clamp(2.2rem, 6vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin: 0 0 16px;
}
.accent {
  color: #63b3ff;
}
.hero-sub {
  color: var(--text-muted);
  font-size: 1.05rem;
  max-width: 480px;
  margin: 0 auto;
}

/* ─── Controls ───────────────────────────────────────────── */
.main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px 80px;
}
.font-domine {
  font-family: 'Domine', 'PingFang SC', sans-serif;
}
.controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 16px;
}
.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.month-select {
  appearance: none;
  background: rgba(255, 255, 255, 0.04)
    url('data:image/svg+xml;charset=UTF-8,<svg width="12" height="12" viewBox="0 0 12 12" xmlns="http://www.w3.org/2000/svg"><path d="M2.5 4.5l3.5 3.5 3.5-3.5" stroke="%2363b3ff" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    no-repeat right 16px center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  color: var(--text);
  font-size: 14px;
  font-weight: 500;
  padding: 8px 40px 8px 16px;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}
.month-select:hover,
.month-select:focus {
  border-color: rgba(99, 179, 255, 0.5);
  background-color: rgba(99, 179, 255, 0.1);
}
.month-select option {
  background: var(--card-bg);
  color: var(--text);
  padding: 8px;
}
.month-select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 16px;
  border-radius: 12px;
  font-size: 14px;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
}
.month-select:hover {
  border-color: #63b3ff;
  background: rgba(255, 255, 255, 0.08);
}

.today-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text);
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.today-btn:hover {
  border-color: rgba(99, 179, 255, 0.5);
  background-color: rgba(99, 179, 255, 0.1);
  color: #63b3ff;
}

.go-wrapper {
  position: relative;
}
.go-btn {
  padding: 8px 20px;
}
.go-dialog {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  z-index: 10;
}
.go-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  padding: 10px 12px;
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  color-scheme: dark;
}
.go-input:focus {
  outline: none;
  border-color: #63b3ff;
}

/* ─── State ──────────────────────────────────────────────── */
.state-msg {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  padding: 60px 0;
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

/* ─── Grid ───────────────────────────────────────────────── */
.grid {
  display: grid;
  /* Desktop: 3 to 6 columns depending on width (min 250px per card) */
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .grid {
    /* Mobile: 1 column */
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .controls {
    gap: 8px;
    margin-bottom: 20px;
  }
  .controls-left,
  .controls-right {
    gap: 6px;
  }
  .month-select {
    font-size: 13px;
    padding: 6px 32px 6px 12px;
    border-radius: 10px;
    background-position: right 10px center;
  }
  .today-btn {
    font-size: 13px;
    padding: 6px 10px;
  }
  .go-btn {
    padding: 6px 14px;
  }
}

/* ─── Card ───────────────────────────────────────────────── */
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 0.25s,
    box-shadow 0.25s,
    border-color 0.25s;
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  border-color: rgba(99, 179, 255, 0.3);
}
.card-media {
  position: relative;
  aspect-ratio: 16/9;
  background: #0d1520;
  overflow: hidden;
}
.card-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s;
}
.card:hover .card-media img,
.card:hover .card-media .video-preview {
  transform: scale(1.05);
}
.video-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  z-index: 1;
}
.video-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s;
  pointer-events: none;
}

.card-body {
  padding: 18px 20px;
}
.card-date {
  font-size: 11px;
  color: #63b3ff;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.card-title {
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 10px;
  line-height: 1.3;
}
.card-excerpt {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0 0 10px;
}
.card-copy {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
}
</style>
