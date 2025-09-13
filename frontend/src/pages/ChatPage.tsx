/**
 * Chat page - main business intelligence conversation interface
 */

import React, { useEffect, useState, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { chatApi, ChatMessage as ChatMessageType, ChatSession } from '../lib/api'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import LoadingSpinner from '../components/LoadingSpinner'
import ChatMessage from '../components/ChatMessage'
import { generateSmartChatTitle, getRandomCreativeTitle } from '../utils/chatTitles'
import { 
  ArrowLeft, 
  Send, 
  Brain, 
  Loader2
} from 'lucide-react'

const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  
  const [session, setSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [hasRenamedSession, setHasRenamedSession] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (sessionId) {
      loadSession()
    } else {
      // Create new session
      createNewSession()
    }
  }, [sessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const renameSessionBasedOnMessage = async (message: string) => {
    if (!session || hasRenamedSession) return
    
    try {
      const smartTitle = generateSmartChatTitle(message, {
        company: user?.company_name,
        industry: user?.industry,
        business_type: user?.business_type,
        company_size: user?.company_size
      })
      
      // Update session name via API
      const updatedSession = await chatApi.updateSession(session.id, {
        session_name: smartTitle
      })
      
      setSession(updatedSession)
      setHasRenamedSession(true)
      
    } catch (error) {
      console.error('Failed to rename session:', error)
      // Still update local state as fallback
      setSession(prev => prev ? { ...prev, session_name: generateSmartChatTitle(message) } : null)
      setHasRenamedSession(true)
    }
  }

  const createNewSession = async () => {
    try {
      const creativeName = getRandomCreativeTitle()
      const newSession = await chatApi.createSession({
        session_name: creativeName
      })
      navigate(`/chat/${newSession.id}`, { replace: true })
    } catch (error) {
      console.error('Failed to create session:', error)
      setIsLoading(false)
    }
  }

  const loadSession = async () => {
    if (!sessionId) return
    
    try {
      const [sessionData, messagesData] = await Promise.all([
        chatApi.getSession(parseInt(sessionId)),
        chatApi.getMessages(parseInt(sessionId))
      ])
      
      setSession(sessionData)
      setMessages(messagesData)
    } catch (error) {
      console.error('Failed to load session:', error)
      navigate('/dashboard')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!newMessage.trim() || isSending || !sessionId) return

    const messageContent = newMessage.trim()
    setNewMessage('')
    setIsSending(true)
    setIsTyping(true)

    // Add user message to UI immediately
    const userMessage: ChatMessageType = {
      id: Date.now(),
      content: messageContent,
      role: 'user',
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    // Rename session based on first message
    if (messages.length === 0) {
      await renameSessionBasedOnMessage(messageContent)
    }

    try {
      const response = await chatApi.sendMessage({
        message: messageContent,
        session_id: parseInt(sessionId),
        business_context: {
          company: user?.company_name,
          industry: user?.industry,
          business_type: user?.business_type,
          company_size: user?.company_size
        }
      })

      // Add AI response to messages
      const aiMessage: ChatMessageType = {
        id: Date.now() + 1,
        content: response.response,
        role: 'assistant',
        created_at: new Date().toISOString(),
        tools_used: response.tools_used
      }
      
      setMessages(prev => [...prev, aiMessage])
      
    } catch (error) {
      console.error('Failed to send message:', error)
      // Add error message
      const errorMessage: ChatMessageType = {
        id: Date.now() + 1,
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        role: 'assistant',
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsSending(false)
      setIsTyping(false)
      inputRef.current?.focus()
    }
  }


  const quickPrompts = [
    "What are the current trends in my industry?",
    "Who are my main competitors?",
    "How can I improve my business strategy?",
    "What market opportunities should I explore?"
  ]

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b flex-shrink-0">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Link to="/dashboard">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Dashboard
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <Brain className="h-6 w-6 text-blue-600" />
                <h1 className="text-xl font-semibold text-gray-900">
                  {session?.session_name || 'Business Chat'}
                </h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {user?.username}
              </span>
              <Button variant="outline" size="sm" onClick={logout}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 h-full flex flex-col">
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <Brain className="h-16 w-16 text-blue-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Welcome to your Business Intelligence Assistant
                </h2>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  I'm here to help you with market research, competitor analysis, 
                  business strategy, and industry insights.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {quickPrompts.map((prompt, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      className="text-left justify-start h-auto py-3 px-4"
                      onClick={() => setNewMessage(prompt)}
                    >
                      {prompt}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    content={message.content}
                    role={message.role}
                    timestamp={new Date(message.created_at)}
                  />
                ))}

                {/* Typing indicator */}
                {isTyping && (
                  <ChatMessage
                    content=""
                    role="assistant"
                    isLoading={true}
                  />
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <div className="flex-shrink-0 pt-4">
            <form onSubmit={handleSendMessage} className="flex space-x-3">
              <div className="flex-1">
                <Input
                  ref={inputRef}
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Ask about your business, market trends, competitors..."
                  disabled={isSending}
                  className="w-full"
                />
              </div>
              <Button 
                type="submit" 
                disabled={!newMessage.trim() || isSending}
                className="px-4"
              >
                {isSending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
