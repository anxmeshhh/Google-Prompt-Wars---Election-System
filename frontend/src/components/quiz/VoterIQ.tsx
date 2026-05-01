import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, CheckCircle2, XCircle, Trophy, Loader2, ArrowRight, PlayCircle, Flame, BookOpen } from 'lucide-react'

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
  const [streak, setStreak] = useState(0)
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [timeLeft, setTimeLeft] = useState(15)
  const [isFinished, setIsFinished] = useState(false)
  const [mistakes, setMistakes] = useState<Question[]>([])
  
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
      handleSelect(-1) // Timeout counts as wrong
    }
  }, [hasStarted, isFinished, selectedOption, timeLeft])

  const handleStart = () => {
    setHasStarted(true)
    setCurrentIndex(0)
    setScore(0)
    setStreak(0)
    setMistakes([])
    setSelectedOption(null)
    setTimeLeft(15)
    setIsFinished(false)
    
    // Refetch to get fresh live simulation questions
    setLoading(true)
    fetch(`${API}/api/quiz/questions`)
      .then(r => r.json())
      .then(data => setQuestions(data.questions || []))
      .finally(() => setLoading(false))
  }

  const handleSelect = (index: number) => {
    if (selectedOption !== null) return
    setSelectedOption(index)
    
    const isCorrect = index === questions[currentIndex].correct_index
    if (isCorrect) {
      setScore(s => s + 1)
      setStreak(s => s + 1)
    } else {
      setStreak(0)
      setMistakes(m => [...m, questions[currentIndex]])
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
      <p style={{ marginTop: 16, color: 'var(--text-muted)' }}>Syncing Live Simulation Data...</p>
    </div>
  )

  if (!hasStarted) {
    return (
      <div className="section" style={{ maxWidth: 600, padding: '40px 24px', textAlign: 'center' }}>
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring' }}>
          <div style={{ width: 100, height: 100, borderRadius: '50%', background: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 32px', border: '2px solid var(--color-primary)', boxShadow: '0 0 40px rgba(99,102,241,0.2)' }}>
            <Brain size={48} style={{ color: 'var(--color-primary)' }} />
          </div>
          <h2 style={{ marginBottom: 16, fontSize: 36, fontWeight: 800 }}>Voter IQ Test</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 18, lineHeight: 1.6, marginBottom: 40 }}>
            Test your knowledge of the Indian electoral system and <strong style={{color: 'var(--color-accent)'}}>Live Simulation Data</strong>. 
            5 questions. 15 seconds each. Can you achieve the rank of Chief Election Commissioner?
          </p>
          <button className="btn btn-primary" onClick={handleStart} style={{ padding: '16px 48px', fontSize: 20, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 12, boxShadow: '0 8px 32px rgba(99,102,241,0.4)' }}>
            <PlayCircle size={28} /> Start Quiz
          </button>
        </motion.div>
      </div>
    )
  }

  if (isFinished) {
    const rank = getRank(score)
    return (
      <div className="section" style={{ maxWidth: 800, padding: '40px 24px' }}>
        <motion.div initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ type: 'spring', bounce: 0.5 }} style={{
          padding: 40, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', textAlign: 'center',
          border: `2px solid ${rank.color}`, boxShadow: `0 20px 60px ${rank.color}20`, marginBottom: 32
        }}>
          <Trophy size={80} style={{ color: rank.color, marginBottom: 24, filter: `drop-shadow(0 0 20px ${rank.color}80)` }} />
          <div style={{ fontSize: 14, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Final Score</div>
          <div style={{ fontSize: 64, fontWeight: 900, color: 'var(--text-primary)', marginBottom: 24 }}>{score} / {questions.length}</div>
          
          <div style={{ fontSize: 14, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Your Rank</div>
          <div style={{ fontSize: 32, fontWeight: 800, color: rank.color, marginBottom: 40 }}>{rank.title}</div>

          <button className="btn btn-secondary" onClick={handleStart} style={{ padding: '14px 40px', fontSize: 16, fontWeight: 600 }}>
            Retake Quiz
          </button>
        </motion.div>

        {/* Educational Summary / Key Takeaways */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="glass" style={{ padding: 32, borderRadius: 'var(--radius-lg)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, color: 'var(--text-primary)' }}>
            <BookOpen size={24} style={{ color: 'var(--color-primary-light)' }} /> Key Takeaways
          </h3>
          {mistakes.length === 0 ? (
            <div style={{ padding: 20, background: 'rgba(16,185,129,0.1)', borderRadius: 8, color: 'var(--color-success)', borderLeft: '4px solid var(--color-success)' }}>
              <strong>Flawless victory!</strong> You have perfect knowledge of the electoral system and the live simulation dashboard.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <p style={{ color: 'var(--text-muted)', marginBottom: 8 }}>Here is what you missed. Review these concepts to improve your Voter IQ:</p>
              {mistakes.map((m, i) => (
                <div key={i} style={{ padding: 20, background: 'rgba(239,68,68,0.05)', borderRadius: 8, borderLeft: '4px solid var(--color-danger)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>{m.question}</div>
                  <div style={{ color: 'var(--color-success)', fontSize: 14, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <CheckCircle2 size={16} /> Correct Answer: {m.options[m.correct_index]}
                  </div>
                  <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    <strong>Explanation:</strong> {m.explanation}
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    )
  }

  const q = questions[currentIndex]
  const isAnswered = selectedOption !== null
  const isUrgent = timeLeft <= 5 && !isAnswered

  // Calculate SVG circle progress
  const radius = 20
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (timeLeft / 15) * circumference

  return (
    <div style={{ 
      minHeight: '80vh', 
      padding: '40px 24px', 
      display: 'flex', 
      justifyContent: 'center',
      background: isUrgent ? 'radial-gradient(circle at 50% 30%, rgba(239,68,68,0.15) 0%, transparent 70%)' : 'transparent',
      transition: 'background 0.5s ease'
    }}>
      <div style={{ maxWidth: 800, width: '100%' }}>
        
        {/* Header Info */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
              Question {currentIndex + 1} of {questions.length}
            </div>
            {streak >= 2 && (
              <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="badge badge-warning" style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '4px 10px' }}>
                <Flame size={14} /> {streak}x STREAK
              </motion.div>
            )}
          </div>

          {/* Circular SVG Timer */}
          <div style={{ position: 'relative', width: 48, height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="48" height="48" style={{ position: 'absolute', transform: 'rotate(-90deg)' }}>
              <circle cx="24" cy="24" r={radius} stroke="var(--bg-secondary)" strokeWidth="4" fill="none" />
              <motion.circle 
                cx="24" cy="24" r={radius} 
                stroke={isUrgent ? "var(--color-danger)" : "var(--color-primary-light)"} 
                strokeWidth="4" fill="none" 
                strokeDasharray={circumference}
                animate={{ strokeDashoffset }}
                transition={{ duration: 1, ease: 'linear' }}
              />
            </svg>
            <span style={{ fontSize: 14, fontWeight: 800, color: isUrgent ? 'var(--color-danger)' : 'var(--text-primary)' }}>
              {timeLeft}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ width: '100%', height: 4, background: 'var(--bg-secondary)', borderRadius: 2, marginBottom: 40, overflow: 'hidden' }}>
          <div style={{ width: `${((currentIndex) / questions.length) * 100}%`, height: '100%', background: 'var(--color-primary)', transition: 'width 0.3s' }} />
        </div>

        <AnimatePresence mode="wait">
          <motion.div 
            key={currentIndex} 
            initial={{ opacity: 0, x: 30 }} 
            animate={{ opacity: 1, x: isUrgent ? [-5, 5, -5, 5, 0] : 0 }} 
            transition={{ x: { duration: 0.4, repeat: isUrgent ? Infinity : 0, repeatType: 'reverse' } }}
            exit={{ opacity: 0, x: -30 }}
          >
            {/* Dynamic Label for Live Questions */}
            {q.id > 100 && (
              <div style={{ display: 'inline-block', padding: '4px 12px', background: 'rgba(236,72,153,0.1)', color: 'var(--color-accent)', borderRadius: 4, fontSize: 12, fontWeight: 700, marginBottom: 16, letterSpacing: 1 }}>
                LIVE OPS DATA SCENARIO
              </div>
            )}
            
            <h2 style={{ fontSize: 28, lineHeight: 1.4, marginBottom: 40, fontWeight: 800 }}>{q.question}</h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {q.options.map((opt, i) => {
                let bg = 'rgba(255,255,255,0.03)'
                let border = '1px solid rgba(255,255,255,0.1)'
                let icon = null

                if (isAnswered) {
                  if (i === q.correct_index) {
                    bg = 'rgba(16,185,129,0.15)'
                    border = '2px solid var(--color-success)'
                    icon = <CheckCircle2 size={24} style={{ color: 'var(--color-success)' }} />
                  } else if (i === selectedOption) {
                    bg = 'rgba(239,68,68,0.15)'
                    border = '2px solid var(--color-danger)'
                    icon = <XCircle size={24} style={{ color: 'var(--color-danger)' }} />
                  } else {
                    bg = 'rgba(0,0,0,0.2)'
                  }
                }

                return (
                  <motion.button
                    key={i}
                    whileHover={!isAnswered ? { scale: 1.02, backgroundColor: 'rgba(255,255,255,0.08)' } : {}}
                    whileTap={!isAnswered ? { scale: 0.98 } : {}}
                    onClick={() => handleSelect(i)}
                    disabled={isAnswered}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      width: '100%', padding: '20px 24px', background: bg, border: border,
                      borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: 18,
                      textAlign: 'left', cursor: isAnswered ? 'default' : 'pointer',
                      backdropFilter: 'blur(10px)',
                      transition: 'all 0.2s', opacity: isAnswered && i !== q.correct_index && i !== selectedOption ? 0.3 : 1
                    }}
                  >
                    {opt}
                    {icon}
                  </motion.button>
                )
              })}
            </div>

            {isAnswered && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                style={{ marginTop: 40, padding: 24, background: 'rgba(99,102,241,0.05)', borderLeft: '4px solid var(--color-primary-light)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: 12, color: 'var(--color-primary-light)', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 700, marginBottom: 12 }}>Detailed Explanation</div>
                <p style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 24 }}>{q.explanation}</p>
                
                <button className="btn btn-primary" onClick={handleNext} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 32px', fontSize: 16, fontWeight: 700 }}>
                  {currentIndex < questions.length - 1 ? 'Next Question' : 'View Final Verdict'} <ArrowRight size={20} />
                </button>
              </motion.div>
            )}

          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
