import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Swords } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

import { API } from '../../config'

const PERSONAS = [
  "The Technocrat", "The Traditionalist", "The Economist", 
  "The Activist", "The Constitutionalist", "The Pragmatist"
]

export default function PromptBattle() {
  const [topic, setTopic] = useState('')
  const [personaA, setPersonaA] = useState(PERSONAS[0])
  const [personaB, setPersonaB] = useState(PERSONAS[1])
  const [loading, setLoading] = useState(false)
  const [battleData, setBattleData] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFight = async () => {
    if (!topic.trim()) return
    setLoading(true)
    setBattleData(null)
    setError(null)

    try {
      const res = await fetch(`${API}/api/battle/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, persona_a: personaA, persona_b: personaB })
      })
      if (!res.ok) throw new Error('Battle generation failed')
      if (!res.body) throw new Error('ReadableStream not supported')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let done = false
      let fullText = ""

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = decoder.decode(value, { stream: true })
          fullText += chunk
          setBattleData(fullText)
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate debate.')
    } finally {
      setLoading(false)
    }
  }


  return (
    <div className="section" style={{ maxWidth: 1000, padding: '40px 24px' }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <h2 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <Swords size={28} style={{ color: 'var(--color-accent)' }} /> Prompt Wars Arena
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 15, maxWidth: 600, margin: '0 auto', lineHeight: 1.6 }}>
          Enter any controversial policy or electoral topic. Watch two specialized AI personas debate it live, 
          scored strictly on logic, evidence, and persuasive power.
        </p>
      </div>

      {/* Setup Form */}
      <div className="glass" style={{
        padding: 24, borderRadius: 'var(--radius-lg)', marginBottom: 40,
        border: '1px solid var(--border)', boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
      }}>
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
            Debate Topic
          </label>
          <input
            type="text"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            placeholder="e.g. 'One Nation One Election', 'Electoral Bonds', 'Compulsory Voting'..."
            style={{
              width: '100%', padding: '14px 16px', background: 'var(--bg-secondary)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)', fontSize: 16, outline: 'none'
            }}
          />
        </div>
        
        <div style={{ display: 'flex', gap: 16, marginBottom: 24, alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--color-primary)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
              Persona A (Red Corner)
            </label>
            <select value={personaA} onChange={e => setPersonaA(e.target.value)} style={{
              width: '100%', padding: '12px', background: 'var(--bg-secondary)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', outline: 'none'
            }}>
              {PERSONAS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          
          <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-muted)', padding: '0 16px', marginTop: 24 }}>VS</div>
          
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--color-accent)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
              Persona B (Blue Corner)
            </label>
            <select value={personaB} onChange={e => setPersonaB(e.target.value)} style={{
              width: '100%', padding: '12px', background: 'var(--bg-secondary)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', outline: 'none'
            }}>
              {PERSONAS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button className="btn btn-primary" onClick={handleFight} disabled={loading || !topic.trim()}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '14px 40px', fontSize: 16, fontWeight: 700, letterSpacing: 2, background: 'linear-gradient(45deg, var(--color-primary), var(--color-accent))', border: 'none' }}>
            {loading ? <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} /> : <Swords size={20} />}
            {loading ? 'SIMULATING DEBATE...' : 'FIGHT!'}
          </button>
        </div>
      </div>

      {error && <div style={{ color: 'var(--color-danger)', textAlign: 'center', marginBottom: 20 }}>{error}</div>}

      {/* Battle Arena */}
      <AnimatePresence>
        {battleData && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            style={{
              padding: 32, borderRadius: 'var(--radius-lg)', background: 'var(--bg-secondary)',
              border: `1px solid var(--border)`,
              boxShadow: `0 8px 32px rgba(0,0,0,0.1)`,
            }}>
            
            <div className="markdown-content" style={{ fontSize: 16, lineHeight: 1.7, color: 'var(--text-primary)' }}>
              <ReactMarkdown>{battleData}</ReactMarkdown>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  )
}
