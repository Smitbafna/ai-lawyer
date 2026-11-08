import axios from "axios"
import type {
  Case,
  ChatRequest,
  ChatResponse,
  SignupCredentials,
  SignupResponse,
  LoginCredentials,
  LoginResponse,
  ApiError,
} from "../types"

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "https://ai-lawyer-d5fs.onrender.com/api"

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
})

// Interceptor to add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const createCase = async (): Promise<Case> => {
  const response = await api.post<Case>("/cases")
  return response.data
}

export const getCase = async (caseId: string): Promise<Case> => {
  const response = await api.get<Case>(`/cases/${caseId}`)
  return response.data
}

export const updateCase = async (
  caseId: string,
  updates: Partial<Case>,
): Promise<Case> => {
  const response = await api.patch<Case>(`/cases/${caseId}`, updates)
  return response.data
}

export const sendChatMessage = async (
  caseId: string,
  request: ChatRequest,
): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>(`/cases/${caseId}/chat`, request)
  return response.data
}

export const getMessages = async (caseId: string): Promise<any[]> => {
  const response = await api.get<any[]>(`/cases/${caseId}/messages`)
  return response.data
}

// Helper to extract structured facts for display
export const getCaseSummary = (caseData: Case | null) => {
  if (!caseData?.structured_facts) return null
  const f = caseData.structured_facts
  return {
    disputeType: f.case_type || "security_deposit_dispute",
    location:
      f.jurisdiction?.state && f.jurisdiction?.city
        ? `${f.jurisdiction.city}, ${f.jurisdiction.state}`
        : f.jurisdiction?.state || f.jurisdiction?.city || "Not provided",
    depositAmount:
      f.security_deposit_amount !== undefined && f.security_deposit_amount !== null
        ? `${f.security_deposit_currency || "₹"}${f.security_deposit_amount}`
        : "Not provided",
    rentalAgreement:
      f.rental_agreement_exists === true
        ? "Yes"
        : f.rental_agreement_exists === false
          ? "No"
          : "Unknown",
    parties: {
      tenant: f.parties?.tenant || "Not provided",
      landlord: f.parties?.landlord || "Not provided",
    },
    propertyAddress: f.property_address || "Not provided",
    vacatingDate: f.vacating_date || "Not provided",
    facts: f.facts || [],
    timeline: f.timeline || [],
    evidence: f.evidence_available || [],
    missingInformation: f.missing_information || caseData.missing_information || [],
  }
}

export interface AuthError extends ApiError {}

export const signup = async (
  credentials: SignupCredentials,
): Promise<SignupResponse> => {
  const response = await api.post<SignupResponse>("/auth/signup", credentials)
  // Store token after successful signup
  if (response.data.access_token) {
    localStorage.setItem("auth_token", response.data.access_token)
  }
  return response.data
}

export const login = async (
  credentials: LoginCredentials,
): Promise<LoginResponse> => {
  const response = await api.post<LoginResponse>("/auth/login", credentials)
  // Store token after successful login
  if (response.data.access_token) {
    localStorage.setItem("auth_token", response.data.access_token)
  }
  return response.data
}

export const getCurrentUser = async (): Promise<SignupResponse["user"]> => {
  const response = await api.get<{ user: SignupResponse["user"] }>("/auth/me")
  return response.data.user
}

export const logout = async (): Promise<void> => {
  const response = await api.post<void>("/auth/logout")
  // Remove token on logout
  localStorage.removeItem("auth_token")
  return response.data
}
