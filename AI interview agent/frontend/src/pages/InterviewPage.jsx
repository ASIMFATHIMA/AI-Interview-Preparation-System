import React, { useEffect, useState } from 'react'
import {
  Award,
  BookOpen,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  HelpCircle,
  Lightbulb,
  ListOrdered,
  Loader2,
  MessageSquare,
  Mic2,
  RefreshCw,
  Sparkles,
  Target,
  TrendingUp,
  UserCheck,
} from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import Alert from '../components/Alert'
import { interviewAPI, jobsAPI } from '../services/api'
import { useSelectedJob } from '../context/JobContext'

const INTERVIEW_TYPES = [
  { value: 'technical', label: 'Technical', icon: Brain, color: 'cyan', desc: 'Core languages, API design, algorithms' },
  { value: 'behavioral', label: 'Behavioral', icon: MessageSquare, color: 'violet', desc: 'STAR-format behavioral scenarios' },
  { value: 'project', label: 'Project-Based', icon: BookOpen, color: 'emerald', desc: 'Deep dive into your portfolio projects' },
  { value: 'role-specific', label: 'Role-Specific', icon: Target, color: 'blue', desc: 'Target internship responsibilities' },
  { value: 'mixed', label: 'Mixed Simulation', icon: Sparkles, color: 'amber', desc: 'All categories combined dynamically' },
]

const DIFFICULTIES = [
  { value: 'easy', label: 'Easy', color: 'emerald' },
  { value: 'medium', label: 'Medium', color: 'amber' },
  { value: 'hard', label: 'Hard', color: 'rose' },
]

const QUESTION_COUNTS = [3, 5, 8, 10]

function ScoreRing({ score, size = 96 }) {
  const r = 40
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#f43f5e'
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} viewBox="0 0 100 100" className="-rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#1e293b" strokeWidth="9" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="9"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="absolute text-center">
        <span className="text-2xl font-extrabold text-white">{score}</span>
        <span className="text-[10px] text-slate-400 block -mt-1">/100</span>
      </div>
    </div>
  )
}

export default function InterviewPage() {
  const [searchParams] = useSearchParams()
  const { selectedJob, setSelectedJob } = useSelectedJob()

  const [activeTab, setActiveTab] = useState('mock') // 'mock' or 'prep'
  const [jobs, setJobs] = useState([])
  const [selectedJobId, setSelectedJobId] = useState(
    searchParams.get('job_id') || selectedJob?.job_id || ''
  )

  // Mock interview configuration
  const [settings, setSettings] = useState({
    job_id: null,
    interview_type: 'technical',
    difficulty: 'medium',
    question_count: 5,
    job_description: '',
  })

  // Mock interview interactive state
  const [session, setSession] = useState(null)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [answerHistory, setAnswerHistory] = useState([])

  // Interview preparation guide state
  const [prepData, setPrepData] = useState(null)
  const [prepLoading, setPrepLoading] = useState(false)

  useEffect(() => {
    jobsAPI
      .list()
      .then((data) => {
        setJobs(data)
        const targetId = searchParams.get('job_id') || selectedJob?.job_id
        if (targetId) {
          const matched = data.find((j) => String(j.job_id) === String(targetId))
          if (matched) {
            setSelectedJobId(matched.job_id)
            setSelectedJob(matched)
            setSettings((s) => ({
              ...s,
              job_id: matched.job_id,
              job_description: matched.description || '',
            }))
          }
        }
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Failed to load jobs.')
      })
  }, [searchParams])

  const handleJobSelect = (e) => {
    const jId = e.target.value
    setSelectedJobId(jId)
    const j = jobs.find((item) => String(item.job_id) === String(jId))
    if (j) {
      setSelectedJob(j)
      setSettings((s) => ({
        ...s,
        job_id: j.job_id,
        job_description: j.description || '',
      }))
    }
  }

  // Start Interactive Mock Interview
  const startInterview = async (e) => {
    if (e) e.preventDefault()
    setLoading(true)
    setError(null)
    setAnswerHistory([])
    setFeedback(null)
    setResult(null)
    try {
      const payload = {
        job_id: settings.job_id ? Number(settings.job_id) : undefined,
        job_description: settings.job_description,
        interview_type: settings.interview_type,
        difficulty: settings.difficulty,
        question_count: Number(settings.question_count),
      }
      const data = await interviewAPI.start(payload)
      setSession(data)
      setAnswer('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start interview.')
    } finally {
      setLoading(false)
    }
  }

  // Submit Answer
  const submitAnswer = async (e) => {
    e.preventDefault()
    if (!answer.trim() || !session) return
    setLoading(true)
    setError(null)
    try {
      const res = await interviewAPI.answer(session.interview_id, {
        answer: answer.trim(),
      })
      setFeedback(res)
      setAnswerHistory((prev) => [
        ...prev,
        {
          questionNumber: session.question_number,
          question: session.question,
          category: session.category,
          answer: answer.trim(),
          feedback: res.feedback,
          score: res.score,
          relevance: res.relevance,
          technical_correctness: res.technical_correctness,
          completeness: res.completeness,
          communication: res.communication,
          missing_points: res.missing_points,
          improvement_suggestions: res.improvement_suggestions,
        },
      ])

      // If finished, load full final report
      if (!res.next_question_available) {
        const finalReport = await interviewAPI.report(session.interview_id)
        setResult(finalReport)
        setSession(null)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to evaluate answer.')
    } finally {
      setLoading(false)
    }
  }

  // Next Question
  const nextQuestion = async () => {
    if (!session) return
    setLoading(true)
    setError(null)
    try {
      const nextQ = await interviewAPI.next(session.interview_id)
      setSession(nextQ)
      setAnswer('')
      setFeedback(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to retrieve next question.')
    } finally {
      setLoading(false)
    }
  }

  // Fetch Interview Preparation Guide
  const loadPrepGuide = async () => {
    setPrepLoading(true)
    setError(null)
    try {
      const targetJob = jobs.find((j) => String(j.job_id) === String(selectedJobId))
      const payload = {
        job_id: selectedJobId ? Number(selectedJobId) : undefined,
        job_title: targetJob?.title || 'Software Engineer Intern',
        company: targetJob?.company || 'Target Company',
        job_description: targetJob?.description || '',
      }
      const data = await interviewAPI.prepare(payload)
      setPrepData(data)
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to generate interview preparation questions.'
      )
    } finally {
      setPrepLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6 bg-slate-950 text-slate-100">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs uppercase font-semibold tracking-wider">
            <Mic2 className="w-4 h-4" />
            M3.3 Interview Preparation Agent
          </div>
          <h1 className="text-3xl font-extrabold text-white mt-1">Interview Preparation</h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Simulate realistic AI interviews customized to your selected internship and generate structured preparation guidance.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1 gap-1 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('mock')}
            className={`px-4 py-2 rounded-lg transition ${
              activeTab === 'mock'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Interactive Mock Interview
          </button>
          <button
            onClick={() => {
              setActiveTab('prep')
              if (!prepData) loadPrepGuide()
            }}
            className={`px-4 py-2 rounded-lg transition ${
              activeTab === 'prep'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Interview Preparation Guide
          </button>
        </div>
      </header>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      {/* ================= TAB 1: INTERACTIVE MOCK INTERVIEW ================= */}
      {activeTab === 'mock' && (
        <div className="space-y-6">
          {/* Setup / Configuration Card if no active session or result */}
          {!session && !result && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    Configure Your Mock Interview
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Questions are generated from your resume + target job requirements + skill gaps.
                  </p>
                </div>

                {jobs.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Target Role:</span>
                    <select
                      value={selectedJobId}
                      onChange={handleJobSelect}
                      className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500"
                    >
                      <option value="">General Internship</option>
                      {jobs.map((job) => (
                        <option key={job.job_id} value={job.job_id}>
                          {job.title} — {job.company}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* 1. Category Selection */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Select Interview Category
                </label>
                <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
                  {INTERVIEW_TYPES.map((t) => {
                    const Icon = t.icon
                    const isSel = settings.interview_type === t.value
                    return (
                      <button
                        key={t.value}
                        type="button"
                        onClick={() =>
                          setSettings({ ...settings, interview_type: t.value })
                        }
                        className={`p-3.5 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                          isSel
                            ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                            : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                        }`}
                      >
                        <div className="flex items-center gap-2 font-bold text-sm text-white">
                          <Icon className={`w-4 h-4 text-${t.color}-400`} />
                          {t.label}
                        </div>
                        <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                          {t.desc}
                        </p>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* 2. Difficulty & Question Count */}
              <div className="grid sm:grid-cols-2 gap-6 pt-2">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                    Difficulty Level
                  </label>
                  <div className="flex gap-2.5">
                    {DIFFICULTIES.map((d) => (
                      <button
                        key={d.value}
                        type="button"
                        onClick={() =>
                          setSettings({ ...settings, difficulty: d.value })
                        }
                        className={`flex-1 py-2 rounded-xl border text-xs font-bold transition cursor-pointer capitalize ${
                          settings.difficulty === d.value
                            ? 'bg-indigo-600 border-indigo-500 text-white'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                        }`}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                    Number of Questions
                  </label>
                  <div className="flex gap-2.5">
                    {QUESTION_COUNTS.map((count) => (
                      <button
                        key={count}
                        type="button"
                        onClick={() =>
                          setSettings({ ...settings, question_count: count })
                        }
                        className={`flex-1 py-2 rounded-xl border text-xs font-bold transition cursor-pointer ${
                          Number(settings.question_count) === count
                            ? 'bg-indigo-600 border-indigo-500 text-white'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                        }`}
                      >
                        {count} Questions
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <button
                onClick={startInterview}
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 font-bold text-sm shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 cursor-pointer transition"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    Preparing interview questions...
                  </>
                ) : (
                  <>
                    <Mic2 className="w-4 h-4" />
                    Start Mock Interview
                  </>
                )}
              </button>
            </div>
          )}

          {/* Active Interview Session */}
          {session && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
              {/* Question Header */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-2.5">
                  <span className="px-3 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 text-xs font-extrabold">
                    Question {session.question_number} of {session.total_questions}
                  </span>
                  <span className="px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 text-xs font-medium uppercase tracking-wider">
                    {session.category}
                  </span>
                </div>
                <span className="text-xs text-slate-400 capitalize">
                  {settings.difficulty} Difficulty
                </span>
              </div>

              {/* The AI Question */}
              <div className="bg-slate-950/80 p-5 rounded-2xl border border-slate-800 space-y-2">
                <div className="text-[11px] uppercase font-bold text-cyan-400 tracking-wider flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5" /> AI Interviewer:
                </div>
                <h2 className="text-lg font-bold text-white leading-relaxed">
                  {session.question}
                </h2>
              </div>

              {/* Feedback from previous answer (if submitted) */}
              {feedback && (
                <div className="bg-slate-950 border border-indigo-500/30 rounded-2xl p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <span className="text-xs uppercase font-bold text-emerald-400 flex items-center gap-1.5">
                      <Award className="w-4 h-4" /> Answer Evaluation
                    </span>
                    <span className="text-sm font-extrabold text-white">
                      Score: <strong className="text-cyan-400">{feedback.score}</strong>/100
                    </span>
                  </div>

                  <p className="text-sm text-slate-200 leading-relaxed">
                    {feedback.feedback}
                  </p>

                  {/* Diagnostic breakdown components */}
                  <div className="grid sm:grid-cols-2 gap-3 text-xs bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                    <div>
                      <strong className="text-slate-400 block">Relevance:</strong>
                      <span className="text-slate-200">
                        {feedback.relevance || 'Directly aligned with prompt'}
                      </span>
                    </div>
                    <div>
                      <strong className="text-slate-400 block">Technical Correctness:</strong>
                      <span className="text-slate-200">
                        {feedback.technical_correctness || 'Sound conceptual accuracy'}
                      </span>
                    </div>
                    <div>
                      <strong className="text-slate-400 block">Completeness:</strong>
                      <span className="text-slate-200">
                        {feedback.completeness || 'Good foundational depth'}
                      </span>
                    </div>
                    <div>
                      <strong className="text-slate-400 block">Communication:</strong>
                      <span className="text-slate-200">
                        {feedback.communication || 'Clear presentation'}
                      </span>
                    </div>
                  </div>

                  {feedback.next_question_available && (
                    <button
                      onClick={nextQuestion}
                      className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-sm text-white flex items-center justify-center gap-2 cursor-pointer transition shadow"
                    >
                      Next Question <ChevronRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              )}

              {/* Student Answer Input */}
              {!feedback && (
                <form onSubmit={submitAnswer} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                      Your Answer
                    </label>
                    <textarea
                      required
                      rows={6}
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      placeholder="Type your response here... (Structure with concrete context, actions taken, and measured outcomes)"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-white placeholder:text-slate-600 outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading || !answer.trim()}
                    className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-sm text-white shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer transition"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        Evaluating response...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        Submit Answer
                      </>
                    )}
                  </button>
                </form>
              )}
            </div>
          )}

          {/* ================= FINAL REPORT ================= */}
          {result && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
                <div>
                  <div className="text-xs uppercase font-bold text-emerald-400 tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Mock Interview Complete
                  </div>
                  <h2 className="text-2xl font-extrabold text-white mt-1">
                    Interview Summary & Final Report
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Questions Answered: {result.questions_answered || answerHistory.length}
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  <ScoreRing score={result.overall_score || 75} />
                  <button
                    onClick={() => {
                      setResult(null)
                      setSession(null)
                    }}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition flex items-center gap-1.5 shadow"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    New Interview
                  </button>
                </div>
              </div>

              {/* Strengths & Areas to Improve */}
              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm uppercase tracking-wider">
                    <CheckCircle2 className="w-4 h-4" />
                    Strengths
                  </div>
                  <ul className="space-y-2 text-xs text-slate-300">
                    {result.strengths?.length > 0 ? (
                      result.strengths.map((s, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-emerald-400 font-bold">•</span>
                          <span>{s}</span>
                        </li>
                      ))
                    ) : (
                      <li>Structured response flow demonstrated.</li>
                    )}
                  </ul>
                </div>

                <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-rose-400 font-bold text-sm uppercase tracking-wider">
                    <TrendingUp className="w-4 h-4" />
                    Areas to Improve
                  </div>
                  <ul className="space-y-2 text-xs text-slate-300">
                    {result.areas_to_improve?.length > 0 ? (
                      result.areas_to_improve.map((a, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-rose-400 font-bold">•</span>
                          <span>{a}</span>
                        </li>
                      ))
                    ) : (
                      <li>Incorporate more quantifiable metrics and STAR structure.</li>
                    )}
                  </ul>
                </div>
              </div>

              {/* Topics to Revise (Technical, Project, HR) */}
              <div className="grid md:grid-cols-3 gap-6">
                <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-2.5">
                  <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs uppercase tracking-wider">
                    <Brain className="w-4 h-4" />
                    Technical Topics to Revise
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {result.technical_topics_to_revise?.length > 0 ? (
                      result.technical_topics_to_revise.map((t, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-cyan-400">•</span>
                          <span>{t}</span>
                        </li>
                      ))
                    ) : (
                      <li>Core language data structures and API validation patterns.</li>
                    )}
                  </ul>
                </div>

                <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-2.5">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
                    <BookOpen className="w-4 h-4" />
                    Project Topics to Revise
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {result.project_topics_to_revise?.length > 0 ? (
                      result.project_topics_to_revise.map((p, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-emerald-400">•</span>
                          <span>{p}</span>
                        </li>
                      ))
                    ) : (
                      <li>Walk through your contributions and debugging decisions.</li>
                    )}
                  </ul>
                </div>

                <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-2.5">
                  <div className="flex items-center gap-2 text-violet-400 font-bold text-xs uppercase tracking-wider">
                    <UserCheck className="w-4 h-4" />
                    HR Preparation
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {result.hr_preparation?.length > 0 ? (
                      result.hr_preparation.map((h, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-violet-400">•</span>
                          <span>{h}</span>
                        </li>
                      ))
                    ) : (
                      <li>Prepare concise answers for motivation and teamwork challenges.</li>
                    )}
                  </ul>
                </div>
              </div>

              {/* Recommended 30-Day Preparation Plan */}
              <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center gap-2 text-amber-400 font-bold text-sm uppercase tracking-wider">
                  <ListOrdered className="w-4 h-4" />
                  Recommended Preparation Plan
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
                  {result.recommended_preparation_plan?.map((step, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 bg-slate-900 border border-slate-800 rounded-xl space-y-1 text-xs"
                    >
                      <span className="text-cyan-400 font-bold uppercase text-[10px]">
                        Phase {idx + 1}
                      </span>
                      <p className="text-slate-200 mt-1 leading-relaxed">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ================= TAB 2: INTERVIEW PREPARATION GUIDE ================= */}
      {activeTab === 'prep' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div>
              <h2 className="text-lg font-bold text-white">
                Comprehensive Question Bank & Preparation Guidance
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Questions across Technical, Resume, Project, Role-Specific, and HR categories.
              </p>
            </div>

            <button
              onClick={loadPrepGuide}
              disabled={prepLoading}
              className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 font-bold text-xs text-white transition flex items-center gap-2 shadow"
            >
              {prepLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Generating questions...
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh Questions
                </>
              )}
            </button>
          </div>

          {prepLoading && (
            <div className="py-20 text-center flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-cyan-400 mb-3" />
              <p className="text-sm text-slate-400">
                Generating categorized interview questions with guidance...
              </p>
            </div>
          )}

          {prepData && !prepLoading && (
            <div className="space-y-4">
              {prepData.questions?.map((q, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3.5 hover:border-slate-700 transition"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-md bg-cyan-500/10 text-cyan-300 font-bold text-xs flex items-center justify-center">
                        {idx + 1}
                      </span>
                      <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 uppercase">
                        {q.category}
                      </span>
                    </div>
                    <span className="text-xs text-amber-400 font-semibold">
                      Difficulty: {q.difficulty}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white leading-relaxed">
                    {q.question}
                  </h3>

                  <div className="grid sm:grid-cols-2 gap-4 text-xs pt-1">
                    <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                      <span className="font-bold text-cyan-400 block uppercase tracking-wider text-[10px]">
                        Why This Question Matters
                      </span>
                      <p className="text-slate-300 leading-relaxed">
                        {q.why_this_question_matters}
                      </p>
                    </div>

                    <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                      <span className="font-bold text-emerald-400 block uppercase tracking-wider text-[10px]">
                        Preparation Guidance
                      </span>
                      <p className="text-slate-300 leading-relaxed">
                        {q.preparation_guidance}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
