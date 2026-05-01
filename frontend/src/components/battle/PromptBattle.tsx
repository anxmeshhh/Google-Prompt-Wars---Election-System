import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Swords, Loader2, Sparkles, Scale, BookOpen, Brain, Trophy } from 'lucide-react'

const API = 'http://localhost:5000'

const PERSONAS = [
  "The Technocrat", "The Traditionalist", "The Economist", 
  "The Activist", "The Constitutionalist", "The Pragmatist"
]

interface Argument {
  point: string
  logic_score: number
  evidence_score: number
  persuasion_score: number
}

interface BattleData {
  persona_a_name: string
  persona_b_name: string
  arguments_a: Argument[]
  arguments_b: Argument[]
  verdict: string
}

export default function PromptBattle() {
  const [topic, setTopic] = useState('')
  const [personaA, setPersonaA] = useState(PERSONAS[0])
  const [personaB, setPersonaB] = useState(PERSONAS[1])
  const [loading, setLoading] = useState(false)
  const [battleData, setBattleData] = useState<BattleData | null>(null)
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
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      if (data.battle_data && data.battle_data.error) throw new Error(data.battle_data.error)
      if (!data.battle_data || !data.battle_data.arguments_a || !data.battle_data.arguments_b) {
        throw new Error("AI returned malformed debate data. Please try again.")
      }
      setBattleData(data.battle_data)
    } catch (err: any) {
      setError(err.message || 'Failed to generate debate.')
    } finally {
      setLoading(false)
    }
  }

  const ScoreBar = ({ label, score, icon: Icon, color }: { label: string, score: number, icon: any, color: string }) => (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Icon size={10} /> {label}</span>
        <span>{score}</span>
      </div>
      <div style={{ width: '100%', height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, overflow: 'hidden' }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 1, delay: 0.5 }}
          style={{ height: '100%', background: color }}
        />
      </div>
    </div>
  )

  const ArgumentCard = ({ arg, align }: { arg: Argument, align: 'left' | 'right' }) => (
    <motion.div initial={{ opacity: 0, x: align === 'left' ? -20 : 20 }} animate={{ opacity: 1, x: 0 }}
      style={{
        padding: 20, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border)', marginBottom: 16,
        borderLeft: align === 'left' ? '3px solid var(--color-primary)' : undefined,
        borderRight: align === 'right' ? '3px solid var(--color-accent)' : undefined,
      }}>
      <p style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6, marginBottom: 16, fontStyle: 'italic' }}>
        "{arg.point}"
      </p>
      <div>
        <ScoreBar label="Logic" score={arg.logic_score} icon={Brain} color="var(--color-primary-light)" />
        <ScoreBar label="Evidence" score={arg.evidence_score} icon={BookOpen} color="var(--color-success)" />
        <ScoreBar label="Persuasion" score={arg.persuasion_score} icon={Sparkles} color="var(--color-accent)" />
      </div>
    </motion.div>
  )

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
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ position: 'relative' }}>
            
            <div style={{ display: 'flex', gap: 24 }}>
              {/* Persona A Side */}
              <div style={{ flex: 1 }}>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', border: '2px solid var(--color-primary)' }}>
                    <Brain size={28} style={{ color: 'var(--color-primary)' }} />
                  </div>
                  <h3 style={{ color: 'var(--text-primary)', margin: 0 }}>{battleData.persona_a_name}</h3>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {battleData.arguments_a?.map((arg, i) => <ArgumentCard key={i} arg={arg} align="left" />)}
                </div>
              </div>

              {/* Center Divider */}
              <div style={{ width: 1, background: 'linear-gradient(180deg, transparent, var(--border), transparent)' }} />

              {/* Persona B Side */}
              <div style={{ flex: 1 }}>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'rgba(236,72,153,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', border: '2px solid var(--color-accent)' }}>
                    <Scale size={28} style={{ color: 'var(--color-accent)' }} />
                  </div>
                  <h3 style={{ color: 'var(--text-primary)', margin: 0 }}>{battleData.persona_b_name}</h3>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {battleData.arguments_b?.map((arg, i) => <ArgumentCard key={i} arg={arg} align="right" />)}
                </div>
              </div>
            </div>

            {/* Final Verdict */}
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 1 }}
              style={{
                marginTop: 40, padding: 32, background: 'rgba(255,255,255,0.03)',
                borderRadius: 'var(--radius-lg)', border: '1px solid rgba(255,255,255,0.1)',
                textAlign: 'center', position: 'relative', overflow: 'hidden'
              }}>
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: 'linear-gradient(90deg, var(--color-primary), var(--color-accent))' }} />
              <Trophy size={32} style={{ color: 'var(--color-warning)', marginBottom: 16 }} />
              <h3 style={{ fontSize: 14, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>Objective AI Verdict</h3>
              <p style={{ fontSize: 18, color: 'var(--text-primary)', lineHeight: 1.6, maxWidth: 700, margin: '0 auto' }}>
                {battleData.verdict}
              </p>
            </motion.div>

          </motion.div>
        )}
      </AnimatePresence>

    </div>
  )
}
