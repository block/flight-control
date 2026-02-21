import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../lib/api'

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default function SkillDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [skill, setSkill] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getSkill(id)
      .then(setSkill)
      .catch((e) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <div className="card p-4 border-red-200 bg-red-50 text-red-700 text-sm">
        Error: {error}
      </div>
    )
  }
  if (!skill) {
    return <div className="text-sm text-slate-500">Loading...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to="/skills" className="text-xs font-medium text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-wide">
            &larr; Skills
          </Link>
          <h1 className="text-lg font-semibold text-slate-900 mt-1">{skill.name}</h1>
        </div>
        <button
          onClick={async () => {
            if (confirm('Delete this skill?')) {
              await api.deleteSkill(skill.id)
              navigate('/skills')
            }
          }}
          className="btn-danger"
        >
          Delete
        </button>
      </div>

      <div className="card p-6 mb-6">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Description</div>
        <p className="text-sm text-slate-700">{skill.description}</p>

        <div className="grid grid-cols-2 gap-x-8 gap-y-3 mt-5 pt-5 border-t border-slate-100">
          {skill.license && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wide w-28 shrink-0">License</span>
              <span className="text-sm text-slate-700">{skill.license}</span>
            </div>
          )}
          {skill.compatibility && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wide w-28 shrink-0">Compatibility</span>
              <span className="text-sm text-slate-700">{skill.compatibility}</span>
            </div>
          )}
          {skill.allowed_tools && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wide w-28 shrink-0">Allowed Tools</span>
              <span className="text-sm font-mono text-slate-700">{skill.allowed_tools}</span>
            </div>
          )}
        </div>
      </div>

      {skill.instructions && (
        <div className="card p-6 mb-6">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Instructions</div>
          <pre className="bg-slate-50 border border-slate-100 p-4 rounded-md text-sm text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
            {skill.instructions}
          </pre>
        </div>
      )}

      {skill.files?.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide mb-4">
            Files ({skill.files.length})
          </h2>
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Path</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Size</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {skill.files.map((file, i) => (
                  <tr
                    key={file.id}
                    className={`hover:bg-slate-50/50 transition-colors ${
                      i < skill.files.length - 1 ? 'border-b border-slate-100' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">{file.file_path}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{file.content_type}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-xs">{formatBytes(file.size_bytes)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => api.downloadSkillFile(skill.id, file.file_path, file.file_path.split('/').pop())}
                        className="text-xs text-teal-600 hover:text-teal-800 font-medium transition-colors"
                      >
                        Download
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
