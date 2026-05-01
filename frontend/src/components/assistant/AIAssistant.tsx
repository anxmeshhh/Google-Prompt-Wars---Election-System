import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, Bot, User, Zap, Shield, Eye, Users, ChevronRight, Activity } from 'lucide-react'

const API = 'http://localhost:5000'

interface ChatMessage {
  id: number
  role: 'user' | 'ai'
  text: string
  agent?: string
  agentLabel?: string
  liveContext?: { sim_time: string; turnout: string; open_incidents: number; avg_queue: number }
  timestamp: Date
}

const AGENT_COLORS: Record<string, string> = {
  election_analyst: '#6366f1',
  fact_checker: '#f59e0b',
  incident_responder: '#ef4444',
  queue_manager: '#10b981',
}

const AGENT_ICONS: Record<string, string> = {
  election_analyst: '🎓',
  fact_checker: '🔍',
  incident_responder: '🚨',
  queue_manager: '📊',
}

const AGENT_NAMES: Record<string, string> = {
  election_analyst: 'Election Analyst',
  fact_checker: 'Fact Checker',
  incident_responder: 'Incident Responder',
  queue_manager: 'Queue Manager',
}

const SUGGESTION_CHIPS = [
  { text: "What's the current turnout?", icon: '📊' },
  { text: "How does EVM voting work?", icon: '🗳️' },
  { text: "Is it true EVMs can be hacked?", icon: '🔍' },
  { text: "When is the best time to vote today?", icon: '⏰' },
  { text: "What are the current active incidents?", icon: '🚨' },
  { text: "Explain VVPAT verification process", icon: '📋' },
  { text: "Which booth has the longest queue?", icon: '📈' },
  { text: "What documents do I need to vote?", icon: '📄' },
]

interface Props {
  token: string | null
  userRole: string
  stats: any
}

export default function AIAssistant({ token, userRole, stats }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  let msgId = useRef(0)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || loading) return

    const userMsg: ChatMessage = {
      id: ++msgId.current,
      role: 'user',
      text: msg,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: msg }),
      })
      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.error || 'Failed to get response')
      }

      const aiMsg: ChatMessage = {
        id: ++msgId.current,
        role: 'ai',
        text: data.response,
        agent: data.agent,
        agentLabel: data.agent_label,
        liveContext: data.live_context_summary,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: ++msgId.current,
        role: 'ai',
        text: `Error: ${err.message || 'Failed to connect to AI service.'}`,
        agent: 'system',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const getRoleIcon = () => {
    if (userRole === 'official') return <Shield size={12} />
    if (userRole === 'observer') return <Eye size={12} />
    return <Users size={12} />
  }

  return (
    <div className="section" style={{ maxWidth: 900, padding: '24px 24px 0' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <h2 style={{ marginBottom: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
          <Bot size={24} style={{ color: 'var(--color-primary)' }} /> AI Election Assistant
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 14, maxWidth: 600, margin: '0 auto' }}>
          Not a chatbot — a <strong style={{ color: 'var(--color-primary-light)' }}>multi-agent system</strong> with 
          real-time election data. Every answer is grounded in live simulation state.
        </p>

        {/* Live Context Badge */}
        {stats && (
          <div style={{
            display: 'inline-flex', gap: 16, marginTop: 12, padding: '6px 16px',
            borderRadius: 99, background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)',
            fontSize: 11, color: 'var(--text-muted)',
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Activity size={10} style={{ color: 'var(--color-success)' }} /> {stats.clock?.time_string}
            </span>
            <span>Turnout: <strong style={{ color: 'var(--color-success)' }}>{stats.turnout_percent}%</strong></span>
            <span>Queue Avg: <strong style={{ color: 'var(--color-accent)' }}>{stats.avg_queue_length}</strong></span>
            <span>Incidents: <strong style={{ color: stats.critical_incidents > 0 ? 'var(--color-danger)' : 'var(--text-muted)' }}>{stats.open_incidents}</strong></span>
          </div>
        )}

        {/* Agent Roster */}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 16, flexWrap: 'wrap' }}>
          {Object.entries(AGENT_NAMES).map(([key, name]) => (
            <div key={key} style={{
              padding: '4px 10px', borderRadius: 99, fontSize: 11, fontWeight: 500,
              background: AGENT_COLORS[key] + '15', color: AGENT_COLORS[key],
              border: `1px solid ${AGENT_COLORS[key]}25`,
            }}>
              {AGENT_ICONS[key]} {name}
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="glass" style={{
        borderRadius: 'var(--radius-lg)', overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
        height: 'calc(100vh - 370px)', minHeight: 400,
      }}>
        {/* Messages */}
        <div style={{
          flex: 1, overflowY: 'auto', padding: 20,
          display: 'flex', flexDirection: 'column', gap: 16,
        }}>
          {messages.length === 0 ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 20 }}>
              <div style={{ fontSize: 48, opacity: 0.3 }}>🤖</div>
              <p style={{ color: 'var(--text-muted)', fontSize: 14, textAlign: 'center', maxWidth: 400 }}>
                Ask me anything about the election. I have access to <strong>real-time simulation data</strong> and 
                will automatically route your question to the best specialist agent.
              </p>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                borderRadius: 99, background: 'rgba(99,102,241,0.1)', color: 'var(--color-primary-light)', fontSize: 11,
              }}>
                {getRoleIcon()} Answering as: {userRole.toUpperCase()}
              </div>

              {/* Suggestion Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', maxWidth: 520 }}>
                {SUGGESTION_CHIPS.map((chip, i) => (
                  <motion.button key={i}
                    initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => sendMessage(chip.text)}
                    style={{
                      padding: '6px 12px', background: 'var(--bg-secondary)',
                      border: '1px solid var(--border)', borderRadius: 99, cursor: 'pointer',
                      color: 'var(--text-secondary)', fontSize: 12,
                      display: 'flex', alignItems: 'center', gap: 4,
                      transition: 'all 0.2s',
                    }}
                    whileHover={{ borderColor: 'var(--color-primary)', color: 'var(--color-primary-light)' }}
                  >
                    <span>{chip.icon}</span> {chip.text}
                  </motion.button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map(msg => (
                <motion.div key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                  style={{
                    display: 'flex', gap: 12,
                    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  }}
                >
                  {/* Avatar */}
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14,
                    background: msg.role === 'user'
                      ? 'linear-gradient(135deg, var(--color-primary), var(--color-accent))'
                      : msg.agent ? (AGENT_COLORS[msg.agent] || 'var(--bg-secondary)') + '20' : 'var(--bg-secondary)',
                    color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                    border: msg.role === 'ai' && msg.agent ? `1px solid ${AGENT_COLORS[msg.agent] || 'var(--border)'}40` : 'none',
                  }}>
                    {msg.role === 'user' ? <User size={14} /> : (AGENT_ICONS[msg.agent || ''] || '🤖')}
                  </div>

                  {/* Bubble */}
                  <div style={{
                    maxWidth: '75%', padding: '12px 16px',
                    borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                    background: msg.role === 'user' ? 'rgba(99,102,241,0.15)' : 'var(--bg-secondary)',
                    border: `1px solid ${msg.role === 'user' ? 'rgba(99,102,241,0.2)' : 'var(--border)'}`,
                  }}>
                    {/* Agent Badge */}
                    {msg.role === 'ai' && msg.agent && msg.agent !== 'system' && (
                      <div style={{
                        fontSize: 10, fontWeight: 600, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4,
                        color: AGENT_COLORS[msg.agent] || 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5,
                      }}>
                        <Zap size={10} /> {AGENT_NAMES[msg.agent] || msg.agent}
                      </div>
                    )}

                    {/* Live Context Tag */}
                    {msg.role === 'ai' && msg.liveContext && (
                      <div style={{
                        fontSize: 10, color: 'var(--text-muted)', marginBottom: 8, padding: '3px 8px',
                        background: 'rgba(16,185,129,0.05)', borderRadius: 4, display: 'inline-flex', gap: 8,
                      }}>
                        <span>⏱ {msg.liveContext.sim_time}</span>
                        <span>📊 {msg.liveContext.turnout}</span>
                        <span>🚨 {msg.liveContext.open_incidents} incidents</span>
                      </div>
                    )}

                    <div style={{
                      fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)',
                      whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                    }}>
                      {msg.text}
                    </div>

                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6, textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </motion.div>
              ))}

              {/* Typing indicator */}
              {loading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%', background: 'var(--bg-secondary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    🤖
                  </div>
                  <div style={{
                    padding: '12px 16px', background: 'var(--bg-secondary)',
                    borderRadius: '16px 16px 16px 4px', border: '1px solid var(--border)',
                    display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-muted)',
                  }}>
                    <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                    Routing to specialist agent...
                  </div>
                </motion.div>
              )}
            </>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div style={{
          padding: '12px 20px', borderTop: '1px solid var(--border)',
          background: 'rgba(8,12,24,0.5)',
        }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask about elections, verify claims, check queues..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              disabled={loading}
              style={{
                flex: 1, padding: '12px 16px',
                background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)',
                fontSize: 14, fontFamily: 'var(--font-body)', outline: 'none',
                opacity: loading ? 0.5 : 1,
              }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="btn btn-primary"
              style={{ padding: '12px 16px', opacity: loading || !input.trim() ? 0.5 : 1 }}
            >
              {loading ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={18} />}
            </button>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
              Powered by Google Gemini · Multi-Agent Routing · Live Data Injection
            </span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
              {getRoleIcon()} {userRole}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
