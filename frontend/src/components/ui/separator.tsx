import * as React from "react"
import { cn } from "cn"

function Separator({
  className,
  ...props
}: React.ComponentProps<"hr"> & {
  className?: string
}) {
  return (
    <hr
      className={cn("my-4 border-t border-coffee-border/50", className)}
      {...props}
    />
  )
}

export { Separator }