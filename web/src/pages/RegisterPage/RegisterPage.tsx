import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { postJson } from '../../api/client'
import type { User } from '../../api/client'
import styles from '../LoginPage/LoginPage.module.css'

export function RegisterPage() {
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  return (
    <main className={styles.page}>
      <section className={styles.loginPanel} aria-labelledby="page-title">
        <header className={styles.brand}>
          <div className={styles.logoMark} aria-hidden="true">WQ</div>
          <h1 id="page-title">Weekly Quiz</h1>
          <p>Create an account to get started.</p>
        </header>
        <div className={styles.loginOptions}>
          <form
            className={styles.loginCard}
            onSubmit={async event => {
              event.preventDefault()
              if (pending) return
              const form = new FormData(event.currentTarget)
              setPending(true)
              setError('')
              try {
                const user = await postJson<User>('/auth/register', {
                  name: String(form.get('name')).trim(),
                  email: String(form.get('email')).trim(),
                  password: form.get('password'),
                  role: form.get('role'),
                })
                // Registering signs you in, so go straight to the dashboard.
                navigate(user.role === 'lecturer' ? '/lecturer' : '/student', { replace: true })
              } catch (problem) {
                setError(problem instanceof Error ? problem.message : 'Unable to create your account.')
              } finally {
                setPending(false)
              }
            }}
          >
            <div className={styles.cardHeading}>
              <span className={styles.roleIcon} aria-hidden="true">R</span>
              <div><h2>Register</h2><p>It takes a moment.</p></div>
            </div>

            <label htmlFor="name">Full name</label>
            <input id="name" name="name" type="text" autoComplete="name" required disabled={pending} />

            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" autoComplete="username" required disabled={pending} />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
              disabled={pending}
            />

            <label htmlFor="role">I am a</label>
            <select id="role" name="role" defaultValue="student" disabled={pending}>
              <option value="student">Student</option>
              <option value="lecturer">Lecturer</option>
            </select>

            {error && <p role="alert">{error}</p>}

            <button type="submit" disabled={pending}>
              {pending ? 'Creating account…' : 'Create account'}
            </button>

            <p className={styles.altAction}>
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </form>
        </div>
      </section>
    </main>
  )
}
