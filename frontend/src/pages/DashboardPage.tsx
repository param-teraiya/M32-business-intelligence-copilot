/**
 * Dashboard page - main landing page after login
 */

import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { chatApi, ChatSession } from '../lib/api'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import LoadingSpinner from '../components/LoadingSpinner'
import ProfileUpdateModal from '../components/ProfileUpdateModal'
import { getRandomCreativeTitle } from '../utils/chatTitles'
import { MessageSquare, Plus, Building, TrendingUp, Users, Brain } from 'lucide-react'

const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth()
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const data = await chatApi.getSessions()
      setSessions(data)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = async () => {
    try {
      const creativeName = getRandomCreativeTitle()
      const newSession = await chatApi.createSession({
        session_name: creativeName
      })
      navigate(`/chat/${newSession.id}`)
    } catch (error) {
      console.error('Failed to create new chat:', error)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Brain className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">
                M32 Business Intelligence
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user?.full_name || user?.username}
              </span>
              <Button variant="outline" onClick={logout}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to your Business Intelligence Dashboard
          </h2>
          <p className="text-gray-600">
            Get AI-powered insights, market research, and strategic recommendations for your business.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={handleNewChat}>
            <CardHeader className="pb-3">
              <div className="flex items-center space-x-2">
                <Plus className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-lg">New Chat</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Start a new conversation with your AI business advisor
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <CardTitle className="text-lg">Market Research</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Get insights on market trends and opportunities
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center space-x-2">
                <Users className="h-5 w-5 text-purple-600" />
                <CardTitle className="text-lg">Competitor Analysis</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Analyze your competition and find differentiation opportunities
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center space-x-2">
                <Building className="h-5 w-5 text-orange-600" />
                <CardTitle className="text-lg">Business Strategy</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Get strategic recommendations for business growth
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        {/* Recent Conversations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Recent Conversations</CardTitle>
                  <Button onClick={handleNewChat}>
                    <Plus className="h-4 w-4 mr-2" />
                    New Chat
                  </Button>
                </div>
                <CardDescription>
                  Your recent business intelligence conversations
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sessions.length === 0 ? (
                  <div className="text-center py-8">
                    <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">No conversations yet</p>
                    <Button onClick={handleNewChat}>Start your first chat</Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {sessions.slice(0, 5).map((session) => (
                      <div
                        key={session.id}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                        onClick={() => navigate(`/chat/${session.id}`)}
                      >
                        <div className="flex items-center space-x-3">
                          <MessageSquare className="h-5 w-5 text-blue-600" />
                          <div>
                            <p className="font-medium text-gray-900">
                              {session.session_name || `Chat ${session.id}`}
                            </p>
                            <p className="text-sm text-gray-500">
                              {session.message_count} messages • {formatDate(session.updated_at)}
                            </p>
                          </div>
                        </div>
                        <div className="text-sm text-gray-400">
                          →
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Business Profile */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Business Profile</CardTitle>
                <CardDescription>
                  Your business information for personalized insights
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">Company</p>
                  <p className="text-sm text-gray-600">
                    {user?.company_name || 'Not specified'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Industry</p>
                  <p className="text-sm text-gray-600">
                    {user?.industry || 'Not specified'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Business Type</p>
                  <p className="text-sm text-gray-600">
                    {user?.business_type || 'Not specified'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Company Size</p>
                  <p className="text-sm text-gray-600">
                    {user?.company_size || 'Not specified'}
                  </p>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full mt-4"
                  onClick={() => setIsProfileModalOpen(true)}
                >
                  Update Profile
                </Button>
              </CardContent>
            </Card>

            {/* Quick Tips */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="text-lg">Quick Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-gray-600">
                    Ask about your specific industry for tailored insights
                  </p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-gray-600">
                    Request competitor analysis with company names
                  </p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-gray-600">
                    Get market trend forecasts for strategic planning
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Profile Update Modal */}
      {user && (
        <ProfileUpdateModal
          isOpen={isProfileModalOpen}
          onClose={() => setIsProfileModalOpen(false)}
          user={user}
        />
      )}
    </div>
  )
}

export default DashboardPage
