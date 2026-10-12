import React, { useEffect, useRef, useState } from 'react'
import {
  Bot,
  BriefcaseBusiness,
  ChevronRight,
  Compass,
  Lightbulb,
  Loader2,
  Send,
  Sparkles,
  User,
} from 'lucide-react'
import { careerAPI, jobsAPI } from '../services/api'
import { useSelectedJob } from '../context/JobContext'

const SAMPLE_PROMPTS = [
  'Which internships match my skills?',
  'Why is this internship a good match for my profile?',
  'What skills am I missing?',
  'What should I learn for this internship?',
  'How can I improve my resume for this job?',
  'Generate a cover letter for this role.',
  'How should I prepare for this interview?',
  'What questions can I expect?',
  'Give me a 30-day preparation plan.',
  'What should I do next?',
]

export default function CareerAssistantPage() {
  const { selectedJob, setSelectedJob } = useSelectedJob()
  const [jobs, setJobs] = useState([])
  const [selectedJobId, setSelectedJobId] = useState(selectedJob?.job_id || '')

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hello! I am your AI Career Companion Agent. Ask me about matching internships, your skill gaps, resume improvements, cover letters, or interview preparation.",
      suggestions: [
        'Which internships match my skills?',
        'What skills am I missing?',
        'Give me a 30-day preparation plan.',
      ],
    },
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    jobsAPI
      .list()
      .then((data) => {
        setJobs(data)
        if (selectedJob && !selectedJobId) {
          setSelectedJobId(selectedJob.job_id)
        }
      })
      .catch(() => {})
  }, [selectedJob])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleJobSelect = (e) => {
    const jId = e.target.value
    setSelectedJobId(jId)
    const j = jobs.find((item) => String(item.job_id) === String(jId))
    if (j) setSelectedJob(j)
  }

  const sendMessage = async (textToSend) => {
    const msg = (textToSend || inputMessage).trim()
    if (!msg || loading) return

    setMessages((prev) => [...prev, { role: 'user', text: msg }])
    setInputMessage('')
    setLoading(true)

    try {
      const payload = {
        message: msg,
        job_id: selectedJobId ? Number(selectedJobId) : undefined,
      }
      const data = await careerAPI.chat(payload)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.response,
          agent: data.routed_agent,
          context_used: data.context_used,
          suggestions: data.suggestions,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: 'I could not connect to the career agent services right now. Please try again.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-6 bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs uppercase font-semibold tracking-wider">
            <Sparkles className="w-4 h-4" />
            M3.4 Conversational Career Assistant
          </div>
          <h1 className="text-3xl font-extrabold text-white mt-1">Career Assistant</h1>
          <p className="text-sm text-slate-400 mt-1">
            Your conversational companion for internships, gap analysis, applications, and interview prep.
          </p>
        </div>

        {/* Selected job pill and selector */}
        {jobs.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-2.5 flex items-center gap-2 text-xs">
            <BriefcaseBusiness className="w-4 h-4 text-cyan-400 shrink-0" />
            <select
              value={selectedJobId}
              onChange={handleJobSelect}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500"
            >
              <option value="">General Career Guidance</option>
              {jobs.map((j) => (
                <option key={j.job_id} value={j.job_id}>
                  {j.title} · {j.company}
                </option>
              ))}
            </select>
          </div>
        )}
      </header>

      {/* Quick Prompt Pills */}
      <div className="space-y-2">
        <span className="text-xs uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
          Suggested Questions:
        </span>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => sendMessage(p)}
              disabled={loading}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition cursor-pointer disabled:opacity-50"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Container */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[560px] overflow-hidden shadow-xl">
        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.map((item, index) => {
            const isUser = item.role === 'user'
            return (
              <div
                key={index}
                className={`flex gap-3 max-w-[85%] ${
                  isUser ? 'ml-auto flex-row-reverse' : ''
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                    isUser
                      ? 'bg-indigo-600 text-white'
                      : 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-400'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div className="space-y-2">
                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
                      isUser
                        ? 'bg-indigo-600 text-white shadow-md'
                        : 'bg-slate-950 border border-slate-800 text-slate-200'
                    }`}
                  >
                    {item.text}
                  </div>

                  {/* Context and Agent badges */}
                  {!isUser && (item.agent || item.context_used?.length > 0) && (
                    <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                      {item.agent && (
                        <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 font-semibold uppercase">
                          Routed: {item.agent.replace(/_/g, ' ')}
                        </span>
                      )}
                      {item.context_used?.map((c, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 capitalize"
                        >
                          {c.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Follow-up suggestions */}
                  {!isUser && item.suggestions?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {item.suggestions.map((s, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => sendMessage(s)}
                          disabled={loading}
                          className="text-[11px] px-2.5 py-1 rounded-md bg-slate-950 hover:bg-slate-800 border border-slate-800 text-cyan-300 transition cursor-pointer flex items-center gap-1"
                        >
                          <ChevronRight className="w-3 h-3" />
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}

          {loading && (
            <div className="flex gap-3 max-w-[85%]">
              <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-400 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                Thinking...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault()
            sendMessage()
          }}
          className="p-4 border-t border-slate-800 bg-slate-950/70 flex gap-2"
        >
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about internships, skills, resume tailoring, or interview prep..."
            disabled={loading}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-500 outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={loading || !inputMessage.trim()}
            className="p-3.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-50 transition cursor-pointer shadow"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
