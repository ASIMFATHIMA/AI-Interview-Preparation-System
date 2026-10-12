import React, { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  BellRing,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  FileText,
  Filter,
  Loader2,
  PencilLine,
  Search,
  Trash2,
  X,
} from 'lucide-react'
import Alert from '../components/Alert'
import { applicationAPI } from '../services/api'

const STATUS_OPTIONS = [
  'All',
  'Saved',
  'Planning to Apply',
  'Applied',
  'Application Under Review',
  'Shortlisted',
  'Interview Scheduled',
  'Interview Completed',
  'Offer Received',
  'Rejected',
  'Withdrawn',
]

const ACTIVE_STATUSES = [
  'Saved',
  'Planning to Apply',
  'Applied',
  'Application Under Review',
  'Shortlisted',
  'Interview Scheduled',
  'Interview Completed',
]

const COMPLETED_STATUSES = ['Offer Received', 'Rejected', 'Withdrawn']

const emptyForm = {
  job_title: '',
  company_name: '',
  job_description: '',
  application_date: '',
  application_deadline: '',
  status: 'Saved',
  interview_date: '',
  interview_time: '',
  interview_status: 'Not Scheduled',
  interview_type: '',
  interview_notes: '',
  interview_outcome: 'Pending',
  notes: '',
  follow_up_information: '',
  next_follow_up_date: '',
}

function toDateInputValue(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toISOString().slice(0, 10)
}

export default function ApplicationTrackerPage() {
  const navigate = useNavigate()
  const [applications, setApplications] = useState([])
  const [dashboard, setDashboard] = useState(null)
  const [reminders, setReminders] = useState(null)
  const [selectedTab, setSelectedTab] = useState('active')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [sortBy, setSortBy] = useState('latest')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [selectedApp, setSelectedApp] = useState(null)
  const [form, setForm] = useState(emptyForm)

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [listResult, statsResult, remindersResult] = await Promise.allSettled([
        applicationAPI.list({ sort_by: sortBy }),
        applicationAPI.getDashboard(),
        applicationAPI.getReminders(),
      ])

      if (listResult.status === 'rejected') {
        throw listResult.reason
      }

      setApplications(listResult.value.applications || [])

      const unavailableData = []
      if (statsResult.status === 'fulfilled') {
        setDashboard(statsResult.value)
      } else {
        setDashboard(null)
        unavailableData.push('application statistics')
        console.error('Unable to load application statistics', statsResult.reason)
      }

      if (remindersResult.status === 'fulfilled') {
        setReminders(remindersResult.value)
      } else {
        setReminders(null)
        unavailableData.push('application reminders')
        console.error('Unable to load application reminders', remindersResult.reason)
      }

      if (unavailableData.length > 0) {
        setError(
          `Applications loaded, but ${unavailableData.join(' and ')} could not be loaded. Please try again.`
        )
      }
    } catch (err) {
      console.error('Unable to load applications', err)
      setError(err?.response?.data?.detail || 'Unable to load applications. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [sortBy])

  const filteredApplications = useMemo(() => {
    const query = search.trim().toLowerCase()
    const visible = applications.filter((app) => {
      if (!query) return true
      const haystack = [
        app.company_name,
        app.company,
        app.job_title,
        app.job_description,
        app.notes,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(query)
    })

    const filtered = statusFilter === 'All'
      ? visible
      : visible.filter((app) => app.status === statusFilter)

    return filtered.filter((app) => {
      if (selectedTab === 'active') {
        return ACTIVE_STATUSES.includes(app.status)
      }
      return COMPLETED_STATUSES.includes(app.status)
    })
  }, [applications, search, selectedTab, statusFilter])

  const openEditor = (app) => {
    setSelectedApp(app)
    setForm({
      job_title: app.job_title || '',
      company_name: app.company_name || app.company || '',
      job_description: app.job_description || '',
      application_date: toDateInputValue(app.application_date),
      application_deadline: toDateInputValue(app.application_deadline || app.deadline),
      status: app.status || 'Saved',
      interview_date: toDateInputValue(app.interview_date),
      interview_time: app.interview_time || '',
      interview_status: app.interview_status || 'Not Scheduled',
      interview_type: app.interview_type || '',
      interview_notes: app.interview_notes || '',
      interview_outcome: app.interview_outcome || 'Pending',
      notes: app.notes || '',
      follow_up_information: app.follow_up_information || '',
      next_follow_up_date: toDateInputValue(app.next_follow_up_date),
    })
  }

  const openResume = (app) => {
    if (!app?.resume_id) {
      setError('No customized resume available')
      return
    }

    navigate(`/resume-customization?job_id=${encodeURIComponent(app.job_id || '')}`)
  }

  const openCoverLetter = (app) => {
    if (!app?.cover_letter_id) {
      setError('No cover letter available')
      return
    }

    navigate(`/cover-letter?job_id=${encodeURIComponent(app.job_id || '')}`)
  }

  const handleSave = async (event) => {
    event.preventDefault()
    if (!selectedApp) return

    setSaving(true)
    try {
      await applicationAPI.update(selectedApp.application_id, {
        job_title: form.job_title,
        company_name: form.company_name,
        job_description: form.job_description,
        application_date: form.application_date ? new Date(form.application_date).toISOString() : null,
        application_deadline: form.application_deadline ? new Date(form.application_deadline).toISOString() : null,
        status: form.status,
        interview_date: form.interview_date ? new Date(form.interview_date).toISOString() : null,
        interview_time: form.interview_time,
        interview_status: form.interview_status,
        interview_type: form.interview_type,
        interview_notes: form.interview_notes,
        interview_outcome: form.interview_outcome,
        notes: form.notes,
        follow_up_information: form.follow_up_information,
        next_follow_up_date: form.next_follow_up_date ? new Date(form.next_follow_up_date).toISOString() : null,
      })
      setSelectedApp(null)
      setForm(emptyForm)
      await loadData()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to update the application.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (applicationId) => {
    const confirmed = window.confirm('Delete this application?')
    if (!confirmed) return

    try {
      await applicationAPI.delete(applicationId)
      setSelectedApp(null)
      await loadData()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to delete the application.')
    }
  }

  const handleStatusChange = async (applicationId, value) => {
    try {
      await applicationAPI.updateStatus(applicationId, value)
      await loadData()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to update status.')
    }
  }

  const summaryCards = [
    { label: 'Total Applications', value: dashboard?.total ?? 0, accent: 'bg-indigo-500/10 text-indigo-300' },
    { label: 'Active Applications', value: dashboard?.active ?? 0, accent: 'bg-cyan-500/10 text-cyan-300' },
    { label: 'Upcoming Deadlines', value: dashboard?.upcoming_deadlines_count ?? 0, accent: 'bg-amber-500/10 text-amber-300' },
    { label: 'Interviews Scheduled', value: dashboard?.interviews_scheduled ?? 0, accent: 'bg-emerald-500/10 text-emerald-300' },
    { label: 'Offers Received', value: dashboard?.offers_received ?? 0, accent: 'bg-purple-500/10 text-purple-300' },
    { label: 'Rejected Applications', value: dashboard?.rejected ?? 0, accent: 'bg-rose-500/10 text-rose-300' },
  ]

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center bg-slate-950 text-slate-400">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-3" />
        <p className="text-sm font-medium">Loading your application tracker...</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-8 bg-slate-950 text-slate-100 min-h-screen">
      <header className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Application Tracker</h1>
          <p className="text-sm text-slate-400 mt-1">Track every internship application, interview milestone and next follow-up from one place.</p>
        </div>
        <Link
          to="/jobs"
          className="inline-flex items-center justify-center px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/20"
        >
          Find Internships
        </Link>
      </header>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      <section className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {summaryCards.map((card) => (
          <div key={card.label} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
            <div className={`inline-flex px-2.5 py-1.5 rounded-full text-[11px] font-semibold ${card.accent}`}>
              {card.label}
            </div>
            <p className="text-3xl font-extrabold text-white mt-4">{card.value}</p>
          </div>
        ))}
      </section>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search applications..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-700 bg-slate-950 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-700 bg-slate-950 text-sm text-slate-300">
              <Filter className="w-4 h-4 text-slate-400" />
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="bg-transparent text-slate-200 outline-none">
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status} className="bg-slate-900">{status}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-700 bg-slate-950 text-sm text-slate-300">
              <CalendarClock className="w-4 h-4 text-slate-400" />
              <select value={sortBy} onChange={(event) => setSortBy(event.target.value)} className="bg-transparent text-slate-200 outline-none">
                <option value="latest" className="bg-slate-900">Latest Application</option>
                <option value="oldest" className="bg-slate-900">Oldest Application</option>
                <option value="upcoming_deadline" className="bg-slate-900">Upcoming Deadline</option>
                <option value="company" className="bg-slate-900">Company Name</option>
                <option value="status" className="bg-slate-900">Status</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3 border-b border-slate-800 pb-2">
        <button
          onClick={() => setSelectedTab('active')}
          className={`px-4 py-2 rounded-xl text-sm font-semibold ${selectedTab === 'active' ? 'bg-indigo-600 text-white' : 'bg-slate-900 text-slate-300 border border-slate-700'}`}
        >
          Active Applications
        </button>
        <button
          onClick={() => setSelectedTab('completed')}
          className={`px-4 py-2 rounded-xl text-sm font-semibold ${selectedTab === 'completed' ? 'bg-indigo-600 text-white' : 'bg-slate-900 text-slate-300 border border-slate-700'}`}
        >
          Completed Applications
        </button>
      </div>

      {reminders && (
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-amber-300 font-semibold text-sm"><BellRing className="w-4 h-4" /> Upcoming Deadlines</div>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              {(reminders.upcoming_deadlines || []).slice(0, 3).map((app) => (
                <li key={app.application_id} className="border-b border-slate-800 pb-2 last:border-0 last:pb-0">{app.company_name || app.company} — {new Date(app.application_deadline || app.deadline).toLocaleDateString()}</li>
              ))}
            </ul>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-emerald-300 font-semibold text-sm"><CalendarClock className="w-4 h-4" /> Scheduled Interviews</div>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              {(reminders.scheduled_interviews || []).slice(0, 3).map((app) => (
                <li key={app.application_id} className="border-b border-slate-800 pb-2 last:border-0 last:pb-0">{app.job_title} — {new Date(app.interview_date).toLocaleDateString()}</li>
              ))}
            </ul>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-cyan-300 font-semibold text-sm"><FileText className="w-4 h-4" /> Upcoming Follow-ups</div>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              {(reminders.upcoming_follow_ups || []).slice(0, 3).map((app) => (
                <li key={app.application_id} className="border-b border-slate-800 pb-2 last:border-0 last:pb-0">{app.company_name || app.company} — {new Date(app.next_follow_up_date).toLocaleDateString()}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {filteredApplications.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-10 text-center">
          <ClipboardList className="w-10 h-10 text-slate-500 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-white">No applications yet.</h2>
          <p className="text-sm text-slate-400 mt-2">Add internships from the Jobs page to start tracking your applications.</p>
          <button onClick={() => navigate('/jobs')} className="mt-5 px-4 py-2 rounded-xl bg-indigo-600 text-white font-semibold">Find Internships</button>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredApplications.map((app) => (
            <div key={app.application_id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="flex flex-col xl:flex-row xl:items-start justify-between gap-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <BriefcaseBusiness className="w-4 h-4 text-indigo-400" />
                    <p className="text-lg font-bold text-white">{app.company_name || app.company || 'Unspecified Company'}</p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-base font-semibold text-slate-200">{app.job_title}</p>
                    <p className="text-xs text-slate-400">{app.job_description || 'No description provided.'}</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                    <span>Applied: {app.application_date ? new Date(app.application_date).toLocaleDateString() : 'Not set'}</span>
                    <span>Deadline: {app.application_deadline || app.deadline ? new Date(app.application_deadline || app.deadline).toLocaleDateString() : 'Not set'}</span>
                    <span>Interview: {app.interview_date ? new Date(app.interview_date).toLocaleDateString() : 'Not scheduled'}</span>
                    <span>Follow-up: {app.next_follow_up_date ? new Date(app.next_follow_up_date).toLocaleDateString() : 'Not set'}</span>
                  </div>
                </div>

                <div className="min-w-[180px] space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                      {app.status}
                    </span>
                    <div className="flex items-center gap-2">
                      <button onClick={() => openEditor(app)} className="text-slate-300 hover:text-white" title="Edit application"><PencilLine className="w-4 h-4" /></button>
                      <button onClick={() => handleDelete(app.application_id)} className="text-rose-400 hover:text-rose-300" title="Delete application"><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </div>

                  <select
                    value={app.status}
                    onChange={(event) => handleStatusChange(app.application_id, event.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none"
                  >
                    {STATUS_OPTIONS.filter((status) => status !== 'All').map((status) => (
                      <option key={status} value={status} className="bg-slate-900">{status}</option>
                    ))}
                  </select>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <button onClick={() => openEditor(app)} className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200">View</button>
                    <button onClick={() => openEditor(app)} className="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white">Edit</button>
                    <button onClick={() => openResume(app)} className="px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white">View Resume</button>
                    <button onClick={() => openCoverLetter(app)} className="px-3 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white">Cover Letter</button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedApp && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="text-xs uppercase text-indigo-400 font-bold">Application Details</p>
                <h2 className="text-2xl font-bold text-white">{selectedApp.company_name || selectedApp.company}</h2>
              </div>
              <button onClick={() => setSelectedApp(null)} className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white"><X className="w-4 h-4" /></button>
            </div>

            <form onSubmit={handleSave} className="space-y-5">
              <div className="grid md:grid-cols-2 gap-4">
                <label className="space-y-2 text-sm text-slate-300">
                  <span>Company Name</span>
                  <input value={form.company_name} onChange={(event) => setForm({ ...form, company_name: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Job Title</span>
                  <input value={form.job_title} onChange={(event) => setForm({ ...form, job_title: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300 md:col-span-2">
                  <span>Job Description</span>
                  <textarea value={form.job_description} onChange={(event) => setForm({ ...form, job_description: event.target.value })} rows={4} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Application Date</span>
                  <input type="date" value={form.application_date} onChange={(event) => setForm({ ...form, application_date: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Application Deadline</span>
                  <input type="date" value={form.application_deadline} onChange={(event) => setForm({ ...form, application_deadline: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Status</span>
                  <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500">
                    {STATUS_OPTIONS.filter((status) => status !== 'All').map((status) => (
                      <option key={status} value={status}>{status}</option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Interview Date</span>
                  <input type="date" value={form.interview_date} onChange={(event) => setForm({ ...form, interview_date: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Interview Time</span>
                  <input type="time" value={form.interview_time} onChange={(event) => setForm({ ...form, interview_time: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Interview Status</span>
                  <select value={form.interview_status} onChange={(event) => setForm({ ...form, interview_status: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500">
                    {['Not Scheduled', 'Scheduled', 'Completed', 'Rescheduled', 'Cancelled'].map((status) => (
                      <option key={status} value={status}>{status}</option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Interview Type</span>
                  <input value={form.interview_type} onChange={(event) => setForm({ ...form, interview_type: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Phone, onsite, panel..." />
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Interview Outcome</span>
                  <select value={form.interview_outcome} onChange={(event) => setForm({ ...form, interview_outcome: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500">
                    {['Pending', 'Passed', 'Failed', 'Selected', 'Waiting for Result'].map((status) => (
                      <option key={status} value={status}>{status}</option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2 text-sm text-slate-300 md:col-span-2">
                  <span>Interview Notes</span>
                  <textarea value={form.interview_notes} onChange={(event) => setForm({ ...form, interview_notes: event.target.value })} rows={3} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300 md:col-span-2">
                  <span>Notes</span>
                  <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} rows={3} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300 md:col-span-2">
                  <span>Follow-up Information</span>
                  <textarea value={form.follow_up_information} onChange={(event) => setForm({ ...form, follow_up_information: event.target.value })} rows={3} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span>Next Follow-up Date</span>
                  <input type="date" value={form.next_follow_up_date} onChange={(event) => setForm({ ...form, next_follow_up_date: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500" />
                </label>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 justify-end pt-4 border-t border-slate-800">
                <button type="button" onClick={() => handleDelete(selectedApp.application_id)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-rose-700 bg-rose-950/60 px-4 py-2.5 text-sm font-semibold text-rose-200 hover:bg-rose-900/70">
                  <Trash2 className="w-4 h-4" /> Delete Application
                </button>
                <button type="submit" disabled={saving} className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-70">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />} Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
