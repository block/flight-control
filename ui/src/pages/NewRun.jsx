import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import ProviderModelSelect from '../components/ProviderModelSelect'

export default function NewRun() {
  const navigate = useNavigate()
  const [credentials, setCredentials] = useState([])
  const [form, setForm] = useState({
    name: 'Ad-hoc Run',
    task_prompt: '',
    agent_type: 'goose',
    agent_config: { provider: 'anthropic', model: 'claude-sonnet-4-5', max_turns: 30 },
    mcp_servers: [],
    credential_ids: [],
    timeout_seconds: 1800,
  })
  const [mcpInput, setMcpInput] = useState({ name: '', command: '', args: '' })
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listCredentials().then(setCredentials).catch(() => {})
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const run = await api.createAdHocRun(form)
      navigate(`/runs/${run.id}`)
    } catch (e) {
      setError(e.message)
    }
  }

  const addMcpServer = () => {
    if (!mcpInput.command) return
    setForm({
      ...form,
      mcp_servers: [
        ...form.mcp_servers,
        {
          name: mcpInput.name || mcpInput.command,
          type: 'stdio',
          command: mcpInput.command,
          args: mcpInput.args ? mcpInput.args.split(' ') : [],
        },
      ],
    })
    setMcpInput({ name: '', command: '', args: '' })
  }

  return (
    <div>
      <h1 className="text-lg font-semibold text-slate-900 mb-6">New Ad-hoc Run</h1>

      {error && (
        <div className="card p-3 border-red-200 bg-red-50 text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card p-6">
        <div className="space-y-6">
          {/* Run Name */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Run Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="input-field"
            />
          </div>

          {/* Task Prompt */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Task Prompt</label>
            <textarea
              required
              rows={6}
              value={form.task_prompt}
              onChange={(e) => setForm({ ...form, task_prompt: e.target.value })}
              className="input-field font-mono text-[13px]"
              placeholder="Describe what you want the agent to do..."
            />
          </div>

          {/* Agent Config */}
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3">Agent Configuration</div>
            <div className="grid grid-cols-3 gap-4">
              <ProviderModelSelect
                provider={form.agent_config.provider}
                model={form.agent_config.model}
                onChange={({ provider, model }) =>
                  setForm({ ...form, agent_config: { ...form.agent_config, provider, model } })
                }
              />
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Timeout (s)</label>
                <input
                  type="number"
                  value={form.timeout_seconds}
                  onChange={(e) => setForm({ ...form, timeout_seconds: parseInt(e.target.value) })}
                  className="input-field"
                />
              </div>
            </div>
          </div>

          {/* MCP Servers */}
          <div className="pt-2 border-t border-slate-100">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3">MCP Servers</div>
            {form.mcp_servers.length > 0 && (
              <div className="space-y-2 mb-3">
                {form.mcp_servers.map((s, i) => (
                  <div key={i} className="flex items-center justify-between bg-slate-50 border border-slate-100 px-3 py-2 rounded-md">
                    <span className="text-sm font-mono text-slate-700">
                      {s.name}: {s.command} {s.args?.join(' ')}
                    </span>
                    <button
                      type="button"
                      onClick={() => setForm({ ...form, mcp_servers: form.mcp_servers.filter((_, j) => j !== i) })}
                      className="text-xs text-red-500 hover:text-red-700 font-medium transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <input
                placeholder="Name"
                value={mcpInput.name}
                onChange={(e) => setMcpInput({ ...mcpInput, name: e.target.value })}
                className="input-field w-32"
              />
              <input
                placeholder="Command (e.g., npx)"
                value={mcpInput.command}
                onChange={(e) => setMcpInput({ ...mcpInput, command: e.target.value })}
                className="input-field flex-1"
              />
              <input
                placeholder="Args (space-separated)"
                value={mcpInput.args}
                onChange={(e) => setMcpInput({ ...mcpInput, args: e.target.value })}
                className="input-field flex-1"
              />
              <button
                type="button"
                onClick={addMcpServer}
                className="btn-secondary shrink-0"
              >
                Add
              </button>
            </div>
          </div>

          {/* Credentials */}
          {credentials.length > 0 && (
            <div className="pt-2 border-t border-slate-100">
              <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3">Credentials</div>
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

          <div className="pt-4 border-t border-slate-100">
            <button type="submit" className="btn-success">
              Start Run
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
