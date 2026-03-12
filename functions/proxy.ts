export const onRequest: PagesFunction = async (context) => {
  const { searchParams } = new URL(context.request.url)
  const targetUrl = searchParams.get('url')

  if (!targetUrl) {
    return new Response('Missing url parameter', { status: 400 })
  }

  try {
    const response = await fetch(targetUrl)
    const { status, statusText, headers } = response

    // Copy relevant headers
    const newHeaders = new Headers(headers)
    newHeaders.set('Access-Control-Allow-Origin', '*')
    newHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')

    // Add attachment header only if download parameter is present
    const isDownload = searchParams.get('download') === '1'
    if (isDownload) {
      const filename = targetUrl.split('/').pop() || 'download'
      newHeaders.set('Content-Disposition', `attachment; filename="${filename}"`)
    }

    return new Response(response.body, {
      status,
      statusText,
      headers: newHeaders,
    })
  } catch (err) {
    return new Response(`Failed to proxy request: ${err}`, { status: 500 })
  }
}
