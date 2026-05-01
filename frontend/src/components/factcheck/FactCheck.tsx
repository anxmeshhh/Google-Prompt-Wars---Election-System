import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Loader2, ShieldAlert, CheckCircle2, AlertTriangle, XCircle, ExternalLink, RefreshCw } from 'lucide-react'

const API = 'http://localhost:5000'

interface VerdictResult {
  claim: string
  verdict: 'TRUE' | 'FALSE' | 'MISLEADING' | 'ERROR'
  confidence_score: number
  reasoning: string
  official_sources: string[]
}

export default function FactCheck({ token }: { token: string | null }) {
  const [claim, setClaim] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<VerdictResult | null>(null)

  const handleVerify = async () => {
    if (!claim.trim()) return
    setLoading(true)
    setResult(null)

    try {
      const res = await fetch(`${API}/api/content/fact-check`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ claim }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Verification failed')
      setResult(data)
    } catch (err: any) {
      setResult({
        claim,
        verdict: 'ERROR',
        confidence_score: 0,
        reasoning: err.message || 'Failed to connect to fact-checking service.',
        official_sources: []
      })
    } finally {
      setLoading(false)
    }
  }

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'TRUE': return 'var(--color-success)'
      case 'FALSE': return 'var(--color-danger)'
      case 'MISLEADING': return 'var(--color-warning)'
      default: return 'var(--text-muted)'
    }
  }

  const getVerdictIcon = (verdict: string) => {
    switch (verdict) {
      case 'TRUE': return <CheckCircle2 size={32} style={{ color: 'var(--color-success)' }} />
      case 'FALSE': return <XCircle size={32} style={{ color: 'var(--color-danger)' }} />
      case 'MISLEADING': return <AlertTriangle size={32} style={{ color: 'var(--color-warning)' }} />
      default: return <ShieldAlert size={32} style={{ color: 'var(--text-muted)' }} />
    }
  }

  return (
    <div className="section" style={{ maxWidth: 800, padding: '40px 24px' }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <h2 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <ShieldAlert size={28} style={{ color: 'var(--color-primary)' }} /> AI Fact Checker
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 15, maxWidth: 600, margin: '0 auto', lineHeight: 1.6 }}>
          Combat election-day misinformation. Paste any suspicious WhatsApp forward, social media post, or rumor below. 
          Our AI will cross-reference it with official ECI rules and live simulation data.
        </p>
      </div>

      {/* Input Area */}
      <div className="glass" style={{
        padding: 24, borderRadius: 'var(--radius-lg)', marginBottom: 32,
        border: '1px solid var(--border)', boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
      }}>
        <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--color-primary-light)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
          Claim to Verify
        </label>
        <textarea
          value={claim}
          onChange={e => setClaim(e.target.value)}
          placeholder="e.g. 'Voting is extended to tomorrow' or 'EVMs can be hacked via Bluetooth'..."
          style={{
            width: '100%', height: 120, padding: 16, background: 'var(--bg-secondary)',
            border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
            color: 'var(--text-primary)', fontSize: 16, fontFamily: 'var(--font-body)',
            resize: 'none', outline: 'none', marginBottom: 16,
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            className="btn btn-primary"
            onClick={handleVerify}
            disabled={loading || !claim.trim()}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 24px', fontSize: 15 }}
          >
            {loading ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Search size={18} />}
            {loading ? 'Analyzing Claim...' : 'Verify Claim'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      <AnimatePresence>
        {loading && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            style={{ textAlign: 'center', color: 'var(--text-muted)', marginBottom: 32 }}>
            <RefreshCw size={24} style={{ animation: 'spin 2s linear infinite', color: 'var(--color-primary)', marginBottom: 16 }} />
            <div style={{ fontSize: 14 }}>Cross-referencing ECI guidelines and live simulation data...</div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Area */}
      <AnimatePresence>
        {result && !loading && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            style={{
              padding: 32, borderRadius: 'var(--radius-lg)', background: 'var(--bg-secondary)',
              border: `2px solid ${getVerdictColor(result.verdict)}`,
              boxShadow: `0 8px 32px ${getVerdictColor(result.verdict)}15`,
            }}>
            
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                {getVerdictIcon(result.verdict)}
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600, marginBottom: 4 }}>
                    AI Verdict
                  </div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: getVerdictColor(result.verdict), letterSpacing: 1 }}>
                    {result.verdict}
                  </div>
                </div>
              </div>
              
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600, marginBottom: 4 }}>
                  Confidence
                </div>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {result.confidence_score}%
                </div>
              </div>
            </div>

            <div style={{ padding: 20, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)', marginBottom: 24 }}>
              <div style={{ fontSize: 12, color: 'var(--color-primary-light)', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600, marginBottom: 8 }}>
                Detailed Reasoning
              </div>
              <div style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                {result.reasoning}
              </div>
            </div>

            {result.official_sources && result.official_sources.length > 0 && (
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600, marginBottom: 12 }}>
                  Official Sources to Verify
                </div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  {result.official_sources.map((source, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', gap: 6, padding: '8px 12px',
                      background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)',
                      borderRadius: 99, fontSize: 12, color: 'var(--text-secondary)'
                    }}>
                      <ExternalLink size={12} style={{ color: 'var(--color-primary)' }} />
                      {source}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
