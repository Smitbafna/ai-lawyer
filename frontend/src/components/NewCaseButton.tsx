import React from "react"

interface NewCaseButtonProps {
  onCreate: () => void
}

export const NewCaseButton: React.FC<NewCaseButtonProps> = ({ onCreate }) => {
  return (
    <button
      onClick={onCreate}
      className="w-full bg-coffee-primary text-coffee-foreground rounded-md hover:bg-coffee-primary-hover transition-colors py-3 px-4 font-medium"
    >
      <span className="mr-2">+</span> New Case
    </button>
  )
}