import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Home, Clock, BookOpen, MessageSquare, ShieldCheck, 
  Swords, Brain, Activity, Wifi, WifiOff 
} from 'lucide-react'
import { io, Socket } from 'socket.io-client'
import './index.css'

// ── Tab Definitions ──
const TABS = [
  { id: 'home',      label: 'Home',        icon: Home },
  { id: 'timeline',  label: 'Timeline',    icon: Clock },
  { id: 'guide',     label: 'Voter Guide', icon: BookOpen },
  { id: 'assistant', label: 'AI Assistant', icon: MessageSquare },
  { id: 'factcheck', label: 'Fact Check',  icon: ShieldCheck },
  { id: 'battle',    label: 'Prompt Wars', icon: Swords },
  { id: 'quiz',      label: 'Voter IQ',    icon: Brain },
  { id: 'liveops',   label: 'Live Ops',    icon: Activity },
] as const

type TabId = typeof TABS[number]['id']

interface Stats {
  total_votes: number
  total_registered: number
  turnout_percent: number
  active_booths: number
  total_booths: number
  avg_queue_length: number
  open_incidents: number
  critical_incidents: number
  total_incidents: number
  clock: {
    time_string: string
    phase: string
    progress_percent: number
    is_polling_active: boolean
    day_complete: boolean
  }
}

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('home')
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [stats, setStats] = useState<Stats | null>(null)

  // ── Socket Connection ──
  useEffect(() => {
    const s = io('http://localhost:5000', {
      transports: ['websocket', 'polling'],
    })

    s.on('connect', () => setConnected(true))
    s.on('disconnect', () => setConnected(false))
    s.on('stats_update', (data: Stats) => setStats(data))

    setSocket(s)
    return () => { s.disconnect() }
  }, [])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── Navbar ── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(8, 12, 24, 0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border)',
        padding: '12px 24px',
      }}>
        <div style={{
          maxWidth: 1200, margin: '0 auto',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 16, flexWrap: 'wrap',
        }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 24 }}>🗳️</span>
            <span style={{
              fontFamily: 'var(--font-heading)', fontWeight: 800,
              fontSize: 20, color: 'var(--text-primary)',
              background: 'linear-gradient(135deg, #f1f5f9, #6366f1)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>ElectaVerse</span>
          </div>

          {/* Live Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {stats?.clock && (
              <div className="badge badge-info" style={{ gap: 6 }}>
                <span>⏱</span>
                <span>{stats.clock.time_string}</span>
                <span style={{ opacity: 0.6 }}>|</span>
                <span>{stats.clock.phase.replace('_', ' ')}</span>
              </div>
            )}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '4px 10px', borderRadius: 99,
              background: connected ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
              color: connected ? 'var(--color-success)' : 'var(--color-danger)',
              fontSize: 12, fontWeight: 600,
            }}>
              {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
              {connected ? 'LIVE' : 'OFFLINE'}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ maxWidth: 1200, margin: '10px auto 0' }}>
          <div className="nav-tabs">
            {TABS.map(tab => (
              <button
                key={tab.id}
                className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <tab.icon size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main style={{ flex: 1 }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            {activeTab === 'home' && <HomePage stats={stats} />}
            {activeTab === 'timeline' && <PlaceholderPage title="Election Timeline" desc="Interactive election phase timeline — coming in Module 5" />}
            {activeTab === 'guide' && <PlaceholderPage title="Voter Guide" desc="Step-by-step voting guide — coming in Module 5" />}
            {activeTab === 'assistant' && <PlaceholderPage title="AI Assistant" desc="Multi-agent AI chat — coming in Module 6" />}
            {activeTab === 'factcheck' && <PlaceholderPage title="Fact Checker" desc="AI-powered claim verification — coming in Module 6" />}
            {activeTab === 'battle' && <PlaceholderPage title="Prompt Wars Arena" desc="AI vs AI policy debates — coming in Module 7" />}
            {activeTab === 'quiz' && <PlaceholderPage title="Voter IQ Quiz" desc="Test your election knowledge — coming in Module 7" />}
            {activeTab === 'liveops' && <PlaceholderPage title="Live Operations" desc="Real-time booth monitoring — coming in Module 8" />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* ── Footer ── */}
      <footer style={{
        textAlign: 'center', padding: '24px',
        borderTop: '1px solid var(--border)',
        color: 'var(--text-muted)', fontSize: 13,
      }}>
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--text-secondary)' }}>
          ElectaVerse
        </span>
        {' '} — AI-Powered Election Intelligence · Built for Google Prompt Wars · © 2026 Animesh Gupta
      </footer>
    </div>
  )
}


// ── Home Page ──
function HomePage({ stats }: { stats: Stats | null }) {
  return (
    <div className="section" style={{ textAlign: 'center', paddingTop: 60 }}>
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
      >
        <p style={{ 
          color: 'var(--color-accent)', fontWeight: 600, fontSize: 14, 
          letterSpacing: 2, textTransform: 'uppercase', marginBottom: 16 
        }}>
          AI-Powered Election Intelligence
        </p>
        <h1 style={{
          marginBottom: 20,
          background: 'linear-gradient(135deg, #f1f5f9 0%, #6366f1 50%, #f59e0b 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          backgroundSize: '200% auto',
        }}>
          Democracy, Decoded.
        </h1>
        <p style={{ fontSize: 18, color: 'var(--text-secondary)', maxWidth: 640, margin: '0 auto 40px' }}>
          Monitor elections in real-time. Fact-check claims instantly. Explore policy debates. 
          Understand your vote — all powered by agentic AI and live simulation.
        </p>
      </motion.div>

      {/* Live Stats Bar */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="glass"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: 1, padding: 1, borderRadius: 'var(--radius-lg)',
            maxWidth: 900, margin: '0 auto 48px',
          }}
        >
          <StatCard label="Total Votes" value={stats.total_votes.toLocaleString()} color="var(--color-primary-light)" />
          <StatCard label="Turnout" value={`${stats.turnout_percent}%`} color="var(--color-success)" />
          <StatCard label="Active Booths" value={stats.active_booths.toString()} color="var(--color-info)" />
          <StatCard label="Avg Queue" value={`${stats.avg_queue_length} voters`} color="var(--color-accent)" />
          <StatCard label="Open Incidents" value={stats.open_incidents.toString()} color={stats.critical_incidents > 0 ? 'var(--color-danger)' : 'var(--color-warning)'} />
          <StatCard label="Sim Time" value={stats.clock.time_string} color="var(--text-secondary)" />
        </motion.div>
      )}

      {/* Feature Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: 16, maxWidth: 900, margin: '0 auto',
      }}>
        {[
          { icon: '⏱', title: 'Election Timeline', desc: 'Interactive phases from announcement to results', color: '#6366f1' },
          { icon: '📋', title: 'Voter Guide', desc: 'Step-by-step process with document checklists', color: '#10b981' },
          { icon: '🤖', title: 'AI Assistant', desc: '5 specialized agents answer any election question', color: '#3b82f6' },
          { icon: '🔍', title: 'Fact Checker', desc: 'Verify claims with AI-powered verdict & confidence', color: '#f59e0b' },
          { icon: '⚔️', title: 'Prompt Wars', desc: 'AI vs AI policy debates with live scoring', color: '#ef4444' },
          { icon: '📊', title: 'Live Ops', desc: 'Real-time booth monitoring with incident tracking', color: '#8b5cf6' },
        ].map((feature, i) => (
          <motion.div
            key={feature.title}
            className="glass"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.08, duration: 0.4 }}
            style={{
              padding: 24, textAlign: 'left', cursor: 'pointer',
              transition: 'all 0.25s',
            }}
            whileHover={{ y: -4, borderColor: feature.color + '40' }}
          >
            <span style={{ fontSize: 28, display: 'block', marginBottom: 12 }}>{feature.icon}</span>
            <h3 style={{ fontSize: 16, marginBottom: 8, color: feature.color }}>{feature.title}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>{feature.desc}</p>
          </motion.div>
        ))}
      </div>
    </div>
  )
}


// ── Stat Card ──
function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{
      padding: '16px 20px',
      background: 'var(--bg-secondary)',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 22, fontWeight: 700, color, fontFamily: 'var(--font-heading)' }}>
        {value}
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {label}
      </div>
    </div>
  )
}


// ── Placeholder Page ──
function PlaceholderPage({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="section" style={{ textAlign: 'center', paddingTop: 80 }}>
      <div className="glass" style={{ 
        padding: 48, maxWidth: 500, margin: '0 auto', 
        borderRadius: 'var(--radius-lg)' 
      }}>
        <h2 style={{ marginBottom: 12 }}>{title}</h2>
        <p style={{ color: 'var(--text-muted)' }}>{desc}</p>
        <div style={{ 
          marginTop: 24, padding: '8px 16px', 
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)',
          display: 'inline-block', fontSize: 13, color: 'var(--color-accent)',
        }}>
          🚧 Under Construction
        </div>
      </div>
    </div>
  )
}

export default App
