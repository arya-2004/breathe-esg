import { useState, useEffect } from 'react'
import axios from 'axios'

function Dashboard({ onReview, user }) {
  const [batches, setBatches] = useState([])
  const [records, setRecords] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')

  const isAdmin = user?.role === 'admin'

  useEffect(() => { fetchBatches() }, [])
  useEffect(() => { fetchRecords() }, [page, statusFilter, selectedBatch])

  const fetchBatches = async () => {
    try {
      const res = await axios.get('/api/batches/', { withCredentials: true })
      setBatches(res.data)
    } catch (err) { console.error('Could not fetch batches') }
  }

  const fetchRecords = async () => {
    try {
      const params = { page }
      if (statusFilter) params.status = statusFilter
      if (selectedBatch) params.batch_id = selectedBatch
      const res = await axios.get('/api/records/', { params, withCredentials: true })
      setRecords(res.data.records)
      setTotal(res.data.total)
    } catch (err) { console.error('Could not fetch records') }
  }

  const handleDelete = async (batchId, filename) => {
    if (!window.confirm(`Delete batch "${filename}"? This will delete all its records.`)) return
    try {
      await axios.delete(`/api/batches/${batchId}/delete/`, { withCredentials: true })
      fetchBatches()
      fetchRecords()
    } catch (err) {
      alert(err.response?.data?.error || 'Delete failed')
    }
  }

  const handleLock = async (batchId, filename) => {
    if (!window.confirm(`Lock batch "${filename}" for audit? This cannot be undone.`)) return
    try {
      await axios.post(`/api/batches/${batchId}/lock/`, {}, { withCredentials: true })
      fetchBatches()
    } catch (err) {
      alert(err.response?.data?.error || 'Lock failed')
    }
  }

  const totalStats = batches.reduce((acc, b) => ({
    total: acc.total + b.total_rows,
    failed: acc.failed + b.failed_rows,
    suspicious: acc.suspicious + b.suspicious_rows,
    clean: acc.clean + b.clean_rows,
  }), { total: 0, failed: 0, suspicious: 0, clean: 0 })

  const statusColor = (s) => {
    if (s === 'approved') return '#3B6D11'
    if (s === 'suspicious') return '#854F0B'
    if (s === 'failed') return '#A32D2D'
    if (s === 'rejected') return '#888'
    return '#333'
  }

  const statusBg = (s) => {
    if (s === 'approved') return '#EAF3DE'
    if (s === 'suspicious') return '#FAEEDA'
    if (s === 'failed') return '#FCEBEB'
    if (s === 'rejected') return '#F1EFE8'
    return '#f5f5f5'
  }

  return (
    <div style={{ padding: '28px 32px' }}>
      <h2 style={{ color: '#2C2C2A', marginBottom: '20px' }}>Dashboard</h2>

      {/* Stats */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '28px' }}>
        {[
          { label: 'Total', value: totalStats.total, color: '#0F6E56' },
          { label: 'Clean', value: totalStats.clean, color: '#3B6D11' },
          { label: 'Suspicious', value: totalStats.suspicious, color: '#854F0B' },
          { label: 'Failed', value: totalStats.failed, color: '#A32D2D' },
        ].map(stat => (
          <div key={stat.label} style={{
            background: 'white',
            border: '1px solid #D3D1C7',
            borderRadius: '8px',
            padding: '14px 20px',
            minWidth: '110px'
          }}>
            <div style={{ fontSize: '26px', fontWeight: '600', color: stat.color }}>{stat.value}</div>
            <div style={{ fontSize: '12px', color: '#888780', marginTop: '2px' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Batches */}
      <h3 style={{ color: '#2C2C2A', marginBottom: '12px', fontSize: '14px', fontWeight: '600' }}>Upload batches</h3>
      {batches.length === 0 && (
        <p style={{ color: '#888780', fontSize: '13px' }}>No uploads yet.</p>
      )}
      {batches.map(batch => (
        <div key={batch.id} style={{
          background: 'white',
          border: `1px solid ${batch.is_locked ? '#0F6E56' : '#D3D1C7'}`,
          borderRadius: '8px',
          padding: '14px 16px',
          marginBottom: '8px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ fontSize: '13px', color: '#2C2C2A' }}>{batch.filename}</strong>
              {batch.is_locked && (
                <span style={{ marginLeft: '8px', fontSize: '11px', color: '#0F6E56', background: '#E1F5EE', padding: '2px 8px', borderRadius: '10px' }}>
                  🔒 Locked
                </span>
              )}
              <span style={{ marginLeft: '10px', color: '#888780', fontSize: '12px' }}>
                {batch.source} · {batch.uploaded_by} · {batch.total_rows} rows
              </span>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                onClick={() => setSelectedBatch(selectedBatch === batch.id ? null : batch.id)}
                style={{ padding: '4px 12px', border: '1px solid #0F6E56', borderRadius: '6px', color: '#0F6E56', background: 'white', fontSize: '12px', cursor: 'pointer' }}
              >
                {selectedBatch === batch.id ? 'Hide ↑' : 'Show ↓'}
              </button>
              {isAdmin && !batch.is_locked && (
                <button
                  onClick={() => handleLock(batch.id, batch.filename)}
                  style={{ padding: '4px 12px', border: '1px solid #0F6E56', borderRadius: '6px', color: '#0F6E56', background: 'white', fontSize: '12px', cursor: 'pointer' }}
                >
                  🔒 Lock
                </button>
              )}
              {isAdmin && !batch.is_locked && (
                <button
                  onClick={() => handleDelete(batch.id, batch.filename)}
                  style={{ padding: '4px 12px', border: '1px solid #A32D2D', borderRadius: '6px', color: '#A32D2D', background: 'white', fontSize: '12px', cursor: 'pointer' }}
                >
                  🗑 Delete
                </button>
              )}
            </div>
          </div>
          <div style={{ marginTop: '8px', fontSize: '12px', display: 'flex', gap: '12px' }}>
            <span style={{ color: '#3B6D11' }}>{batch.clean_rows} clean</span>
            <span style={{ color: '#854F0B' }}>{batch.suspicious_rows} suspicious</span>
            <span style={{ color: '#A32D2D' }}>{batch.failed_rows} failed</span>
          </div>
        </div>
      ))}

      {/* Records */}
      <div style={{ marginTop: '24px' }}>
        <h3 style={{ color: '#2C2C2A', marginBottom: '12px', fontSize: '14px', fontWeight: '600' }}>Records</h3>
        <div style={{ display: 'flex', gap: '6px', marginBottom: '12px' }}>
          {['', 'pending', 'suspicious', 'failed', 'approved', 'rejected'].map(s => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1) }}
              style={{
                padding: '4px 12px',
                borderRadius: '20px',
                border: '1px solid #D3D1C7',
                background: statusFilter === s ? '#1a1a1a' : 'white',
                color: statusFilter === s ? 'white' : '#5F5E5A',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              {s === '' ? 'All' : s}
            </button>
          ))}
        </div>

        <div style={{ background: 'white', border: '1px solid #D3D1C7', borderRadius: '8px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f7f8f5', borderBottom: '1px solid #D3D1C7', textAlign: 'left' }}>
                {['Row', 'Source', 'Date', 'Description', 'Quantity', 'Unit', 'Status', ''].map(h => (
                  <th key={h} style={{ padding: '10px 14px', fontWeight: '500', color: '#888780', fontSize: '12px' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {records.length === 0 && (
                <tr><td colSpan={8} style={{ padding: '20px', color: '#888780', textAlign: 'center' }}>No records found</td></tr>
              )}
              {records.map(record => (
                <tr key={record.id} style={{ borderBottom: '1px solid #F1EFE8' }}>
                  <td style={{ padding: '10px 14px' }}>{record.source_row_number}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ background: '#F1EFE8', color: '#5F5E5A', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>{record.source}</span>
                  </td>
                  <td style={{ padding: '10px 14px' }}>{record.date}</td>
                  <td style={{ padding: '10px 14px' }}>{record.description}</td>
                  <td style={{ padding: '10px 14px' }}>{record.quantity}</td>
                  <td style={{ padding: '10px 14px' }}>{record.unit}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ color: statusColor(record.status), background: statusBg(record.status), padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>
                      {record.status}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <button
                      onClick={() => onReview(record)}
                      style={{ cursor: 'pointer', fontSize: '12px', color: '#0F6E56', background: 'none', border: 'none', fontWeight: '500' }}
                    >
                      Review →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginTop: '12px', alignItems: 'center' }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
            style={{ padding: '4px 10px', border: '1px solid #D3D1C7', borderRadius: '6px', cursor: 'pointer', background: 'white' }}>←</button>
          <span style={{ fontSize: '13px', color: '#5F5E5A' }}>Page {page}</span>
          <button onClick={() => setPage(p => p + 1)} disabled={page * 50 >= total}
            style={{ padding: '4px 10px', border: '1px solid #D3D1C7', borderRadius: '6px', cursor: 'pointer', background: 'white' }}>→</button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard