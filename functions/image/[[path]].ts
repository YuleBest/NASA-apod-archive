export const onRequest: PagesFunction<{ ASSETS: { fetch: typeof fetch } }> = async (context) => {
  const url = new URL(context.request.url)
  const pathParts = url.pathname.split('/').filter(Boolean)
  const target = pathParts[1]

  if (!target) {
    return new Response('Missing target', { status: 400 })
  }

  const origin = url.origin
  let targetDate = target

  // Internal fetch helper to use ASSETS if available
  const internalFetch = async (path: string) => {
    if (context.env.ASSETS) {
      return context.env.ASSETS.fetch(new URL(path, origin))
    }
    return fetch(new URL(path, origin))
  }

  try {
    if (target === 'latest') {
      const updateRes = await internalFetch('/database/update.json')
      if (!updateRes.ok) throw new Error('Failed to fetch update.json')
      const updateData = (await updateRes.json()) as { dates: string[] }
      targetDate = updateData.dates[updateData.dates.length - 1]
    }

    if (!targetDate || !/^\d{4}-\d{2}-\d{2}$/.test(targetDate)) {
      return new Response('Invalid date format', { status: 400 })
    }

    const ym = targetDate.slice(0, 7)
    const monthRes = await internalFetch(`/database/${ym}.json`)
    if (!monthRes.ok) throw new Error(`Failed to fetch ${ym}.json`)
    const monthData = (await monthRes.json()) as any[]
    const entry = monthData.find((e: any) => e.date === targetDate)

    if (!entry || (!entry.hdurl && !entry.url)) {
      return new Response('Image not found', { status: 404 })
    }

    const imageUrl = entry.hdurl || entry.url
    const imageRes = await fetch(imageUrl)

    // Copy headers and set CORS
    const responseHeaders = new Headers(imageRes.headers)
    responseHeaders.set('Access-Control-Allow-Origin', '*')
    responseHeaders.set('Cache-Control', 'public, max-age=86400')
    responseHeaders.delete('Content-Disposition')

    return new Response(imageRes.body, {
      status: imageRes.status,
      statusText: imageRes.statusText,
      headers: responseHeaders,
    })
  } catch (err) {
    return new Response(`Error: ${err}`, { status: 500 })
  }
}
