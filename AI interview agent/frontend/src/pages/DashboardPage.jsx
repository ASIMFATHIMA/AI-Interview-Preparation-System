import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { profileAPI, resumeAPI } from '../services/api'
import Alert from '../components/Alert'
import {
  User,
  GraduationCap,
  Building,
  MapPin,
  FileText,
  Upload,
  Edit3,
  Cpu,
  Clock,
  CheckCircle2,
  Sparkles,
  Loader2,
  AlertCircle,
  ExternalLink,
} from 'lucide-react'

export default function DashboardPage() {
  const { user, refreshUser } = useAuth()
  const navigate = useNavigate()

  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [parseNotice, setParseNotice] = useState(null)
  const [parsingId, setParsingId] = useState(null)

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      await refreshUser()
      const resumeData = await resumeAPI.listResumes()
      setResumes(resumeData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  const handleParseResume = async (resumeId) => {
    setParsingId(resumeId)
    try {
      const res = await resumeAPI.reparseResume(resumeId)
      await refreshUser()
      setParseNotice(res.message || 'Resume parsed successfully.')
    } catch (err) {
      setParseNotice(err.response?.data?.detail || 'Failed to parse resume.')
    } finally {
      setParsingId(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center bg-slate-950 text-slate-400">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-3" />
        <p className="text-sm font-medium">Loading your student dashboard...</p>
      </div>
    )
  }

  const latestResume = resumes.length > 0 ? resumes[0] : null

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8 bg-slate-950 text-slate-100">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-950 via-slate-900 to-cyan-950 border border-slate-800/80 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles className="w-3.5 h-3.5" />
              <span> Profile Foundation</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">
              Welcome, {user?.name || 'Student'}!
            </h1>
            <p className="text-sm text-slate-400 max-w-xl">
              Manage your academic profile and uploaded resumes. Your profile will power intelligent AI internship matching and mock interview simulations.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/profile"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition cursor-pointer"
            >
              <Edit3 className="w-4 h-4" />
              <span>Edit Profile</span>
            </Link>
            <Link
              to="/profile#resume"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Resume</span>
            </Link>
          </div>
        </div>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {parseNotice && (
        <Alert
          type="info"
          message={parseNotice}
          onClose={() => setParseNotice(null)}
        />
      )}

      {/* Main Grid: Profile Overview & Resume Summary */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* Card 1: Student Profile & Education */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5 text-indigo-400">
                <User className="w-5 h-5" />
                <h2 className="text-base font-bold text-white">Student Profile</h2>
              </div>
              <Link
                to="/profile"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
              >
                Edit Details <ExternalLink className="w-3 h-3" />
              </Link>
            </div>

            <div className="mt-6 space-y-4 text-xs">
              <div className="flex items-start justify-between py-2 border-b border-slate-800/60">
                <span className="text-slate-400 font-medium">Full Name</span>
                <span className="text-white font-semibold">{user?.name || 'Not provided'}</span>
              </div>

              <div className="flex items-start justify-between py-2 border-b border-slate-800/60">
                <span className="text-slate-400 font-medium">Email Address</span>
                <span className="text-slate-200 font-mono">{user?.email}</span>
              </div>

              <div className="flex items-start justify-between py-2 border-b border-slate-800/60">
                <span className="text-slate-400 font-medium flex items-center gap-1.5">
                  <GraduationCap className="w-3.5 h-3.5 text-indigo-400" /> Degree & Major
                </span>
                <span className="text-white text-right max-w-[200px]">
                  {user?.degree ? `${user.degree} in ${user.field_of_study || ''}` : 'Not specified'}
                </span>
              </div>

              <div className="flex items-start justify-between py-2 border-b border-slate-800/60">
                <span className="text-slate-400 font-medium flex items-center gap-1.5">
                  <Building className="w-3.5 h-3.5 text-indigo-400" /> Institution
                </span>
                <span className="text-white text-right max-w-[200px]">{user?.institution || 'Not specified'}</span>
              </div>

              <div className="flex items-start justify-between py-2">
                <span className="text-slate-400 font-medium flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400" /> Location
                </span>
                <span className="text-white">{user?.location || 'Not specified'}</span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-500">
              Profile completeness: {user?.institution && user?.degree ? '100%' : '60%'}
            </span>
            <Link
              to="/profile"
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium transition cursor-pointer"
            >
              Update Profile Info
            </Link>
          </div>
        </div>

        {/* Card 2: Resume Status */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5 text-cyan-400">
                <FileText className="w-5 h-5" />
                <h2 className="text-base font-bold text-white">Active Resume</h2>
              </div>
              <span className="text-xs text-slate-400">
                {resumes.length} {resumes.length === 1 ? 'file' : 'files'} uploaded
              </span>
            </div>

            {latestResume ? (
              <div className="mt-6 space-y-4">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 font-bold text-xs">
                        {latestResume.file_type}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white truncate max-w-[200px]">
                          {latestResume.original_name}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {(latestResume.file_size / 1024).toFixed(1)} KB • Uploaded on{' '}
                          {new Date(latestResume.uploaded_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>

                    <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {latestResume.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-slate-900 text-xs">
                    <button
                      onClick={() => handleParseResume(latestResume.resume_id)}
                      disabled={parsingId === latestResume.resume_id}
                      className="flex-1 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 font-medium transition cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <Cpu className="w-3.5 h-3.5" />
                      <span>{parsingId === latestResume.resume_id ? 'Parsing resume...' : 'Parse Resume'}</span>
                    </button>
                    <Link
                      to="/profile#resume"
                      className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                    >
                      Manage
                    </Link>
                  </div>
                </div>

                <div className="p-3 bg-slate-950/40 rounded-xl border border-slate-800/60 text-xs text-slate-400 flex items-start gap-2">
                  <Clock className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  <span>
                    Parsed resume information is stored securely and shown in your profile.
                  </span>
                </div>
              </div>
            ) : (
              <div className="mt-8 text-center py-6 space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-slate-800 text-slate-500 flex items-center justify-center mx-auto">
                  <FileText className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-white">No Resume Uploaded</div>
                  <p className="text-xs text-slate-400 max-w-xs mx-auto">
                    Upload your resume in PDF or DOCX format to get started.
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-end">
            <Link
              to="/profile#resume"
              className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs transition cursor-pointer shadow-lg shadow-cyan-600/20 flex items-center gap-1.5"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{latestResume ? 'Upload / Replace Resume' : 'Upload Resume'}</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
