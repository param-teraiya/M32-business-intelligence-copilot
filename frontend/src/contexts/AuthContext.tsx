/**
 * Authentication context for managing user state and auth operations
 */

import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi, User } from '@/lib/api'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithToken: (user: User, token: string) => void
  register: (data: any) => Promise<void>
  logout: () => void
  updateUser: (userData: User) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = () => {
      console.log('🔍 AuthContext: Checking existing auth...')
      const token = localStorage.getItem('token')
      const savedUser = localStorage.getItem('user')
      console.log('📦 AuthContext: Found in localStorage', { token: !!token, savedUser: !!savedUser })
      
      if (token && savedUser) {
        try {
          // Trust the saved user data (since we just logged in)
          const user = JSON.parse(savedUser)
          console.log('✅ AuthContext: Restoring user from localStorage', user)
          setUser(user)
        } catch (error) {
          console.error('❌ AuthContext: Invalid saved data, clearing', error)
          // Invalid saved data, clear storage
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          setUser(null)
        }
      } else {
        console.log('❌ AuthContext: No saved auth data found')
      }
      
      setIsLoading(false)
      console.log('✅ AuthContext: Initial auth check complete')
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login({ email, password })
      const { access_token, user: userData } = response
      
      // Store token and user data
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)
      setIsLoading(false) // Ensure loading is false after login
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  }

  const register = async (data: any) => {
    try {
      const user = await authApi.register(data)
      // After registration, automatically log in
      await login(data.email, data.password)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed')
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const loginWithToken = (user: User, token: string) => {
    console.log('🔐 AuthContext: loginWithToken called', { user, token })
    // Store token and user data
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    console.log('💾 AuthContext: Data stored in localStorage')
    setUser(user)
    setIsLoading(false) // Ensure loading is false after login
    console.log('✅ AuthContext: User set, loading false', { isAuthenticated: !!user })
  }

  const updateUser = (userData: User) => {
    setUser(userData)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    loginWithToken,
    register,
    logout,
    updateUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
