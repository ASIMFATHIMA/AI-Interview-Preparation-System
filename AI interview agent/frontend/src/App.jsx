import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { JobProvider } from './context/JobContext'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ProfilePage from './pages/ProfilePage'
import JobsPage from './pages/JobsPage'
import SkillGapPage from './pages/SkillGapPage'
import CoverLetterPage from './pages/CoverLetterPage'
import InterviewPage from './pages/InterviewPage'
import CareerAssistantPage from './pages/CareerAssistantPage'
import ResumeProfilePage from './pages/ResumeProfilePage'
import ResumeCustomizationPage from './pages/ResumeCustomizationPage'
import ApplicationTrackerPage from './pages/ApplicationTrackerPage'

function AppRoutes() {
  const { user, loading } = useAuth()

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      <Navbar />

      <main className="flex-1">
        <Routes>
          {/* Public Authentication Routes */}
          <Route
            path="/login"
            element={user && !loading ? <Navigate to="/dashboard" replace /> : <LoginPage />}
          />
          <Route
            path="/register"
            element={user && !loading ? <Navigate to="/dashboard" replace /> : <RegisterPage />}
          />

          {/* Protected Application Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route path="/resume/profile/:candidateId" element={<ProtectedRoute><ResumeProfilePage /></ProtectedRoute>} />
          <Route path="/jobs" element={<ProtectedRoute><JobsPage /></ProtectedRoute>} />
          <Route path="/application-tracker" element={<ProtectedRoute><ApplicationTrackerPage /></ProtectedRoute>} />
          <Route path="/skill-gap" element={<ProtectedRoute><SkillGapPage /></ProtectedRoute>} />

          {/* Resume Customization — linked from SkillGapPage as /resume-customization */}
          <Route path="/resume-customization" element={<ProtectedRoute><ResumeCustomizationPage /></ProtectedRoute>} />
          <Route path="/resume/customize" element={<ProtectedRoute><ResumeCustomizationPage /></ProtectedRoute>} />

          <Route path="/cover-letter" element={<ProtectedRoute><CoverLetterPage /></ProtectedRoute>} />
          <Route path="/interview" element={<ProtectedRoute><InterviewPage /></ProtectedRoute>} />
          <Route path="/career-assistant" element={<ProtectedRoute><CareerAssistantPage /></ProtectedRoute>} />

          {/* Default Redirection */}
          <Route
            path="/"
            element={<Navigate to={user ? '/dashboard' : '/login'} replace />}
          />
          <Route
            path="*"
            element={<Navigate to="/dashboard" replace />}
          />
        </Routes>
      </main>

      <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500 bg-slate-950">
        AI Career Companion Agent &bull; Milestone 3 — Skill Gap &middot; Resume &middot; Cover Letter &middot; Interview &middot; Career Assistant
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <JobProvider>
        <Router>
          <AppRoutes />
        </Router>
      </JobProvider>
    </AuthProvider>
  )
}
