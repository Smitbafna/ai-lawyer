import * as React from "react"
import { cn } from "cn"

function Tooltip({
  children,
  className,
  ...props
}: React.ComponentProps<"div"> & {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={cn("relative inline-block", className)}
      {...props}
    >
      {children}
    </div>
  )
}

export { Tooltip }