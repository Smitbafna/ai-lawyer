import React, { useState, useEffect, useCallback } from 'react'
import { ChatPanel } from '../components/ChatPanel'
import { CaseSummary } from '../components/CaseSummary'
import { Button } from '../components/ui/button'
import { createCase, getCase } from '../services/api'
import type { Case } from '../types'

export const ChatPage: React.FC = () => {
  const [currentCase, setCurrentCase] = useState<Case | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  const createNewCase = useCallback(async () => {
    if (isCreating) return
    setIsCreating(true)
    try {
      const newCase = await createCase()
      setCurrentCase({
        ...newCase,
        chatItems: [],
      })
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create case')
    } finally {
      setIsCreating(false)
    }
  }, [isCreating])

  useEffect(() => {
    if (currentCase?.id) {
      const fetchCase = async () => {
        try {
          const caseData = await getCase(currentCase.id)
          setCurrentCase(caseData)
        } catch (err: any) {
          alert(err.response?.data?.detail || 'Failed to load case')
        }
      }
      fetchCase()
    }
  }, [currentCase?.id])

  const handleCaseUpdated = (updatedCase: any) => {
    setCurrentCase((prev) => ({
      ...(prev || {}),
      ...updatedCase,
      chatItems: prev?.chatItems
        ? [...prev.chatItems, ...(updatedCase.chatItems || [])]
        : updatedCase.chatItems || [],
    }))
  }

  return (
    <div className='coffee-bg'>
      <div className='flex h-screen w-full'>
        {/* Left Sidebar */}
        <div className='sidebar w-64 border-r border-coffee-border bg-coffee-surface flex flex-col shrink-0'>
          <div className='sidebar-header border-b border-coffee-border py-4 px-6'>
            <div className='sidebar-title text-2xl font-semibold coffee-primary'>Kuku</div>
            <div className='sidebar-subtitle text-sm coffee-muted'>AI Legal Assistant</div>
          </div>
          <div className='sidebar-content flex-1 p-4'>
            {/* Same button in both states, so it is rendered once */}
            <div className='flex justify-center mb-4'>
              <Button size='sm' loading={isCreating} onClick={createNewCase}>
                <span className='text-base leading-none'>+</span> New Case
              </Button>
            </div>

            {currentCase && (
              <>
                <div className='case-badge text-sm mb-4'>
                  <p className='coffee-primary'>Active Case: {currentCase.id.substring(0, 8)}...</p>
                  <p className='coffee-muted'>Status: {currentCase.status}</p>
                </div>
                <div className='chat-history mt-4 space-y-2 text-sm'>
                  <p className='coffee-muted text-xs font-medium mb-1'>Chat History</p>
                  {currentCase.chatItems && currentCase.chatItems.length > 0 ? (
                    <div className='space-y-1 max-h-80 overflow-y-auto'>
                      {currentCase.chatItems.map((item, i) => (
                        <div
                          key={i}
                          onClick={() => console.log('Select chat:', item.id)}
                          className='coffee-surface p-2 rounded-sm text-coffee-muted text-xs line-clamp-3 cursor-pointer hover:bg-coffee-input transition-colors'
                        >
                          <div className='font-medium coffee-primary'>{item.title || `Chat ${i + 1}`}</div>
                          <div>{item.last_message ? item.last_message.substring(0, 80) + (item.last_message.length > 80 ? '...' : '') : ''}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className='coffee-muted text-xs'>No chat history yet</p>
                  )}
                </div>
              </>
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
        </div>

        {/* Case Summary Panel - Right Sidebar */}
        {currentCase && (
          <div className='case-panel max-w-80 w-80 border-l border-coffee-surface bg-coffee-surface flex-none'>
            <CaseSummary caseData={currentCase} />
          </div>
        )}
      </div>
    </div>
  )
}