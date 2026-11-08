export interface Case {
  id: string
  case_type: string
  jurisdiction_state: string | null
  jurisdiction_city: string | null
  status: string
  structured_facts: CaseStructuredFacts | null
  missing_information: string[] | null
  created_at: string | null
  updated_at: string | null
  chatItems?: Array<{
    id: string
    title: string | null
    last_message: string | null
    last_message_time: string | null
  }> | null
}

export interface CaseStructuredFacts {
  case_type?: string
  jurisdiction?: {
    state?: string | null
    city?: string | null
  }
  parties?: {
    tenant?: string | null
    landlord?: string | null
  }
  property_address?: string | null
  rental_start_date?: string | null
  rental_end_date?: string | null
  vacating_date?: string | null
  security_deposit_amount?: number | null
  security_deposit_currency?: string | null
  deposit_payment_date?: string | null
  deposit_payment_method?: string | null
  rental_agreement_exists?: boolean | null
  refund_clause?: string | null
  landlord_response?: string | null
  facts?: string[]
  timeline?: Array<{ date?: string | null; event?: string | null }>
  evidence_available?: string[]
  missing_information?: string[]
}

export interface Message {
  id: string
  conversation_id: string
  role: "user" | "assistant"
  content: string
  created_at: string | null
}

export interface ChatRequest {
  message: string
}

export interface ChatResponse {
  assistant_message: string
  updated_case: Case
  missing_information: string[]
  intake_status: string
}

export interface ApiError {
  detail: string
}

// Legal notice document types
export type DocumentType = "legal_notice" | "complaint" | "reply" | "application"

export interface DocumentRequirementsResponse {
  case_id: string
  document_type: DocumentType
  required_information: string[]
  available_information: string[]
  missing_information: string[]
  confirmation_required: boolean
  can_generate: boolean
  blocking_reasons: string[]
}

export interface DocumentResponse {
  document_id: string | null
  case_id: string
  document_type: DocumentType
  status: string
  message: string
  blocking_reasons: string[]
}

export interface AuthError extends ApiError {

export interface SignupCredentials {
  full_name: string
  email: string
  password: string
  confirmPassword?: string
}

export interface SignupResponse {
  user: {
    id: string
    full_name: string
    email: string
    created_at: string
  }
  access_token: string
}

export interface LoginCredentials {
  email: string
  password: string
}

// Legal assessment response types
export interface LegalAnswerResponse {
  legal_answer: {
    disposition: string
    confidence: number
    answer: string
    explanation?: string
    cited_provisions: Array<{
      provision_identifier: string
      section: string
      legal_proposition: string
      qualifications?: string
    }>
    unresolved_claims: string[]
  }
  grounding_check: {
    check_details: string
  }
}

export interface LoginResponse {
  user: {
    id: string
    full_name: string
    email: string
    created_at: string
  }
  access_token: string
}

