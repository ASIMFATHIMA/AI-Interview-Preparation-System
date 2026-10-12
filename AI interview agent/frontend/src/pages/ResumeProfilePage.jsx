import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Award, BriefcaseBusiness, Code2, GraduationCap, Loader2, UserRound } from 'lucide-react'
import Alert from '../components/Alert'
import { resumeAPI } from '../services/api'

export default function ResumeProfilePage() {
  const { candidateId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    resumeAPI.getProfile(candidateId).then(setData).catch((err) => {
      setError(err.response?.data?.detail || 'Unable to load your resume profile.')
    })
  }, [candidateId])

  if (error) return <div className="max-w-5xl mx-auto px-6 py-10"><Alert type="error" message={error} /></div>
  if (!data) return <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center bg-slate-950"><Loader2 className="animate-spin text-cyan-400" /></div>

  const profile = data.profile
  return <div className="max-w-6xl mx-auto px-6 py-10 space-y-8 bg-slate-950 text-slate-100">
    <div><p className="text-xs uppercase tracking-widest text-cyan-400">Resume Profile</p><h1 className="text-3xl font-extrabold text-white mt-2">{profile.name || 'Candidate Profile'}</h1><p className="text-sm text-slate-400 mt-1">{data.resume.original_name} · {data.resume.status}</p></div>
    <div className="grid lg:grid-cols-2 gap-6">
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4"><h2 className="font-bold text-white flex items-center gap-2"><UserRound className="w-4 h-4 text-cyan-400" />Personal Information</h2><div className="grid sm:grid-cols-2 gap-3 text-sm"><div><span className="text-slate-500">Email</span><p>{profile.email || 'Not provided'}</p></div><div><span className="text-slate-500">Phone</span><p>{profile.phone || 'Not provided'}</p></div><div><span className="text-slate-500">Location</span><p>{profile.location || 'Not provided'}</p></div></div></section>
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4"><h2 className="font-bold text-white flex items-center gap-2"><Code2 className="w-4 h-4 text-emerald-400" />Skills</h2><div className="flex flex-wrap gap-2">{profile.skills.length ? profile.skills.map((skill) => <span key={skill} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 text-xs">{skill}</span>) : <span className="text-sm text-slate-500">No skills extracted.</span>}</div></section>
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4"><h2 className="font-bold text-white flex items-center gap-2"><GraduationCap className="w-4 h-4 text-indigo-400" />Education</h2>{profile.education.length ? profile.education.map((item, index) => <div key={index} className="border-b border-slate-800 pb-3 last:border-0"><p className="font-semibold">{item.degree || 'Degree'}</p><p className="text-sm text-slate-400">{item.institution || 'Institution not provided'}</p><p className="text-xs text-slate-500">{item.start_year || ''}{item.end_year ? ` - ${item.end_year}` : ''}</p></div>) : <span className="text-sm text-slate-500">No education extracted.</span>}</section>
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4"><h2 className="font-bold text-white flex items-center gap-2"><BriefcaseBusiness className="w-4 h-4 text-amber-400" />Experience & Projects</h2>{profile.experience.map((item, index) => <div key={`experience-${index}`} className="border-b border-slate-800 pb-3"><p className="font-semibold">{item.role || 'Experience'}</p><p className="text-sm text-slate-400">{item.company || 'Company not provided'}</p><p className="text-xs text-slate-500">{item.description || ''}</p></div>)}{profile.projects.map((item, index) => <div key={`project-${index}`}><p className="font-semibold">{item.project_name || 'Project'}</p><p className="text-sm text-slate-400">{item.description || ''}</p></div>)}{!profile.experience.length && !profile.projects.length && <span className="text-sm text-slate-500">No experience or projects extracted.</span>}</section>
    </div>
    <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6"><h2 className="font-bold text-white flex items-center gap-2 mb-4"><Award className="w-4 h-4 text-amber-400" />Next Career Actions</h2><div className="flex flex-wrap gap-3"><Link to="/jobs" className="px-4 py-2 rounded-xl bg-cyan-600 text-sm font-semibold">Job Matching</Link><Link to="/skill-gap" className="px-4 py-2 rounded-xl bg-indigo-600 text-sm font-semibold">Skill Gap Analysis</Link><Link to="/cover-letter" className="px-4 py-2 rounded-xl bg-emerald-600 text-sm font-semibold">Cover Letter</Link><Link to="/interview" className="px-4 py-2 rounded-xl bg-amber-600 text-sm font-semibold">Mock Interview</Link><Link to="/career-assistant" className="px-4 py-2 rounded-xl bg-slate-700 text-sm font-semibold">Career Assistant</Link></div></section>
  </div>
}