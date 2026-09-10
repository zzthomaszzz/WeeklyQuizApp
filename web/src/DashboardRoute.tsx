import { useEffect, useState } from 'react'
import { Navigate } from 'react-router'
import { ApiError, request } from './api/client'
import type { DashboardData, User } from './api/client'
import { Dashboard } from './pages/StudentsDashboard/Dashboard'
import { LecturerDashboard } from './pages/LecturerDashboard/LecturerDashboard'

export function DashboardRoute({ role }: { role?: User['role'] }) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')
  const [unauthorized, setUnauthorized] = useState(false)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let active = true
    setError('')
    setData(null)
    request<DashboardData>('/dashboard').then(result => {
      if (active) setData(result)
    }).catch(error => {
      if (!active) return
      if (error instanceof ApiError && error.status === 401) setUnauthorized(true)
      else setError(error.message)
    })
    return () => { active = false }
  }, [retry])
  if (unauthorized) return <Navigate to="/login" replace />
  if (error) return <main className="dashboard"><div className="quiz-section"><p role="alert">{error}</p><button className="text-button" onClick={() => setRetry(value => value + 1)}>Try again</button></div></main>
  if (!data) return <main className="dashboard"><p role="status">Loading your dashboard…</p></main>
  if (role !== data.user.role) return <Navigate to={data.user.role === 'lecturer' ? '/lecturer' : '/student'} replace />
  return data.user.role === 'lecturer' ? <LecturerDashboard data={data} /> : <Dashboard data={data} />
}
