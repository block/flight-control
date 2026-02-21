import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../lib/api'

const statusConfig = {
  queued: { label: 'Queued', class: 'bg-amber-50 text-amber-700 border border-amber-200' },
  assigned: { label: 'Assigned', class: 'bg-blue-50 text-blue-700 border border-blue-200' },
  running: { label: 'Running', class: 'bg-blue-50 text-blue-700 border border-blue-200' },
  completed: { label: 'Completed', class: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
  failed: { label: 'Failed', class: 'bg-red-50 text-red-700 border border-red-200' },
  cancelled: { label: 'Cancelled', class: 'bg-slate-50 text-slate-600 border border-slate-200' },
}

export default function JobDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [runs, setRuns] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.getJob(id), api.listRuns({ job_id: id })])
      .then(([j, r]) => { setJob(j); setRuns(r) })
      .catch((e) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <div className="card p-4 border-red-200 bg-red-50 text-red-700 text-sm">
        Error: {error}
      </div>
    )
  }
  if (!job) {
    return <div className="text-sm text-slate-500">Loading...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to="/jobs" className="text-xs font-medium text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-wide">
            &larr; Jobs
          </Link>
          <h1 className="text-lg font-semibold text-slate-900 mt-1">{job.name}</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={async () => {
              const run = await api.triggerRun(job.id)
              navigate(`/runs/${run.id}`)
            }}
            className="btn-success"
          >
            Run Now
          </button>
          <button
            onClick={async () => {
              if (confirm('Delete this job?')) {
                await api.deleteJob(job.id)
                navigate('/jobs')
              }
            }}
            className="btn-danger"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="card p-6 mb-6">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Task Prompt</div>
        <pre className="bg-slate-50 border border-slate-100 p-4 rounded-md text-sm text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
          {job.task_prompt}
        </pre>

        <div className="grid grid-cols-2 gap-x-8 gap-y-3 mt-5 pt-5 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wide w-24 shrink-0">Agent</span>
            <span className="text-sm font-mono text-slate-700">{job.agent_type}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wide w-24 shrink-0">Timeout</span>
            <span className="text-sm font-mono text-slate-700">{job.timeout_seconds}s</span>
          </div>
        </div>

        {job.mcp_servers?.length > 0 && (
          <div className="mt-5 pt-5 border-t border-slate-100">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">MCP Servers</div>
            <div className="flex flex-wrap gap-2">
              {job.mcp_servers.map((s, i) => (
                <span key={i} className="text-xs font-mono bg-slate-50 border border-slate-150 px-2.5 py-1 rounded-md text-slate-600">
                  {s.name || s.command} ({s.type})
                </span>
              ))}
            </div>
          </div>
        )}

        {job.credential_ids?.length > 0 && (
          <div className="mt-5 pt-5 border-t border-slate-100">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Credentials</div>
            <div className="flex flex-wrap gap-2">
              {job.credential_ids.map((c) => (
                <span key={c} className="text-xs font-mono bg-slate-50 border border-slate-150 px-2.5 py-1 rounded-md text-slate-600">
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-5 pt-5 border-t border-slate-100">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Skills</div>
          {job.skill_ids === null || job.skill_ids === undefined ? (
            <span className="text-sm text-slate-500">All workspace skills</span>
          ) : job.skill_ids.length === 0 ? (
            <span className="text-sm text-slate-500">No skills</span>
          ) : (
            <div className="flex flex-wrap gap-2">
              {job.skill_ids.map((s) => (
                <span key={s} className="text-xs font-mono bg-slate-50 border border-slate-150 px-2.5 py-1 rounded-md text-slate-600">
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide">
          Run History
        </h2>
      </div>

      {runs.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-slate-500">No runs yet.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Run ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Started</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Duration</th>
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
                      className="font-mono text-xs text-slate-700 hover:text-teal-600 transition-colors"
                    >
                      {run.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                    {run.started_at ? new Date(run.started_at).toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                    {run.started_at && run.completed_at
                      ? `${Math.round((new Date(run.completed_at) - new Date(run.started_at)) / 1000)}s`
                      : '-'}
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
