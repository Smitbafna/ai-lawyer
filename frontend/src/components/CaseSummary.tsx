import React from "react"
import type { Case } from "../types"
import { getCaseSummary } from "../services/api"

interface CaseSummaryProps {
  caseData: Case | null
}

export const CaseSummary: React.FC<CaseSummaryProps> = ({ caseData }) => {
  const summary = getCaseSummary(caseData)

  if (!summary) {
    return (
      <div className="case-summary">
        <h3>Case Summary</h3>
        <p style={{ color: "#6b7280", fontSize: "0.875rem" }}>No case data available.</p>
      </div>
    )
  }

  return (
    <div className="case-summary">
      <h3>Case Summary</h3>
      <div className="summary-row">
        <span className="summary-label">Dispute Type:</span>
        <span className="summary-value">{summary.disputeType}</span>
      </div>
      <div className="summary-row">
        <span className="summary-label">Location:</span>
        <span className="summary-value">{summary.location}</span>
      </div>
      <div className="summary-row">
        <span className="summary-label">Deposit Amount:</span>
        <span className="summary-value">{summary.depositAmount}</span>
      </div>
      <div className="summary-row">
        <span className="summary-label">Rental Agreement:</span>
        <span className="summary-value">{summary.rentalAgreement}</span>
      </div>
      <div className="summary-row">
        <span className="summary-label">Tenant:</span>
        <span className="summary-value">{summary.parties.tenant}</span>
      </div>
      <div className="summary-row">
        <span className="summary-label">Landlord:</span>
        <span className="summary-value">{summary.parties.landlord}</span>
      </div>
      <div className="summary-row">
        <span className="summary-label">Property:</span>
        <span className="summary-value">{summary.propertyAddress}</span>
      </div>
      <div className="summary-row">
        <span className="summary-label">Vacating Date:</span>
        <span className="summary-value">{summary.vacatingDate}</span>
      </div>
      {summary.facts.length > 0 && (
        <div className="summary-section">
          <div className="summary-section-title">Key Facts:</div>
          <ul className="summary-list">
            {summary.facts.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
      )}
      {summary.timeline.length > 0 && (
        <div className="summary-section">
          <div className="summary-section-title">Timeline:</div>
          <ul className="summary-list">
            {summary.timeline.map((t, i) => (
              <li key={i}>
                {t.date ? `${t.date}: ` : ""}{t.event || ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="summary-section">
        <div className="summary-section-title">Missing Information:</div>
        <ul className="summary-list">
          {summary.missingInformation.length > 0 ? (
            summary.missingInformation.map((m, i) => (
              <li key={i}>{m}</li>
            ))
          ) : (
            <li style={{ color: "#9ca3af" }}>None</li>
          )}
        </ul>
      </div>
    </div>
  )
}