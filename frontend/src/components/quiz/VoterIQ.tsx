import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, CheckCircle2, XCircle, Trophy, Clock, Loader2, ArrowRight, PlayCircle } from 'lucide-react'

const API = 'http://localhost:5000'

interface Question {
  id: number
  question: string
  options: string[]
  correct_index: number
  explanation: string
}

export default function VoterIQ() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)
  
  // Game State
  const [hasStarted, setHasStarted] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [score, setScore] = useState(0)
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [timeLeft, setTimeLeft] = useState(15)
  const [isFinished, setIsFinished] = useState(false)
  
  useEffect(() => {
    fetch(`${API}/api/quiz/questions`)
      .then(r => r.json())
      .then(data => setQuestions(data.questions || []))
      .catch(err => console.error('Failed to load quiz:', err))
      .finally(() => setLoading(false))
  }, [])

  // Timer Logic
  useEffect(() => {
    if (hasStarted && !isFinished && selectedOption === null && timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(t => t - 1), 1000)
      return () => clearTimeout(timer)
    } else if (timeLeft === 0 && selectedOption === null) {
      // Time up
      setSelectedOption(-1) // -1 means no selection (wrong)
    }
  }, [hasStarted, isFinished, selectedOption, timeLeft])

  const handleStart = () => {
    setHasStarted(true)
    setCurrentIndex(0)
    setScore(0)
    setSelectedOption(null)
    setTimeLeft(15)
    setIsFinished(false)
  }

  const handleSelect = (index: number) => {
    if (selectedOption !== null) return // Already answered
    setSelectedOption(index)
    if (index === questions[currentIndex].correct_index) {
      setScore(s => s + 1)
    }
  }

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(i => i + 1)
      setSelectedOption(null)
      setTimeLeft(15)
    } else {
      setIsFinished(true)
    }
  }

  const getRank = (score: number) => {
    if (score <= 2) return { title: 'First-Time Voter', color: 'var(--text-muted)' }
    if (score <= 4) return { title: 'Booth Level Officer', color: 'var(--color-primary-light)' }
    return { title: 'Chief Election Commissioner', color: 'var(--color-warning)' }
  }

  if (loading) return (
    <div className="section" style={{ textAlign: 'center', paddingTop: 80 }}>
      <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-primary)' }} />
    </div>
  )

  if (!hasStarted) {
    return (
      <div className="section" style={{ maxWidth: 600, padding: '40px 24px', textAlign: 'center' }}>
        <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px', border: '2px solid var(--color-primary)' }}>
          <Brain size={40} style={{ color: 'var(--color-primary)' }} />
        </div>
        <h2 style={{ marginBottom: 16 }}>Voter IQ Test</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 16, lineHeight: 1.6, marginBottom: 40 }}>
          Test your knowledge of the Indian electoral system. 5 questions. 15 seconds each. 
          Can you achieve the rank of Chief Election Commissioner?
        </p>
        <button className="btn btn-primary" onClick={handleStart} style={{ padding: '14px 40px', fontSize: 18, fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 12 }}>
          <PlayCircle size={24} /> Start Quiz
        </button>
      </div>
    )
  }

  if (isFinished) {
    const rank = getRank(score)
    return (
      <div className="section" style={{ maxWidth: 600, padding: '40px 24px', textAlign: 'center' }}>
        <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} style={{
          padding: 40, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)',
          border: `2px solid ${rank.color}`, boxShadow: `0 0 40px ${rank.color}20`
        }}>
          <Trophy size={64} style={{ color: rank.color, marginBottom: 24 }} />
          <div style={{ fontSize: 14, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Final Score</div>
          <div style={{ fontSize: 48, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 24 }}>{score} / {questions.length}</div>
          
          <div style={{ fontSize: 14, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Your Rank</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: rank.color, marginBottom: 40 }}>{rank.title}</div>

          <button className="btn btn-secondary" onClick={handleStart} style={{ padding: '12px 32px' }}>
            Retake Quiz
          </button>
        </motion.div>
      </div>
    )
  }

  const q = questions[currentIndex]
  const isAnswered = selectedOption !== null

  return (
    <div className="section" style={{ maxWidth: 800, padding: '40px 24px' }}>
      
      {/* Header Info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
          Question {currentIndex + 1} of {questions.length}
        </div>
        <div style={{ 
          display: 'flex', alignItems: 'center', gap: 8, padding: '6px 16px', borderRadius: 99,
          background: timeLeft <= 5 ? 'rgba(239,68,68,0.1)' : 'rgba(99,102,241,0.1)',
          color: timeLeft <= 5 ? 'var(--color-danger)' : 'var(--color-primary-light)',
          fontWeight: 700, fontSize: 18
        }}>
          <Clock size={18} /> 00:{timeLeft.toString().padStart(2, '0')}
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ width: '100%', height: 4, background: 'var(--bg-secondary)', borderRadius: 2, marginBottom: 40, overflow: 'hidden' }}>
        <div style={{ width: `${((currentIndex) / questions.length) * 100}%`, height: '100%', background: 'var(--color-primary)', transition: 'width 0.3s' }} />
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={currentIndex} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
          <h2 style={{ fontSize: 24, lineHeight: 1.4, marginBottom: 32 }}>{q.question}</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {q.options.map((opt, i) => {
              let bg = 'var(--bg-secondary)'
              let border = '1px solid var(--border)'
              let icon = null

              if (isAnswered) {
                if (i === q.correct_index) {
                  bg = 'rgba(16,185,129,0.1)'
                  border = '2px solid var(--color-success)'
                  icon = <CheckCircle2 size={20} style={{ color: 'var(--color-success)' }} />
                } else if (i === selectedOption) {
                  bg = 'rgba(239,68,68,0.1)'
                  border = '2px solid var(--color-danger)'
                  icon = <XCircle size={20} style={{ color: 'var(--color-danger)' }} />
                } else {
                  opacity: 0.5
                }
              }

              return (
                <button
                  key={i}
                  onClick={() => handleSelect(i)}
                  disabled={isAnswered}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    width: '100%', padding: '16px 20px', background: bg, border: border,
                    borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: 16,
                    textAlign: 'left', cursor: isAnswered ? 'default' : 'pointer',
                    transition: 'all 0.2s', opacity: isAnswered && i !== q.correct_index && i !== selectedOption ? 0.5 : 1
                  }}
                >
                  {opt}
                  {icon}
                </button>
              )
            })}
          </div>

          {isAnswered && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              style={{ marginTop: 32, padding: 20, background: 'rgba(255,255,255,0.05)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: 12, color: 'var(--color-primary-light)', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600, marginBottom: 8 }}>Explanation</div>
              <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 20 }}>{q.explanation}</p>
              
              <button className="btn btn-primary" onClick={handleNext} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 24px' }}>
                {currentIndex < questions.length - 1 ? 'Next Question' : 'View Results'} <ArrowRight size={16} />
              </button>
            </motion.div>
          )}

        </motion.div>
      </AnimatePresence>
    </div>
  )
}
