import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Database, Search, Table2, RefreshCcw, Loader2 } from 'lucide-react'

import { API } from '../../config'

interface TableData {
  table: string
  columns: string[]
  data: any[]
}

export default function DataHub({ token }: { token: string | null }) {
  const [tables, setTables] = useState<string[]>([])
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [tableData, setTableData] = useState<TableData | null>(null)
  const [loadingTables, setLoadingTables] = useState(true)
  const [loadingData, setLoadingData] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  // Fetch list of tables
  useEffect(() => {
    fetchTables()
  }, [])

  const fetchTables = async () => {
    setLoadingTables(true)
    try {
      const res = await fetch(`${API}/api/database/tables`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      setTables(data.tables || [])
      if (data.tables && data.tables.length > 0 && !selectedTable) {
        setSelectedTable(data.tables[0])
      }
    } catch (err) {
      console.error('Failed to fetch tables:', err)
    } finally {
      setLoadingTables(false)
    }
  }

  // Fetch data when selected table changes
  useEffect(() => {
    if (selectedTable) {
      fetchTableData(selectedTable)
    }
  }, [selectedTable])

  const fetchTableData = async (tableName: string) => {
    setLoadingData(true)
    try {
      const res = await fetch(`${API}/api/database/query?table=${tableName}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      if (data.columns && data.data) {
        setTableData(data)
      } else {
        setTableData(null)
      }
    } catch (err) {
      console.error(`Failed to fetch data for ${tableName}:`, err)
      setTableData(null)
    } finally {
      setLoadingData(false)
    }
  }

  // Filter rows based on search
  const filteredData = tableData?.data.filter(row => {
    if (!searchTerm) return true
    // Search across all string/number columns
    return Object.values(row).some(val => 
      String(val).toLowerCase().includes(searchTerm.toLowerCase())
    )
  }) || []

  return (
    <div className="section" style={{ maxWidth: 1400, padding: '32px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 32 }}>
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <Database size={28} className="text-primary" /> Data Hub
          </h2>
          <p style={{ color: 'var(--text-muted)' }}>Raw MySQL Database Explorer. Proving the hybrid system architecture.</p>
        </div>
        <button className="btn btn-secondary" onClick={() => selectedTable && fetchTableData(selectedTable)} disabled={loadingData} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <RefreshCcw size={16} className={loadingData ? "spin" : ""} /> Refresh Data
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: 24, alignItems: 'start' }}>
        
        {/* Left Sidebar: Tables List */}
        <div className="glass" style={{ padding: 16, borderRadius: 'var(--radius-md)' }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 16 }}>
            Tables ({tables.length})
          </div>
          
          {loadingTables ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 20 }}>
              <Loader2 size={24} className="spin text-primary" />
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {tables.map(t => (
                <button
                  key={t}
                  onClick={() => setSelectedTable(t)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px',
                    width: '100%', textAlign: 'left', borderRadius: 'var(--radius-sm)',
                    background: selectedTable === t ? 'rgba(99,102,241,0.1)' : 'transparent',
                    border: '1px solid',
                    borderColor: selectedTable === t ? 'rgba(99,102,241,0.3)' : 'transparent',
                    color: selectedTable === t ? 'var(--color-primary-light)' : 'var(--text-secondary)',
                    fontWeight: selectedTable === t ? 600 : 400,
                    cursor: 'pointer', transition: 'all 0.2s'
                  }}
                >
                  <Table2 size={16} /> {t}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right Content: Data Grid */}
        <div className="glass" style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 600 }}>
          
          {/* Toolbar */}
          <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
              {selectedTable ? `SELECT * FROM ${selectedTable} LIMIT 100` : 'Select a table'}
            </div>
            
            <div style={{ position: 'relative', width: 250 }}>
              <Search size={14} style={{ position: 'absolute', left: 12, top: 9, color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                placeholder="Search rows..." 
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                style={{
                  width: '100%', padding: '6px 12px 6px 32px',
                  background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)',
                  fontSize: 13, outline: 'none'
                }}
              />
            </div>
          </div>

          {/* Table Container */}
          <div style={{ flex: 1, overflowX: 'auto', overflowY: 'auto', padding: 24 }}>
            {loadingData ? (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                 <Loader2 size={32} className="spin text-primary" />
              </div>
            ) : !tableData ? (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                 No data available or error loading table.
              </div>
            ) : filteredData.length === 0 ? (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                 Table is empty or no results match your search.
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--border)' }}>
                    {tableData.columns.map(col => (
                      <th key={col} style={{ padding: '12px 16px', color: 'var(--color-primary-light)', fontWeight: 600, whiteSpace: 'nowrap' }}>
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((row, idx) => (
                    <motion.tr 
                      key={idx} 
                      initial={{ opacity: 0 }} 
                      animate={{ opacity: 1 }}
                      transition={{ delay: Math.min(idx * 0.02, 0.5) }}
                      style={{ borderBottom: '1px solid var(--border)', background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)' }}
                    >
                      {tableData.columns.map(col => {
                        let val = row[col]
                        // Truncate extremely long JSON strings to keep table clean
                        if (typeof val === 'string' && val.length > 50) {
                          val = val.substring(0, 47) + '...'
                        }
                        if (val === null) val = <span style={{ color: 'var(--text-muted)' }}>NULL</span>
                        return (
                          <td key={col} style={{ padding: '12px 16px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                            {val}
                          </td>
                        )
                      })}
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          
          <div style={{ padding: '12px 24px', borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--text-muted)', textAlign: 'right' }}>
            Showing {filteredData.length} rows {searchTerm ? '(filtered)' : ''}
          </div>
        </div>

      </div>
    </div>
  )
}
