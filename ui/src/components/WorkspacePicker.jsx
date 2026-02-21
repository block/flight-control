import { useState, useRef, useEffect } from 'react'
import { useWorkspace } from '../lib/workspace'
import { api } from '../lib/api'

export default function WorkspacePicker() {
  const { workspaces, currentWorkspace, switchWorkspace, refreshWorkspaces } = useWorkspace()
  const [open, setOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const ref = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
        setCreating(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!newName.trim()) return
    const slug = newName.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
    try {
      const ws = await api.createWorkspace({ name: newName.trim(), slug })
      await refreshWorkspaces()
      setNewName('')
      setCreating(false)
      setOpen(false)
      switchWorkspace(ws.id)
    } catch (err) {
      console.error('Failed to create workspace:', err)
    }
  }

  if (!currentWorkspace) return null

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px] font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        {currentWorkspace.name}
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-56 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50">
          {workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => {
                if (ws.id !== currentWorkspace.id) switchWorkspace(ws.id)
                setOpen(false)
              }}
              className={`w-full text-left px-3 py-2 text-[13px] hover:bg-slate-50 transition-colors ${
                ws.id === currentWorkspace.id ? 'font-medium text-slate-900 bg-slate-50' : 'text-slate-600'
              }`}
            >
              {ws.name}
            </button>
          ))}

          <div className="border-t border-slate-100 mt-1 pt-1">
            {creating ? (
              <form onSubmit={handleCreate} className="px-3 py-2">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Workspace name"
                  autoFocus
                  className="w-full px-2 py-1 text-[13px] border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-slate-400"
                />
                <div className="flex gap-1 mt-1.5">
                  <button
                    type="submit"
                    className="px-2 py-0.5 text-[12px] font-medium bg-slate-900 text-white rounded hover:bg-slate-800"
                  >
                    Create
                  </button>
                  <button
                    type="button"
                    onClick={() => { setCreating(false); setNewName('') }}
                    className="px-2 py-0.5 text-[12px] text-slate-500 hover:text-slate-700"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <button
                onClick={() => setCreating(true)}
                className="w-full text-left px-3 py-2 text-[13px] text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-colors"
              >
                + Create Workspace
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
