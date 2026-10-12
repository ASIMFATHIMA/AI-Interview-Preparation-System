import React, { createContext, useContext, useState, useEffect } from 'react'

const JobContext = createContext(null)

export function JobProvider({ children }) {
  const [selectedJob, setSelectedJobState] = useState(() => {
    try {
      const saved = localStorage.getItem('selected_job')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  const setSelectedJob = (job) => {
    setSelectedJobState(job)
    try {
      if (job) {
        localStorage.setItem('selected_job', JSON.stringify(job))
        localStorage.setItem('selected_job_id', String(job.job_id || ''))
      } else {
        localStorage.removeItem('selected_job')
        localStorage.removeItem('selected_job_id')
      }
    } catch (e) {
      console.error('Failed to save selected job to localStorage', e)
    }
  }

  const clearSelectedJob = () => setSelectedJob(null)

  return (
    <JobContext.Provider
      value={{
        selectedJob,
        selectedJobId: selectedJob?.job_id || null,
        setSelectedJob,
        clearSelectedJob,
      }}
    >
      {children}
    </JobContext.Provider>
  )
}

export function useSelectedJob() {
  const context = useContext(JobContext)
  if (!context) {
    throw new Error('useSelectedJob must be used within a JobProvider')
  }
  return context
}

export default JobContext
