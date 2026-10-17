import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { logout } from '../api/client'

interface SiteHeaderProps {
  workspace: string
  userName?: string
}

export function SiteHeader({ workspace, userName }: SiteHeaderProps) {
  const navigate = useNavigate()
  const [pending, setPending] = useState(false)

  async function signOut() {
    if (pending) return
    setPending(true)
    try {
      await logout()
    } catch {
      // The session cookie is httpOnly, so the browser cannot clear it
      // itself. Returning to login is still better than leaving someone
      // on a page they can no longer use.
    } finally {
      navigate('/login', { replace: true })
    }
  }

  return (
    <header className="site-header">
      <Link className="brand-link" to="/">
        <span className="brand-symbol">WQ</span>
        Weekly Quiz
        <span className="brand-divider">/</span>
        <span className="workspace-name">{workspace}</span>
      </Link>
      <div className="header-account">
        {userName && <span className="workspace-name">{userName}</span>}
        <button
          type="button"
          className="text-button"
          onClick={signOut}
          disabled={pending}
        >
          {pending ? 'Signing out…' : 'Sign out'}
        </button>
      </div>
    </header>
  )
}
