import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

const statusConfig = {
  queued: { label: 'Queued', class: 'bg-amber-50 text-amber-700 border border-amber-200' },
  assigned: { label: 'Assigned', class: 'bg-blue-50 text-blue-700 border border-blue-200' },
  running: { label: 'Running', class: 'bg-blue-50 text-blue-700 border border-blue-200' },
  completed: { label: 'Completed', class: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
  failed: { label: 'Failed', class: 'bg-red-50 text-red-700 border border-red-200' },
  cancelled: { label: 'Cancelled', class: 'bg-slate-50 text-slate-600 border border-slate-200' },
  timeout: { label: 'Timeout', class: 'bg-orange-50 text-orange-700 border border-orange-200' },
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [runs, setRuns] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.getMetrics(), api.listRuns()])
      .then(([m, r]) => {
        setMetrics(m)
        setRuns(r.slice(0, 10))
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div className="card p-4 border-red-200 bg-red-50 text-red-700 text-sm">
        Error: {error}
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-lg font-semibold text-slate-900 mb-6">Dashboard</h1>

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="Queue Depth" value={metrics.queue_depth || 0} />
          <StatCard label="Running" value={metrics.runs?.running || 0} accent />
          <StatCard
            label="Completed"
            value={metrics.runs?.completed || 0}
          />
          <StatCard
            label="Workers Online"
            value={(metrics.workers?.online || 0) + (metrics.workers?.busy || 0)}
          />
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide">
          Recent Runs
        </h2>
        <Link
          to="/runs/new"
          className="text-[13px] font-medium text-teal-600 hover:text-teal-700 transition-colors"
        >
          New run &rarr;
        </Link>
      </div>

      {runs.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-slate-500">
            No runs yet.{' '}
            <Link to="/runs/new" className="text-teal-600 hover:text-teal-700 font-medium">
              Create one
            </Link>
          </p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Created
                </th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run, i) => (
                <tr
                  key={run.id}
                  className={`hover:bg-slate-50/50 transition-colors ${
                    i < runs.length - 1 ? 'border-b border-slate-100' : ''
                  }`}
                >
                  <td className="px-4 py-3">
                    <Link
                      to={`/runs/${run.id}`}
                      className="text-sm font-medium text-slate-900 hover:text-teal-600 transition-colors"
                    >
                      {run.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                    {new Date(run.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, accent }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-semibold mt-1 tabular-nums ${accent ? 'text-teal-600' : 'text-slate-900'}`}>
        {value}
      </div>
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
