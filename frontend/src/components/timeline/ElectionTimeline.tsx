import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp, MessageSquare, Send, Loader2, Shield, Eye, Users, Activity } from 'lucide-react'

const API = import.meta.env.PROD ? '' : 'http://localhost:5000'

interface Phase {
  id: number
  phase_key: string
  title: string
  description: string
  icon: string
  start_label: string
  end_label: string
  duration_info: string
  key_activities: string[]
  my_actions: string[]
  all_role_actions?: Record<string, string[]>
  display_order: number
}

interface Props {
  token: string | null
  userRole: string
  currentPhase?: string
  stats?: any
}

export default function ElectionTimeline({ token, userRole, currentPhase, stats }: Props) {
  const [phases, setPhases] = useState<Phase[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [askingAI, setAskingAI] = useState<number | null>(null)
  const [aiQuestion, setAiQuestion] = useState('')
  const [aiAnswer, setAiAnswer] = useState<string | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/content/timeline`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setPhases(data.phases || []))
      .catch(err => console.error('Failed to load timeline:', err))
      .finally(() => setLoading(false))
  }, [token])

  const handleAskAI = async (phaseId: number) => {
    if (!aiQuestion.trim()) return
    setAiLoading(true)
    setAiAnswer(null)
    try {
      const res = await fetch(`${API}/api/content/timeline/${phaseId}/ask-ai`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: aiQuestion }),
      })
      const data = await res.json()
      setAiAnswer(data.answer || data.error || 'No answer received.')
    } catch {
      setAiAnswer('Failed to connect to AI service.')
    } finally {
      setAiLoading(false)
    }
  }

  const getRoleIcon = () => {
    if (userRole === 'official') return <Shield size={14} />
    if (userRole === 'observer') return <Eye size={14} />
    return <Users size={14} />
  }

  const getRoleLabel = () => {
    if (userRole === 'official') return 'Official Duties'
    if (userRole === 'observer') return 'Observer Checkpoints'
    return 'Your Actions'
  }

  if (loading) {
    return (
      <div className="section" style={{ textAlign: 'center', paddingTop: 80 }}>
        <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-primary)' }} />
        <p style={{ color: 'var(--text-muted)', marginTop: 12 }}>Loading Election Timeline...</p>
      </div>
    )
  }

  return (
    <div className="section" style={{ maxWidth: 900 }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <h2 style={{ marginBottom: 8 }}>Election Timeline</h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: 600, margin: '0 auto' }}>
          The complete Indian election cycle — from announcement to results. 
          All data sourced from ECI guidelines. Click any phase to explore.
        </p>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 12, padding: '4px 12px', borderRadius: 99, background: 'rgba(99,102,241,0.1)', color: 'var(--color-primary-light)', fontSize: 12, fontWeight: 600 }}>
          {getRoleIcon()} Viewing as: {userRole.toUpperCase()}
        </div>
      </div>

      {/* Live Simulation Progress */}
      {stats && stats.clock && (
        <div style={{ marginBottom: 40 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
            <span>Election Day Progress</span>
            <span>{stats.clock.progress_percent}%</span>
          </div>
          <div style={{ width: '100%', height: 6, background: 'var(--bg-secondary)', borderRadius: 3, overflow: 'hidden' }}>
            <motion.div 
              initial={{ width: 0 }} 
              animate={{ width: `${stats.clock.progress_percent}%` }}
              transition={{ duration: 1 }}
              style={{ height: '100%', background: 'linear-gradient(90deg, var(--color-primary), var(--color-success))' }}
            />
          </div>
          {stats.open_incidents > 0 && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
              style={{ marginTop: 12, fontSize: 12, padding: '8px 12px', background: 'rgba(239,68,68,0.1)', color: 'var(--color-danger)', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Activity size={14} style={{ animation: 'pulse 2s infinite' }} />
              Live Ticker: {stats.open_incidents} active incidents currently being triaged by AI system.
            </motion.div>
          )}
        </div>
      )}

      {/* Vertical Timeline */}
      <div style={{ position: 'relative', paddingLeft: 40 }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: 15, top: 0, bottom: 0, width: 2,
          background: 'linear-gradient(180deg, var(--color-primary) 0%, var(--color-accent) 100%)',
          opacity: 0.3,
        }} />

        {phases.map((phase, i) => {
          const isActive = currentPhase === phase.phase_key
          const isExpanded = expandedId === phase.id
          const isAskOpen = askingAI === phase.id

          return (
            <motion.div key={phase.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
              style={{ marginBottom: 24, position: 'relative' }}
            >
              {/* Timeline dot */}
              <div style={{
                position: 'absolute', left: -33, top: 20, width: 16, height: 16,
                borderRadius: '50%', zIndex: 2,
                background: isActive ? 'var(--color-success)' : 'var(--color-primary)',
                boxShadow: isActive ? '0 0 12px rgba(16,185,129,0.5)' : '0 0 8px rgba(99,102,241,0.3)',
                border: '2px solid var(--bg-primary)',
              }} />
              {isActive && (
                <div style={{
                  position: 'absolute', left: -37, top: 16, width: 24, height: 24,
                  borderRadius: '50%', border: '2px solid var(--color-success)',
                  animation: 'pulse 2s ease-in-out infinite', opacity: 0.4,
                }} />
              )}

              {/* Phase Card */}
              <div className="glass" style={{
                borderRadius: 'var(--radius-lg)', overflow: 'hidden',
                border: isActive ? '1px solid rgba(16,185,129,0.3)' : undefined,
                transition: 'all 0.3s',
              }}>
                {/* Header — always visible */}
                <button onClick={() => { setExpandedId(isExpanded ? null : phase.id); setAskingAI(null); setAiAnswer(null) }}
                  style={{
                    width: '100%', padding: '20px 24px', border: 'none', cursor: 'pointer',
                    background: 'none', textAlign: 'left', display: 'flex', alignItems: 'center', gap: 16,
                  }}>
                  <span style={{ fontSize: 32, flexShrink: 0 }}>{phase.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <h3 style={{ fontSize: 17, color: 'var(--text-primary)', margin: 0 }}>{phase.title}</h3>
                      {isActive && (
                        <span className="badge badge-success" style={{ fontSize: 10 }}>● LIVE NOW</span>
                      )}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                      <span>{phase.start_label} → {phase.end_label}</span>
                      <span style={{ opacity: 0.5 }}>|</span>
                      <span>{phase.duration_info}</span>
                    </div>
                  </div>
                  {isExpanded ? <ChevronUp size={20} style={{ color: 'var(--text-muted)' }} /> : <ChevronDown size={20} style={{ color: 'var(--text-muted)' }} />}
                </button>

                {/* Expanded Content */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      style={{ overflow: 'hidden' }}
                    >
                      <div style={{ padding: '0 24px 24px', borderTop: '1px solid var(--border)' }}>
                        {/* Real-Time Live Data (If Active) */}
                        {isActive && stats && (
                          <div style={{
                            margin: '16px 0', padding: 16, borderRadius: 'var(--radius-sm)',
                            background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)',
                            display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
                              <Activity size={16} style={{ color: 'var(--color-success)' }} />
                              <h4 style={{ margin: 0, fontSize: 13, color: 'var(--color-success)', textTransform: 'uppercase', letterSpacing: 1 }}>Live Phase Data</h4>
                            </div>
                            <div style={{ display: 'flex', gap: 24, width: '100%' }}>
                               <div style={{ display: 'flex', flexDirection: 'column' }}>
                                 <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Turnout</span>
                                 <span style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>{stats.turnout_percent}%</span>
                               </div>
                               <div style={{ display: 'flex', flexDirection: 'column' }}>
                                 <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Avg Queue</span>
                                 <span style={{ fontSize: 18, fontWeight: 600, color: 'var(--color-accent)' }}>{stats.avg_queue_length} <span style={{fontSize: 12, fontWeight: 400}}>voters</span></span>
                               </div>
                               <div style={{ display: 'flex', flexDirection: 'column' }}>
                                 <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Open Incidents</span>
                                 <span style={{ fontSize: 18, fontWeight: 600, color: stats.open_incidents > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>{stats.open_incidents}</span>
                               </div>
                               <div style={{ display: 'flex', flexDirection: 'column' }}>
                                 <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Active Booths</span>
                                 <span style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>{stats.active_booths} / {stats.total_booths}</span>
                               </div>
                            </div>
                          </div>
                        )}

                        {/* Description */}
                        <p style={{ margin: '16px 0', lineHeight: 1.7, color: 'var(--text-secondary)', fontSize: 14 }}>
                          {phase.description}
                        </p>

                        {/* Key Activities */}
                        <div style={{ marginBottom: 20 }}>
                          <h4 style={{ fontSize: 13, color: 'var(--color-accent)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                            Key Activities
                          </h4>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8 }}>
                            {phase.key_activities.map((activity, j) => (
                              <div key={j} style={{
                                padding: '8px 12px', background: 'var(--bg-secondary)',
                                borderRadius: 'var(--radius-sm)', fontSize: 13, color: 'var(--text-secondary)',
                                display: 'flex', alignItems: 'flex-start', gap: 8,
                              }}>
                                <span style={{ color: 'var(--color-primary)', flexShrink: 0, marginTop: 1 }}>▸</span>
                                {activity}
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* RBAC: My Actions */}
                        <div style={{
                          padding: 16, borderRadius: 'var(--radius-sm)',
                          background: userRole === 'official' ? 'rgba(99,102,241,0.06)' : userRole === 'observer' ? 'rgba(245,158,11,0.06)' : 'rgba(16,185,129,0.06)',
                          border: '1px solid',
                          borderColor: userRole === 'official' ? 'rgba(99,102,241,0.15)' : userRole === 'observer' ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)',
                          marginBottom: 16,
                        }}>
                          <h4 style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10,
                            color: userRole === 'official' ? 'var(--color-primary-light)' : userRole === 'observer' ? 'var(--color-accent)' : 'var(--color-success)',
                            textTransform: 'uppercase', letterSpacing: 1,
                          }}>
                            {getRoleIcon()} {getRoleLabel()}
                          </h4>
                          {phase.my_actions.map((action, j) => (
                            <div key={j} style={{ padding: '6px 0', fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 8 }}>
                              <span style={{ flexShrink: 0 }}>✓</span> {action}
                            </div>
                          ))}
                        </div>

                        {/* Ask AI */}
                        <div>
                          <button onClick={() => { setAskingAI(isAskOpen ? null : phase.id); setAiAnswer(null); setAiQuestion('') }}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px',
                              background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
                              borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                              color: 'var(--color-primary-light)', fontSize: 13, fontWeight: 500,
                            }}>
                            <MessageSquare size={14} /> Ask AI about this phase
                          </button>

                          <AnimatePresence>
                            {isAskOpen && (
                              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
                                style={{ marginTop: 12 }}>
                                <div style={{ display: 'flex', gap: 8 }}>
                                  <input
                                    type="text"
                                    placeholder={`Ask about ${phase.title}...`}
                                    value={aiQuestion}
                                    onChange={e => setAiQuestion(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleAskAI(phase.id)}
                                    style={{
                                      flex: 1, padding: '10px 14px', background: 'var(--bg-secondary)',
                                      border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                                      color: 'var(--text-primary)', fontSize: 14, fontFamily: 'var(--font-body)',
                                      outline: 'none',
                                    }}
                                  />
                                  <button onClick={() => handleAskAI(phase.id)} disabled={aiLoading || !aiQuestion.trim()}
                                    className="btn btn-primary" style={{ padding: '10px 14px' }}>
                                    {aiLoading ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={16} />}
                                  </button>
                                </div>

                                {aiAnswer && (
                                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                    style={{
                                      marginTop: 12, padding: 16, background: 'var(--bg-secondary)',
                                      borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--color-primary)',
                                    }}>
                                    <div style={{ fontSize: 10, color: 'var(--color-primary-light)', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase' }}>
                                      🤖 AI Response (as {userRole})
                                    </div>
                                    <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                                      {aiAnswer}
                                    </div>
                                  </motion.div>
                                )}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
