const apiOrigin = (import.meta.env.VITE_API_ORIGIN || '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function errorMessage(body) {
  if (typeof body?.detail === 'string') {
    return body.detail
  }

  if (body && typeof body === 'object') {
    return Object.entries(body)
      .map(
        ([field, messages]) =>
          `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`,
      )
      .join(' ')
  }

  return 'The server could not complete this request.'
}

async function request(path, organization, options = {}) {
  let response

  try {
    // The browser supplies the multipart boundary when the body is FormData.
    response = await fetch(`${apiOrigin}/api/${path}`, {
      ...options,
      headers: { 'X-Organization': organization },
    })
  } catch (error) {
    // Switching organizations cancels old list requests without showing an error.
    if (error.name === 'AbortError') {
      throw error
    }

    throw new ApiError(
      'Cannot reach the server. Refresh to check the current state before retrying.',
      0,
    )
  }

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(errorMessage(body), response.status)
  }

  if (body === null) {
    throw new ApiError(
      'The server returned an unreadable response. Refresh to check the current state.',
      response.status,
    )
  }

  return body
}

export function getTransactions(organization, page, filters, signal) {
  const params = new URLSearchParams({
    page,
    page_size: filters.pageSize,
    ordering: filters.ordering,
  })

  if (filters.search) {
    params.set('search', filters.search)
  }

  if (filters.status) {
    params.set('status', filters.status)
  }

  return request(`transactions/?${params}`, organization, { signal })
}

export function getLineItems(organization, signal) {
  return request('line-items/', organization, { signal })
}

export function importStatement(organization, file) {
  const body = new FormData()
  body.append('file', file)

  return request('imports/', organization, { method: 'POST', body })
}

export function performAction(organization, action, id) {
  const path =
    action === 'ignore' ? `transactions/${id}/ignore/` : `matches/${id}/${action}/`

  return request(path, organization, { method: 'POST' })
}
