import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, Users, MapPin, Search } from 'lucide-react'

const API = 'http://localhost:5000'

interface Booth {
  id: string
  name: string
  constituency: string
  queue_length: number
  total_votes_cast: number
  registered_voters: number
  evm_status: string
  vvpat_status: string
  is_active: boolean
}

interface Incident {
  id: string
  booth_id: string
  booth_name: string
  constituency: string
  incident_type: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  status: string
  description: string
  reported_at: string
}

export default function LiveDashboard({ token }: { token: string | null }) {
  const [booths, setBooths] = useState<Booth[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  // ── Fetch Initial Data ──
  useEffect(() => {
    const fetchData = async () => {
      try {
        const headers = { 'Authorization': `Bearer ${token}` }
        const [boothsRes, incidentsRes] = await Promise.all([
          fetch(`${API}/api/booths`, { headers }),
          fetch(`${API}/api/incidents`, { headers })
        ])
        const boothsData = await boothsRes.json()
        const incidentsData = await incidentsRes.json()

        // Sort booths by queue length (highest first)
        const sortedBooths = (boothsData.booths || []).sort((a: Booth, b: Booth) => b.queue_length - a.queue_length)
        setBooths(sortedBooths)
        setIncidents(incidentsData.incidents || [])
      } catch (err) {
        console.error("Failed to load live ops data", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()

    // Setup polling since WebSocket in App.tsx doesn't pass down events to children easily yet.
    // In a real app we'd use a Context provider for the socket.
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [token])

  const filteredBooths = booths.filter(b => 
    b.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    b.constituency.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const activeIncidents = incidents.filter(i => i.status === 'open' || i.status === 'triaging')

  if (loading && booths.length === 0) {
    return (
      <div className="section" style={{ textAlign: 'center', paddingTop: 100 }}>
        <p style={{ color: 'var(--text-muted)' }}>Initializing Live Operations...</p>
      </div>
    )
  }

  return (
    <div className="section" style={{ maxWidth: 1400 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}>
        <div>
          <h2 style={{ marginBottom: 4 }}>Live Operations</h2>
          <p style={{ color: 'var(--text-muted)' }}>Real-time monitoring command center.</p>
        </div>
        <div style={{ position: 'relative', width: 300 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Search booths or constituencies..." 
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              width: '100%', padding: '8px 12px 8px 36px',
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)',
              fontFamily: 'var(--font-body)', outline: 'none'
            }}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 24 }}>
        
        {/* Left Column: Booths Grid */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <h3 style={{ fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <MapPin size={16} className="text-primary" /> Active Polling Stations ({filteredBooths.length})
          </h3>
          
          <div style={{ 
            display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 
          }}>
            {filteredBooths.map((booth) => (
              <BoothCard key={booth.id} booth={booth} />
            ))}
          </div>
        </div>

        {/* Right Column: Incident Feed */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <h3 style={{ fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={16} style={{ color: 'var(--color-danger)' }} /> Active Incidents
            {activeIncidents.length > 0 && (
              <span className="badge badge-danger" style={{ marginLeft: 'auto' }}>{activeIncidents.length}</span>
            )}
          </h3>
          
          <div className="glass" style={{ padding: 16, maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
            {activeIncidents.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 20 }}>No active incidents.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {activeIncidents.map(inc => (
                  <motion.div key={inc.id} layout initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
                    style={{
                      padding: 12, borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-secondary)', borderLeft: `3px solid ${getSeverityColor(inc.severity)}`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: getSeverityColor(inc.severity) }}>
                        {inc.incident_type.replace(/_/g, ' ')}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {new Date(inc.reported_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, marginBottom: 6, lineHeight: 1.4 }}>{inc.description}</p>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', gap: 4, alignItems: 'center' }}>
                      <MapPin size={10} /> {inc.booth_name} ({inc.constituency})
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function BoothCard({ booth }: { booth: Booth }) {
  // Determine pressure level based on queue size
  let pressure = 'low'; let pressureColor = 'var(--color-success)';
  if (booth.queue_length > 50) { pressure = 'high'; pressureColor = 'var(--color-danger)'; }
  else if (booth.queue_length > 20) { pressure = 'medium'; pressureColor = 'var(--color-warning)'; }

  const evmOk = booth.evm_status === 'operational' || booth.evm_status === 'replaced';

  return (
    <div className="glass" style={{ padding: 16, transition: 'all 0.2s', borderTop: `2px solid ${pressureColor}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 15 }}>{booth.name}</div>
        <div className={`badge ${!evmOk ? 'badge-danger' : 'badge-info'}`}>
          {evmOk ? 'Online' : 'EVM Fault'}
        </div>
      </div>
      
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 4 }}>
        <MapPin size={12} /> {booth.constituency}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div style={{ background: 'var(--bg-secondary)', padding: 10, borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2 }}>Queue</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: pressureColor, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Users size={16} /> {booth.queue_length}
          </div>
        </div>
        <div style={{ background: 'var(--bg-secondary)', padding: 10, borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2 }}>Turnout</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
            {Math.round((booth.total_votes_cast / Math.max(booth.registered_voters, 1)) * 100)}%
          </div>
        </div>
      </div>
    </div>
  )
}

function getSeverityColor(severity: string) {
  switch(severity) {
    case 'critical': return 'var(--color-danger)';
    case 'high': return 'var(--color-warning)';
    case 'medium': return 'var(--color-accent)';
    default: return 'var(--color-info)';
  }
}
