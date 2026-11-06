import React from "react"
import type { Message as MessageType } from "../types"

interface MessageProps {
  message: MessageType
}

export const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === "user"
  return (
    <div
      className={`message ${isUser ? "message-user" : "message-assistant"}`}
    >
      <div className="message-meta">
        {isUser ? "You" : "Assistant"} • {new Date(message.created_at || Date.now()).toLocaleString()}
      </div>
      <div className="whitespace-pre-wrap">{message.content}</div>
    </div>
  )
}