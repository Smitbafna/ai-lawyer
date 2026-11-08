import React from "react"
import type { Message as MessageType } from "../types"

interface MessageProps {
  message: MessageType
}

export const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === "user"
  const maxWidth = isUser ? "75%" : "auto"
  const userClass = "message-user coffee-primary"
  const assistantClass = "message-assistant coffee-foreground"

  return (
    <div
      className={isUser ? userClass : assistantClass}
      style={{ maxWidth: maxWidth, marginBottom: "1rem" }}
    >
      <div className="message-meta">
        {isUser ? "You" : "Assistant"} • {new Date(message.created_at || Date.now()).toLocaleString()}
      </div>
      <div className="message-bubble" style={{ whiteSpace: "pre-wrap", backgroundColor: "white", borderRadius: "0.5rem", padding: "0.5rem" }}>
        {message.content}
      </div>
    </div>
  )
}