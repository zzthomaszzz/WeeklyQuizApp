
import styles from './LoginPage.module.css';

export function LoginPage() {
    return (
        <main className={styles.page}>
            <section className={styles.loginPanel} aria-labelledby="page-title">
                <header className={styles.brand}>
                    <div className={styles.logoMark} aria-hidden="true">WQ</div>
                    <h1 id="page-title">Weekly Quiz</h1>
                    <p>Sign in to see the quizzes.</p>
                </header>

                <div className={styles.loginOptions}>
                    <form className={styles.loginCard}>
                        <div className={styles.cardHeading}>
                            <span className={styles.roleIcon} aria-hidden="true">L</span>
                            <div>
                                <h2>Login</h2>
                                <p>Get in</p>
                            </div>
                        </div>
                        <label htmlFor="name">Name</label>
                        <input id="name" name="name" type="text" autoComplete="username" required />
                        <label htmlFor="password">Password</label>
                        <input id="password" name="password" type="password" autoComplete="password" required />
                        <button type="submit">Submit</button>
                    </form>

                  
                </div>
            </section>
        </main>
    );
}
