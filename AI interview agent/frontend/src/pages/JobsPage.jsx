import React, { useEffect, useState } from 'react'
import {
  BriefcaseBusiness,
  BookOpen,
  Loader2,
  Mic2,
  Target,
  Wand2,
} from 'lucide-react'
import Alert from '../components/Alert'
import { applicationAPI, jobsAPI, matchingAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'
import { useSelectedJob } from '../context/JobContext'

export default function JobsPage() {
  const [jobs, setJobs] = useState([])
  const { selectedJob, setSelectedJob } = useSelectedJob()
  const [selected, setSelected] = useState(selectedJob || null)
  const [match, setMatch] = useState(null)
  const [trackedJobIds, setTrackedJobIds] = useState(new Set())
  const [trackingJobId, setTrackingJobId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  const navigate = useNavigate()

  // Load jobs
  useEffect(() => {
    const loadJobs = async () => {
      try {
        setLoading(true)
        setError(null)

        const data = await jobsAPI.list()

        const jobList = Array.isArray(data)
          ? data
          : data?.jobs || data?.items || []

        setJobs(jobList)

        // Restore previously selected job
        if (selectedJob?.job_id) {
          const found = jobList.find(
            (job) => String(job.job_id) === String(selectedJob.job_id)
          )

          if (found) {
            setSelected(found)
          }
        }
      } catch (err) {
        console.error('Failed to load jobs:', err)

        setError(
          err?.response?.data?.detail ||
            err?.message ||
            'Failed to load jobs.'
        )
      } finally {
        setLoading(false)
      }
    }

    loadJobs()
  }, [selectedJob])

  useEffect(() => {
    let cancelled = false

    const loadTrackedApplications = async () => {
      try {
        const response = await applicationAPI.list({ sort_by: 'latest' })
        if (cancelled) return

        const jobIds = new Set(
          (response.applications || [])
            .map((app) => String(app.job_id || ''))
            .filter(Boolean)
        )
        setTrackedJobIds(jobIds)
      } catch (err) {
        console.warn('Unable to load tracked applications:', err)
      }
    }

    loadTrackedApplications()

    return () => {
      cancelled = true
    }
  }, [])

  const isJobTracked = (job) => {
    if (!job?.job_id) return false
    return trackedJobIds.has(String(job.job_id))
  }

  const addToTracker = async (job) => {
    if (!job) return

    const jobId = Number(job.job_id)
    if (!Number.isSafeInteger(jobId) || jobId <= 0) {
      setError('This job is missing an ID and cannot be added to the tracker.')
      return
    }

    const jobIdKey = String(jobId)
    setTrackingJobId(jobIdKey)
    setError(null)
    setSuccessMessage(null)

    try {
      await applicationAPI.create({
        job_id: jobId,
        job_title: job.title || job.job_title,
        company: job.company,
        company_name: job.company,
        job_description: job.description || job.job_description || '',
        application_deadline: job.deadline || job.application_deadline || null,
        status: 'Saved',
      })

      setTrackedJobIds((current) => new Set(current).add(jobIdKey))
      setSuccessMessage('Application added to your tracker successfully.')
    } catch (err) {
      if (err?.response?.status === 409) {
        setTrackedJobIds((current) => new Set(current).add(jobIdKey))
        setError('This internship is already in your application tracker.')
        return
      }

      console.error('Unable to add job to tracker:', err)
      if (err?.response?.status === 401 || err?.response?.status === 403) {
        setError('Please log in again.')
      } else if (err?.response?.status && err.response.status < 500) {
        setError(err.response.data?.detail || 'Unable to add this internship to the tracker.')
      } else {
        setError('Unable to add this internship to the tracker. Please try again.')
      }
    } finally {
      setTrackingJobId(null)
    }
  }

  // Analyze selected job
  const analyze = async (job) => {
    if (!job) return

    setSelected(job)
    setSelectedJob(job)
    setMatch(null)
    setError(null)

    try {
      const response = await matchingAPI.analyze({
        job_id: job.job_id,
      })

      setMatch(response)
    } catch (err) {
      console.error('Job matching error:', err)

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to analyze this job.'
      )
    }
  }

  // Save job and navigate
  const navigateTo = (path, job) => {
    if (!job) {
      setError('Please select a job first.')
      return
    }

    setSelected(job)
    setSelectedJob(job)

    // Save selected job for other agents/pages
    localStorage.setItem('selectedJob', JSON.stringify(job))

    navigate(`${path}?job_id=${encodeURIComponent(job.job_id)}`)
  }

  // Open Cover Letter page
  const openCoverLetter = (job) => {
    if (!job) {
      setError('Please select an internship first.')
      return
    }

    setSelected(job)
    setSelectedJob(job)

    // Store complete selected job
    localStorage.setItem('selectedJob', JSON.stringify(job))

    navigate(`/cover-letter?job_id=${encodeURIComponent(job.job_id)}`)
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6 bg-slate-950 text-slate-100 min-h-screen">

      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-white">
            Jobs & Internship Matching
          </h1>

          <p className="text-sm text-slate-400 mt-1">
            Compare your verified resume evidence with available roles and run
            Milestone 3 career agents.
          </p>
        </div>

        {selected && (
          <div className="bg-slate-900 border border-cyan-500/30 rounded-xl px-4 py-2 text-xs">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">
              Active Selected Internship:
            </span>

            <strong className="text-cyan-300 font-bold">
              {selected.title || selected.job_title}
            </strong>

            <span className="text-slate-400 ml-1.5">
              • {selected.company}
            </span>
          </div>
        )}
      </header>

      {/* Error */}
      {error && (
        <Alert
          type="error"
          message={error}
          onClose={() => setError(null)}
        />
      )}
      {successMessage && (
        <Alert
          type="success"
          message={successMessage}
          onClose={() => setSuccessMessage(null)}
        />
      )}

      {/* Loading */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-center">
          <Loader2 className="w-8 h-8 animate-spin text-cyan-400 mb-3" />

          <p className="text-sm text-slate-400">
            Loading internships...
          </p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-slate-400">
          No jobs are available yet.
        </div>
      ) : (
        <div className="grid lg:grid-cols-2 gap-6 items-start">

          {/* Job Listings */}
          <div className="space-y-4">

            {jobs.map((job) => {
              const isSelected =
                String(selected?.job_id) === String(job.job_id)

              const title = job.title || job.job_title
              const description =
                job.description || job.job_description || ''

              return (
                <div
                  key={job.job_id}
                  className={`bg-slate-900 border rounded-2xl p-5 space-y-3 transition ${
                    isSelected
                      ? 'border-cyan-500/60 shadow-lg shadow-cyan-950/20'
                      : 'border-slate-800 hover:border-slate-700'
                  }`}
                >

                  {/* Job Header */}
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <h2 className="font-bold text-white text-base">
                        {title}
                      </h2>

                      <p className="text-xs text-cyan-400 font-medium mt-0.5">
                        {job.company}
                      </p>
                    </div>

                    <BriefcaseBusiness className="text-slate-500 shrink-0 w-5 h-5" />
                  </div>

                  {/* Location */}
                  <p className="text-xs text-slate-400">
                    {job.location || 'Location flexible'}

                    {job.experience && (
                      <> • {job.experience}</>
                    )}
                  </p>

                  {/* Description */}
                  <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                    {description}
                  </p>

                  {/* Skills */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {(job.required_skills || []).map((skill, index) => (
                      <span
                        key={`${skill}-${index}`}
                        className="px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 text-[11px]"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>

                  {/* Actions */}
                  <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 pt-2 border-t border-slate-800/80">

                    <button
                      onClick={() => analyze(job)}
                      className="py-1.5 px-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white flex items-center justify-center gap-1 transition"
                    >
                      <Target className="w-3.5 h-3.5" />
                      Match
                    </button>

                    <button
                      onClick={() => navigateTo('/skill-gap', job)}
                      className="py-1.5 px-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-xs font-semibold text-white flex items-center justify-center gap-1 transition"
                    >
                      Skill Gap
                    </button>

                    {isJobTracked(job) ? (
                      <button
                        disabled
                        className="py-1.5 px-2 rounded-lg bg-emerald-900/40 text-emerald-200 text-xs font-semibold cursor-not-allowed opacity-80"
                      >
                        ✓ Added to Tracker
                      </button>
                    ) : (
                      <button
                        onClick={() => addToTracker(job)}
                        className="py-1.5 px-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white flex items-center justify-center gap-1 transition"
                      >
                        {trackingJobId === String(job.job_id) ? 'Saving...' : 'Add to Tracker'}
                      </button>
                    )}

                    <button
                      onClick={() =>
                        navigateTo('/resume-customization', job)
                      }
                      className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 flex items-center justify-center gap-1 transition"
                    >
                      <Wand2 className="w-3.5 h-3.5" />
                      Tailor
                    </button>

                    <button
                      onClick={() => openCoverLetter(job)}
                      className="py-1.5 px-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white flex items-center justify-center gap-1 transition"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      Cover
                    </button>

                    <button
                      onClick={() => navigateTo('/interview', job)}
                      className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 flex items-center justify-center gap-1 transition"
                    >
                      <Mic2 className="w-3.5 h-3.5" />
                      Prep
                    </button>

                  </div>
                </div>
              )
            })}

          </div>

          {/* Selected Job Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-fit sticky top-24 space-y-5">

            {!selected ? (
              <div className="text-center py-16 text-slate-400 text-sm">
                Select a role to view verified match diagnostics and
                workflow actions.
              </div>
            ) : !match ? (

              <div className="space-y-4">

                <div>
                  <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
                    Selected Role
                  </span>

                  <h2 className="text-xl font-bold text-white mt-1">
                    {selected.title || selected.job_title}
                  </h2>

                  <p className="text-sm text-slate-400">
                    {selected.company}
                  </p>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">
                  {selected.description ||
                    selected.job_description ||
                    ''}
                </p>

                <div className="space-y-2 pt-2 border-t border-slate-800">

                  <span className="text-xs font-semibold text-slate-400 block">
                    Run Milestone 3 Agents for this role:
                  </span>

                  <div className="grid grid-cols-2 gap-2">

                    <button
                      onClick={() => analyze(selected)}
                      className="py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white flex items-center justify-center gap-1.5"
                    >
                      <Target className="w-3.5 h-3.5" />
                      Match Score
                    </button>

                    <button
                      onClick={() =>
                        navigateTo('/skill-gap', selected)
                      }
                      className="py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-xs font-bold text-white"
                    >
                      Skill Gap Analysis
                    </button>

                    {isJobTracked(selected) ? (
                      <button
                        disabled
                        className="py-2.5 rounded-xl bg-emerald-900/40 text-emerald-200 text-xs font-bold cursor-not-allowed opacity-80"
                      >
                        ✓ Added to Tracker
                      </button>
                    ) : (
                      <button
                        onClick={() => addToTracker(selected)}
                        className="py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white"
                      >
                        {trackingJobId === String(selected.job_id) ? 'Saving...' : 'Add to Tracker'}
                      </button>
                    )}

                    <button
                      onClick={() =>
                        navigateTo('/resume-customization', selected)
                      }
                      className="py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 flex items-center justify-center gap-1.5"
                    >
                      <Wand2 className="w-3.5 h-3.5" />
                      Tailor Resume
                    </button>

                    <button
                      onClick={() => openCoverLetter(selected)}
                      className="py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-bold text-white flex items-center justify-center gap-1.5"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      Cover Letter
                    </button>

                  </div>

                  <button
                    onClick={() =>
                      navigateTo('/interview', selected)
                    }
                    className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 flex items-center justify-center gap-1.5"
                  >
                    <Mic2 className="w-3.5 h-3.5" />
                    Prepare Mock Interview
                  </button>

                </div>
              </div>

            ) : (

              <div className="space-y-5">

                <div>
                  <h2 className="text-xl font-bold text-white">
                    {selected.title || selected.job_title}
                  </h2>

                  <p className="text-xs text-cyan-400">
                    {selected.company}
                  </p>
                </div>

                {/* Match Score */}
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-extrabold text-cyan-400">
                    {match.match_score ?? 0}
                  </span>

                  <span className="text-sm text-slate-500">
                    /100
                  </span>

                  {match.recommendation && (
                    <span className="ml-auto text-xs font-bold text-emerald-400">
                      {match.recommendation}
                    </span>
                  )}
                </div>

                {/* Scores */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  {[
                    ['Skills', match.skill_score],
                    ['Experience', match.experience_score],
                    ['Education', match.education_score],
                    ['Projects', match.project_score],
                  ].map(([label, score]) => (
                    <div
                      key={label}
                      className="p-3 bg-slate-950 rounded-xl border border-slate-800/80"
                    >
                      <span className="text-slate-500 block text-[10px]">
                        {label}
                      </span>

                      <strong className="text-white text-base font-bold">
                        {score ?? 0}%
                      </strong>
                    </div>
                  ))}
                </div>

                {/* Explanation */}
                {match.explanation && (
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {match.explanation}
                  </p>
                )}

                {/* Missing Requirements */}
                <div>
                  <h3 className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                    Missing Requirements
                  </h3>

                  <p className="text-xs text-amber-300 mt-1 font-medium">
                    {match.missing_skills?.join(', ') ||
                      'None identified'}
                  </p>
                </div>

                {/* Agent Actions */}
                <div className="space-y-2 pt-2 border-t border-slate-800">

                  <div className="grid grid-cols-2 gap-2">

                    <button
                      onClick={() =>
                        navigateTo('/skill-gap', selected)
                      }
                      className="py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-xs font-bold text-white"
                    >
                      Skill Gap
                    </button>

                    <button
                      onClick={() =>
                        navigateTo('/resume-customization', selected)
                      }
                      className="py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white flex items-center justify-center gap-1.5"
                    >
                      <Wand2 className="w-3.5 h-3.5" />
                      Tailor Resume
                    </button>

                    <button
                      onClick={() => openCoverLetter(selected)}
                      className="py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-bold text-white flex items-center justify-center gap-1.5"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      Cover Letter
                    </button>

                    <button
                      onClick={() =>
                        navigateTo('/interview', selected)
                      }
                      className="py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 flex items-center justify-center gap-1.5"
                    >
                      <Mic2 className="w-3.5 h-3.5" />
                      Mock Interview
                    </button>

                  </div>

                </div>

              </div>
            )}

          </div>
        </div>
      )}
    </div>
  )
}