import { useEffect, useState } from 'react';

function App() {
  const [status, setStatus] = useState('...');
  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(d => setStatus(d.status))
      .catch(() => setStatus('failed'));
  }, []);
  return <h1>Quiz App — API: {status}</h1>;
}

export default App;