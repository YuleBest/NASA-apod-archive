<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useHead } from '@unhead/vue'
import { Document } from 'flexsearch'
import { fetchAvailableMonths, fetchMonth, isVideo, type ApodEntry } from '@/composables/useApod'

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

const allMonths = ref<string[]>([])
const allAvailableDates = ref<string[]>([])
const validYears = ref<string[]>([])
const years = computed(() => validYears.value)

const selectedYear = ref('')
const selectedMonthPart = ref('')

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
    const res = await fetch('/database/update.json')
    if (res.ok) {
      const data: { dates: string[] } = await res.json()
      allAvailableDates.value = data.dates
    }
  } catch (err) {
    console.warn('Failed to fetch update.json', err)
  }

  try {
    allMonths.value = await fetchAvailableMonths()
    if (allMonths.value.length) {
      const rawYears = [...new Set(allMonths.value.map((m) => m.slice(0, 4)))]

      const yearResults = await Promise.all(
        rawYears.map(async (y) => {
          const monthsInYear = allMonths.value.filter((m) => m.startsWith(y))
          const results = await Promise.all(
            monthsInYear.map(async (m) => {
              try {
                const entries = await fetchMonth(m)
                return entries.length > 0
              } catch {
                return false
              }
            }),
          )
          return results.some((r) => r)
        }),
      )

      validYears.value = rawYears.filter((_, i) => yearResults[i])

      if (validYears.value.length) {
        selectedYear.value = validYears.value[0] ?? ''
        await checkValidMonths(selectedYear.value)
        selectedMonthPart.value = availableMonthsForYear.value[0] ?? ''
        await loadMonth()
      }

      // Background pre-load search index after 2 seconds
      setTimeout(() => {
        loadSearchIndex()
      }, 2000)
    }
  } catch (e: unknown) {
    console.error('Error during initial data fetch:', e)
  }
})

const todayStr = (() => {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  return formatter.format(new Date()) // Returns YYYY-MM-DD
})()

const latestDateBtn = computed(() => {
  if (!allAvailableDates.value.length) return { label: 'Latest', date: '' }
  const latest = allAvailableDates.value[allAvailableDates.value.length - 1]!
  const isToday = latest === todayStr
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
  router.push(`/${date}`)
}

function formatDate(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function getFirstSentence(text?: string | null) {
  if (!text) return ''
  // Split by first period followed by a space or end of string.
  const match = text.match(/^.*?\.(?=\s|$)/)
  return match ? match[0] : text.slice(0, 120) + '...'
}

// ── Search Logic ───────────────────────────────────────────
interface SearchDoc {
  d: string // date
  t: string // title
  e: string // explanation
}

const searchQuery = ref('')
const searchResults = ref<SearchDoc[]>([])
const isSearching = ref(false)
const searchLoading = ref(false)
const indexReady = ref(false)
let searchIndex: any = null

interface SearchResultField {
  field: string
  result: Array<{ id: string; doc: SearchDoc }>
}

async function loadSearchIndex() {
  if (indexReady.value || searchLoading.value) return
  searchLoading.value = true
  try {
    const res = await fetch('/database/search.json')
    if (!res.ok) throw new Error('Failed to load search index')
    const data: SearchDoc[] = await res.json()

    searchIndex = new Document({
      document: {
        id: 'd',
        index: [
          { field: 't', tokenize: 'forward', resolution: 9 },
          { field: 'e', tokenize: 'forward', resolution: 9 },
        ],
        store: ['d', 't', 'e'],
      },
      // Custom encoder to avoid library issues
      encode: (str: string) =>
        str
          .toLowerCase()
          .replace(/[^a-z0-9]/g, ' ')
          .split(/\s+/),
      suggest: true,
      cache: true,
    } as any)

    // Non-blocking chunked adding
    const CHUNK_SIZE = 100
    let offset = 0

    const processNextChunk = () => {
      const end = Math.min(offset + CHUNK_SIZE, data.length)
      for (let i = offset; i < end; i++) {
        searchIndex.add(data[i])
      }
      offset = end

      if (offset < data.length) {
        // Schedule next chunk to keep main thread responsive
        if ('requestIdleCallback' in window) {
          ;(window as any).requestIdleCallback(processNextChunk)
        } else {
          setTimeout(processNextChunk, 1)
        }
      } else {
        indexReady.value = true
        searchLoading.value = false
        console.log('Search index loaded successfully')
      }
    }

    processNextChunk()
  } catch (err) {
    console.error('Search init error:', err)
    searchLoading.value = false
  }
}

watch(searchQuery, (q) => {
  if (!q.trim()) {
    searchResults.value = []
    isSearching.value = false
    return
  }
  isSearching.value = q.length > 1
  if (q.length > 2 && indexReady.value && searchIndex) {
    const res = searchIndex.search(q, { limit: 20, enrich: true }) as SearchResultField[]
    if (res.length > 0) {
      const allResults: SearchDoc[] = []
      res.forEach((fieldResult) => {
        if (fieldResult.result) {
          fieldResult.result.forEach((item) => {
            allResults.push(item.doc)
          })
        }
      })
      // Unique results by date
      const unique = Array.from(new Map(allResults.map((it) => [it.d, it])).values())
      searchResults.value = unique
    } else {
      searchResults.value = []
    }
  }
})

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
  isSearching.value = false
}
</script>

<template>
  <div class="app">
    <header class="hero">
      <div class="hero-content">
        <div class="hero-badge">🔭 NASA</div>
        <h1>Astronomy Picture<br /><span class="accent">of the Day</span></h1>
        <p class="hero-sub">A curated archive of the universe's most breathtaking images</p>
      </div>
    </header>

    <main class="main">
      <div class="controls">
        <div class="controls-left">
          <select v-model="selectedYear" class="month-select" @change="onYearChange()">
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
          <select v-model="selectedMonthPart" class="month-select" @change="loadMonth()">
            <option v-for="m in availableMonthsForYear" :key="m" :value="m">{{ m }}</option>
          </select>

          <div class="search-wrapper">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search APOD..."
              class="search-input"
              @focus="loadSearchIndex"
            />
            <button v-if="searchQuery" class="search-clear" @click="clearSearch()">×</button>
            <div v-if="searchLoading" class="search-indicator">
              <div class="search-spinner-sm"></div>
              <span>Preparing...</span>
            </div>
          </div>
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

      <!-- Search Results Overlay -->
      <div v-if="isSearching" class="search-results">
        <div v-if="searchResults.length === 0" class="search-empty">
          No results for "{{ searchQuery }}"
        </div>
        <div v-else class="search-list">
          <div
            v-for="res in searchResults"
            :key="res.d"
            class="search-item"
            @click="goToDate(res.d)"
          >
            <span class="search-item-date">{{ res.d }}</span>
            <div class="search-item-body">
              <div class="search-item-title">{{ res.t }}</div>
              <div class="search-item-snippet">{{ getFirstSentence(res.e) }}</div>
            </div>
          </div>
        </div>
      </div>

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
            />
            <video
              v-else-if="isVideo(entry.url) && entry.url"
              :src="entry.url"
              autoplay
              loop
              muted
              playsinline
              class="video-preview"
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
  padding: 80px 24px 60px;
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

/* ── Search ─────────────────────────────────────────────── */
.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.search-input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 16px;
  padding-right: 32px;
  border-radius: 12px;
  font-size: 14px;
  width: 200px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.search-input:focus {
  width: 300px;
  border-color: #63b3ff;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 4px rgba(99, 179, 255, 0.15);
}
.search-clear {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 18px;
  cursor: pointer;
}
.search-indicator {
  position: absolute;
  right: -90px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
  pointer-events: none;
}
.search-spinner-sm {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: #63b3ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.search-results {
  margin-top: 10px;
  background: rgba(13, 20, 31, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: 16px;
  max-height: 400px;
  overflow-y: auto;
  position: absolute;
  left: 20px;
  right: 20px;
  z-index: 1000;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}
.search-empty {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
}
.search-item {
  display: flex;
  gap: 20px;
  padding: 16px 24px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.search-item:last-child {
  border-bottom: none;
}
.search-item:hover {
  background: rgba(99, 179, 255, 0.1);
}
.search-item-date {
  font-size: 13px;
  color: var(--text-muted);
  font-family: monospace;
  white-space: nowrap;
}
.search-item-title {
  font-weight: 600;
  color: #63b3ff;
  margin-bottom: 4px;
}
.search-item-snippet {
  font-size: 13px;
  color: var(--text-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
    /* Mobile: 2 columns */
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
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
