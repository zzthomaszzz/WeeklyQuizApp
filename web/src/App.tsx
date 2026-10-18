import { Routes, Route } from 'react-router'
import { LoginPage } from './pages/LoginPage/LoginPage'
import { DashboardRoute } from './DashboardRoute'
import { TakeQuizPage } from './pages/TakeQuiz/TakeQuizPage'
import { AuthorQuizPage } from './pages/AuthorQuiz/AuthorQuizPage'

function App() {
  return <Routes>
    <Route path="/" element={<DashboardRoute />} />
    <Route path="/student" element={<DashboardRoute role="student" />} />
    <Route path="/lecturer" element={<DashboardRoute role="lecturer" />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/quizzes/:quizId" element={<TakeQuizPage />} />
    <Route path="/lecturer/courses/:courseId/quizzes/new" element={<AuthorQuizPage />} />
    <Route path="*" element={<h1>Page not found</h1>} />
  </Routes>
}
export default App
