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

export function isValidEntry(e: ApodEntry): boolean {
  return !e.no_data && e.http_status !== 429 && !!e.url && !!e.title
}

export async function fetchMonth(yearMonth: string): Promise<ApodEntry[]> {
  if (cache.has(yearMonth)) return cache.get(yearMonth)!
  const res = await fetch(`/database/${yearMonth}.json`)
  if (!res.ok) throw new Error(`Failed to load ${yearMonth}`)
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

/** 从 update.json 获取所有已下载月份列表（YYYY-MM） */
export async function fetchAvailableMonths(): Promise<string[]> {
  const res = await fetch('/database/update.json')
  if (!res.ok) return []
  const data: { dates: string[] } = await res.json()
  const months = [...new Set(data.dates.map((d) => d.slice(0, 7)))].sort().reverse()
  return months
}

export function isVideo(url: string | null): boolean {
  if (!url) return false
  return url.endsWith('.mp4') || url.includes('youtube.com') || url.includes('vimeo.com')
}
