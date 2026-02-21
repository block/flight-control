import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function Credentials() {
  const [credentials, setCredentials] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', env_var: '', value: '', description: '' })
  const [error, setError] = useState(null)

  const fetchCreds = () => api.listCredentials().then(setCredentials).catch((e) => setError(e.message))

  useEffect(() => { fetchCreds() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await api.createCredential(form)
      setForm({ name: '', env_var: '', value: '', description: '' })
      setShowForm(false)
      fetchCreds()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Credentials</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className={showForm ? 'btn-secondary' : 'btn-primary'}
        >
          {showForm ? 'Cancel' : 'Add Credential'}
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
                  placeholder="e.g., anthropic-api-key"
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Environment Variable</label>
                <input
                  type="text"
                  required
                  value={form.env_var}
                  onChange={(e) => setForm({ ...form, env_var: e.target.value })}
                  placeholder="e.g., ANTHROPIC_API_KEY"
                  className="input-field font-mono"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Value</label>
              <input
                type="password"
                required
                value={form.value}
                onChange={(e) => setForm({ ...form, value: e.target.value })}
                placeholder="The secret value (encrypted at rest)"
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Description (optional)</label>
              <input
                type="text"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="input-field"
              />
            </div>
            <div className="pt-2">
              <button type="submit" className="btn-primary">
                Save Credential
              </button>
            </div>
          </div>
        </form>
      )}

      {credentials.length === 0 && !showForm ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-slate-500">No credentials stored.</p>
        </div>
      ) : (
        credentials.length > 0 && (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Env Variable</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Description</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {credentials.map((cred, i) => (
                  <tr
                    key={cred.id}
                    className={`hover:bg-slate-50/50 transition-colors ${
                      i < credentials.length - 1 ? 'border-b border-slate-100' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-medium text-slate-900">{cred.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">{cred.env_var}</td>
                    <td className="px-4 py-3 text-slate-500">{cred.description || <span className="text-slate-300">-</span>}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={async () => {
                          if (confirm(`Delete credential "${cred.name}"?`)) {
                            await api.deleteCredential(cred.id)
                            fetchCreds()
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
