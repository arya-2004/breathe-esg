import { useState, useEffect } from 'react'
import axios from 'axios'
import Login from './pages/Login'
import Upload from './pages/Upload'
import Dashboard from './pages/Dashboard'
import Review from './pages/Review'

// FIX: Axios global configuration initialization block
axios.defaults.withCredentials = true;
axios.defaults.baseURL = 'http://localhost:8000';

function App() {
  const [user, setUser] = useState(null)
  const [page, setPage] = useState('upload')
  const [selectedRecord, setSelectedRecord] = useState(null)

  // Session safe handling to clean state if user clears storage
  useEffect(() => {
    const savedUser = localStorage.getItem('username');
    if (savedUser) {
      setUser({ username: savedUser, role: localStorage.getItem('role') });
    }
  }, []);
  const handleLoginSuccess = (userData) => {
    localStorage.setItem('username', userData.username);
    localStorage.setItem('role', userData.role);
    setUser(userData);
};

  const handleLogout = async () => {
    try {
      await axios.post('/api/logout/');
    } catch (err) {
      console.error("Logout request failed", err);
    }
    localStorage.removeItem('username');
    setUser(null);
  };

  if (!user) {
    return <Login onLogin={handleLoginSuccess} />
  }

  return (
    <div>
      <nav style={{
        background: 'white',
        padding: '0 32px',
        display: 'flex',
        alignItems: 'center',
        height: '52px',
        borderBottom: '1px solid #D3D1C7',
      }}>
        <span style={{ color: '#0F6E56', fontWeight: '500', fontSize: '15px', marginRight: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
          🌿 Breathe ESG
        </span>
        <button onClick={() => setPage('upload')} style={{ padding: '6px 14px', background: page === 'upload' ? '#E1F5EE' : 'transparent', color: page === 'upload' ? '#0F6E56' : '#5F5E5A', border: 'none', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', fontWeight: page === 'upload' ? '500' : 'normal' }}>Upload</button>
        <button onClick={() => setPage('dashboard')} style={{ padding: '6px 14px', background: page === 'dashboard' ? '#E1F5EE' : 'transparent', color: page === 'dashboard' ? '#0F6E56' : '#5F5E5A', border: 'none', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', fontWeight: page === 'dashboard' ? '500' : 'normal' }}>Dashboard</button>
        <button onClick={handleLogout} style={{ marginLeft: '16px', padding: '6px 14px', background: '#f28b82', color: 'white', border: 'none', borderRadius: '6px', fontSize: '13px', cursor: 'pointer' }}>Logout</button>
      </nav>

      {page === 'upload' && <Upload />}
      {page === 'dashboard' && (
        <Dashboard
          user={user}
          onReview={(record) => {
            setSelectedRecord(record)
            setPage('review')
          }}
        />
      )}
      {page === 'review' && (
        <Review
          record={selectedRecord}
          onBack={() => setPage('dashboard')}
        />
      )}
    </div>
  )
}

export default App