import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Send, Loader2, Bot, User, Shield, Eye, Users, Activity, Plus, Clock } from 'lucide-react'

import { API } from '../../config'

interface ChatMessage {
  id: number
  role: 'user' | 'ai'
  text: string
  agent?: string
  agentLabel?: string
  liveContext?: { sim_time: string; turnout: string; open_incidents: number; avg_queue: number }
  timestamp: Date
}

interface ChatHistoryItem {
  message: string
  agent: string
  response: string
  timestamp: string
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
]

interface Props {
  token: string | null
  userRole: string
  stats: any
}

export default function AIAssistant({ token, userRole, stats }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [history, setHistory] = useState<ChatHistoryItem[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sentiment, setSentiment] = useState<{score: number, magnitude: number} | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  let msgId = useRef(0)

  // Fetch History
  useEffect(() => {
    fetch(`${API}/api/chat/history`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => {
        if (data.history) {
          setHistory(data.history)

          // Populate main chat view (history comes DESC, so reverse it)
          const loadedMessages: ChatMessage[] = []
            ;[...data.history].reverse().forEach((item: any) => {
              loadedMessages.push({
                id: ++msgId.current,
                role: 'user',
                text: item.message,
                timestamp: new Date(item.timestamp)
              })
              loadedMessages.push({
                id: ++msgId.current,
                role: 'ai',
                text: item.response,
                agent: item.agent,
                timestamp: new Date(item.timestamp)
              })
            })
          setMessages(loadedMessages)
        }
      })
      .catch(err => console.error('Failed to load history:', err))
  }, [token])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    // Auto-resize
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 150)}px`
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

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
    if (inputRef.current) inputRef.current.style.height = 'auto'
    setLoading(true)

    try {
      // 1. Analyze Sentiment in the background
      fetch(`${API}/api/ai/sentiment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ text: msg }),
      }).then(r => r.json()).then(d => {
        if(d.sentiment) setSentiment(d.sentiment)
      }).catch(e => console.error("NLP error:", e))

      // 2. Get AI Response
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: msg }),
      })
      const data = await res.json()

      if (!res.ok) throw new Error(data.error || 'Failed to get response')

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

      // Optimistically add to history
      setHistory(prev => [{
        message: msg,
        agent: data.agent,
        response: data.response,
        timestamp: new Date().toISOString()
      }, ...prev])

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
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const startNewChat = () => {
    setMessages([])
    setInput('')
    if (inputRef.current) inputRef.current.style.height = 'auto'
    inputRef.current?.focus()
  }

  const getRoleIcon = () => {
    if (userRole === 'official') return <Shield size={14} />
    if (userRole === 'observer') return <Eye size={14} />
    return <Users size={14} />
  }

  return (
    <div style={{
      display: 'flex',
      height: 'calc(100vh - 140px)', // adjust based on navbar height
      minHeight: 600,
      background: 'var(--bg-primary)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border)',
      overflow: 'hidden'
    }}>
      {/* ── SIDEBAR (History) ── */}
      <div style={{
        width: 280,
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <div style={{ padding: 16 }}>
          <button onClick={startNewChat} style={{
            width: '100%', display: 'flex', alignItems: 'center', gap: 8,
            padding: '10px 14px', background: 'transparent',
            border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)', cursor: 'pointer', transition: 'all 0.2s',
          }} onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
            onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
            <Plus size={16} /> New Chat
          </button>
        </div>

        <div style={{ padding: '0 16px 8px', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Recent Conversations
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0 12px 16px' }}>
          {history.length === 0 ? (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              No chat history yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {history.map((item, i) => (
                <div key={i} style={{
                  padding: '10px 12px', borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer', transition: 'all 0.2s',
                }}
                  onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                  onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: 4 }}>
                    {item.message}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: AGENT_COLORS[item.agent] || 'var(--text-muted)' }}>
                      {AGENT_ICONS[item.agent] || '🤖'} {AGENT_NAMES[item.agent] || 'Assistant'}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      {new Date(item.timestamp).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: 16, borderTop: '1px solid var(--border)', background: 'rgba(8,12,24,0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--color-primary-light)' }}>
            {getRoleIcon()} <span style={{ fontWeight: 600 }}>{userRole.toUpperCase()} VIEW</span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            AI responses are tailored to your role.
          </div>
        </div>
      </div>

      {/* ── MAIN CHAT AREA ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)', position: 'relative' }}>

        {/* Header / Live Stats */}
        {stats && (
          <div style={{
            padding: '12px 24px', borderBottom: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(10px)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              {sentiment && (
                <div style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6, background: 'var(--bg-secondary)', padding: '4px 10px', borderRadius: 20 }}>
                  <span title={`Score: ${sentiment.score}, Mag: ${sentiment.magnitude}`}>
                    {sentiment.score > 0.25 ? '😊 Positive' : sentiment.score < -0.25 ? '😠 Negative' : '😐 Neutral'}
                  </span>
                </div>
              )}
              <div style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)' }}>
                <Shield size={14} /> System Context: 
                <span style={{ color: 'var(--color-primary-light)' }}>
                  Phase: {stats?.clock?.phase || 'PRE_POLLING'} | Turnout: {stats?.turnout_percent || 0}%
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-muted)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <Activity size={12} style={{ color: 'var(--color-success)' }} /> {stats.clock?.time_string}
              </span>
              <span>Turnout: <strong style={{ color: 'var(--text-primary)' }}>{stats.turnout_percent}%</strong></span>
              <span>Queues: <strong style={{ color: 'var(--color-accent)' }}>{stats.avg_queue_length}</strong></span>
              <span>Incidents: <strong style={{ color: stats.open_incidents > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>{stats.open_incidents}</strong></span>
            </div>
          </div>
        )}

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px 0' }} aria-live="polite">
          <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 32, padding: '0 24px' }}>

            {messages.length === 0 ? (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 400, gap: 24 }}>
                <div style={{
                  width: 64, height: 64, borderRadius: 16,
                  background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(16,185,129,0.2))',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(255,255,255,0.1)'
                }}>
                  <Bot size={32} style={{ color: 'var(--color-primary)' }} />
                </div>
                <h2 style={{ margin: 0, fontSize: 24 }}>How can I assist you today?</h2>
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', maxWidth: 500, margin: 0, lineHeight: 1.6 }}>
                  I have real-time access to the election simulation. I can check queue times,
                  verify claims, explain procedures, or triage incidents based on your role.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, width: '100%', maxWidth: 600, marginTop: 16 }}>
                  {SUGGESTION_CHIPS.map((chip, i) => (
                    <div key={i} onClick={() => sendMessage(chip.text)} style={{
                      padding: '16px', background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                      borderRadius: 'var(--radius-md)', cursor: 'pointer', transition: 'all 0.2s',
                      display: 'flex', alignItems: 'flex-start', gap: 12,
                    }}
                      onMouseOver={e => e.currentTarget.style.borderColor = 'var(--color-primary-light)'}
                      onMouseOut={e => e.currentTarget.style.borderColor = 'var(--border)'}
                    >
                      <span style={{ fontSize: 18 }}>{chip.icon}</span>
                      <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{chip.text}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : (
              <>
                {messages.map(msg => (
                  <motion.div key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{
                      display: 'flex', gap: 20,
                      flexDirection: 'row', // ChatGPT style always left aligned, but we can differentiate by icon
                    }}
                  >
                    {/* Avatar */}
                    <div style={{
                      width: 36, height: 36, borderRadius: '8px', flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
                      background: msg.role === 'user'
                        ? 'var(--bg-secondary)'
                        : msg.agent ? (AGENT_COLORS[msg.agent] || 'var(--bg-secondary)') + '20' : 'rgba(99,102,241,0.2)',
                      border: msg.role === 'user' ? '1px solid var(--border)' : `1px solid ${AGENT_COLORS[msg.agent || ''] || 'var(--color-primary)'}40`,
                    }}>
                      {msg.role === 'user' ? <User size={20} style={{ color: 'var(--text-secondary)' }} /> : (AGENT_ICONS[msg.agent || ''] || '🤖')}
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1, minWidth: 0, paddingTop: 6 }}>
                      {/* Name Plate */}
                      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                        {msg.role === 'user' ? 'You' : (AGENT_NAMES[msg.agent || ''] || 'Assistant')}

                        {msg.role === 'ai' && msg.liveContext && (
                          <span style={{
                            fontSize: 10, fontWeight: 500, color: 'var(--color-success)', padding: '2px 6px',
                            background: 'rgba(16,185,129,0.1)', borderRadius: 4, display: 'inline-flex', alignItems: 'center', gap: 4
                          }}>
                            <Clock size={10} /> Data from {msg.liveContext.sim_time}
                          </span>
                        )}
                      </div>

                      {/* Message Body */}
                      <div style={{
                        fontSize: 15, lineHeight: 1.7, color: 'var(--text-secondary)',
                        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                      }}>
                        {msg.text}
                      </div>
                    </div>
                  </motion.div>
                ))}

                {/* Typing Indicator */}
                {loading && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', gap: 20 }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: '8px', background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Loader2 size={18} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-primary)' }} />
                    </div>
                    <div style={{ flex: 1, paddingTop: 8, fontSize: 15, color: 'var(--text-muted)' }}>
                      Analyzing live data and generating response...
                    </div>
                  </motion.div>
                )}
              </>
            )}
            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div style={{ padding: '0 24px 24px' }}>
          <div style={{
            maxWidth: 800, margin: '0 auto',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: '12px 16px',
            display: 'flex', alignItems: 'flex-end', gap: 12,
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
          }}>
            <textarea
              ref={inputRef}
              placeholder="Message ElectaVerse..."
              value={input}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              disabled={loading}
              rows={1}
              style={{
                flex: 1, background: 'transparent', border: 'none',
                color: 'var(--text-primary)', fontSize: 15, lineHeight: 1.5,
                fontFamily: 'var(--font-body)', outline: 'none', resize: 'none',
                maxHeight: 150, padding: '4px 0',
                opacity: loading ? 0.5 : 1,
              }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              style={{
                background: loading || !input.trim() ? 'var(--border)' : 'var(--color-primary)',
                color: loading || !input.trim() ? 'var(--text-muted)' : 'white',
                border: 'none', borderRadius: 'var(--radius-sm)',
                width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s', flexShrink: 0
              }}
            >
              <Send size={16} />
            </button>
          </div>
          <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-muted)', marginTop: 12 }}>
            AI Assistant uses real-time simulation data and routes queries to specialized agents.
          </div>
        </div>

      </div>
    </div>
  )
}
