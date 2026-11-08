import React, { useState, useCallback, useEffect } from "react"
import { DocumentType, DocumentRequirementsResponse, DocumentResponse } from "../types"
import { postDocumentRequirements, postDocumentGenerate, getDocument, patchDocument } from "../services/api"
import { Button } from "./ui/button"
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from "./ui/dialog"
import { Card, CardContent, CardFooter } from "./ui/card"
import { Skeleton } from "./ui/skeleton"
import { Badge } from "./ui/badge"
import { Alert, AlertTitle, AlertDescription } from "./ui/alert"

interface LegalNoticeDialogProps {
  isOpen: boolean
  onClose: () => void
  currentCase: import("../types").Case | null
}

export const LegalNoticeDialog: React.FC<LegalNoticeDialogProps> = ({ isOpen, onClose, currentCase }) => {
  const [requirementsLoading, setRequirementsLoading] = useState(false)
  const [requirements, setRequirements] = useState<DocumentRequirementsResponse | null>(null)
  const [generateLoading, setGenerateLoading] = useState(false)
  const [document, setDocument] = useState<DocumentResponse | null>(null)
  const [draftContent, setDraftContent] = useState<string>("")
  const [unsavedChanges, setUnsavedChanges] = useState(false)

  const handlePrepare = useCallback(async () => {
    if (!currentCase) return
    setRequirementsLoading(true)
    setRequirements(null)
    try {
      const result = await postDocumentRequirements({
        case_id: currentCase.id,
        document_type: "legal_notice",
      })
      setRequirements(result)
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to check requirements")
    } finally {
      setRequirementsLoading(false)
    }
  }, [currentCase])

  const handleGenerate = useCallback(async () => {
    if (!currentCase || !requirements || !requirements.can_generate) return
    setGenerateLoading(true)
    try {
      const result = await postDocumentGenerate({
        case_id: currentCase.id,
        document_type: "legal_notice",
        user_instructions: draftContent || undefined,
      })
      setDocument(result)
      setGenerateLoading(false)
      if (result.document_id) {
        const doc = await getDocument(result.document_id)
        setDraftContent(doc.content || "")
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to generate document")
    } finally {
      setGenerateLoading(false)
    }
  }, [currentCase, requirements, draftContent])

  const handleSave = useCallback(async () => {
    if (!document || !draftContent) return
    setGenerateLoading(true)
    try {
      const result = await patchDocument(document.document_id, {
        case_id: currentCase.id,
        document_type: "legal_notice",
        user_instructions: draftContent,
      })
      setDocument(result)
      setUnsavedChanges(false)
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to save document")
    } finally {
      setGenerateLoading(false)
    }
  }, [document, draftContent, currentCase])

  if (!currentCase) {
    return null
  }

  if (!requirements && !document) {
    return (
      <div className="p-4 coffee-surface">
        <Button
          size="sm"
          onClick={handlePrepare}
          disabled={requirementsLoading}
          className="w-full justify-center"
        >
          {requirementsLoading ? "Checking requirements..." : "Prepare Legal Notice"}
        </Button>
      </div>
    )
  }

  if (requirements && !document) {
    const canGenerate = requirements.can_generate
    const missingInfo = requirements.missing_information
    const blockingReasons = requirements.blocking_reasons

    return (
      <div className="coffee-surface p-6">
        <Alert variant="default">
          <AlertTitle>Requirements Check</AlertTitle>
          <AlertDescription>
            {canGenerate
              ? "All requirements are met. You can generate the legal notice."
              : "Missing information or blocking restrictions apply."}
          </AlertDescription>
        </Alert>

        {missingInfo.length > 0 && (
          <div className="mt-4 p-3 coffee-border rounded-md mb-4">
            <div className="text-xs coffee-warning mb-2">Missing Information</div>
            <div className="space-y-1 text-sm">
              {missingInfo.map((item, i) => (
                <span key={i} className="coffee-warning text-sm inline-block min-w-0 px-2 py-1 rounded bg-coffee-input mr-1">
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}

        {requirements.confirmation_required && (
          <div className="mt-4 p-3 coffee-border rounded-md mb-4">
            <div className="text-xs coffee-primary mb-2">Confirmation Required</div>
            <div className="text-sm coffee-muted-foreground">
              Some facts require your confirmation before the notice can be generated.
            </div>
          </div>
        )}

        {blockingReasons.length > 0 && (
          <div className="mt-4 p-3 coffee-border rounded-md mb-4">
            <div className="text-xs coffee-error mb-2">Generation Blocked</div>
            <div className="text-sm coffee-foreground">
              {blockingReasons.map((reason, i) => (
                <div key={i} className="text-sm mb-1">
                  ⚠ {reason}
                </div>
              ))}
            </div>
          </div>
        )}

        {canGenerate && (
          <Button
            size="sm"
            onClick={handleGenerate}
            disabled={generateLoading}
            className="w-full mt-3"
          >
            {generateLoading ? "Generating..." : "Generate Legal Notice"}
          </Button>
        )}

        {canGenerate === false && (
          <Button
            size="sm"
            onClick={handlePrepare}
            disabled={requirementsLoading}
            className="w-full mt-3"
          >
            {requirementsLoading ? "Checking requirements..." : "Prepare Legal Notice"}
          </Button>
        )}
      </div>
    )
  }

  if (document) {
    return (
      <div className="coffee-surface p-6">
        <Alert variant="default">
          <AlertTitle>Legal Notice Generated</AlertTitle>
          <AlertDescription>{document.message}</AlertDescription>
        </Alert>

        <div className="mt-4">
          <div className="text-sm coffee-muted mb-2">
            Status: {document.status}
            {document.document_id && (
              <span className="ml-2">
                • ID: {document.document_id.substring(0, 8)}...
              </span>
            )}
          </div>

          <Card>
            <CardContent>
              <div className="space-y-2 text-sm coffee-foreground">
                <div className="whitespace-pre-wrap" style={{ whiteSpace: "pre-wrap", backgroundColor: "white", padding: "1rem", borderRadius: "0.5rem" }}>
                  {draftContent || (
                    <Skeleton className="h-64 rounded-md bg-coffee-input animate-pulse" />
                  )}
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button
                size="sm"
                onClick={handleSave}
                disabled={generateLoading || unsavedChanges}
                className="w-full"
              >
                {generateLoading ? "Saving..." : unsavedChanges ? "Saving..." : "Save Changes"}
              </Button>
              <Button
                size="sm"
                onClick={onClose}
                variant="outline"
                className="w-full mt-2"
              >
                Close
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    )
  }

  return null
}
