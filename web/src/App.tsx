import { Routes, Route } from 'react-router';
import { LoginPage } from './pages/LoginPage/LoginPage';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="*" element={<h1>Page not found</h1>} />
    </Routes>
  );
}
export default App;