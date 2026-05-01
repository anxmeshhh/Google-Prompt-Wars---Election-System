import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp, MessageSquare, Send, Loader2, FileText, Lightbulb, Shield, Eye, Users, CheckCircle2, Activity } from 'lucide-react'

const API = 'http://localhost:5000'

interface Step {
  id: number
  step_number: number
  title: string
  description: string
  icon: string
  documents_required: string[]
  tips: string[]
  my_note: string
  all_role_notes?: Record<string, string>
  sim_phase_link: string | null
  display_order: number
}

interface Props {
  token: string | null
  userRole: string
  currentPhase?: string
  stats?: any
}

export default function VoterGuide({ token, userRole, currentPhase, stats }: Props) {
  const [steps, setSteps] = useState<Step[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [askingAI, setAskingAI] = useState<number | null>(null)
  const [aiQuestion, setAiQuestion] = useState('')
  const [aiAnswer, setAiAnswer] = useState<string | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/content/voter-guide`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setSteps(data.steps || []))
      .catch(err => console.error('Failed to load voter guide:', err))
      .finally(() => setLoading(false))
  }, [token])

  const handleAskAI = async (stepId: number) => {
    if (!aiQuestion.trim()) return
    setAiLoading(true)
    setAiAnswer(null)
    try {
      const res = await fetch(`${API}/api/content/voter-guide/${stepId}/ask-ai`, {
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

  const getRoleColor = () => {
    if (userRole === 'official') return 'var(--color-primary-light)'
    if (userRole === 'observer') return 'var(--color-accent)'
    return 'var(--color-success)'
  }

  const getRoleBg = () => {
    if (userRole === 'official') return 'rgba(99,102,241,0.06)'
    if (userRole === 'observer') return 'rgba(245,158,11,0.06)'
    return 'rgba(16,185,129,0.06)'
  }

  const getRoleLabel = () => {
    if (userRole === 'official') return '👔 Booth Officer Note'
    if (userRole === 'observer') return '👁️ Observer Note'
    return '🗳️ Voter Tip'
  }

  if (loading) {
    return (
      <div className="section" style={{ textAlign: 'center', paddingTop: 80 }}>
        <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-primary)' }} />
        <p style={{ color: 'var(--text-muted)', marginTop: 12 }}>Loading Voter Guide...</p>
      </div>
    )
  }

  return (
    <div className="section" style={{ maxWidth: 900 }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <h2 style={{ marginBottom: 8 }}>
          {userRole === 'official' ? 'Booth Officer Guide' : userRole === 'observer' ? 'Observer Compliance Guide' : 'Step-by-Step Voter Guide'}
        </h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: 600, margin: '0 auto' }}>
          {userRole === 'official'
            ? 'Complete booth management protocol aligned with ECI procedures.'
            : userRole === 'observer'
            ? 'Monitoring and compliance checklist for election observers.'
            : 'Everything you need to know to cast your vote confidently.'
          }
        </p>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 12, padding: '4px 12px', borderRadius: 99, background: getRoleBg(), color: getRoleColor(), fontSize: 12, fontWeight: 600, border: '1px solid', borderColor: getRoleColor() + '30' }}>
          {userRole === 'official' ? <Shield size={14} /> : userRole === 'observer' ? <Eye size={14} /> : <Users size={14} />}
          {userRole.toUpperCase()} VIEW
        </div>
      </div>

      {/* Steps */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {steps.map((step, i) => {
          const isActive = currentPhase && step.sim_phase_link === currentPhase
          const isExpanded = expandedId === step.id
          const isAskOpen = askingAI === step.id

          return (
            <motion.div key={step.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
            >
              <div className="glass" style={{
                borderRadius: 'var(--radius-lg)', overflow: 'hidden',
                border: isActive ? '1px solid rgba(16,185,129,0.3)' : undefined,
                boxShadow: isActive ? '0 0 20px rgba(16,185,129,0.08)' : undefined,
              }}>
                {/* Header */}
                <button onClick={() => { setExpandedId(isExpanded ? null : step.id); setAskingAI(null); setAiAnswer(null) }}
                  style={{
                    width: '100%', padding: '20px 24px', border: 'none', cursor: 'pointer',
                    background: 'none', textAlign: 'left', display: 'flex', alignItems: 'center', gap: 16,
                  }}>
                  {/* Step Number Circle */}
                  <div style={{
                    width: 48, height: 48, borderRadius: '50%', flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 20, fontWeight: 800, fontFamily: 'var(--font-heading)',
                    background: isActive
                      ? 'linear-gradient(135deg, var(--color-success), #059669)'
                      : 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
                    color: 'white',
                    boxShadow: isActive ? '0 4px 12px rgba(16,185,129,0.3)' : '0 4px 12px rgba(99,102,241,0.2)',
                  }}>
                    {step.step_number}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                      <span style={{ fontSize: 20 }}>{step.icon}</span>
                      <h3 style={{ fontSize: 17, color: 'var(--text-primary)', margin: 0 }}>{step.title}</h3>
                      {isActive && <span className="badge badge-success" style={{ fontSize: 10 }}>● ACTIVE NOW</span>}
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0, lineHeight: 1.4,
                      display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const, overflow: 'hidden',
                    }}>
                      {step.description}
                    </p>
                  </div>
                  {isExpanded ? <ChevronUp size={20} style={{ color: 'var(--text-muted)' }} /> : <ChevronDown size={20} style={{ color: 'var(--text-muted)' }} />}
                </button>

                {/* Expanded Content */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}
                      style={{ overflow: 'hidden' }}>
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

                        {/* Full Description */}
                        <p style={{ margin: '16px 0', fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                          {step.description}
                        </p>

                        {/* Documents Required */}
                        {step.documents_required.length > 0 && (
                          <div style={{ marginBottom: 20 }}>
                            <h4 style={{ fontSize: 13, color: 'var(--color-info)', display: 'flex', alignItems: 'center', gap: 6, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                              <FileText size={14} /> Documents Required
                            </h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 8 }}>
                              {step.documents_required.map((doc, j) => (
                                <div key={j} style={{
                                  padding: '8px 12px', background: 'var(--bg-secondary)',
                                  borderRadius: 'var(--radius-sm)', fontSize: 13, color: 'var(--text-secondary)',
                                  display: 'flex', alignItems: 'center', gap: 8,
                                }}>
                                  <CheckCircle2 size={14} style={{ color: 'var(--color-info)', flexShrink: 0 }} />
                                  {doc}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Tips */}
                        {step.tips.length > 0 && (
                          <div style={{ marginBottom: 20 }}>
                            <h4 style={{ fontSize: 13, color: 'var(--color-accent)', display: 'flex', alignItems: 'center', gap: 6, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                              <Lightbulb size={14} /> Tips
                            </h4>
                            {step.tips.map((tip, j) => (
                              <div key={j} style={{
                                padding: '8px 0', fontSize: 13, color: 'var(--text-secondary)',
                                display: 'flex', gap: 8, borderBottom: j < step.tips.length - 1 ? '1px solid rgba(255,255,255,0.03)' : 'none',
                              }}>
                                <span style={{ color: 'var(--color-accent)', flexShrink: 0 }}>💡</span> {tip}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* RBAC: Role-Specific Note */}
                        <div style={{
                          padding: 16, borderRadius: 'var(--radius-sm)',
                          background: getRoleBg(),
                          border: `1px solid ${getRoleColor()}25`,
                          marginBottom: 16,
                        }}>
                          <div style={{ fontSize: 12, fontWeight: 600, color: getRoleColor(), marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                            {getRoleLabel()}
                          </div>
                          <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                            {step.my_note}
                          </p>
                        </div>

                        {/* Ask AI */}
                        <div>
                          <button onClick={() => { setAskingAI(isAskOpen ? null : step.id); setAiAnswer(null); setAiQuestion('') }}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px',
                              background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
                              borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                              color: 'var(--color-primary-light)', fontSize: 13, fontWeight: 500,
                            }}>
                            <MessageSquare size={14} /> Ask AI about this step
                          </button>

                          <AnimatePresence>
                            {isAskOpen && (
                              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
                                style={{ marginTop: 12 }}>
                                <div style={{ display: 'flex', gap: 8 }}>
                                  <input
                                    type="text"
                                    placeholder={`Ask about: ${step.title}...`}
                                    value={aiQuestion}
                                    onChange={e => setAiQuestion(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleAskAI(step.id)}
                                    style={{
                                      flex: 1, padding: '10px 14px', background: 'var(--bg-secondary)',
                                      border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                                      color: 'var(--text-primary)', fontSize: 14, fontFamily: 'var(--font-body)',
                                      outline: 'none',
                                    }}
                                  />
                                  <button onClick={() => handleAskAI(step.id)} disabled={aiLoading || !aiQuestion.trim()}
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
