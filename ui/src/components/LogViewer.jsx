import { useEffect, useState, useRef } from 'react'
import { api, getWorkspaceId } from '../lib/api'

export default function LogViewer({ runId, isActive }) {
  const [logs, setLogs] = useState([])
  const [useSSE, setUseSSE] = useState(isActive)
  const bottomRef = useRef(null)
  const containerRef = useRef(null)

  // Fetch logs from artifact on mount and when run completes
  useEffect(() => {
    api.getRunLogs(runId).then((fetched) => {
      setLogs((prev) => fetched.length > 0 ? fetched : prev)
    }).catch(() => {})
  }, [runId, isActive])

  // SSE for live streaming
  useEffect(() => {
    if (!isActive) return

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
    if (useSSE || !isActive) return

    const interval = setInterval(async () => {
      const maxSeq = logs.length > 0 ? Math.max(...logs.map((l) => l.sequence)) : 0
      const newLogs = await api.getRunLogs(runId, maxSeq)
      if (newLogs.length > 0) {
        setLogs((prev) => [...prev, ...newLogs])
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [runId, isActive, useSSE, logs.length])

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  return (
    <div
      ref={containerRef}
      className="bg-slate-900 text-slate-300 rounded-lg border border-slate-800 p-4 font-mono text-[13px] leading-relaxed overflow-auto max-h-[600px]"
    >
      {isActive && (
        <div className="flex items-center gap-2 mb-3 pb-3 border-b border-slate-800">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
          </span>
          <span className="text-xs text-slate-500">Live</span>
        </div>
      )}
      {logs.length === 0 ? (
        <div className="text-slate-600">
          {isActive ? 'Waiting for output...' : 'No logs available.'}
        </div>
      ) : (
        logs.map((log, i) => (
          <div
            key={i}
            className={`whitespace-pre-wrap ${log.stream === 'stderr' ? 'text-red-400' : ''}`}
          >
            {log.line}
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  )
}
