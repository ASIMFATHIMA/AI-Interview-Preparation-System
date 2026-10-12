import React, { useEffect, useState } from 'react'
import {
  BriefcaseBusiness,
  Check,
  Copy,
  Download,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
  Wand2,
} from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import Alert from '../components/Alert'
import { jobsAPI, resumeAPI } from '../services/api'
import { useSelectedJob } from '../context/JobContext'

export default function ResumeCustomizationPage() {
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
  })

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  // Load available jobs and prefill from selected job
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
          })
        }
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Failed to load jobs list.')
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
      })
    }
  }

  const generateTailoredResume = async (e) => {
    if (e) e.preventDefault()
    setLoading(true)
    setError(null)
    setCopied(false)
    try {
      const payload = {
        job_id: form.job_id ? Number(form.job_id) : undefined,
        job_title: form.job_title,
        company: form.company,
        job_description: form.job_description,
      }
      const data = await resumeAPI.customize(payload)
      setResult(data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Failed to generate tailored resume. Please verify your resume is uploaded.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (!result?.tailored_resume) return
    navigator.clipboard.writeText(result.tailored_resume)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    if (!result?.tailored_resume) return
    const blob = new Blob([result.tailored_resume], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const safeTitle = (result.job_title || 'Tailored_Resume')
      .replace(/\s+/g, '_')
      .replace(/[^\w-]/g, '')
    a.download = `${safeTitle}_Resume.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6 bg-slate-950 text-slate-100">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs uppercase font-semibold tracking-wider">
            <Wand2 className="w-4 h-4" />
            Resume Customization Agent
          </div>
          <h1 className="text-3xl font-extrabold text-white mt-1">Tailored Resume</h1>
          <p className="text-sm text-slate-400 mt-1">
            Align your verified experience and projects with your selected internship. Zero hallucinations.
          </p>
        </div>

        {form.job_title && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs">
            <span className="text-slate-400">Selected Internship:</span>{' '}
            <strong className="text-cyan-300 font-semibold">{form.job_title}</strong>
            <span className="text-slate-500 mx-1.5">•</span>
            <span className="text-slate-300">{form.company}</span>
          </div>
        )}
      </header>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      <div className="grid lg:grid-cols-[380px_1fr] gap-6 items-start">
        {/* Controls Column */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BriefcaseBusiness className="w-4 h-4 text-indigo-400" />
              Target Internship
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Select or modify the role you want to tailor your resume for.
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
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:border-indigo-500 outline-none"
              >
                {jobs.map((job) => (
                  <option key={job.job_id} value={job.job_id}>
                    {job.title} — {job.company}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Target Role
              </label>
              <input
                type="text"
                required
                value={form.job_title}
                onChange={(e) => setForm({ ...form, job_title: e.target.value })}
                placeholder="e.g. Python AI Intern"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Company
              </label>
              <input
                type="text"
                required
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                placeholder="e.g. ABC Technologies"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Job Description / Keywords
              </label>
              <textarea
                rows={5}
                value={form.job_description}
                onChange={(e) => setForm({ ...form, job_description: e.target.value })}
                placeholder="Paste the job description or core skill requirements..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:border-indigo-500 outline-none resize-y"
              />
            </div>
          </div>

          <button
            onClick={generateTailoredResume}
            disabled={loading || !form.job_title.trim()}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 font-semibold text-sm shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer transition"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                Generating tailored resume...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-cyan-300" />
                Tailor Resume
              </>
            )}
          </button>
        </div>

        {/* Results Column */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 min-h-[500px] flex flex-col justify-between space-y-6">
          {!result && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-16 px-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4">
                <FileText className="w-8 h-8 text-indigo-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Generate Your Tailored Resume</h3>
              <p className="text-sm text-slate-400 mt-2 max-w-sm">
                Click "Tailor Resume" to restructure your verified skills and highlighted projects specifically for{' '}
                <strong className="text-slate-200">{form.job_title || 'the target role'}</strong>.
              </p>
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-20">
              <Loader2 className="w-10 h-10 animate-spin text-cyan-400 mb-4" />
              <h3 className="text-base font-semibold text-white">Generating tailored resume...</h3>
              <p className="text-xs text-slate-400 mt-1">
                Prioritizing relevant skills, projects, and keywords with TinyLlama...
              </p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-5">
              {/* Header metadata */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="text-xs text-slate-400">Target Role:</div>
                  <h2 className="text-xl font-bold text-white">{result.job_title}</h2>
                  <p className="text-xs text-cyan-400 mt-0.5">Company: {result.company}</p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={generateTailoredResume}
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
                    title="Download as Markdown"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition shadow"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download
                  </button>
                </div>
              </div>

              {/* Badges for Relevant Skills and Keywords Used */}
              <div className="grid sm:grid-cols-2 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                    Relevant Skills Highlighted:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {result.relevant_skills?.length > 0 ? (
                      result.relevant_skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-2.5 py-1 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-medium"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">None identified</span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                    Job Keywords Integrated:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {result.keywords_used?.length > 0 ? (
                      result.keywords_used.map((kw) => (
                        <span
                          key={kw}
                          className="px-2.5 py-1 rounded-md bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-medium"
                        >
                          {kw}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">General matching</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Formatted Markdown Resume Output */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Tailored Resume Preview
                </label>
                <textarea
                  readOnly
                  value={result.tailored_resume}
                  className="w-full min-h-[500px] bg-slate-950 border border-slate-800 rounded-xl p-5 font-mono text-xs text-slate-200 leading-relaxed outline-none focus:border-cyan-500 select-all"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
