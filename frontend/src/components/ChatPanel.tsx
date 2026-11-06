import React, { useState, useEffect, useCallback } from "react"
import { Message } from "./Message"
import type { Message as MessageType, ChatRequest } from "../types"
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
      <div className="p-4 border-b border-gray-200">
        <h2 className="font-semibold text-gray-900">Conversation</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4" id="messages-container">
        {messages.length === 0 && !loading && (
          <div className="text-sm text-gray-500">No messages yet. Start the conversation!</div>
        )}
        {messages.map((msg) => (
          <Message key={msg.id} message={msg} />
        ))}
        {error && <div className="error-msg">{error}</div>}
      </div>
      <form onSubmit={handleSend} className="chat-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? "Sending..." : "Send"}
        </button>
      </form>
    </div>
  )
}