import React from "react"
import type { LegalAnswerResponse } from "../types"
import { Typewriter } from "./Typewriter"

interface LegalAssessmentProps {
  isLoading: boolean
  error: string | null
  response: LegalAnswerResponse | null
  onNewAssessment: () => void
}

const dispositionLabels: Record<string, string> = {
  full_refund: "Full Refund",
  partial_refund: "Partial Refund",
  over_cap_refund: "Over-Cap Refund",
  abstain: "Abstention",
  clarify: "Clarification Needed",
}

const dispositionColors: Record<string, string> = {
  full_refund: "coffee-success",
  partial_refund: "coffee-warning",
  over_cap_refund: "coffee-error",
  abstain: "coffee-muted",
  clarify: "coffee-primary",
}

export const LegalAssessment: React.FC<LegalAssessmentProps> = ({ isLoading, error, response, onNewAssessment }) => {
  if (isLoading) {
    return (
      <div className="p-4 coffee-surface">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-coffee-muted animate-bounce"></span>
          <span>Analyzing legal provisions...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 coffee-border rounded-md mb-4 coffee-surface">
        <p className="font-medium coffee-error">Error: {error}</p>
      </div>
    )
  }

  if (!response) {
    return null
  }

  const { legal_answer, grounding_check } = response
  const { disposition, confidence, answer, cited_provisions, explanation } = legal_answer
  const colorClass = dispositionColors[disposition] || "coffee-muted"

  return (
    <div className="space-y-6">
      {/* Disposition Banner */}
      <div className={`p-4 rounded-xl mb-6 ${colorClass}-bg`}>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium {colorClass}">{dispositionLabels[disposition]}</span>
          {confidence > 0 && (
            <span className="text-sm opacity-80">{Math.round(confidence * 100)}% confidence</span>
          )}
        </div>
      </div>

      {/* Plain-Language Answer */}
      <div>
        <h3 className="font-medium text-sm coffee-foreground mb-2">Plain-Legal Explanation</h3>
        <p className="text-sm coffee-foreground whitespace-pre-wrap line-clamp-6">{answer}</p>
      </div>

      {/* Typewriter Effect for Reasoning/Explanation */}
      {explanation && (
        <div>
          <h3 className="font-medium text-sm coffee-foreground mb-2">Reasoning</h3>
          <Typewriter text={explanation} batchSize={2} delay={40} />
        </div>
      )}

      {/* Applicable Provisions */}
      {cited_provisions.length > 0 && (
        <div>
          <h3 className="font-medium text-sm coffee-foreground mb-3">Applicable Provisions</h3>
          <div className="space-y-3">
            {cited_provisions.map((prov) => (
              <div
                key={prov.provision_identifier}
                className={`p-4 rounded-xl border-2 border-opacity-50 transition-all duration-500 ${colorClass}-50`}
              >
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full mt-1 bg-{colorClass}"></div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm coffee-foreground">{prov.provision_identifier}</p>
                    <p className="text-xs coffee-muted">{prov.section}</p>
                    <p className="text-xs coffee-muted-foreground">{prov.legal_proposition}</p>
                    {prov.qualifications && (
                      <p className="text-xs coffee-muted-foreground mt-1">{prov.qualifications}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Next Steps */}
      {legal_answer.unresolved_claims && legal_answer.unresolved_claims.length > 0 && (
        <div>
          <h3 className="font-medium text-sm coffee-foreground mb-2">Recommended Next Steps</h3>
          <ol className="list-decimal inside pl-5 text-sm coffee-foreground">
            {legal_answer.unresolved_claims.map((claim, i) => (
              <li key={i}>{claim}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Clarification or Abstention Details */}
      {disposition === "clarify" && (
        <div>
          <h3 className="font-medium text-sm coffee-foreground mb-2">What Information is Needed</h3>
          <p className="text-sm coffee-muted-foreground whitespace-pre-wrap line-clamp-4">{grounding_check.check_details}</p>
        </div>
      )}

      {disposition === "abstain" && (
        <div>
          <h3 className="font-medium text-sm coffee-foreground mb-2">Unable to Provide Legal Conclusion</h3>
          <p className="text-sm coffee-muted-foreground whitespace-pre-wrap line-clamp-4">{grounding_check.check_details}</p>
        </div>
      )}

      {/* New Assessment Button */}
      {onNewAssessment && (
        <div className="pt-4 border-t border-coffee-border">
          <button
            onClick={onNewAssessment}
            className="w-full padding-3 rounded-xl text-sm font-medium coffee-primary bg-coffee-primary-100 text-coffee-primary hover:bg-coffee-primary-200 transition-colors"
          >
            Get Fresh Assessment
          </button>
        </div>
      )}
    </div>
  )
}