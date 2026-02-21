import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default function Skills() {
  const [skills, setSkills] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [skillMdFile, setSkillMdFile] = useState(null)
  const [extraFiles, setExtraFiles] = useState([])
  const [zipFile, setZipFile] = useState(null)

  const fetchSkills = () => api.listSkills().then(setSkills).catch((e) => setError(e.message))

  useEffect(() => { fetchSkills() }, [])

  const resetForm = () => {
    setSkillMdFile(null)
    setExtraFiles([])
    setZipFile(null)
    setShowForm(false)
    setError(null)
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!skillMdFile) return

    setUploading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('skill_md', skillMdFile)
      if (zipFile) {
        formData.append('zip_file', zipFile)
      } else if (extraFiles.length > 0) {
        for (const f of extraFiles) {
          formData.append('files', f)
        }
      }
      await api.uploadSkill(formData)
      resetForm()
      fetchSkills()
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Skills</h1>
        <button
          onClick={() => showForm ? resetForm() : setShowForm(true)}
          className={showForm ? 'btn-secondary' : 'btn-primary'}
        >
          {showForm ? 'Cancel' : 'Upload Skill'}
        </button>
      </div>

      {error && (
        <div className="card p-3 border-red-200 bg-red-50 text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleUpload} className="card p-6 mb-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                SKILL.md <span className="text-red-400">*</span>
              </label>
              <input
                type="file"
                accept=".md"
                required
                onChange={(e) => setSkillMdFile(e.target.files[0])}
                className="input-field text-sm file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
              />
              <p className="text-xs text-slate-400 mt-1">
                SKILL.md with YAML frontmatter (name, description) and markdown instructions
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Additional Files (optional)
              </label>
              <input
                type="file"
                multiple
                onChange={(e) => { setExtraFiles(Array.from(e.target.files)); setZipFile(null) }}
                className="input-field text-sm file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
              />
              <p className="text-xs text-slate-400 mt-1">Scripts, references, or assets</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Or Zip Archive (optional)
              </label>
              <input
                type="file"
                accept=".zip"
                onChange={(e) => { setZipFile(e.target.files[0]); setExtraFiles([]) }}
                className="input-field text-sm file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
              />
            </div>
            <div className="pt-2">
              <button type="submit" disabled={uploading} className="btn-primary">
                {uploading ? 'Uploading...' : 'Upload Skill'}
              </button>
            </div>
          </div>
        </form>
      )}

      {skills.length === 0 && !showForm ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-slate-500">No skills uploaded yet.</p>
        </div>
      ) : (
        skills.length > 0 && (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Files</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Size</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Created</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {skills.map((skill, i) => (
                  <tr
                    key={skill.id}
                    className={`hover:bg-slate-50/50 transition-colors ${
                      i < skills.length - 1 ? 'border-b border-slate-100' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <Link
                        to={`/skills/${skill.id}`}
                        className="font-medium text-slate-900 hover:text-teal-600 transition-colors"
                      >
                        {skill.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-500 max-w-xs truncate">{skill.description}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-xs">{skill.file_count}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-xs">{formatBytes(skill.total_size_bytes)}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                      {new Date(skill.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right space-x-3">
                      <Link
                        to={`/skills/${skill.id}`}
                        className="text-xs text-slate-500 hover:text-slate-700 font-medium transition-colors"
                      >
                        View
                      </Link>
                      <button
                        onClick={async () => {
                          if (confirm(`Delete skill "${skill.name}"?`)) {
                            await api.deleteSkill(skill.id)
                            fetchSkills()
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
