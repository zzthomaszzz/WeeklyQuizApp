import { Link } from 'react-router';
import styles from './DevPage.module.css';


const teamMembers = [
  {

    name: '[Thomas]',
    role: '[Developer]',

  },
  {

    name: '[Shan]',
    role: '[Developer]',

  },
  {

    name: '[Yuan]',
    role: '[Developer]',

  },
];

export function DevPage() {
  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.brand}>
            <span className={styles.logoMark} aria-hidden="true">WQ</span>
            <span>Weekly Quiz</span>
          </div>
          <Link className={styles.backLink} to="/login">Back to login</Link>
        </header>

        <main>
          <h1 className={styles.pageTitle}>Development team</h1>

          <ul className={styles.teamGrid} aria-label="Development team members">
            {teamMembers.map((member) => (
              <li key={member.name} className={styles.card}>
                <h2>{member.name}</h2>
                <p className={styles.role}>{member.role}</p>
              </li>
            ))}
          </ul>
        </main>

        <footer className={styles.footer}>Weekly Quiz · Development team</footer>
      </div>
    </div>
  );
}
