import axios from 'axios'

export const API_BASE_URL = import.meta.env.DEV
  ? '/api'
  : (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

// Create centralized Axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: Attach JWT Bearer token if available
api.interceptors.request.use(
  (config) => {
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: Extract clean error messages and handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // If token is invalid or expired and not on login/register, clear and redirect
    if (error.response?.status === 401) {
      const isAuthEndpoint =
        error.config?.url?.includes('/auth/login') ||
        error.config?.url?.includes('/auth/register')
      if (!isAuthEndpoint) {
        localStorage.removeItem('token')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// Authentication APIs
export const authAPI = {
  register: async (data) => {
    const response = await api.post('/auth/register', data)
    return response.data
  },
  login: async (data) => {
    const response = await api.post('/auth/login', data)
    return response.data
  },
  getMe: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

// Student Profile APIs
export const profileAPI = {
  getProfile: async () => {
    const response = await api.get('/profile/me')
    return response.data
  },
  updateProfile: async (data) => {
    const response = await api.put('/profile/me', data)
    return response.data
  },
}

// Resume Upload & Management APIs
export const resumeAPI = {
  /**
   * Upload a resume file (PDF/DOCX). Returns upload metadata + parsed data.
   * @param {FormData} formData - FormData with 'file' key
   */
  uploadResume: async (formData) => {
    // Let the browser set Content-Type so it includes the multipart boundary.
    const response = await api.post('/resume/upload', formData)
    return response.data
  },

  getProfile: async (candidateId) => {
    const response = await api.get(`/resume/profile/${candidateId}`)
    return response.data
  },

  listResumes: async () => {
    const response = await api.get('/resume')
    return response.data
  },

  getResume: async (resumeId) => {
    const response = await api.get(`/resume/${resumeId}`)
    return response.data
  },

  deleteResume: async (resumeId) => {
    const response = await api.delete(`/resume/${resumeId}`)
    return response.data
  },

  /**
   * Re-parse an already-uploaded resume by its ID.
   * Returns updated structured parsed data.
   */
  reparseResume: async (resumeId) => {
    const response = await api.post(`/resume/${resumeId}/parse`)
    return response.data
  },

  /**
   * M3.2 Resume Customization Agent
   */
  customize: async (data) => (await api.post('/resume/customize', data)).data,
  customizeHistory: async () => (await api.get('/resume/customize/history')).data,
}

// Parsed Resume Data APIs
export const parsedResumeAPI = {
  /**
   * Get all structured parsed resume data (skills, education, experience,
   * projects, certifications, achievements) for the authenticated student.
   */
  getParsedResume: async () => {
    const response = await api.get('/resume-parsed/me')
    return response.data
  },
}

export const jobsAPI = {
  list: async () => (await api.get('/jobs')).data,
  create: async (data) => (await api.post('/jobs', data)).data,
  search: async (data) => (await api.post('/jobs/search', data)).data,
  matchResume: async (data = {}) => (await api.post('/jobs/match-resume', data)).data,
}

export const matchingAPI = {
  analyze: async (data) => (await api.post('/matching/analyze', data)).data,
  history: async () => (await api.get('/matching/history')).data,
}

export const skillGapAPI = {
  analyze: async (data) => (await api.post('/skill-gap/analyze', data)).data,
  history: async () => (await api.get('/skill-gap/history')).data,
}

export const coverLetterAPI = {
  generate: async (data) => (await api.post('/cover-letter/generate', data)).data,
  regenerate: async (data) => (await api.post('/cover-letter/regenerate', data)).data,
  history: async () => (await api.get('/cover-letter')).data,
}

export const interviewAPI = {
  prepare: async (data) => (await api.post('/interview/prepare', data)).data,
  questions: async (data) => (await api.post('/interview/questions', data)).data,
  start: async (data) => (await api.post('/interview/start', data)).data,
  history: async () => (await api.get('/interview')).data,
  answer: async (id, data) => (await api.post(`/interview/${id}/answer`, data)).data,
  next: async (id) => (await api.post(`/interview/${id}/next`)).data,
  report: async (id) => (await api.get(`/interview/${id}/report`)).data,
  result: async (id) => (await api.get(`/interview/${id}/result`)).data,
  get: async (id) => (await api.get(`/interview/${id}`)).data,
}

export const careerAPI = {
  chat: async (data) => (await api.post('/career-assistant/chat', data)).data,
  history: async () => (await api.get('/career-assistant/history')).data,
}

export const careerAssistantAPI = careerAPI


// Application Tracking APIs (M4.1)
export const applicationAPI = {
  /**
   * Create a new application record for a saved/selected job.
   */
  create: async (data) => (await api.post('/applications', data)).data,

  /**
   * List applications for the authenticated student.
   * Supports optional status, company, job_title filters and sort_by ordering.
   */
  list: async (params = {}) => {
    const response = await api.get('/applications', { params })
    return response.data
  },

  /**
   * Get dashboard statistics (counts by status + upcoming deadlines).
   */
  stats: async () => (await api.get('/applications/stats')).data,
  getDashboard: async () => (await api.get('/applications/dashboard')).data,
  getReminders: async () => (await api.get('/applications/reminders')).data,

  /**
   * Get a single application by ID.
   */
  get: async (id) => (await api.get(`/applications/${id}`)).data,

  /**
   * Update an existing application (all mutable fields).
   */
  update: async (id, data) => (await api.put(`/applications/${id}`, data)).data,

  /**
   * Update only the status field of an application.
   */
  updateStatus: async (id, status) =>
    (await api.patch(`/applications/${id}/status`, { status })).data,

  updateInterview: async (id, data) =>
    (await api.patch(`/applications/${id}/interview`, data)).data,

  updateNotes: async (id, data) =>
    (await api.patch(`/applications/${id}/notes`, data)).data,

  /**
   * Delete an application by ID.
   */
  delete: async (id) => (await api.delete(`/applications/${id}`)).data,
}

// Token and Session Helpers
export const authUtils = {
  setToken: (token) => {
    localStorage.setItem('token', token)
  },
  getToken: () => {
    return localStorage.getItem('token')
  },
  removeToken: () => {
    localStorage.removeItem('token')
  },
  isAuthenticated: () => {
    return !!localStorage.getItem('token')
  },
}

export function getApiErrorMessage(error) {
  const status = error.response?.status
  const detail = error.response?.data?.detail

  if (!error.response) {
    return `Unable to connect to the server. Please make sure FastAPI is running at ${API_BASE_URL}/.`
  }

  if (status === 401) {
    return 'Invalid email or password.'
  }

  if (status === 404) {
    return 'Login endpoint was not found. Please check the API configuration.'
  }

  if (status === 422 && Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(', ')
  }

  if (status >= 500) {
    return 'Server error. Please try again.'
  }

  if (typeof detail === 'string') {
    return detail
  }

  return 'Something went wrong. Please try again.'
}

export default api
