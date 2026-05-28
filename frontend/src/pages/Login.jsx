import { useState } from 'react'
import axios from 'axios'

function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    try {
      const response = await axios.post(
        'http://localhost:8000/api/login/',
        { username, password },
        { withCredentials: true }
      )
      onLogin(response.data)
    } catch (err) {
      setError('Invalid username or password')
    }
  }

  return (
    <div style={{
      maxWidth: '320px',
      margin: '100px auto',
      padding: '24px',
      border: '1px solid #ddd',
      borderRadius: '8px'
    }}>
      <h2>Breathe ESG</h2>

      <div style={{ marginBottom: '12px' }}>
        <label>Username</label>
        <input
          type='text'
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{ display: 'block', width: '100%', padding: '8px', marginTop: '4px' }}
        />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>Password</label>
        <input
          type='password'
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ display: 'block', width: '100%', padding: '8px', marginTop: '4px' }}
        />
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <button
        onClick={handleSubmit}
        style={{ width: '100%', padding: '10px', background: '#1a1a1a', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
      >
        Sign in
      </button>
    </div>
  )
}

export default Login