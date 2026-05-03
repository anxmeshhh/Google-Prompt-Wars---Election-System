import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Loader2, ShieldAlert, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

import { API } from '../../config'

export default function FactCheck({ token }: { token: string | null }) {
  const [claim, setClaim] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [translating, setTranslating] = useState(false)

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
      if (!res.ok) throw new Error('Verification failed')
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
          setResult(fullText)
        }
      }
    } catch (err: any) {
      setResult(`## Verdict: ERROR\n**Confidence Score:** 0%\n\n### Reasoning\n${err.message || 'Failed to connect to fact-checking service.'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleTranslate = async () => {
    if (!result) return
    setTranslating(true)
    try {
      const res = await fetch(`${API}/api/ai/translate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: result, target: 'hi' }),
      })
      if (!res.ok) throw new Error('Translation failed')
      const data = await res.json()
      setResult(data.translated)
    } catch (err) {
      console.error(err)
    } finally {
      setTranslating(false)
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
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            style={{
              padding: 32, borderRadius: 'var(--radius-lg)', background: 'var(--bg-secondary)',
              border: `1px solid var(--border)`,
              boxShadow: `0 8px 32px rgba(0,0,0,0.1)`,
              position: 'relative'
            }}>
            
            <div style={{ position: 'absolute', top: 16, right: 16 }}>
              <button 
                onClick={handleTranslate} 
                disabled={translating || loading}
                className="btn" 
                style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '6px 12px', fontSize: 13 }}
              >
                {translating ? 'Translating...' : 'Aि Translate to Hindi'}
              </button>
            </div>

            <div className="markdown-content" style={{ fontSize: 16, lineHeight: 1.7, color: 'var(--text-primary)' }}>
              <ReactMarkdown>{result}</ReactMarkdown>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
