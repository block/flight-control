import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

function formatTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString()
}

export default function Schedules() {
  const [schedules, setSchedules] = useState([])
  const [jobs, setJobs] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', job_definition_id: '', cron_expression: '', enabled: true })
  const [error, setError] = useState(null)

  const fetchSchedules = () => api.listSchedules().then(setSchedules).catch((e) => setError(e.message))

  useEffect(() => {
    fetchSchedules()
    api.listJobs().then(setJobs).catch(() => {})
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      await api.createSchedule(form)
      setForm({ name: '', job_definition_id: '', cron_expression: '', enabled: true })
      setShowForm(false)
      fetchSchedules()
    } catch (e) {
      setError(e.message)
    }
  }

  const toggleEnabled = async (schedule) => {
    try {
      await api.updateSchedule(schedule.id, { enabled: !schedule.enabled })
      fetchSchedules()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Schedules</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className={showForm ? 'btn-secondary' : 'btn-primary'}
        >
          {showForm ? 'Cancel' : 'Add Schedule'}
        </button>
      </div>

      {error && (
        <div className="card p-3 border-red-200 bg-red-50 text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleCreate} className="card p-6 mb-6">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Name</label>
                <input
                  type="text"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g., Nightly code review"
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Job</label>
                <select
                  required
                  value={form.job_definition_id}
                  onChange={(e) => setForm({ ...form, job_definition_id: e.target.value })}
                  className="input-field"
                >
                  <option value="">Select a job...</option>
                  {jobs.map((job) => (
                    <option key={job.id} value={job.id}>{job.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Cron Expression</label>
              <input
                type="text"
                required
                value={form.cron_expression}
                onChange={(e) => setForm({ ...form, cron_expression: e.target.value })}
                placeholder="e.g., 0 2 * * * (daily at 2am)"
                className="input-field font-mono"
              />
              <p className="mt-1 text-xs text-slate-400">
                Format: minute hour day-of-month month day-of-week
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="schedule-enabled"
                checked={form.enabled}
                onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
                className="rounded border-slate-300"
              />
              <label htmlFor="schedule-enabled" className="text-sm text-slate-700">Enabled</label>
            </div>
            <div className="pt-2">
              <button type="submit" className="btn-primary">
                Create Schedule
              </button>
            </div>
          </div>
        </form>
      )}

      {schedules.length === 0 && !showForm ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-slate-500">No schedules configured.</p>
        </div>
      ) : (
        schedules.length > 0 && (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Job</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Cron</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Next Run</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Last Run</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map((sched, i) => (
                  <tr
                    key={sched.id}
                    className={`hover:bg-slate-50/50 transition-colors ${
                      i < schedules.length - 1 ? 'border-b border-slate-100' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-medium text-slate-900">{sched.name || sched.id}</td>
                    <td className="px-4 py-3">
                      <Link to={`/jobs/${sched.job_definition_id}`} className="text-blue-600 hover:text-blue-800">
                        {sched.job_name || sched.job_definition_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">{sched.cron_expression}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleEnabled(sched)}
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium transition-colors ${
                          sched.enabled
                            ? 'bg-green-50 text-green-700 hover:bg-green-100'
                            : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                        }`}
                      >
                        {sched.enabled ? 'Enabled' : 'Disabled'}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{formatTime(sched.next_run_at)}</td>
                    <td className="px-4 py-3 text-xs">
                      {sched.last_run_id ? (
                        <Link to={`/runs/${sched.last_run_id}`} className="text-blue-600 hover:text-blue-800">
                          {formatTime(sched.last_run_at)}
                        </Link>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={async () => {
                          if (confirm(`Delete schedule "${sched.name || sched.id}"?`)) {
                            await api.deleteSchedule(sched.id)
                            fetchSchedules()
                          }
                        }}
                        className="text-xs text-red-500 hover:text-red-700 font-medium transition-colors"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  )
}
