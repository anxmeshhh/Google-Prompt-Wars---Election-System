import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Home, Clock, BookOpen, MessageSquare, ShieldCheck,
  Swords, Brain, Activity, Database, Wifi, WifiOff,
  LogOut, User, Mail, Lock, Eye, EyeOff, ChevronRight
} from 'lucide-react'
import { io, Socket } from 'socket.io-client'
import LiveDashboard from './components/liveops/LiveDashboard'
import ElectionTimeline from './components/timeline/ElectionTimeline'
import VoterGuide from './components/guide/VoterGuide'
import AIAssistant from './components/assistant/AIAssistant'
import FactCheck from './components/factcheck/FactCheck'
import PromptBattle from './components/battle/PromptBattle'
import VoterIQ from './components/quiz/VoterIQ'
import DataHub from './components/datahub/DataHub'
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google'
import { trackEvent } from './firebase'
import './index.css'

// Smart API URL routing:
// - localhost:5173 (dev) → localhost:5000 (Flask dev server)
// - GCE VM (34.41.130.216) → '' (Nginx same-origin proxy)
// - Firebase Hosting (HTTPS) → Cloudflare tunnel (HTTPS, avoids mixed content)
const GCE_TUNNEL = 'https://broader-bits-ozone-pointed.trycloudflare.com'
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  if (!import.meta.env.PROD) return 'http://localhost:5000'
  const host = window.location.hostname
  if (host === 'electaverse.web.app' || host === 'electaverse.firebaseapp.com') return GCE_TUNNEL
  if (host.endsWith('.trycloudflare.com')) return ''  // Already on tunnel
  return ''  // GCE same-origin
}
const API = getApiUrl()

// ── Tab Definitions ──
const TABS = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'timeline', label: 'Timeline', icon: Clock },
  { id: 'guide', label: 'Voter Guide', icon: BookOpen },
  { id: 'assistant', label: 'AI Assistant', icon: MessageSquare },
  { id: 'factcheck', label: 'Fact Check', icon: ShieldCheck },
  { id: 'battle', label: 'Prompt Wars', icon: Swords },
  { id: 'quiz', label: 'Voter IQ', icon: Brain },
  { id: 'liveops', label: 'Live Ops', icon: Activity },
  { id: 'database', label: 'Data Hub', icon: Database },
] as const

type TabId = typeof TABS[number]['id']

interface UserData {
  id: number; name: string; email: string;
  role: string; constituency_id: string | null;
}

interface Stats {
  total_votes: number; total_registered: number; turnout_percent: number;
  active_booths: number; total_booths: number; avg_queue_length: number;
  open_incidents: number; critical_incidents: number; total_incidents: number;
  clock: { time_string: string; phase: string; progress_percent: number; is_polling_active: boolean; day_complete: boolean; }
}

// ═══════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════
function App() {
  const [user, setUser] = useState<UserData | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('electaverse_token'))
  const [authLoading, setAuthLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabId>('home')
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [stats, setStats] = useState<Stats | null>(null)
  const [highContrast, setHighContrast] = useState(false)
  const [textScale, setTextScale] = useState<'normal' | 'large' | 'xlarge'>('normal')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', highContrast ? 'high-contrast' : 'default')
  }, [highContrast])

  useEffect(() => {
    document.documentElement.setAttribute('data-text-scale', textScale)
  }, [textScale])

  // ── Check existing session ──
  useEffect(() => {
    if (token) {
      fetch(`${API}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(data => setUser(data.user))
        .catch(() => { localStorage.removeItem('electaverse_token'); setToken(null) })
        .finally(() => setAuthLoading(false))
    } else {
      setAuthLoading(false)
    }
  }, [token])

  // ── Socket Connection (only when logged in) ──
  useEffect(() => {
    if (!user) return
    const s = io(API || undefined, { transports: ['polling'], upgrade: false })
    s.on('connect', () => setConnected(true))
    s.on('disconnect', () => setConnected(false))
    s.on('stats_update', (data: Stats) => setStats(data))
    setSocket(s)
    return () => { s.disconnect() }
  }, [user])

  const handleLogin = useCallback((userData: UserData, authToken: string) => {
    localStorage.setItem('electaverse_token', authToken)
    setToken(authToken)
    setUser(userData)
    trackEvent('login', { method: 'email', role: userData.role })
  }, [])

  const handleLogout = useCallback(() => {
    if (token) {
      fetch(`${API}/api/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(() => { })
    }
    localStorage.removeItem('electaverse_token')
    setToken(null)
    setUser(null)
    setStats(null)
    socket?.disconnect()
  }, [token, socket])

  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
        <div style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 40 }}>🗳️</span>
          <p style={{ color: 'var(--text-muted)', marginTop: 12 }}>Loading...</p>
        </div>
      </div>
    )
  }

  // ── Not logged in → show auth page ──
  if (!user) {
    return <AuthPage onLogin={handleLogin} />
  }

  // ── Logged in → show main app ──
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Skip Navigation for Accessibility */}
      <a href="#main-content" className="skip-nav">Skip to main content</a>

      {/* Navbar */}
      <nav aria-label="Main navigation" style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(8, 12, 24, 0.85)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border)', padding: '12px 24px',
      }}>
        <div style={{
          maxWidth: 1200, margin: '0 auto',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 24 }}>🗳️</span>
            <span style={{
              fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: 20,
              background: 'linear-gradient(135deg, #f1f5f9, #6366f1)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>ElectaVerse</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
            {/* Accessibility Menu - hidden on small screens */}
            <div className="a11y-controls" style={{ display: 'flex', gap: 4 }}>
              <button onClick={() => setHighContrast(!highContrast)} title="Toggle High Contrast" style={{
                background: 'none', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--text-primary)', padding: '2px 6px', cursor: 'pointer', fontSize: 12
              }}>
                {highContrast ? '🎨 Normal' : '👁️ Contrast'}
              </button>
              <select aria-label="Text Scale" value={textScale} onChange={e => setTextScale(e.target.value as any)} style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 4, fontSize: 12, padding: '2px 4px'
              }}>
                <option value="normal">A</option>
                <option value="large">A+</option>
                <option value="xlarge">A++</option>
              </select>
            </div>
            {stats?.clock && (
              <div className="badge badge-info" style={{ gap: 6 }}>
                <span>⏱</span><span>{stats.clock.time_string}</span>
                <span style={{ opacity: 0.6 }}>|</span>
                <span>{stats.clock.phase.replace('_', ' ')}</span>
              </div>
            )}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 99,
              background: connected ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
              color: connected ? 'var(--color-success)' : 'var(--color-danger)', fontSize: 12, fontWeight: 600,
            }}>
              {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
              {connected ? 'LIVE' : 'OFFLINE'}
            </div>
            {/* User Menu */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '6px 12px', borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 700, color: 'white',
              }}>
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="user-name-text" style={{ fontSize: 13 }}>
                <div style={{ color: 'var(--text-primary)', fontWeight: 500, lineHeight: 1.2 }}>{user.name}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase' }}>{user.role}</div>
              </div>
              <button onClick={handleLogout} style={{
                background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
                padding: 4, display: 'flex',
              }} title="Logout" aria-label="Logout">
                <LogOut size={14} />
              </button>
            </div>
          </div>
        </div>
        <div style={{ maxWidth: 1200, margin: '10px auto 0' }}>
          <div className="nav-tabs" role="tablist" aria-label="Application sections">
            {TABS.map(tab => (
              <button key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-controls={`panel-${tab.id}`}
                id={`tab-${tab.id}`}
                className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => { setActiveTab(tab.id); trackEvent('tab_switch', { tab: tab.id }) }}>
                <tab.icon size={14} aria-hidden="true" style={{ marginRight: 4, verticalAlign: -2 }} />{tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main id="main-content" role="main" aria-label="Main content" style={{ flex: 1 }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            role="tabpanel"
            id={`panel-${activeTab}`}
            aria-labelledby={`tab-${activeTab}`}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}>
            {activeTab === 'home' && <HomePage stats={stats} user={user} />}
            {activeTab === 'timeline' && <ElectionTimeline token={token} userRole={user.role} currentPhase={stats?.clock?.phase} stats={stats} />}
            {activeTab === 'guide' && <VoterGuide token={token} userRole={user.role} currentPhase={stats?.clock?.phase} stats={stats} />}
            {activeTab === 'assistant' && <AIAssistant token={token} userRole={user.role} stats={stats} />}
            {activeTab === 'factcheck' && <FactCheck token={token} />}
            {activeTab === 'battle' && <PromptBattle />}
            {activeTab === 'quiz' && <VoterIQ />}
            {activeTab === 'liveops' && <LiveDashboard token={token} />}
            {activeTab === 'database' && <DataHub />}
          </motion.div>
        </AnimatePresence>
      </main>

      <footer style={{
        textAlign: 'center', padding: '24px', borderTop: '1px solid var(--border)',
        color: 'var(--text-muted)', fontSize: 13,
      }}>
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--text-secondary)' }}>ElectaVerse</span>
        {' '} — AI-Powered Election Intelligence · Built for Google Prompt Wars · © 2026
      </footer>
    </div>
  )
}


// ═══════════════════════════════════════════════════
// AUTH PAGE — Login / Signup
// ═══════════════════════════════════════════════════
function AuthPage({ onLogin }: { onLogin: (user: UserData, token: string) => void }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [role, setRole] = useState('voter')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
    const body = mode === 'login'
      ? { email, password }
      : { name, email, password, role }

    try {
      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Something went wrong')
        return
      }
      onLogin(data.user, data.token)
    } catch {
      setError('Cannot connect to server. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSuccess = async (credentialResponse: any) => {
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credentialResponse.credential, role }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Google login failed')
        return
      }
      onLogin(data.user, data.token)
    } catch {
      setError('Cannot connect to server for Google Login.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || '896456277671-tbi2jc4cdppnu3blcrbsguesuvmfo0fu.apps.googleusercontent.com'}>
      <div style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-primary)', padding: 24,
        backgroundImage: 'radial-gradient(circle at 30% 20%, rgba(99,102,241,0.08) 0%, transparent 50%), radial-gradient(circle at 70% 80%, rgba(245,158,11,0.06) 0%, transparent 50%)',
      }}>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="glass-strong"
        style={{ width: '100%', maxWidth: 440, padding: 'clamp(24px, 6vw, 40px)', borderRadius: 'var(--radius-xl)' }}
      >
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <span style={{ fontSize: 48 }}>🗳️</span>
          <h1 style={{
            fontSize: 28, marginTop: 12,
            background: 'linear-gradient(135deg, #f1f5f9 0%, #6366f1 50%, #f59e0b 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>ElectaVerse</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 4 }}>
            {mode === 'login' ? 'Welcome back, citizen.' : 'Join the intelligence network.'}
          </p>
        </div>

        {/* Toggle */}
        <div style={{
          display: 'flex', gap: 4, padding: 4, marginBottom: 24,
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)',
        }}>
          {(['login', 'signup'] as const).map(m => (
            <button key={m} onClick={() => { setMode(m); setError('') }}
              style={{
                flex: 1, padding: '8px 0', border: 'none', borderRadius: 6, cursor: 'pointer',
                fontSize: 13, fontWeight: 600, fontFamily: 'var(--font-body)', transition: 'all 0.25s',
                background: mode === m ? 'var(--color-primary)' : 'transparent',
                color: mode === m ? 'white' : 'var(--text-muted)',
                boxShadow: mode === m ? '0 2px 8px rgba(99,102,241,0.3)' : 'none',
              }}>
              {m === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Name (signup only) */}
          <AnimatePresence>
            {mode === 'signup' && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}>
                <InputField icon={<User size={16} />} type="text" placeholder="Full Name"
                  value={name} onChange={setName} />
              </motion.div>
            )}
          </AnimatePresence>

          <InputField icon={<Mail size={16} />} type="email" placeholder="Email Address"
            value={email} onChange={setEmail} />

          <div style={{ position: 'relative' }}>
            <InputField icon={<Lock size={16} />} type={showPw ? 'text' : 'password'}
              placeholder="Password" value={password} onChange={setPassword} />
            <button type="button" onClick={() => setShowPw(!showPw)} style={{
              position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
            }}>
              {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          {/* Role (signup only) */}
          <AnimatePresence>
            {mode === 'signup' && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}>
                <div style={{ display: 'flex', gap: 8 }}>
                  {[
                    { val: 'voter', label: '🗳️ Voter', desc: 'View & vote' },
                    { val: 'official', label: '👔 Official', desc: 'Manage booths' },
                    { val: 'observer', label: '👁️ Observer', desc: 'Monitor & report' },
                  ].map(r => (
                    <button key={r.val} type="button" onClick={() => setRole(r.val)}
                      style={{
                        flex: 1, padding: '10px 8px', border: '1px solid',
                        borderColor: role === r.val ? 'var(--color-primary)' : 'var(--border)',
                        borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                        background: role === r.val ? 'rgba(99,102,241,0.1)' : 'var(--bg-surface)',
                        transition: 'all 0.2s',
                      }}>
                      <div style={{ fontSize: 16 }}>{r.label.split(' ')[0]}</div>
                      <div style={{ fontSize: 11, color: role === r.val ? 'var(--color-primary-light)' : 'var(--text-muted)', marginTop: 2 }}>
                        {r.label.split(' ')[1]}
                      </div>
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error */}
          {error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: 'rgba(239,68,68,0.1)', color: 'var(--color-danger)', fontSize: 13 }}>
              {error}
            </motion.div>
          )}

          {/* Submit */}
          <button type="submit" disabled={loading} className="btn btn-primary" style={{
            width: '100%', padding: '12px', justifyContent: 'center', fontSize: 15, fontWeight: 600, marginTop: 8,
            opacity: loading ? 0.7 : 1,
          }}>
            {loading ? 'Please wait...' : (mode === 'login' ? 'Sign In' : 'Create Account')}
            {!loading && <ChevronRight size={16} />}
          </button>

          {/* Google Login */}
          <div style={{ marginTop: 8, display: 'flex', justifyContent: 'center' }}>
            <GoogleLogin 
              onSuccess={handleGoogleSuccess}
              onError={() => setError('Google Sign-In was unsuccessful')}
              theme="filled_black"
              shape="rectangular"
              text={mode === 'login' ? 'signin_with' : 'signup_with'}
            />
          </div>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 12, color: 'var(--text-muted)' }}>
          Powered by Google Gemini · Agentic AI Election Intelligence
        </p>
      </motion.div>
      </div>
    </GoogleOAuthProvider>
  )
}


// ── Input Field ──
function InputField({ icon, type, placeholder, value, onChange, id }: {
  icon: React.ReactNode; type: string; placeholder: string; value: string; onChange: (v: string) => void; id?: string
}) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '10px 14px', borderRadius: 'var(--radius-sm)',
      background: 'var(--bg-surface)', border: '1px solid var(--border)',
      transition: 'border-color 0.2s',
    }}>
      <span style={{ color: 'var(--text-muted)', display: 'flex' }} aria-hidden="true">{icon}</span>
      <input type={type} placeholder={placeholder} value={value}
        id={id} aria-label={placeholder}
        onChange={e => onChange(e.target.value)} required
        style={{
          flex: 1, background: 'none', border: 'none', outline: 'none',
          color: 'var(--text-primary)', fontSize: 14, fontFamily: 'var(--font-body)',
        }} />
    </div>
  )
}


// ═══════════════════════════════════════════════════
// HOME PAGE
// ═══════════════════════════════════════════════════
function HomePage({ stats, user }: { stats: Stats | null; user: UserData }) {
  return (
    <div className="section" style={{ textAlign: 'center', paddingTop: 60 }}>
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
        <p style={{ color: 'var(--color-accent)', fontWeight: 600, fontSize: 14, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>
          Welcome, {user.name}
        </p>
        <h1 style={{
          marginBottom: 20,
          background: 'linear-gradient(135deg, #f1f5f9 0%, #6366f1 50%, #f59e0b 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>Democracy, Decoded.</h1>
        <p style={{ fontSize: 18, color: 'var(--text-secondary)', maxWidth: 640, margin: '0 auto 40px' }}>
          Monitor elections in real-time. Fact-check claims instantly. Explore policy debates.
          Understand your vote — all powered by agentic AI and live simulation.
        </p>
      </motion.div>

      {stats && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }} className="glass"
          style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: 1, padding: 1, borderRadius: 'var(--radius-lg)', maxWidth: 900, margin: '0 auto 48px',
          }}>
          <StatCard label="Total Votes" value={stats.total_votes.toLocaleString()} color="var(--color-primary-light)" />
          <StatCard label="Turnout" value={`${stats.turnout_percent}%`} color="var(--color-success)" />
          <StatCard label="Active Booths" value={stats.active_booths.toString()} color="var(--color-info)" />
          <StatCard label="Avg Queue" value={`${stats.avg_queue_length} voters`} color="var(--color-accent)" />
          <StatCard label="Open Incidents" value={stats.open_incidents.toString()} color={stats.critical_incidents > 0 ? 'var(--color-danger)' : 'var(--color-warning)'} />
          <StatCard label="Sim Time" value={stats.clock.time_string} color="var(--text-secondary)" />
        </motion.div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16, maxWidth: 900, margin: '0 auto' }}>
        {[
          { icon: '⏱', title: 'Election Timeline', desc: 'Interactive phases from announcement to results', color: '#6366f1' },
          { icon: '📋', title: 'Voter Guide', desc: 'Step-by-step process with document checklists', color: '#10b981' },
          { icon: '🤖', title: 'AI Assistant', desc: '5 specialized agents answer any election question', color: '#3b82f6' },
          { icon: '🔍', title: 'Fact Checker', desc: 'Verify claims with AI-powered verdict & confidence', color: '#f59e0b' },
          { icon: '⚔️', title: 'Prompt Wars', desc: 'AI vs AI policy debates with live scoring', color: '#ef4444' },
          { icon: '📊', title: 'Live Ops', desc: 'Real-time booth monitoring with incident tracking', color: '#8b5cf6' },
        ].map((feature, i) => (
          <motion.div key={feature.title} className="glass"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.08, duration: 0.4 }}
            style={{ padding: 24, textAlign: 'left', cursor: 'pointer', transition: 'all 0.25s' }}
            whileHover={{ y: -4, borderColor: feature.color + '40' }}>
            <span style={{ fontSize: 28, display: 'block', marginBottom: 12 }}>{feature.icon}</span>
            <h3 style={{ fontSize: 16, marginBottom: 8, color: feature.color }}>{feature.title}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>{feature.desc}</p>
          </motion.div>
        ))}
      </div>
    </div>
  )
}


function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ padding: '16px 20px', background: 'var(--bg-secondary)', textAlign: 'center' }}>
      <div style={{ fontSize: 22, fontWeight: 700, color, fontFamily: 'var(--font-heading)' }}>{value}</div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</div>
    </div>
  )
}


export default App
