import React from "react"

interface NewCaseButtonProps {
  onCreate: () => void
}

export const NewCaseButton: React.FC<NewCaseButtonProps> = ({ onCreate }) => {
  return (
    <button
      onClick={onCreate}
      className="btn-new"
    >
      <span>+</span> New Case
    </button>
  )
}