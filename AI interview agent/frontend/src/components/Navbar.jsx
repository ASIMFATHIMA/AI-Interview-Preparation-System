import React from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Layers, LayoutDashboard, User, LogOut, BriefcaseBusiness, MessageCircle, Mic2, ClipboardList } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path) => location.pathname === path

  return (
    <header className="border-b border-slate-800/80 bg-slate-900/70 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to="/dashboard" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform duration-200">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold bg-gradient-to-r from-white via-slate-200 to-indigo-200 bg-clip-text text-transparent">
              AI Career Companion
            </h1>
            <p className="text-[11px] text-slate-400">Student Profile & Internship Agent</p>
          </div>
        </Link>

        {/* Navigation Links & User Actions */}
        {user ? (
          <div className="flex items-center gap-4">
            <nav className="flex items-center gap-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800 text-xs">
              <Link
                to="/dashboard"
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium transition ${
                  isActive('/dashboard')
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                Dashboard
              </Link>
              <Link
                to="/profile"
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium transition ${
                  isActive('/profile')
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <User className="w-3.5 h-3.5" />
                Profile & Resume
              </Link>
              <Link
                to="/profile#resume"
                className={`hidden md:flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium transition ${location.hash === '#resume' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'}`}
              >
                Resume Upload
              </Link>
              <Link
                to="/jobs"
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium transition ${isActive('/jobs') ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'}`}
              >
                <BriefcaseBusiness className="w-3.5 h-3.5" /> Jobs
              </Link>
              <Link
                to="/application-tracker"
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium transition ${isActive('/application-tracker') ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'}`}
              >
                <ClipboardList className="w-3.5 h-3.5" /> Application Tracker
              </Link>
              <Link
                to="/skill-gap"
                className={`hidden lg:flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium transition ${isActive('/skill-gap') ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'}`}
              >
                Skill Gaps
              </Link>
              <Link
                to="/interview"
                className={`hidden lg:flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium transition ${isActive('/interview') ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'}`}
              >
                <Mic2 className="w-3.5 h-3.5" /> Interview
              </Link>
              <Link
                to="/career-assistant"
                className={`hidden xl:flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium transition ${isActive('/career-assistant') ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'}`}
              >
                <MessageCircle className="w-3.5 h-3.5" /> Assistant
              </Link>
            </nav>

            <div className="hidden sm:flex items-center gap-2 pl-2 border-l border-slate-800">
              <div className="text-right">
                <div className="text-xs font-semibold text-white">{user.name}</div>
                <div className="text-[10px] text-slate-400 truncate max-w-[140px]">{user.email}</div>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-2 rounded-xl bg-slate-800/80 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 border border-slate-700 hover:border-rose-800/60 transition cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 text-xs">
            <Link
              to="/login"
              className="text-slate-300 hover:text-white font-medium px-3 py-1.5 rounded-lg transition"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-xl shadow-lg shadow-indigo-600/20 transition"
            >
              Create Account
            </Link>
          </div>
        )}
      </div>
    </header>
  )
}
