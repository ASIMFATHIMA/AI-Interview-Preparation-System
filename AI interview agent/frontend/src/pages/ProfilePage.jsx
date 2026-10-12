import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { API_BASE_URL, profileAPI, resumeAPI, parsedResumeAPI } from '../services/api'
import Alert from '../components/Alert'
import {
  User,
  Mail,
  Phone,
  MapPin,
  GraduationCap,
  BookOpen,
  Building,
  Save,
  Upload,
  FileText,
  Trash2,
  RefreshCw,
  Loader2,
  CheckCircle2,
  FileCheck,
  Eye,
  Info,
  Briefcase,
  Code2,
  Award,
  Star,
} from 'lucide-react'

export default function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const navigate = useNavigate()

  // Profile Form state
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    phone: '',
    location: '',
    degree: '',
    field_of_study: '',
    institution: '',
    github_url: '',
    linkedin_url: '',
    portfolio_url: '',
  })
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileSuccess, setProfileSuccess] = useState(null)
  const [profileError, setProfileError] = useState(null)

  // Resumes state
  const [resumes, setResumes] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadStage, setUploadStage] = useState('')
  const [resumeSuccess, setResumeSuccess] = useState(null)
  const [resumeError, setResumeError] = useState(null)
  const [inspectResume, setInspectResume] = useState(null)

  // Parsed resume data state
  const [parsedData, setParsedData] = useState(null)
  const [parsedLoading, setParsedLoading] = useState(false)
  const [parsedError, setParsedError] = useState(null)

  const loadData = async () => {
    try {
      const p = await profileAPI.getProfile()
      setProfile({
        name: p.name || '',
        email: p.email || '',
        phone: p.phone || '',
        location: p.location || '',
        degree: p.degree || '',
        field_of_study: p.field_of_study || '',
        institution: p.institution || '',
        github_url: p.github_url || '',
        linkedin_url: p.linkedin_url || '',
        portfolio_url: p.portfolio_url || '',
      })

      const rList = await resumeAPI.listResumes()
      setResumes(rList)

      try {
        const parsed = await parsedResumeAPI.getParsedResume()
        setParsedData(parsed.data || null)
      } catch (err) {
        setParsedError(err.response?.data?.detail || 'Failed to load parsed resume data.')
      }
    } catch (err) {
      setProfileError(err.response?.data?.detail || 'Failed to load profile data.')
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (window.location.hash === '#resume') {
      window.requestAnimationFrame(() => {
        document.getElementById('resume')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    }
  }, [])

  const handleProfileChange = (e) => {
    setProfile({
      ...profile,
      [e.target.name]: e.target.value,
    })
    if (profileSuccess) setProfileSuccess(null)
    if (profileError) setProfileError(null)
  }

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setProfileLoading(true)
    setProfileSuccess(null)
    setProfileError(null)

    try {
      const updated = await profileAPI.updateProfile({
        name: profile.name.trim(),
        phone: profile.phone?.trim() || null,
        location: profile.location?.trim() || null,
        degree: profile.degree?.trim() || null,
        field_of_study: profile.field_of_study?.trim() || null,
        institution: profile.institution?.trim() || null,
        github_url: profile.github_url?.trim() || null,
        linkedin_url: profile.linkedin_url?.trim() || null,
        portfolio_url: profile.portfolio_url?.trim() || null,
      })
      await refreshUser()
      setProfileSuccess('Profile details saved successfully.')
    } catch (err) {
      setProfileError(err.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setProfileLoading(false)
    }
  }

  const handleUploadResume = async (e) => {
    e.preventDefault()
    if (!selectedFile) {
      setResumeError('Please select a PDF or DOCX resume file first.')
      return
    }

    setUploadLoading(true)
    setUploadStage('Uploading Resume...')
    setResumeSuccess(null)
    setResumeError(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      setUploadStage('Analyzing Resume...')
      const res = await resumeAPI.uploadResume(formData)
      if (!res.success || res.parse_error || !res.candidate_id || !res.resume_id) {
        throw new Error(res.parse_error || 'Resume processing did not complete successfully.')
      }
      setUploadStage('Saving Profile...')
      setResumeSuccess(`Uploaded "${res.resume.original_name}" successfully. Opening your resume profile...`)
      setParsedData(res.parsed || null)
      setSelectedFile(null)
      navigate(`/resume/profile/${res.candidate_id}`)
    } catch (err) {
      if (err.response?.data?.detail) {
        setResumeError(err.response.data.detail)
      } else if (!err.response) {
        setResumeError(
          `Unable to connect to the server. Please make sure FastAPI is running at ${API_BASE_URL}/.`
        )
      } else {
        setResumeError(`Resume upload failed (HTTP ${err.response.status}).`)
      }
    } finally {
      setUploadLoading(false)
      setUploadStage('')
    }
  }

  const handleDeleteResume = async (resumeId) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) return

    try {
      await resumeAPI.deleteResume(resumeId)
      setResumeSuccess('Resume deleted successfully.')
      setResumes(resumes.filter((r) => r.resume_id !== resumeId))
      if (inspectResume?.resume_id === resumeId) {
        setInspectResume(null)
      }
    } catch (err) {
      setResumeError(err.response?.data?.detail || 'Failed to delete resume.')
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-10 bg-slate-950 text-slate-100">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Student Profile & Resume</h1>
        <p className="text-sm text-slate-400 mt-1">
          Keep your educational background, contact details, and resume up-to-date.
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Section 1: Professional Profile Form (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5 text-indigo-400">
                <User className="w-5 h-5" />
                <h2 className="text-lg font-bold text-white">Personal & Academic Details</h2>
              </div>
              <span className="text-xs text-slate-500 font-mono">ID: #{user?.student_id}</span>
            </div>

            {profileSuccess && (
              <Alert type="success" message={profileSuccess} onClose={() => setProfileSuccess(null)} />
            )}
            {profileError && (
              <Alert type="error" message={profileError} onClose={() => setProfileError(null)} />
            )}

            <form onSubmit={handleSaveProfile} className="space-y-5 text-xs">
              {/* Row 1: Full Name & Email */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1.5">
                    Full Name <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
                    <input
                      type="text"
                      name="name"
                      required
                      placeholder="e.g. Student Name"
                      value={profile.name}
                      onChange={handleProfileChange}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1.5">
                    Email Address (Account ID)
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-600 absolute left-3.5 top-2.5" />
                    <input
                      type="email"
                      name="email"
                      disabled
                      value={profile.email}
                      className="w-full bg-slate-950/50 border border-slate-800/60 rounded-xl pl-10 pr-3 py-2 text-slate-400 cursor-not-allowed font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Row 2: Phone & Location */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1.5">Phone Number</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
                    <input
                      type="tel"
                      name="phone"
                      placeholder="e.g. 9876543210"
                      value={profile.phone}
                      onChange={handleProfileChange}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1.5">Location</label>
                  <div className="relative">
                    <MapPin className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
                    <input
                      type="text"
                      name="location"
                      placeholder="e.g. Chennai, India"
                      value={profile.location}
                      onChange={handleProfileChange}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>
              </div>

              {/* Row 3: Degree & Field of Study */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1.5">Degree</label>
                  <div className="relative">
                    <GraduationCap className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
                    <input
                      type="text"
                      name="degree"
                      placeholder="e.g. B.Tech / B.E."
                      value={profile.degree}
                      onChange={handleProfileChange}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1.5">Field of Study</label>
                  <div className="relative">
                    <BookOpen className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
                    <input
                      type="text"
                      name="field_of_study"
                      placeholder="e.g. Artificial Intelligence and Data Science"
                      value={profile.field_of_study}
                      onChange={handleProfileChange}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>
              </div>

              {/* Row 4: Institution */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1.5">College / Institution</label>
                <div className="relative">
                  <Building className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
                  <input
                    type="text"
                    name="institution"
                    placeholder="e.g. ABC College of Engineering & Technology"
                    value={profile.institution}
                    onChange={handleProfileChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Professional Links */}
              <div className="pt-4 border-t border-slate-800 space-y-4">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Online Presence & Portfolio
                </h3>

                <div>
                  <label className="block text-slate-400 font-medium mb-1">GitHub Profile URL</label>
                  <input
                    type="url"
                    name="github_url"
                    placeholder="https://github.com/your-username"
                    value={profile.github_url}
                    onChange={handleProfileChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono text-xs"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 font-medium mb-1">LinkedIn Profile URL</label>
                  <input
                    type="url"
                    name="linkedin_url"
                    placeholder="https://linkedin.com/in/your-profile"
                    value={profile.linkedin_url}
                    onChange={handleProfileChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono text-xs"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 font-medium mb-1">Personal Portfolio / Website</label>
                  <input
                    type="url"
                    name="portfolio_url"
                    placeholder="https://yourportfolio.dev"
                    value={profile.portfolio_url}
                    onChange={handleProfileChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono text-xs"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={profileLoading}
                  className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition cursor-pointer shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center gap-2"
                >
                  {profileLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Saving Profile...</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      <span>Save Profile</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Parsed Resume Data Section */}
          {parsedData && (
            <div className="bg-slate-900/80 border border-emerald-900/40 rounded-2xl p-6 shadow-xl space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="text-sm font-bold text-white flex items-center gap-2 text-emerald-400">
                  <FileCheck className="w-4 h-4" />
                  <span>Resume Extracted Information</span>
                </h3>
                {parsedError && (
                  <span className="text-[10px] text-amber-400">{parsedError}</span>
                )}
              </div>

              {parsedLoading && (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading extracted data...
                </div>
              )}

              {/* Personal Information */}
              {(parsedData.name || parsedData.email || parsedData.phone) && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-indigo-400" /> Personal Information
                  </h4>
                  <div className="grid sm:grid-cols-2 gap-2 text-xs">
                    {parsedData.name && (
                      <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Name</span>
                        <span className="text-white font-medium">{parsedData.name}</span>
                      </div>
                    )}
                    {parsedData.email && (
                      <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Email</span>
                        <span className="text-white font-medium">{parsedData.email}</span>
                      </div>
                    )}
                    {parsedData.phone && (
                      <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Phone</span>
                        <span className="text-white font-medium">{parsedData.phone}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Skills */}
              {parsedData.skills && parsedData.skills.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Code2 className="w-3.5 h-3.5 text-cyan-400" /> Skills
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {parsedData.skills.map((skill, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[11px] font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Education */}
              {parsedData.education && parsedData.education.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <GraduationCap className="w-3.5 h-3.5 text-indigo-400" /> Education
                  </h4>
                  <div className="space-y-2">
                    {parsedData.education.map((edu, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs">
                        <div className="text-white font-medium">{edu.degree || 'Degree'}</div>
                        {edu.institution && <div className="text-slate-400">{edu.institution}</div>}
                        {(edu.start_year || edu.end_year) && (
                          <div className="text-slate-500 text-[10px]">{edu.start_year || ''} - {edu.end_year || ''}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience */}
              {parsedData.experience && parsedData.experience.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-emerald-400" /> Experience
                  </h4>
                  <div className="space-y-2">
                    {parsedData.experience.map((exp, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs">
                        <div className="text-white font-medium">{exp.role || 'Role'}</div>
                        <div className="text-slate-400">{exp.company}</div>
                        {(exp.start_date || exp.end_date) && (
                          <div className="text-slate-500 text-[10px]">{exp.start_date || ''} - {exp.end_date || 'Present'}</div>
                        )}
                        {exp.description && <div className="text-slate-400 mt-1 text-[11px]">{exp.description}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Projects */}
              {parsedData.projects && parsedData.projects.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Code2 className="w-3.5 h-3.5 text-purple-400" /> Projects
                  </h4>
                  <div className="space-y-2">
                    {parsedData.projects.map((proj, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs">
                        <div className="text-white font-medium">{proj.project_name || 'Project'}</div>
                        {proj.technologies && <div className="text-cyan-400 text-[10px]">{proj.technologies}</div>}
                        {proj.description && <div className="text-slate-400 mt-1 text-[11px]">{proj.description}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Certifications */}
              {parsedData.certifications && parsedData.certifications.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-amber-400" /> Certifications
                  </h4>
                  <div className="space-y-2">
                    {parsedData.certifications.map((cert, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs">
                        <div className="text-white font-medium">{cert.certification_name || 'Certification'}</div>
                        {cert.organization && <div className="text-slate-400">{cert.organization}</div>}
                        {cert.year && <div className="text-slate-500 text-[10px]">{cert.year}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Achievements */}
              {parsedData.achievements && parsedData.achievements.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Star className="w-3.5 h-3.5 text-yellow-400" /> Achievements
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
                    {parsedData.achievements.map((ach, idx) => (
                      <li key={idx}>{ach}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

        </div>

        {/* Section 2: Resume Section (1 col) */}
        <div id="resume" className="space-y-6">
          {/* Upload Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            <div className="flex items-center gap-2 text-cyan-400 pb-3 border-b border-slate-800">
              <Upload className="w-5 h-5" />
              <h2 className="text-base font-bold text-white">Upload Resume</h2>
            </div>

            {resumeSuccess && (
              <Alert type="success" message={resumeSuccess} onClose={() => setResumeSuccess(null)} />
            )}
            {resumeError && (
              <Alert type="error" message={resumeError} onClose={() => setResumeError(null)} />
            )}

            <form onSubmit={handleUploadResume} className="space-y-4 text-xs">
              <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-2xl p-6 text-center transition bg-slate-950/40">
                <FileText className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                <label className="block text-slate-300 font-semibold cursor-pointer">
                  <span>{selectedFile ? selectedFile.name : 'Choose File'}</span>
                  <input
                    type="file"
                    accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    onChange={(e) => {
                      if (e.target.files?.[0]) setSelectedFile(e.target.files[0])
                    }}
                    className="hidden"
                  />
                </label>
                <p className="text-[11px] text-slate-500 mt-1">PDF or DOCX • Maximum 5 MB</p>
              </div>

              <button
                type="submit"
                disabled={uploadLoading || !selectedFile}
                className="w-full py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition cursor-pointer disabled:opacity-40 flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/20"
              >
                {uploadLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                      <span>{uploadStage || 'Processing Resume...'}</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Upload Resume</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Uploaded Resumes List */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 text-indigo-400">
                <FileCheck className="w-4 h-4" />
                <span>My Resumes ({resumes.length})</span>
              </h3>
            </div>

            {resumes.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-xs">
                No resumes uploaded yet. Upload your PDF or DOCX file above.
              </div>
            ) : (
              <div className="space-y-3">
                {resumes.map((r) => (
                  <div
                    key={r.resume_id}
                    className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2 hover:border-slate-700 transition"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="w-8 h-8 rounded-lg bg-indigo-950 border border-indigo-800/50 flex items-center justify-center font-bold text-[10px] text-indigo-300">
                          {r.file_type}
                        </span>
                        <div>
                          <div className="text-xs font-semibold text-white truncate max-w-[150px]">
                            {r.original_name}
                          </div>
                          <div className="text-[10px] text-slate-500">
                            {(r.file_size / 1024).toFixed(1)} KB •{' '}
                            {new Date(r.uploaded_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>

                      <span className="px-2 py-0.5 rounded text-[9px] font-mono uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {r.status}
                      </span>
                    </div>

                    {/* Action Buttons: View, Delete, Replace */}
                    <div className="flex items-center justify-end gap-1.5 pt-2 border-t border-slate-900 text-[11px]">
                      <button
                        onClick={() => setInspectResume(r)}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3" />
                        <span>View</span>
                      </button>

                      <label className="px-2.5 py-1 rounded-lg bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-900/40 transition cursor-pointer flex items-center gap-1">
                        <RefreshCw className="w-3 h-3" />
                        <span>Replace</span>
                        <input
                          type="file"
                          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                          onChange={(e) => {
                            if (e.target.files?.[0]) {
                              setSelectedFile(e.target.files[0])
                              window.scrollTo({ top: 0, behavior: 'smooth' })
                            }
                          }}
                          className="hidden"
                        />
                      </label>

                      <button
                        onClick={() => handleDeleteResume(r.resume_id)}
                        className="px-2 py-1 rounded-lg bg-rose-950/60 hover:bg-rose-900/80 text-rose-400 border border-rose-900/40 transition cursor-pointer"
                        title="Delete Resume"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Inspect Modal / Box */}
            {inspectResume && (
              <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-indigo-900/40 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-indigo-300 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5" /> Resume Metadata
                  </span>
                  <button
                    onClick={() => setInspectResume(null)}
                    className="text-slate-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>
                <div className="space-y-1 font-mono text-[11px] text-slate-300">
                  <div><strong>ID:</strong> #{inspectResume.resume_id}</div>
                  <div><strong>Original Name:</strong> {inspectResume.original_name}</div>
                  <div><strong>Stored Name:</strong> {inspectResume.stored_name}</div>
                  <div><strong>Type:</strong> {inspectResume.file_type}</div>
                  <div><strong>Size:</strong> {inspectResume.file_size} bytes</div>
                  <div><strong>Status:</strong> {inspectResume.status}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
