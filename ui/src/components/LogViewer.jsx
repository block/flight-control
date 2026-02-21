import { useEffect, useRef } from 'react'

export default function LogViewer({ logs, isActive }) {
  const bottomRef = useRef(null)
  const containerRef = useRef(null)

  // Filter to only stdout/stderr
  const filteredLogs = logs.filter((l) => l.stream === 'stdout' || l.stream === 'stderr')

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [filteredLogs.length])

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
      {filteredLogs.length === 0 ? (
        <div className="text-slate-600">
          {isActive ? 'Waiting for output...' : 'No logs available.'}
        </div>
      ) : (
        filteredLogs.map((log, i) => (
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
