import React, { useEffect, useState } from "react"
import ReactDOM from "react-dom/client"
import { ChatPage } from "./pages/ChatPage"
import { AuthPage } from "./components/AuthPage"
import "./index.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loggingIn, setLoggingIn] = useState(false)

  // First, remove any stale token to force login page to show
  useEffect(() => {
    localStorage.removeItem("auth_token")
    setIsAuthenticated(false)
    setLoggingIn(false)
  }, [])

  // Then check for existing auth token - handles case where storage
  // event doesn't fire in same-document context (common browser quirk)
  useEffect(() => {
    const token = localStorage.getItem("auth_token")
    setIsAuthenticated(!!token)
  }, [])

  // Listen for auth token changes from login flow
  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === "auth_token") {
        setIsAuthenticated(!!event.newValue)
        setLoggingIn(false)
      }
    }

    window.addEventListener("storage", handleStorageChange)

    return () => {
      window.removeEventListener("storage", handleStorageChange)
    }
  }, [])

  return (
    <React.Fragment>
      {isAuthenticated ? <ChatPage /> : <AuthPage />}
    </React.Fragment>
  )
}
