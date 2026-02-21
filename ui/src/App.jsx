import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import JobDetail from './pages/JobDetail'
import RunDetail from './pages/RunDetail'
import Workers from './pages/Workers'
import Credentials from './pages/Credentials'
import Schedules from './pages/Schedules'
import NewRun from './pages/NewRun'
import Skills from './pages/Skills'
import SkillDetail from './pages/SkillDetail'
import WorkspacePicker from './components/WorkspacePicker'

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/jobs', label: 'Jobs' },
  { path: '/schedules', label: 'Schedules' },
  { path: '/runs/new', label: 'New Run' },
  { path: '/workers', label: 'Workers' },
  { path: '/credentials', label: 'Credentials' },
  { path: '/skills', label: 'Skills' },
]

export default function App() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-stone-50">
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center h-14 gap-8">
            <Link to="/" className="flex items-center gap-2 shrink-0">
              <span className="text-[15px] font-bold tracking-tight text-slate-900">
                Flight Control
              </span>
            </Link>
            <div className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive =
                  item.path === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                      isActive
                        ? 'bg-slate-100 text-slate-900'
                        : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </div>
            <div className="ml-auto">
              <WorkspacePicker />
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-6 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
          <Route path="/runs/new" element={<NewRun />} />
          <Route path="/runs/:id" element={<RunDetail />} />
          <Route path="/workers" element={<Workers />} />
          <Route path="/credentials" element={<Credentials />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/skills/:id" element={<SkillDetail />} />
          <Route path="/schedules" element={<Schedules />} />
        </Routes>
      </main>
    </div>
  )
}
