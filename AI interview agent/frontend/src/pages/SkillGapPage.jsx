import React, { useEffect, useState } from 'react'
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  GraduationCap,
  Layers,
  Lightbulb,
  Loader2,
  Map,
  Target,
  Wand2,
} from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import Alert from '../components/Alert'
import { jobsAPI, skillGapAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useSelectedJob } from '../context/JobContext'

const priorityClass = {
  High: 'text-rose-300 border-rose-500/30 bg-rose-500/10',
  Medium: 'text-amber-300 border-amber-500/30 bg-amber-500/10',
  Low: 'text-slate-300 border-slate-700 bg-slate-800',
}

export default function SkillGapPage() {
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
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
  const [expanded, setExpanded] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  // Load available jobs and prefill from selected job
  useEffect(() => {
    jobsAPI
      .list()
      .then((availableJobs) => {
        setJobs(availableJobs)
        const targetId = searchParams.get('job_id') || selectedJob?.job_id
        if (targetId) {
          const matched = availableJobs.find(
            (job) => String(job.job_id) === String(targetId)
          )
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
        } else if (availableJobs.length > 0 && !form.job_title) {
          const first = availableJobs[0]
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
      .catch((err) =>
        setError(err.response?.data?.detail || 'Unable to load saved jobs.')
      )
  }, [searchParams])

  const selectSavedJob = (e) => {
    const jId = e.target.value
    setSelectedJobId(jId)
    const selected = jobs.find((job) => String(job.job_id) === String(jId))
    if (selected) {
      setSelectedJob(selected)
      setForm({
        job_id: selected.job_id,
        job_title: selected.title,
        company: selected.company,
        job_description: selected.description || '',
      })
    }
  }

  const analyze = async (e) => {
    if (e) e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const payload = {
        job_id: form.job_id ? Number(form.job_id) : undefined,
        job_title: form.job_title,
        company: form.company,
        job_description: form.job_description,
      }
      const data = await skillGapAPI.analyze(payload)
      setResult(data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Unable to analyze this skill gap. Please check your resume and job description.'
      )
    } finally {
      setLoading(false)
    }
  }

  const matchingSkills = result?.matching_skills || result?.matched_skills || []
  const partialSkills = result?.partial_skills || []
  const missingSkills = result?.missing_skills || []
  const preferredMissing = result?.preferred_missing_skills || []
  const experienceGaps = result?.experience_gaps || []
  const qualificationGaps = result?.qualification_gaps || []
  const projectGaps = result?.project_gaps || []
  const recommendations = result?.recommendations || []

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6 bg-slate-950 text-slate-100">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs uppercase font-semibold tracking-wider">
            <Target className="w-4 h-4" />
            M3.1 Skill Gap Analysis Agent
          </div>
          <h1 className="text-3xl font-extrabold text-white mt-1">Skill Gap Analysis</h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Compare your verified student profile and resume against your selected internship to uncover missing requirements and actionable learning recommendations.
          </p>
        </div>

        {form.job_title && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs shadow-md">
            <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">
              Selected Internship:
            </span>
            <div className="text-cyan-300 font-bold text-sm mt-0.5">
              {form.job_title}
            </div>
            <div className="text-slate-400 text-xs">{form.company}</div>
          </div>
        )}
      </header>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      <div className="grid lg:grid-cols-[380px_1fr] gap-6 items-start">
        {/* Left Form Column */}
        <form
          onSubmit={analyze}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5"
        >
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BriefcaseBusiness className="w-4 h-4 text-cyan-400" />
              Target Role Information
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Select a job from your matched internships or paste a description.
            </p>
          </div>

          {jobs.length > 0 && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Load From Available Jobs
              </label>
              <select
                value={selectedJobId}
                onChange={selectSavedJob}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:border-cyan-500 outline-none"
              >
                {jobs.map((job) => (
                  <option key={job.job_id} value={job.job_id}>
                    {job.title} · {job.company}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Job Title
            </label>
            <input
              required
              name="job_title"
              value={form.job_title}
              onChange={(e) => setForm({ ...form, job_title: e.target.value })}
              placeholder="e.g. Python Backend Developer"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Company
            </label>
            <input
              name="company"
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
              placeholder="e.g. ABC Technologies"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Job Description
            </label>
            <textarea
              required
              minLength={10}
              rows={6}
              name="job_description"
              value={form.job_description}
              onChange={(e) =>
                setForm({ ...form, job_description: e.target.value })
              }
              placeholder="Paste requirements, required/preferred skills, responsibilities..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-cyan-500 resize-y"
            />
          </div>

          <div className="border-t border-slate-800 pt-4">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold block">
              Candidate Resume Source:
            </span>
            <div className="text-white text-xs font-medium mt-1">
              {user?.name || 'Authenticated Student Profile'}
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Verified skills and project records loaded automatically.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !form.job_title.trim()}
            className="w-full py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 font-semibold text-sm shadow-lg shadow-cyan-900/30 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer transition"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                Analyzing your profile...
              </>
            ) : (
              <>
                <Target className="w-4 h-4" />
                Analyze Skill Gap
              </>
            )}
          </button>
        </form>

        {/* Right Results Column */}
        <div className="space-y-6">
          {!result && !loading && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 min-h-[440px] flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-4">
                <Target className="w-8 h-8 text-cyan-400" />
              </div>
              <h3 className="text-lg font-bold text-white">
                Discover Your Skill Gaps
              </h3>
              <p className="text-sm text-slate-400 mt-2 max-w-sm">
                Click <strong className="text-cyan-300">"Analyze Skill Gap"</strong> to compare your verified resume skills against{' '}
                <strong className="text-white">{form.job_title || 'the selected role'}</strong>.
              </p>
            </div>
          )}

          {loading && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 min-h-[440px] flex flex-col items-center justify-center text-center">
              <Loader2 className="w-10 h-10 animate-spin text-cyan-400 mb-4" />
              <h3 className="text-base font-semibold text-white">Analyzing your profile...</h3>
              <p className="text-xs text-slate-400 mt-1">
                Comparing skills, detecting gaps, and generating recommendations...
              </p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-6">
              {/* Score and summary header */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-semibold">
                      Selected Internship:
                    </span>
                    <h2 className="text-2xl font-bold text-white">{result.job_title}</h2>
                    <p className="text-sm text-cyan-400 mt-0.5">
                      {result.company || 'Target Company'}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-center">
                      <span className="text-[10px] uppercase text-slate-400 block font-semibold">
                        Skill Match
                      </span>
                      <strong className="text-2xl text-cyan-400 font-extrabold">
                        {result.skill_match_score}%
                      </strong>
                    </div>

                    <div className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-center">
                      <span className="text-[10px] uppercase text-slate-400 block font-semibold">
                        Skill Gap
                      </span>
                      <strong className="text-2xl text-rose-400 font-extrabold">
                        {result.skill_gap_score}%
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Quick navigation actions */}
                <div className="flex flex-wrap gap-2.5 mt-4 pt-1">
                  <Link
                    to={`/resume-customization?job_id=${result.job_id || selectedJobId}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600/30 text-xs font-semibold transition"
                  >
                    <Wand2 className="w-3.5 h-3.5" />
                    Tailor Resume for this Role
                  </Link>
                  <Link
                    to={`/cover-letter?job_id=${result.job_id || selectedJobId}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-600/30 text-xs font-semibold transition"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    Generate Cover Letter
                  </Link>
                  <Link
                    to={`/interview?job_id=${result.job_id || selectedJobId}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600/20 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-600/30 text-xs font-semibold transition"
                  >
                    <Target className="w-3.5 h-3.5" />
                    Prepare Interview Questions
                  </Link>
                </div>
              </div>

              {/* Skills Classification Grid */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* 1. Matching Skills */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                      Matching Skills
                    </h3>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {matchingSkills.length > 0 ? (
                      matchingSkills.map((s) => (
                        <span
                          key={s}
                          className="px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-1.5"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">
                        No direct skill matches identified in verified profile.
                      </span>
                    )}
                  </div>
                </div>

                {/* 2. Partially Demonstrated Skills */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-amber-400" />
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                      Partially Demonstrated
                    </h3>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {partialSkills.length > 0 ? (
                      partialSkills.map((s) => (
                        <span
                          key={s}
                          className="px-3 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-semibold"
                        >
                          ◐ {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">
                        No partial matches identified.
                      </span>
                    )}
                  </div>
                </div>

                {/* 3. Missing Critical Skills */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                      Missing Critical Skills
                    </h3>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {missingSkills.length > 0 ? (
                      missingSkills.map((s) => (
                        <span
                          key={s}
                          className="px-3 py-1.5 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs font-semibold"
                        >
                          ✕ {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-emerald-400 font-medium">
                        All critical required skills matched!
                      </span>
                    )}
                  </div>
                </div>

                {/* 4. Preferred Skills Missing */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-slate-400" />
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                      Preferred Skills Missing
                    </h3>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {preferredMissing.length > 0 ? (
                      preferredMissing.map((s) => (
                        <span
                          key={s}
                          className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-xs font-medium"
                        >
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">
                        No optional preferred skill gaps.
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* 5, 6, 7. Experience, Qualification, and Project Gaps */}
              <div className="grid md:grid-cols-3 gap-6">
                {/* Experience Gaps */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2.5">
                  <div className="flex items-center gap-2">
                    <BriefcaseBusiness className="w-4 h-4 text-indigo-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      Experience Gaps
                    </h4>
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {experienceGaps.length > 0 ? (
                      experienceGaps.map((eg, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-amber-400 font-bold">•</span>
                          <span>{eg}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-emerald-400">Experience requirement satisfied.</li>
                    )}
                  </ul>
                </div>

                {/* Qualification Gaps */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2.5">
                  <div className="flex items-center gap-2">
                    <GraduationCap className="w-4 h-4 text-cyan-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      Qualification Gaps
                    </h4>
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {qualificationGaps.length > 0 ? (
                      qualificationGaps.map((qg, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-amber-400 font-bold">•</span>
                          <span>{qg}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-emerald-400">Academic background aligns well.</li>
                    )}
                  </ul>
                </div>

                {/* Project Gaps */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2.5">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-emerald-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      Project Gaps
                    </h4>
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {projectGaps.length > 0 ? (
                      projectGaps.map((pg, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-amber-400 font-bold">•</span>
                          <span>{pg}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-emerald-400">Demonstrated projects cover core stack.</li>
                    )}
                  </ul>
                </div>
              </div>

              {/* 8. Actionable Recommendations (Numbered List) */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
                <div className="flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    Personalized Recommendations
                  </h3>
                </div>
                <ol className="space-y-2.5 mt-2">
                  {recommendations.map((rec, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-sm text-slate-200"
                    >
                      <span className="w-6 h-6 rounded-lg bg-cyan-600/20 text-cyan-300 font-bold text-xs flex items-center justify-center shrink-0">
                        {index + 1}
                      </span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {/* Detailed Breakdown for every missing skill */}
              {result.skill_gaps?.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    Detailed Skill Gap Diagnostics
                  </h3>
                  <div className="space-y-2.5">
                    {result.skill_gaps.map((gap) => (
                      <div
                        key={gap.skill}
                        className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/60"
                      >
                        <button
                          type="button"
                          onClick={() =>
                            setExpanded(expanded === gap.skill ? null : gap.skill)
                          }
                          className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-800/30 transition cursor-pointer"
                        >
                          <div className="flex items-center gap-3">
                            <span className="font-semibold text-white text-sm">
                              {gap.skill}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-bold border ${priorityClass[gap.priority] || priorityClass.Low}`}
                            >
                              {gap.priority}
                            </span>
                            <span className="text-xs text-slate-400 capitalize">
                              {gap.requirement_type || 'Required'}
                            </span>
                          </div>
                          <ChevronDown
                            className={`w-4 h-4 text-slate-400 transition-transform ${expanded === gap.skill ? 'rotate-180' : ''}`}
                          />
                        </button>

                        {expanded === gap.skill && (
                          <div className="p-4 border-t border-slate-800 space-y-3 text-xs text-slate-300 bg-slate-950">
                            <div>
                              <strong className="text-slate-200">Why It Matters:</strong>{' '}
                              <span>{gap.why_it_matters || gap.reason}</span>
                            </div>
                            <div>
                              <strong className="text-slate-200">Recommended Action:</strong>{' '}
                              <span className="text-cyan-300">
                                {gap.recommended_action || gap.recommendation}
                              </span>
                            </div>
                            <div>
                              <strong className="text-slate-200">Suggested Project / Topic:</strong>{' '}
                              <span>{gap.suggested_topic_project || gap.project_recommendation}</span>
                            </div>
                            {gap.learning_path?.length > 0 && (
                              <div>
                                <strong className="text-slate-200 block mb-1">
                                  Learning Roadmap Steps:
                                </strong>
                                <ul className="list-disc list-inside space-y-0.5 text-slate-400 pl-1">
                                  {gap.learning_path.map((step, idx) => (
                                    <li key={idx}>{step}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
