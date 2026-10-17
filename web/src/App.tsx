import { Routes, Route } from 'react-router'
import { LoginPage } from './pages/LoginPage/LoginPage'
import { DevPage } from './pages/DevPage/DevPage'
import { DashboardRoute } from './DashboardRoute'
import { RegisterPage } from './pages/RegisterPage/RegisterPage'
import { TakeQuizPage } from './pages/TakeQuiz/TakeQuizPage'

function App() {
  return <Routes>
    <Route path="/" element={<DashboardRoute />} />
    <Route path="/student" element={<DashboardRoute role="student" />} />
    <Route path="/lecturer" element={<DashboardRoute role="lecturer" />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/quizzes/:quizId" element={<TakeQuizPage />} />
    <Route path="/dev" element={<DevPage />} />
    <Route path="*" element={<h1>Page not found</h1>} />
  </Routes>
}
export default App
