import { ref } from 'vue'

export interface ApodEntry {
  date: string
  title: string | null
  explanation: string | null
  url: string | null
  hdurl: string | null
  copyright?: string
  no_data?: boolean
  http_status?: number
}

const cache = new Map<string, ApodEntry[]>()

export const transitionDate = ref('')

export function isValidEntry(entry: ApodEntry | null | undefined): entry is ApodEntry {
  if (!entry) return false
  if (entry.no_data) return false
  if (entry.http_status === 400 || entry.http_status === 429) return false
  return !!(entry.date && entry.title && entry.url)
}

let updateInfoCache: {
  files?: Record<string, string>
  ranges?: [string, string][]
} | null = null

async function getUpdateInfo() {
  if (updateInfoCache) return updateInfoCache
  const res = await fetch('/database/update.json')
  if (res.ok) {
    updateInfoCache = await res.json()
  }
  return updateInfoCache
}

export async function fetchMonth(yearMonth: string): Promise<ApodEntry[]> {
  if (cache.has(yearMonth)) return cache.get(yearMonth)!

  // Resolve filename from update.json mapping if available
  const info = await getUpdateInfo()
  const filename = info?.files?.[yearMonth] || `${yearMonth}.json`

  const res = await fetch(`/database/${filename}`)
  if (!res.ok) throw new Error(`Failed to load ${yearMonth} (${filename})`)
  const data: ApodEntry[] = await res.json()
  const filtered = data.filter(isValidEntry)
  cache.set(yearMonth, filtered)
  return filtered
}

export async function fetchEntry(date: string): Promise<ApodEntry | null> {
  const yearMonth = date.slice(0, 7)
  const entries = await fetchMonth(yearMonth)
  return entries.find((e) => e.date === date) ?? null
}

/** 获取所有可用日期列表 */
export async function fetchAllAvailableDates(): Promise<string[]> {
  const data = await getUpdateInfo()
  if (!data) return []

  if (data.ranges) {
    const dates: string[] = []
    for (const range of data.ranges) {
      if (range.length === 2) {
        const start = new Date(range[0])
        const end = new Date(range[1])
        const curr = new Date(start)
        while (curr <= end) {
          dates.push(curr.toISOString().split('T')[0]!)
          curr.setDate(curr.getDate() + 1)
        }
      }
    }
    return dates.sort()
  }

  return []
}

/** 从 update.json 获取所有已下载月份列表（YYYY-MM） */
export async function fetchAvailableMonths(): Promise<string[]> {
  const dates = await fetchAllAvailableDates()
  if (!dates.length) return []
  const months = [...new Set(dates.map((d: string) => d.slice(0, 7)))].sort().reverse()
  return months
}

export function isVideo(url: string | null): boolean {
  if (!url) return false
  return url.endsWith('.mp4') || url.includes('youtube.com') || url.includes('vimeo.com')
}
