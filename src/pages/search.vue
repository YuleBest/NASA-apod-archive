<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useHead } from '@unhead/vue'
import { Document } from 'flexsearch'

const router = useRouter()

useHead({
  title: 'Search | NASA APOD Archive',
  meta: [
    {
      name: 'description',
      content: 'Search through over 25 years of NASA Astronomy Picture of the Day images.',
    },
  ],
})

const inputRef = ref<HTMLInputElement | null>(null)

interface SearchDoc {
  d: string // date
  t: string // title
  e: string // explanation
}

const searchQuery = ref('')
const searchResults = ref<SearchDoc[]>([])
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
          { field: 't', tokenize: 'full', resolution: 9 },
          { field: 'e', tokenize: 'forward', resolution: 5 },
        ],
        store: ['d', 't', 'e'],
      },
      // Simplified encoder for better word boundaries
      encode: (str: string) =>
        str
          .toLowerCase()
          .replace(/[^a-z0-9]/g, ' ')
          .split(/\s+/)
          .filter(Boolean),
      suggest: true,
      cache: true,
    } as any)

    const CHUNK_SIZE = 1000
    let offset = 0

    const processNextChunk = () => {
      const end = Math.min(offset + CHUNK_SIZE, data.length)
      for (let i = offset; i < end; i++) {
        searchIndex.add(data[i])
      }
      offset = end

      if (offset < data.length) {
        if ('requestIdleCallback' in window) {
          ;(window as any).requestIdleCallback(processNextChunk)
        } else {
          setTimeout(processNextChunk, 1)
        }
      } else {
        indexReady.value = true
        searchLoading.value = false
      }
    }

    processNextChunk()
  } catch (err) {
    console.error('Search init error:', err)
    searchLoading.value = false
  }
}

onMounted(() => {
  loadSearchIndex()
  // Ensure focus happens after render
  setTimeout(() => {
    inputRef.value?.focus()
  }, 100)
})

watch(searchQuery, (q) => {
  if (!q.trim()) {
    searchResults.value = []
    return
  }
  if (q.length > 1 && indexReady.value && searchIndex) {
    // Improved search: use enrichment and better logic for multi-word
    const res = searchIndex.search(q, {
      limit: 50,
      enrich: true,
      bool: 'or', // Allow finding any of the words
    }) as SearchResultField[]

    if (res.length > 0) {
      const allResults: SearchDoc[] = []
      res.forEach((fieldResult) => {
        if (fieldResult.result) {
          fieldResult.result.forEach((item) => {
            allResults.push(item.doc)
          })
        }
      })
      // Unique results by date, prioritize title matches
      const unique = Array.from(new Map(allResults.map((it) => [it.d, it])).values())
      searchResults.value = unique
    } else {
      searchResults.value = []
    }
  }
})

function goToDate(date: string) {
  router.push(`/${date}`)
}

function getFirstSentence(text?: string | null) {
  if (!text) return ''
  const match = text.match(/^.*?\.(?=\s|$)/)
  return match ? match[0] : text.slice(0, 120) + '...'
}

function clearSearch() {
  searchQuery.value = ''
}
</script>

<template>
  <div class="search-page">
    <header class="search-header">
      <div class="container">
        <button class="back-link" @click="router.back()">← Back</button>
        <div class="search-box">
          <input
            ref="inputRef"
            v-model="searchQuery"
            type="text"
            placeholder="Search the cosmos..."
            class="search-input"
          />
          <button v-if="searchQuery" class="clear-btn" @click="clearSearch()">×</button>
        </div>
        <div v-if="searchLoading" class="loading-status">Indexing...</div>
      </div>
    </header>

    <main class="container">
      <div v-if="!searchQuery" class="search-info">
        <h3>Discover APOD</h3>
        <p>
          Enter keywords like "Mars", "Nebula", or "Curiosity" to search over 25 years of NASA
          Astronomy Pictures of the Day.
        </p>
      </div>

      <div v-else-if="searchResults.length === 0 && !searchLoading" class="no-results">
        No results found for "{{ searchQuery }}"
      </div>

      <div v-else class="results-list">
        <div v-for="res in searchResults" :key="res.d" class="result-item" @click="goToDate(res.d)">
          <div class="result-meta">
            <span class="result-date">{{ res.d }}</span>
          </div>
          <div class="result-content">
            <h2 class="result-title">{{ res.t }}</h2>
            <p class="result-snippet">{{ getFirstSentence(res.e) }}</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.search-page {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  padding-bottom: 80px;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 20px;
}

.search-header {
  position: sticky;
  top: 0;
  background: rgba(6, 12, 23, 0.8);
  backdrop-filter: blur(20px);
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
  z-index: 100;
}

.search-header .container {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-link {
  background: none;
  border: none;
  color: #63b3ff;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.search-box {
  flex: 1;
  position: relative;
}

.search-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 12px 16px;
  padding-right: 40px;
  border-radius: 12px;
  font-size: 16px;
  outline: none;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: #63b3ff;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 4px rgba(99, 179, 255, 0.15);
}

.clear-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 20px;
  cursor: pointer;
}

.loading-status {
  font-size: 12px;
  color: var(--text-muted);
}

.search-info {
  text-align: center;
  padding: 100px 0;
  color: var(--text-muted);
}

.search-info h3 {
  color: var(--text);
  font-size: 24px;
  margin-bottom: 12px;
}

.no-results {
  text-align: center;
  padding: 100px 0;
  color: var(--text-muted);
}

.results-list {
  padding: 24px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  border-color: rgba(99, 179, 255, 0.4);
  background: rgba(99, 179, 255, 0.05);
  transform: translateY(-2px);
}

.result-meta {
  margin-bottom: 8px;
}

.result-date {
  font-size: 12px;
  font-family: monospace;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 4px;
}

.result-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #63b3ff;
}

.result-snippet {
  font-size: 14px;
  color: var(--text-muted);
  line-height: 1.6;
}
</style>
