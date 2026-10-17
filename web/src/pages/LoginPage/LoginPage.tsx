import { useState } from 'react'
import { useNavigate } from 'react-router'
import { request } from '../../api/client'
import type { User } from '../../api/client'
import styles from './LoginPage.module.css'

export function LoginPage() {
    const navigate = useNavigate()
    const [error, setError] = useState('')
    const [pending, setPending] = useState(false)
    return (
        <main className={styles.page}>
            <section className={styles.loginPanel} aria-labelledby="page-title">
                <header className={styles.brand}>
                    <div className={styles.logoMark} aria-hidden="true">WQ</div>
                    <h1 id="page-title">Weekly Quiz</h1>
                    <p>Sign in to see your quizzes.</p>
                </header>
                <div className={styles.loginOptions}>
                    <form className={styles.loginCard} onSubmit={async event => {
                        event.preventDefault()
                        if (pending) return
                        const form = new FormData(event.currentTarget)
                        setPending(true)
                        setError('')
                        try {
                            const user = await request<User>('/auth/login', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ email: String(form.get('email')).trim(), password: form.get('password') }),
                            })
                            navigate(user.role === 'lecturer' ? '/lecturer' : '/student', { replace: true })
                        } catch (error) {
                            setError(error instanceof Error ? error.message : 'Unable to sign in.')
                        } finally { setPending(false) }
                    }}>
                        <div className={styles.cardHeading}>
                            <span className={styles.roleIcon} aria-hidden="true">L</span>
                            <div><h2>Login</h2><p>Enter your account details.</p></div>
                        </div>
                        <label htmlFor="email">Email</label>
                        <input id="email" name="email" type="email" autoComplete="username" required disabled={pending} />
                        <label htmlFor="password">Password</label>
                        <input id="password" name="password" type="password" autoComplete="current-password" required disabled={pending} />
                        {error && <p role="alert">{error}</p>}
                        <button type="submit" disabled={pending}>{pending ? 'Signing in…' : 'Submit'}</button>
                    </form>
                </div>
            </section>
        </main>
    )
}
