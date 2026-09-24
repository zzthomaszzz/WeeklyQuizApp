import { Routes, Route } from 'react-router'
import { LoginPage } from './pages/LoginPage/LoginPage'
import { DashboardRoute } from './DashboardRoute'

function App() {
  return <Routes>
    <Route path="/" element={<DashboardRoute />} />
    <Route path="/student" element={<DashboardRoute role="student" />} />
    <Route path="/lecturer" element={<DashboardRoute role="lecturer" />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="*" element={<h1>Page not found</h1>} />
  </Routes>
}
export default App
