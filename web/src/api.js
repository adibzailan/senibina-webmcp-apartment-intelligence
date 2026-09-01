async function request(path, options = {}) {
  const { headers = {}, ...rest } = options
  const response = await fetch(path, {
    credentials: 'same-origin',
    ...rest,
    headers: { 'Content-Type': 'application/json', ...headers },
  })
  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('json') ? await response.json() : await response.blob()
  if (!response.ok) throw Object.assign(new Error(body.error || 'REQUEST_FAILED'), { body, status: response.status })
  return body
}

export const api = {
  context: (signal) => request('/api/context', { signal }),
  create: (input, signal) => request('/api/studies', { method: 'POST', body: JSON.stringify(input), signal }),
  state: (id, signal) => request(`/api/studies/${id}`, { signal }),
  proposal: (id, input, signal) => request(`/api/studies/${id}/proposal`, { method: 'PUT', body: JSON.stringify(input), signal }),
  confirm: (id, revision) => request(`/api/studies/${id}/confirmation`, {
    method: 'POST', headers: { 'X-User-Activation': 'trusted' },
    body: JSON.stringify({ proposal_revision: revision }),
  }),
  analyse: (id, signal) => request(`/api/studies/${id}/analysis`, { method: 'POST', signal }),
  result: (id, signal) => request(`/api/studies/${id}/result`, { signal }),
  model: (id, signal) => request(`/api/studies/${id}/export.3dm`, { signal }),
}
