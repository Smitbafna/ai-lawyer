import React, { useState, useEffect, useCallback } from "react"
import { ChatPanel } from "../components/ChatPanel"
import { CaseSummary } from "../components/CaseSummary"
import { createCase, getCase } from "../services/api"
import type { Case } from "../types"

export const ChatPage: React.FC = () => {
  const [currentCase, setCurrentCase] = useState<Case | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createNewCase = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const newCase = await createCase()
      setCurrentCase(newCase)
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create case")
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
          setError(err.response?.data?.detail || "Failed to load case")
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
    <div className="app">
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title">AI Lawyer</div>
          <div className="sidebar-subtitle">Tenant-Landlord Dispute Intake</div>
        </div>
        <div className="sidebar-content">
          {currentCase ? (
            <>
              <button className="btn-new" onClick={createNewCase} style={{ marginBottom: "1rem" }}>
                <span>+</span> New Case
              </button>
              <div className="case-badge">
                <p>Active Case: {currentCase.id.substring(0, 8)}...</p>
                <p>Status: {currentCase.status}</p>
              </div>
            </>
          ) : (
            <button className="btn-new" onClick={createNewCase}>
              <span>+</span> New Case
            </button>
          )}
        </div>
        {currentCase && (
          <div className="case-summary" style={{ margin: "1rem" }}>
            <CaseSummary caseData={currentCase} />
          </div>
        )}
      </div>
      <div className="main">
        {!currentCase ? (
          <div className="empty-state">
            <div>👋</div>
            <p>Create a new case to begin intake</p>
          </div>
        ) : (
          <div className="chat-area">
            <div className="messages-container">
              <ChatPanel caseId={currentCase.id} onCaseUpdated={handleCaseUpdated} />
            </div>
          </div>
        )}
        {loading && (
          <div className="loading-msg">Loading...</div>
        )}
        {error && (
          <div className="error-msg">{error}</div>
        )}
      </div>
    </div>
  )
}