import { useState } from 'react'
import axios from 'axios'

function Review({ record, onBack }) {
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const handleAction = async (action) => {
    console.log('cookies:', document.cookie)
    try {
      await axios.post(
        `http://localhost:8000/api/records/${record.id}/${action}/`,
        {},
        { withCredentials: true }
      )
      setDone(true)
    } catch (err) {
      console.log('error:', err.response?.status, err.response?.data)
      setError('Action failed. Try again.')
    }
  }

  if (done) {
    return (
      <div style={{ padding: '24px' }}>
        <p style={{ color: 'green', fontWeight: 'bold' }}>Done! Row updated.</p>
        <button onClick={onBack}>Back to dashboard</button>
      </div>
    )
  }

  return (
    <div style={{ padding: '24px', maxWidth: '600px' }}>
      <button onClick={onBack} style={{ marginBottom: '16px', cursor: 'pointer' }}>
        ← Back
      </button>

      <h2>Review — Row {record.source_row_number}</h2>

      <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          {[
            { label: 'Source', value: record.source },
            { label: 'Scope', value: record.scope },
            { label: 'Date', value: record.date },
            { label: 'Description', value: record.description },
            { label: 'Quantity', value: record.quantity },
            { label: 'Unit', value: record.unit },
          ].map(field => (
            <div key={field.label}>
              <div style={{ fontSize: '11px', color: '#888' }}>{field.label}</div>
              <div style={{ fontWeight: '500' }}>{field.value}</div>
            </div>
          ))}
        </div>
      </div>

      {record.transformations?.length > 0 && (
        <div style={{ background: '#f5f5f5', borderRadius: '6px', padding: '10px 14px', marginBottom: '12px', fontSize: '12px', color: '#555' }}>
          <strong>Transformations:</strong> {record.transformations.join(' · ')}
        </div>
      )}

      {record.validation_errors?.length > 0 && (
        <div style={{ background: '#fff0f0', border: '1px solid #ffcccc', borderRadius: '6px', padding: '10px 14px', marginBottom: '12px', fontSize: '13px', color: 'red' }}>
          <strong>Validation errors:</strong> {record.validation_errors.join(', ')}
        </div>
      )}

      {record.analysis_flags?.length > 0 && (
        <div style={{ background: '#fff8e6', border: '1px solid #ffd966', borderRadius: '6px', padding: '10px 14px', marginBottom: '12px', fontSize: '13px', color: '#854f0b' }}>
          <strong>Suspicious:</strong> {record.analysis_flags.join(', ')}
        </div>
      )}

      <details style={{ marginBottom: '16px' }}>
        <summary style={{ cursor: 'pointer', fontSize: '13px', color: '#555' }}>
          View original raw data
        </summary>
        <pre style={{ background: '#f5f5f5', padding: '12px', borderRadius: '6px', fontSize: '11px', overflowX: 'auto', marginTop: '8px' }}>
          {JSON.stringify(record.raw_data, null, 2)}
        </pre>
      </details>

      {error && <p style={{ color: 'red', fontSize: '13px' }}>{error}</p>}

      <div style={{ display: 'flex', gap: '8px' }}>
        <button onClick={() => handleAction('approve')} style={{ padding: '8px 20px', background: '#eaf3de', border: '1px solid #3b6d11', color: '#3b6d11', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
          Approve
        </button>
        <button onClick={() => handleAction('reject')} style={{ padding: '8px 20px', background: '#fff0f0', border: '1px solid #a32d2d', color: '#a32d2d', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
          Reject
        </button>
        <button onClick={onBack} style={{ padding: '8px 20px', border: '1px solid #ddd', borderRadius: '6px', cursor: 'pointer' }}>
          Skip
        </button>
      </div>
    </div>
  )
}

export default Review