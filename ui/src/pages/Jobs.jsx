import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import ProviderModelSelect from '../components/ProviderModelSelect'

export default function Jobs() {
  const [jobs, setJobs] = useState([])
  const [credentials, setCredentials] = useState([])
  const [skills, setSkills] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    name: '', task_prompt: '', agent_type: 'goose', timeout_seconds: 1800,
    agent_config: { provider: 'anthropic', model: 'claude-sonnet-4-5' },
    credential_ids: [],
    skill_ids: null, // null = all workspace skills
  })
  const [skillMode, setSkillMode] = useState('all') // 'all' or 'select'
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.listJobs().then(setJobs).catch((e) => setError(e.message))
    api.listCredentials().then(setCredentials).catch(() => {})
    api.listSkills().then(setSkills).catch(() => {})
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      const job = await api.createJob(form)
      navigate(`/jobs/${job.id}`)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Job Definitions</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className={showForm ? 'btn-secondary' : 'btn-primary'}
        >
          {showForm ? 'Cancel' : 'New Job'}
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
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Name</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Task Prompt</label>
              <textarea
                required
                rows={4}
                value={form.task_prompt}
                onChange={(e) => setForm({ ...form, task_prompt: e.target.value })}
                className="input-field"
                placeholder="Describe what you want the agent to do..."
              />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Agent Type</label>
                <select
                  value={form.agent_type}
                  onChange={(e) => setForm({ ...form, agent_type: e.target.value })}
                  className="input-field"
                >
                  <option value="goose">Goose</option>
                </select>
              </div>
              <ProviderModelSelect
                provider={form.agent_config.provider}
                model={form.agent_config.model}
                onChange={({ provider, model }) =>
                  setForm({ ...form, agent_config: { ...form.agent_config, provider, model } })
                }
              />
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Timeout (seconds)</label>
                <input
                  type="number"
                  value={form.timeout_seconds}
                  onChange={(e) => setForm({ ...form, timeout_seconds: parseInt(e.target.value) })}
                  className="input-field"
                />
              </div>
            </div>
            {credentials.length > 0 && (
              <div className="pt-2 border-t border-slate-100">
                <label className="block text-sm font-medium text-slate-700 mb-2">Credentials</label>
                <div className="flex flex-wrap gap-2">
                  {credentials.map((cred) => (
                    <label
                      key={cred.id}
                      className={`flex items-center gap-2 text-sm px-3 py-2 rounded-md border cursor-pointer transition-colors ${
                        form.credential_ids.includes(cred.name)
                          ? 'bg-teal-50 border-teal-200 text-teal-800'
                          : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={form.credential_ids.includes(cred.name)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setForm({ ...form, credential_ids: [...form.credential_ids, cred.name] })
                          } else {
                            setForm({ ...form, credential_ids: form.credential_ids.filter((c) => c !== cred.name) })
                          }
                        }}
                        className="accent-teal-600"
                      />
                      <span className="font-medium">{cred.name}</span>
                      <span className="text-xs text-slate-400 font-mono">({cred.env_var})</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            {skills.length > 0 && (
              <div className="pt-2 border-t border-slate-100">
                <label className="block text-sm font-medium text-slate-700 mb-2">Skills</label>
                <div className="flex items-center gap-4 mb-2">
                  <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
                    <input
                      type="radio"
                      checked={skillMode === 'all'}
                      onChange={() => { setSkillMode('all'); setForm({ ...form, skill_ids: null }) }}
                      className="accent-teal-600"
                    />
                    All workspace skills
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
                    <input
                      type="radio"
                      checked={skillMode === 'select'}
                      onChange={() => { setSkillMode('select'); setForm({ ...form, skill_ids: [] }) }}
                      className="accent-teal-600"
                    />
                    Select specific
                  </label>
                </div>
                {skillMode === 'select' && (
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill) => (
                      <label
                        key={skill.id}
                        className={`flex items-center gap-2 text-sm px-3 py-2 rounded-md border cursor-pointer transition-colors ${
                          (form.skill_ids || []).includes(skill.name)
                            ? 'bg-teal-50 border-teal-200 text-teal-800'
                            : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={(form.skill_ids || []).includes(skill.name)}
                          onChange={(e) => {
                            const ids = form.skill_ids || []
                            if (e.target.checked) {
                              setForm({ ...form, skill_ids: [...ids, skill.name] })
                            } else {
                              setForm({ ...form, skill_ids: ids.filter((s) => s !== skill.name) })
                            }
                          }}
                          className="accent-teal-600"
                        />
                        <span className="font-medium">{skill.name}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}
            <div className="pt-2">
              <button type="submit" className="btn-primary">
                Create Job
              </button>
            </div>
          </div>
        </form>
      )}

      {jobs.length === 0 && !showForm ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-slate-500">No jobs defined yet.</p>
        </div>
      ) : (
        jobs.length > 0 && (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Agent</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Created</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job, i) => (
                  <tr
                    key={job.id}
                    className={`hover:bg-slate-50/50 transition-colors ${
                      i < jobs.length - 1 ? 'border-b border-slate-100' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <Link
                        to={`/jobs/${job.id}`}
                        className="font-medium text-slate-900 hover:text-teal-600 transition-colors"
                      >
                        {job.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-xs">{job.agent_type}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                      {new Date(job.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={async () => {
                          const run = await api.triggerRun(job.id)
                          navigate(`/runs/${run.id}`)
                        }}
                        className="btn-success text-xs px-3 py-1"
                      >
                        Run
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
