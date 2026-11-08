import React from "react"
import type { Case } from "../types"

interface CaseSummaryProps {
  caseData: Case | null
}

export const CaseSummary: React.FC<CaseSummaryProps> = ({ caseData }) => {
  if (!caseData) {
    return (
      <div className="case-summary p-4 coffee-surface">
        <h3 className="text-xs font-medium coffee-primary mb-3">Case Summary</h3>
        <p className="coffee-muted text-sm">No case data available.</p>
      </div>
    )
  }

  const structuredFacts = caseData.structured_facts || {}

  return (
    <div className="case-summary p-4 coffee-surface">
      <h3 className="text-xs font-medium coffee-primary mb-4">Case Summary</h3>

      <div className="border-b border-coffee-border pb-3 mb-3">
        <h4 className="text-xs font-medium coffee-muted mb-2">Case Details</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="coffee-muted text-xs block">Dispute Type</span>
            <span className="coffee-primary block">{structuredFacts.case_type || "security_deposit_dispute"}</span>
          </div>
          <div>
            <span className="coffee-muted text-xs block">Location</span>
            <span className="coffee-primary block">{structuredFacts.jurisdiction?.city && structuredFacts.jurisdiction.state
              ? `${structuredFacts.jurisdiction.city}, ${structuredFacts.jurisdiction.state}`
              : structuredFacts.jurisdiction?.state || structuredFacts.jurisdiction?.city || "Not provided"}</span>
          </div>
          <div>
            <span className="coffee-muted text-xs block">Deposit Amount</span>
            <span className="coffee-primary block">{structuredFacts.security_deposit_amount !== undefined && structuredFacts.security_deposit_amount !== null
              ? `${structuredFacts.security_deposit_currency || "₹"}${structuredFacts.security_deposit_amount}`
              : "Not provided"}</span>
          </div>
          <div>
            <span className="coffee-muted text-xs block">Rental Agreement</span>
            <span className="coffee-primary block">{structuredFacts.rental_agreement_exists === true ? "Yes" : structuredFacts.rental_agreement_exists === false ? "No" : "Unknown"}</span>
          </div>
        </div>
      </div>

      {structuredFacts.parties?.tenant || structuredFacts.parties?.landlord && (
        <div className="border-b border-coffee-border pb-3 mb-3">
          <h4 className="text-xs font-medium coffee-muted mb-2">Parties</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="coffee-muted text-xs block">Tenant</span>
              <span className="coffee-primary block">{structuredFacts.parties?.tenant || "Not provided"}</span>
            </div>
            <div>
              <span className="coffee-muted text-xs block">Landlord</span>
              <span className="coffee-primary block">{structuredFacts.parties?.landlord || "Not provided"}</span>
            </div>
          </div>
        </div>
      )}

      {structuredFacts.property_address && (
        <div className="border-b border-coffee-border pb-3 mb-3">
          <h4 className="text-xs font-medium coffee-muted mb-2">Property</h4>
          <p className="coffee-primary text-sm">{structuredFacts.property_address}</p>
        </div>
      )}

      {structuredFacts.vacating_date && (
        <div>
          <h4 className="text-xs font-medium coffee-muted mb-2">Vacating Date</h4>
          <p className="coffee-primary text-sm">{structuredFacts.vacating_date}</p>
        </div>
      )}

      {caseData.missing_information && caseData.missing_information.length > 0 && (
        <div className="mt-4 p-3 coffee-border rounded-md mb-4">
          <h4 className="text-xs font-medium coffee-warning mb-2">Information Needed</h4>
          <div className="space-y-1 text-sm">
            {caseData.missing_information.map((item, i) => (
              <span key={i} className="coffee-warning text-sm inline-block px-2 py-1 rounded bg-coffee-input mr-1">
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {!caseData.missing_information || caseData.missing_information.length === 0 && (
        <div className="mt-3 pt-3 border-t border-coffee-border">
          <p className="coffee-muted text-xs">No missing information</p>
        </div>
      )}
    </div>
  )
}