import { useEffect, useState } from 'react'
import { api, getWorkspaceId } from '../lib/api'

/**
 * Shared hook for fetching + streaming run logs.
 * Returns { logs, isStreaming } where each log is { stream, line, sequence }.
 */
export default function useRunLogs(runId, isActive) {
  const [logs, setLogs] = useState([])
  const [useSSE, setUseSSE] = useState(isActive)

  // Fetch logs from artifact on mount and when run completes
  useEffect(() => {
    if (!runId) return
    api.getRunLogs(runId).then((fetched) => {
      setLogs((prev) => fetched.length > 0 ? fetched : prev)
    }).catch(() => {})
  }, [runId, isActive])

  // SSE for live streaming
  useEffect(() => {
    if (!runId || !isActive) return

    const token = localStorage.getItem('api_key') || 'admin'
    const params = new URLSearchParams({ token, workspace_id: getWorkspaceId() })
    const es = new EventSource(`/api/v1/runs/${runId}/logs/stream?${params}`)

    es.addEventListener('log', (event) => {
      const data = JSON.parse(event.data)
      setLogs((prev) => [...prev, data])
    })

    es.onerror = () => {
      es.close()
      setUseSSE(false)
    }

    return () => es.close()
  }, [runId, isActive])

  // Polling fallback
  useEffect(() => {
    if (!runId || useSSE || !isActive) return

    const interval = setInterval(async () => {
      const maxSeq = logs.length > 0 ? Math.max(...logs.map((l) => l.sequence)) : 0
      const newLogs = await api.getRunLogs(runId, maxSeq)
      if (newLogs.length > 0) {
        setLogs((prev) => [...prev, ...newLogs])
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [runId, isActive, useSSE, logs.length])

  return { logs, isStreaming: isActive }
}
