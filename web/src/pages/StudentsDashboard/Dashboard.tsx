import { useState } from 'react'
import './Dashboard.css'
import type { DashboardData } from '../../api/client'

export function Dashboard({ data }: { data: DashboardData }) {
  const { user, courses } = data
  const quizzes = data.quizzes.map(quiz => ({ ...quiz, course: courses.find(item => item.id === quiz.course_id)?.code ?? '' }))
  const [search, setSearch] = useState('')
  const [course, setCourse] = useState('all')
  const filtered = quizzes.filter(q => (course === 'all' || String(q.course_id) === course) && `${q.title} ${q.course}`.toLowerCase().includes(search.toLowerCase()))
  return <div className="dashboard">
    <header className="site-header"><a className="brand-link" href="/"><span className="brand-symbol">WQ</span>Weekly Quiz<span className="brand-divider">/</span><span className="workspace-name">Student workspace</span></a><span className="workspace-name">{user.name}</span></header>
    <main className="dashboard-main">
      <div className="page-intro"><div><h1>Weekly quizzes</h1><p className="intro-copy">View your course quizzes.</p></div></div>
      <section className="quiz-section" aria-labelledby="quizzes-title"><div className="section-heading"><h2 id="quizzes-title">Your quizzes <span>{filtered.length}</span></h2></div>
        <div className="quiz-toolbar"><div className="filters"><input type="search" aria-label="Search quizzes" placeholder="Search quizzes…" value={search} onChange={e => setSearch(e.target.value)} /><select aria-label="Course" value={course} onChange={e => setCourse(e.target.value)}><option value="all">All courses</option>{courses.map(item => <option key={item.id} value={item.id}>{item.code}</option>)}</select></div></div>
        <div className="quiz-list" aria-live="polite">{filtered.map(quiz => <article className="quiz-row" key={quiz.id}><div className="week-number"><span>WEEK</span><strong>{String(quiz.week_number).padStart(2, '0')}</strong></div><div className="quiz-detail"><p>{quiz.course}</p><h3>{quiz.title}</h3></div></article>)}{filtered.length === 0 && <div className="empty-state"><h3>No quizzes found</h3><p>{quizzes.length === 0 ? "No quizzes are currently open for your enrolled courses." : "Try another search or choose a different course."}</p><button className="text-button" onClick={() => { setSearch(''); setCourse('all') }}>Clear filters</button></div>}</div>
      </section><footer className="dashboard-footer"><span>Weekly Quiz</span></footer>
    </main>
  </div>
}





