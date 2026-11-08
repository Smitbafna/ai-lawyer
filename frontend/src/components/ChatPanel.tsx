import React, { useState, useEffect, useCallback } from "react"
import { Message } from "./Message"
import type { Message as MessageType } from "../types"
import { sendChatMessage, getMessages } from "../services/api"

interface ChatPanelProps {
  caseId: string
  onCaseUpdated: (updatedCase: any) => void
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ caseId, onCaseUpdated }) => {
  const [messages, setMessages] = useState<MessageType[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadMessages = useCallback(async () => {
    try {
      const data = await getMessages(caseId)
      setMessages(data)
    } catch (err: any) {
      console.error("Failed to load messages", err)
    }
  }, [caseId])

  useEffect(() => {
    loadMessages()
  }, [caseId, loadMessages])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input
    setInput("")
    setLoading(true)
    setError(null)

    const tempUserMessage: MessageType = {
      id: "temp-" + Date.now(),
      conversation_id: "",
      role: "user",
      content: userMessage,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMessage])

    try {
      const response = await sendChatMessage(caseId, { message: userMessage })
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMessage.id),
        {
          id: "temp-assistant-" + Date.now(),
          conversation_id: "",
          role: "assistant",
          content: response.assistant_message,
          created_at: new Date().toISOString(),
        },
      ])
      // Re-fetch messages from database to persist user's message in the UI
      const fetchedMessages = await getMessages(caseId)
      setMessages(fetchedMessages)
      onCaseUpdated(response.updated_case)
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to send message. Please try again.")
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Chat Header */}
      <div className="p-4 border-b border-coffee-border coffee-surface">
        <h2 className="font-semibold coffee-foreground">Conversation</h2>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !loading && (
          <div className="empty-state text-center py-8 coffee-surface">
            <div className="text-4xl coffee-muted mb-2">👋</div>
            <p className="text-coffee-muted text-base">Start the conversation!</p>
          </div>
        )}
        {messages.map((msg) => (
          <Message key={msg.id} message={msg} />
        ))}
        {error && <div className="error-msg coffee-error mt-4 p-3 rounded-md coffee-surface">{error}</div>}
      </div>

      {/* Composer Form */}
      <form onSubmit={handleSend} className="chat-form coffee-surface">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={loading}
            className="flex-1 border border-coffee-border rounded-md px-3 py-2 coffee-text focus:outline-none focus:ring-2 focus:ring-coffee-primary"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className='bg-coffee-primary text-coffee-foreground rounded-md hover:bg-coffee-primary-hover transition-colors px-4 py-2'
          >
            {loading ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </div>
  )
}