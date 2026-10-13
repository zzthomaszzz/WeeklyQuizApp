import { useState } from 'react'
import '../StudentsDashboard/Dashboard.css'
import type { DashboardData } from '../../api/client'
import './LecturerDashboard.css'


export function LecturerDashboard({ data }: { data: DashboardData }) {
  const { user, courses, quizzes } = data
  const [courseId, setCourseId] = useState('all')
  const [search, setSearch] = useState('')
  const visibleQuizzes = quizzes.filter(quiz => {
    const course = courses.find(item => item.id === quiz.course_id)
    return (courseId === 'all' || quiz.course_id === Number(courseId)) &&
      `${quiz.title} ${course?.code}`.toLowerCase().includes(search.toLowerCase())
  })

  return <div className="dashboard lecturer-dashboard">
    <header className="site-header">
      <a className="brand-link" href="/lecturer"><span className="brand-symbol">WQ</span>Weekly Quiz<span className="brand-divider">/</span><span className="workspace-name">Lecturer workspace</span></a>
      <span className="workspace-name">{user.name}</span>
    </header>
    <main className="dashboard-main">
      <div className="page-intro"><h1>Lecturer dashboard</h1><p className="intro-copy">Your courses and weekly quizzes.</p></div>
      <section className="quiz-section" aria-labelledby="courses-title">
        <div className="section-heading"><h2 id="courses-title">Your courses</h2></div>
        {courses.length === 0 && <p className="intro-copy">No courses have been assigned to you yet.</p>}<div className="lecturer-courses">{courses.map(course => <button key={course.id} className="lecturer-course" aria-pressed={courseId === String(course.id)} onClick={() => setCourseId(courseId === String(course.id) ? 'all' : String(course.id))}>
          <span className="course-code">{course.code}</span><strong>{course.name}</strong><span>{quizzes.filter(quiz => quiz.course_id === course.id).length} quizzes</span>
        </button>)}</div>
      </section>
      <section className="quiz-section lecturer-quizzes" aria-labelledby="lecturer-quizzes-title">
        <div className="section-heading"><h2 id="lecturer-quizzes-title">Your quizzes</h2><span className="sample-label">{visibleQuizzes.length} quizzes</span></div>
        <div className="quiz-toolbar"><div className="filters">
          <input type="search" aria-label="Search quizzes" placeholder="Search quizzes…" value={search} onChange={event => setSearch(event.target.value)} />
          <select aria-label="Course" value={courseId} onChange={event => setCourseId(event.target.value)}><option value="all">All courses</option>{courses.map(course => <option key={course.id} value={course.id}>{course.code}</option>)}</select>
        </div></div>
        <div className="quiz-list" aria-live="polite">{visibleQuizzes.map(quiz => <article className="quiz-row" key={quiz.id}>
          <div className="week-number"><span>WEEK</span><strong>{String(quiz.week_number).padStart(2, '0')}</strong></div>
          <div className="quiz-detail"><p>{courses.find(course => course.id === quiz.course_id)?.code}</p><h3>{quiz.title}</h3></div>
        </article>)}{visibleQuizzes.length === 0 && <div className="empty-state"><h3>No quizzes found</h3><p>Try another search or course.</p><button className="text-button" onClick={() => { setSearch(''); setCourseId('all') }}>Clear filters</button></div>}</div>
      </section>
      <footer className="dashboard-footer">Weekly Quiz</footer>
    </main>
  </div>
}

