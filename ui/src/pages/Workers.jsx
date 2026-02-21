import { useEffect, useState } from 'react'
import { api } from '../lib/api'

const statusConfig = {
  online: { label: 'Online', class: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
  busy: { label: 'Busy', class: 'bg-blue-50 text-blue-700 border border-blue-200' },
  offline: { label: 'Offline', class: 'bg-slate-50 text-slate-500 border border-slate-200' },
}

export default function Workers() {
  const [workers, setWorkers] = useState([])
  const [error, setError] = useState(null)
  const [showOffline, setShowOffline] = useState(false)

  useEffect(() => {
    const fetch = () => api.listWorkers().then(setWorkers).catch((e) => setError(e.message))
    fetch()
    const interval = setInterval(fetch, 10000)
    return () => clearInterval(interval)
  }, [])

  if (error) {
    return (
      <div className="card p-4 border-red-200 bg-red-50 text-red-700 text-sm">
        Error: {error}
      </div>
    )
  }

  const activeWorkers = workers.filter((w) => w.status === 'online' || w.status === 'busy')
  const offlineWorkers = workers.filter((w) => w.status === 'offline')

  return (
    <div>
      <h1 className="text-lg font-semibold text-slate-900 mb-6">Workers</h1>

      {activeWorkers.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-slate-500">
            No active workers. Start a worker with{' '}
            <code className="font-mono text-xs bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded">
              docker compose up worker
            </code>
          </p>
        </div>
      ) : (
        <WorkerTable workers={activeWorkers} />
      )}

      {offlineWorkers.length > 0 && (
        <div className="mt-6">
          <button
            onClick={() => setShowOffline(!showOffline)}
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 transition-colors"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showOffline ? 'rotate-90' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
            Previous Workers
            <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded-full">
              {offlineWorkers.length}
            </span>
          </button>

          {showOffline && (
            <div className="mt-3">
              <WorkerTable workers={offlineWorkers} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function WorkerTable({ workers }) {
  return (
    <div className="card overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100">
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Current Run</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Last Heartbeat</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Labels</th>
          </tr>
        </thead>
        <tbody>
          {workers.map((w, i) => (
            <tr
              key={w.id}
              className={`hover:bg-slate-50/50 transition-colors ${
                i < workers.length - 1 ? 'border-b border-slate-100' : ''
              }`}
            >
              <td className="px-4 py-3">
                <div className="font-medium text-slate-900 text-sm">{w.name}</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">{w.id}</div>
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={w.status} />
              </td>
              <td className="px-4 py-3 font-mono text-xs text-slate-500">
                {w.current_run_id || <span className="text-slate-300">-</span>}
              </td>
              <td className="px-4 py-3 font-mono text-xs text-slate-500">
                {new Date(w.last_heartbeat).toLocaleString()}
              </td>
              <td className="px-4 py-3">
                {w.labels && Object.keys(w.labels).length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(w.labels).map(([k, v]) => (
                      <span
                        key={k}
                        className="text-xs font-mono bg-slate-50 border border-slate-100 px-2 py-0.5 rounded text-slate-600"
                      >
                        {k}={v}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-slate-300">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function StatusBadge({ status }) {
  const config = statusConfig[status] || {
    label: status,
    class: 'bg-slate-50 text-slate-600 border border-slate-200',
  }
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${config.class}`}>
      {config.label}
    </span>
  )
}
