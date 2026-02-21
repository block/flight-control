import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../lib/api'
import LogViewer from '../components/LogViewer'

const statusConfig = {
  queued: { label: 'Queued', class: 'bg-amber-50 text-amber-700 border border-amber-200' },
  assigned: { label: 'Assigned', class: 'bg-blue-50 text-blue-700 border border-blue-200' },
  running: { label: 'Running', class: 'bg-blue-50 text-blue-700 border border-blue-200' },
  completed: { label: 'Completed', class: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
  failed: { label: 'Failed', class: 'bg-red-50 text-red-700 border border-red-200' },
  cancelled: { label: 'Cancelled', class: 'bg-slate-50 text-slate-600 border border-slate-200' },
  timeout: { label: 'Timeout', class: 'bg-orange-50 text-orange-700 border border-orange-200' },
}

export default function RunDetail() {
  const { id } = useParams()
  const [run, setRun] = useState(null)
  const [artifacts, setArtifacts] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchRun = () => {
      api.getRun(id).then(setRun).catch((e) => setError(e.message))
    }
    fetchRun()
    const interval = setInterval(fetchRun, 5000)
    return () => clearInterval(interval)
  }, [id])

  useEffect(() => {
    api.listArtifacts(id).then(setArtifacts).catch(() => {})
  }, [id, run?.status])

  if (error) {
    return (
      <div className="card p-4 border-red-200 bg-red-50 text-red-700 text-sm">
        Error: {error}
      </div>
    )
  }
  if (!run) return <div className="text-sm text-slate-500">Loading...</div>

  const isActive = ['queued', 'assigned', 'running'].includes(run.status)
  const config = statusConfig[run.status] || {
    label: run.status,
    class: 'bg-slate-50 text-slate-600 border border-slate-200',
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to="/" className="text-xs font-medium text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-wide">
            &larr; Dashboard
          </Link>
          <div className="flex items-center gap-3 mt-1">
            <h1 className="text-lg font-semibold text-slate-900">{run.name}</h1>
            <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${config.class}`}>
              {config.label}
            </span>
          </div>
          <span className="font-mono text-xs text-slate-400 mt-0.5 block">{run.id}</span>
        </div>
        {isActive && (
          <button
            onClick={async () => {
              await api.cancelRun(run.id)
              setRun({ ...run, status: 'cancelled' })
            }}
            className="btn-danger"
          >
            Cancel Run
          </button>
        )}
      </div>

      <div className="card p-6 mb-6">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Task Prompt</div>
        <pre className="bg-slate-50 border border-slate-100 p-4 rounded-md text-sm text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
          {run.task_prompt}
        </pre>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-3 mt-5 pt-5 border-t border-slate-100">
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Agent</div>
            <div className="text-sm font-mono text-slate-700">{run.agent_type}</div>
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Worker</div>
            <div className="text-sm font-mono text-slate-700">{run.worker_id || '-'}</div>
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Started</div>
            <div className="text-sm font-mono text-slate-700">
              {run.started_at ? new Date(run.started_at).toLocaleString() : '-'}
            </div>
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Exit Code</div>
            <div className="text-sm font-mono text-slate-700">{run.exit_code ?? '-'}</div>
          </div>
        </div>

        {run.result && (
          <div className="mt-5 pt-5 border-t border-slate-100">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Result</div>
            <pre className="bg-slate-50 border border-slate-100 p-4 rounded-md text-sm text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
              {run.result}
            </pre>
          </div>
        )}
      </div>

      {artifacts.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide mb-3">Artifacts</h2>
          <div className="card divide-y divide-slate-100">
            {artifacts.map((artifact) => (
              <div key={artifact.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <span className="text-sm font-medium text-slate-700">{artifact.filename}</span>
                  <span className="text-xs text-slate-400 ml-2">
                    {artifact.size_bytes < 1024
                      ? `${artifact.size_bytes} B`
                      : `${(artifact.size_bytes / 1024).toFixed(1)} KB`}
                  </span>
                </div>
                <button
                  onClick={() => api.downloadArtifact(id, artifact.id, artifact.filename)}
                  className="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Download
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide mb-3">Output</h2>
      <LogViewer runId={run.id} isActive={isActive} />
    </div>
  )
}
