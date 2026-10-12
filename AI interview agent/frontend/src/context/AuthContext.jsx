import React, { createContext, useContext, useState, useEffect } from 'react'
import { authAPI, authUtils, profileAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load user profile on startup if token exists
  const loadUser = async () => {
    if (!authUtils.isAuthenticated()) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const profile = await profileAPI.getProfile()
      setUser(profile)
    } catch {
      authUtils.removeToken()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUser()
  }, [])

  const login = async (email, password) => {
    const data = await authAPI.login({ email, password })
    authUtils.setToken(data.access_token)
    await loadUser()
    return data
  }

  const register = async (name, email, password) => {
    const data = await authAPI.register({ name, email, password })
    return data
  }

  const logout = () => {
    authUtils.removeToken()
    setUser(null)
  }

  const refreshUser = async () => {
    try {
      const profile = await profileAPI.getProfile()
      setUser(profile)
      return profile
    } catch {
      // Ignored
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        refreshUser,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
