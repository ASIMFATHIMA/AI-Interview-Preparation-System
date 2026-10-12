import React, { useEffect, useState } from 'react'
import {
  BookOpen,
  BriefcaseBusiness,
  Check,
  Copy,
  Download,
  FileText,
  Loader2,
  RefreshCw,
  Send,
  Sparkles,
} from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import Alert from '../components/Alert'
import { coverLetterAPI, jobsAPI } from '../services/api'
import { useSelectedJob } from '../context/JobContext'

export default function CoverLetterPage() {
  const [searchParams] = useSearchParams()
  const { selectedJob, setSelectedJob } = useSelectedJob()

  const [jobs, setJobs] = useState([])
  const [selectedJobId, setSelectedJobId] = useState(
    searchParams.get('job_id') || selectedJob?.job_id || ''
  )
  const [form, setForm] = useState({
    job_id: null,
    job_title: '',
    company: '',
    job_description: '',
    additional_instructions: '',
  })

  const [letter, setLetter] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

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
            setForm({
              job_id: matched.job_id,
              job_title: matched.title,
              company: matched.company,
              job_description: matched.description || '',
              additional_instructions: '',
            })
          }
        } else if (data.length > 0 && !form.job_title) {
          const first = data[0]
          setSelectedJobId(first.job_id)
          setSelectedJob(first)
          setForm({
            job_id: first.job_id,
            job_title: first.title,
            company: first.company,
            job_description: first.description || '',
            additional_instructions: '',
          })
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
      setForm({
        job_id: j.job_id,
        job_title: j.title,
        company: j.company,
        job_description: j.description || '',
        additional_instructions: '',
      })
    }
  }

  const generate = async (e) => {
    if (e) e.preventDefault()
    setLoading(true)
    setError(null)
    setCopied(false)
    try {
      const payload = {
        job_id: form.job_id ? Number(form.job_id) : undefined,
        company: form.company,
        job_title: form.job_title,
        job_description: form.job_description,
        additional_instructions: form.additional_instructions,
      }
      const data = await coverLetterAPI.generate(payload)
      setLetter(data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Failed to generate cover letter. Please ensure your profile is uploaded.'
      )
    } finally {
      setLoading(false)
    }
  }

  const regenerate = async () => {
    setLoading(true)
    setError(null)
    setCopied(false)
    try {
      const payload = {
        job_id: form.job_id ? Number(form.job_id) : undefined,
        company: form.company,
        job_title: form.job_title,
        job_description: form.job_description,
        additional_instructions: form.additional_instructions,
      }
      const data = await coverLetterAPI.regenerate(payload)
      setLetter(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to regenerate cover letter.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    if (!letter?.cover_letter) return
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(letter.cover_letter)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = letter.cover_letter
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
      setError('Failed to copy text. Please copy it manually.')
    }
  }

  const handleDownload = () => {
    if (!letter?.cover_letter) return
    const blob = new Blob([letter.cover_letter], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const safeTitle = (letter.job_title || 'Cover_Letter')
      .replace(/\s+/g, '_')
      .replace(/[^\w-]/g, '')
    a.download = `${safeTitle}_Cover_Letter.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6 bg-slate-950 text-slate-100">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-xs uppercase font-semibold tracking-wider">
            <BookOpen className="w-4 h-4" />
            Cover Letter Agent
          </div>
          <h1 className="text-3xl font-extrabold text-white mt-1">
            Personalized Cover Letter
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Generate a targeted, truthful cover letter for your selected internship using only your verified student profile, projects, and skills.
          </p>
        </div>

        {form.job_title && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs shadow-md">
            <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">
              Selected Internship:
            </span>
            <div className="text-emerald-300 font-bold text-sm mt-0.5">
              {form.job_title}
            </div>
            <div className="text-slate-400 text-xs">{form.company}</div>
          </div>
        )}
      </header>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      <div className="grid lg:grid-cols-[380px_1fr] gap-6 items-start">
        {/* Input Form Column */}
        <form
          onSubmit={generate}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5"
        >
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BriefcaseBusiness className="w-4 h-4 text-emerald-400" />
              Role & Company
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Select or customize the target role details.
            </p>
          </div>

          {jobs.length > 0 && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Load From Available Jobs
              </label>
              <select
                value={selectedJobId}
                onChange={handleJobSelect}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:border-emerald-500 outline-none"
              >
                {jobs.map((job) => (
                  <option key={job.job_id} value={job.job_id}>
                    {job.title} — {job.company}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Company
            </label>
            <input
              required
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
              placeholder="e.g. ABC Technologies"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Job Title
            </label>
            <input
              required
              value={form.job_title}
              onChange={(e) => setForm({ ...form, job_title: e.target.value })}
              placeholder="e.g. Python AI Intern"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Job Description
            </label>
            <textarea
              required
              minLength={10}
              rows={5}
              value={form.job_description}
              onChange={(e) => setForm({ ...form, job_description: e.target.value })}
              placeholder="Paste the key responsibilities and qualifications..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-emerald-500 resize-y"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Special Instructions (Optional)
            </label>
            <input
              value={form.additional_instructions}
              onChange={(e) =>
                setForm({ ...form, additional_instructions: e.target.value })
              }
              placeholder="e.g. Emphasize open-source contributions"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-emerald-500"
            />
          </div>

          <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
            <span className="font-semibold text-slate-300 block">
              Standard Cover Letter Structure:
            </span>
            <div>1. Professional Greeting</div>
            <div>2. Introduction & Role Target</div>
            <div>3. Why This Role & Company</div>
            <div>4. Relevant Verified Skills & Projects</div>
            <div>5. Why Candidate Background Fits</div>
            <div>6. Professional Closing</div>
          </div>

          <button
            type="submit"
            disabled={loading || !form.job_title.trim() || !form.company.trim()}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 font-semibold text-sm shadow-lg shadow-emerald-950/30 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer transition"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                Generating cover letter...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Generate Cover Letter
              </>
            )}
          </button>
        </form>

        {/* Results Column */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 min-h-[500px] flex flex-col justify-between space-y-5">
          {!letter && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-20 px-4">
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4">
                <FileText className="w-8 h-8 text-emerald-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Generate Your Cover Letter</h3>
              <p className="text-sm text-slate-400 mt-2 max-w-sm">
                Click "Generate Cover Letter" to craft a personalized letter connecting your verified skills with{' '}
                <strong className="text-slate-200">{form.job_title || 'this internship'}</strong>.
              </p>
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-20">
              <Loader2 className="w-10 h-10 animate-spin text-emerald-400 mb-4" />
              <h3 className="text-base font-semibold text-white">Generating cover letter...</h3>
              <p className="text-xs text-slate-400 mt-1">
                Synthesizing verified profile evidence and job requirements with TinyLlama...
              </p>
            </div>
          )}

          {letter && !loading && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-xl font-bold text-white">
                    {letter.job_title}
                  </h2>
                  <p className="text-xs text-emerald-400 mt-0.5">
                    Company: {letter.company}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={regenerate}
                    title="Regenerate"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Regenerate
                  </button>
                  <button
                    onClick={handleCopy}
                    title="Copy to clipboard"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        Copy
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleDownload}
                    title="Download Text File"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white transition shadow"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Generated Cover Letter (Editable)
                </label>
                <textarea
                  value={letter.cover_letter}
                  onChange={(e) =>
                    setLetter({ ...letter, cover_letter: e.target.value })
                  }
                  className="w-full min-h-[440px] bg-slate-950 border border-slate-800 rounded-xl p-5 text-sm text-slate-200 leading-relaxed outline-none focus:border-emerald-500 select-all"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
