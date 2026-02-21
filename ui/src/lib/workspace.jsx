import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from './api'

const WorkspaceContext = createContext(null)

export function WorkspaceProvider({ children }) {
  const [workspaces, setWorkspaces] = useState([])
  const [currentWorkspace, setCurrentWorkspace] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadWorkspaces = useCallback(async () => {
    try {
      const list = await api.listWorkspaces()
      setWorkspaces(list)

      const savedId = localStorage.getItem('workspace_id') || 'default'
      const current = list.find((w) => w.id === savedId) || list[0]
      if (current) {
        setCurrentWorkspace(current)
        localStorage.setItem('workspace_id', current.id)
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadWorkspaces()
  }, [loadWorkspaces])

  const switchWorkspace = useCallback((workspaceId) => {
    localStorage.setItem('workspace_id', workspaceId)
    window.location.reload()
  }, [])

  return (
    <WorkspaceContext.Provider
      value={{ workspaces, currentWorkspace, switchWorkspace, loading, refreshWorkspaces: loadWorkspaces }}
    >
      {children}
    </WorkspaceContext.Provider>
  )
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext)
  if (!ctx) throw new Error('useWorkspace must be used within WorkspaceProvider')
  return ctx
}
