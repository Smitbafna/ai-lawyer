import React, { useState, useEffect, useCallback } from 'react'
import { ChatPanel } from '../components/ChatPanel'
import { CaseSummary } from '../components/CaseSummary'
import { createCase, getCase } from '../services/api'
import type { Case } from '../types'

export const ChatPage: React.FC = () => {
  const [currentCase, setCurrentCase] = useState<Case | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [input, setInput] = useState('')

  const createNewCase = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const newCase = await createCase()
      setCurrentCase(newCase)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create case')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (currentCase?.id) {
      const fetchCase = async () => {
        try {
          const caseData = await getCase(currentCase.id)
          setCurrentCase(caseData)
        } catch (err: any) {
          setError(err.response?.data?.detail || 'Failed to load case')
        }
      }
      fetchCase()
    }
  }, [currentCase?.id])

  const handleCaseUpdated = (updatedCase: any) => {
    setCurrentCase((prev) => ({
      ...(prev || {}),
      ...updatedCase,
    }))
  }

  return (
    <div className='coffee-bg'>
      <div className='flex h-screen w-full'>
        {/* Left Sidebar */}
        <div className='sidebar w-64 border-r border-coffee-border bg-coffee-surface flex flex-col'>
          <div className='sidebar-header border-b border-coffee-border py-4 px-6'>
            <div className='sidebar-title text-2xl font-semibold coffee-primary'>Kuku</div>
            <div className='sidebar-subtitle text-sm coffee-muted'>AI Legal Assistant</div>
          </div>
          <div className='sidebar-content flex-1 p-4'>
            {currentCase ? (
              <>
                <button className='btn-new w-full mb-2' onClick={createNewCase}>
                  <span className='mr-2'>+</span> New Case
                </button>
                <div className='case-badge text-sm mb-4'>
                  <p className='coffee-primary'>Active Case: {currentCase.id.substring(0, 8)}...</p>
                  <p className='coffee-muted'>Status: {currentCase.status}</p>
                </div>
              </>
            ) : (
              <button className='btn-new w-full mb-4' onClick={createNewCase}>
                <span className='mr-2'>+</span> New Case
              </button>
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className='flex-1 flex flex-col overflow-hidden'>
          <div className='chat-box flex-1 bg-coffee-bg border-b border-coffee-border p-4 overflow-y-auto'>
            {currentCase ? (
              <div className='messages-container'>
                <ChatPanel caseId={currentCase.id} onCaseUpdated={handleCaseUpdated} />
              </div>
            ) : (
              <div className='empty-state text-center py-12'>
                <div className='text-4xl coffee-muted'>👋</div>
                <p className='mt-2 coffee-muted text-lg'>Create a new case to begin intake</p>
              </div>
            )}
          </div>

          <div className='p-4 border-t border-coffee-border coffee-bg flex items-center justify-between'>
            {loading && <div className='coffee-muted text-sm'>Loading...</div>}
            {error && <div className='coffee-text text-sm coffee-error'>{error}</div>}
            <input
              type='text'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder='Type your message...'
              disabled={loading}
              className='flex-1 border border-coffee-border rounded-md padding-2 coffee-text focus:outline-none focus:ring-2 focus:ring-coffee-primary'
            />
            <button
              className='bg-coffee-primary text-coffee-foreground rounded-md hover:bg-coffee-primary-hover transition-colors px-4 py-2'
              disabled={loading || !input.trim()}
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>

        {/* Case Summary Panel - Right Sidebar */}
        {currentCase && (
          <div className='case-panel w-80 border-l border-coffee-border bg-coffee-surface flex flex-col'>
            <CaseSummary caseData={currentCase} />
          </div>
        )}
      </div>
    </div>
  )
}
