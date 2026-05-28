import { useState } from 'react'
import axios from 'axios'

function UploadCard({ title, subtitle, source, apiUrl, icon }) {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    setLoading(true)
    setError('')
    setSummary(null)
    try {
      const response = await axios.post(apiUrl, formData, { withCredentials: true })
      setSummary(response.data)
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      border: '1px solid #D3D1C7',
      borderRadius: '10px',
      padding: '28px 20px',
      textAlign: 'center',
      flex: 1,
      background: 'white'
    }}>
      <div style={{ fontSize: '32px', marginBottom: '10px' }}>{icon}</div>
      <h3 style={{ color: '#2C2C2A', marginBottom: '6px', fontSize: '14px' }}>{title}</h3>
      <p style={{ color: '#888780', fontSize: '12px', marginBottom: '16px' }}>{subtitle}</p>

      <input
        type='file'
        accept='.csv'
        onChange={handleFile}
        style={{ display: 'none' }}
        id={source}
      />
      <label htmlFor={source} style={{
        display: 'inline-block',
        padding: '8px 20px',
        background: '#1a1a1a',
        color: 'white',
        borderRadius: '6px',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: '500'
      }}>
        {loading ? 'Uploading...' : 'Choose file'}
      </label>

      {error && <p style={{ color: 'red', marginTop: '8px', fontSize: '12px' }}>{error}</p>}

      {summary && (
        <div style={{
          marginTop: '14px',
          background: '#E1F5EE',
          borderRadius: '6px',
          padding: '10px 12px',
          textAlign: 'left',
          fontSize: '12px'
        }}>
          <p style={{ fontWeight: '600', marginBottom: '6px', color: '#085041' }}>
            {summary.filename} uploaded
          </p>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <span style={{ color: '#333' }}>Total: {summary.total}</span>
            <span style={{ color: '#3B6D11' }}>Clean: {summary.clean}</span>
            <span style={{ color: '#854F0B' }}>Suspicious: {summary.suspicious}</span>
            <span style={{ color: '#A32D2D' }}>Failed: {summary.failed}</span>
          </div>
        </div>
      )}
    </div>
  )
}

function Upload() {
  return (
    <div style={{ padding: '28px 32px' }}>
      <h2 style={{ color: '#2C2C2A', marginBottom: '6px' }}>Upload emission data</h2>
      <p style={{ color: '#888780', fontSize: '13px', marginBottom: '24px' }}>
        Upload CSV files from each data source below
      </p>
      <div style={{ display: 'flex', gap: '16px' }}>
        <UploadCard
          title='SAP fuel & procurement'
          subtitle='Flat file CSV export'
          source='sap'
          apiUrl='http://localhost:8000/api/upload/sap/'
          icon='🗂️'
        />
        <UploadCard
          title='Utility electricity'
          subtitle='Portal CSV export'
          source='utility'
          apiUrl='http://localhost:8000/api/upload/utility/'
          icon='⚡'
        />
        <UploadCard
          title='Corporate travel'
          subtitle='Concur/Navan export'
          source='travel'
          apiUrl='http://localhost:8000/api/upload/travel/'
          icon='✈️'
        />
      </div>
    </div>
  )
}

export default Upload