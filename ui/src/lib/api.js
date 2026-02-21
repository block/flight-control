const API_BASE = '/api/v1'

function getHeaders() {
  const token = localStorage.getItem('api_key') || 'admin'
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: getHeaders(),
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // Jobs
  listJobs: () => request('/jobs'),
  getJob: (id) => request(`/jobs/${id}`),
  createJob: (data) => request('/jobs', { method: 'POST', body: JSON.stringify(data) }),
  updateJob: (id, data) => request(`/jobs/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteJob: (id) => request(`/jobs/${id}`, { method: 'DELETE' }),
  triggerRun: (jobId) => request(`/jobs/${jobId}/run`, { method: 'POST' }),

  // Runs
  listRuns: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/runs${qs ? '?' + qs : ''}`)
  },
  getRun: (id) => request(`/runs/${id}`),
  createAdHocRun: (data) => request('/runs', { method: 'POST', body: JSON.stringify(data) }),
  cancelRun: (id) => request(`/runs/${id}/cancel`, { method: 'POST' }),
  getRunLogs: (id, after = 0) => request(`/runs/${id}/logs?after=${after}`),
  listArtifacts: (runId) => request(`/runs/${runId}/artifacts`),
  downloadArtifact: async (runId, artifactId, filename) => {
    const token = localStorage.getItem('api_key') || 'admin'
    const res = await fetch(`${API_BASE}/runs/${runId}/artifacts/${artifactId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  },

  // Credentials
  listCredentials: () => request('/credentials'),
  createCredential: (data) => request('/credentials', { method: 'POST', body: JSON.stringify(data) }),
  updateCredential: (id, data) => request(`/credentials/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCredential: (id) => request(`/credentials/${id}`, { method: 'DELETE' }),

  // Schedules
  listSchedules: () => request('/schedules'),
  createSchedule: (data) => request('/schedules', { method: 'POST', body: JSON.stringify(data) }),
  updateSchedule: (id, data) => request(`/schedules/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSchedule: (id) => request(`/schedules/${id}`, { method: 'DELETE' }),

  // System
  health: () => request('/health'),
  listWorkers: () => request('/system/workers'),
  getMetrics: () => request('/system/metrics'),
}
