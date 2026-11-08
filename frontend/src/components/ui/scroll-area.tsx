import * as React from "react"
import { cn } from "cn"

function ScrollArea({
  className,
  ...props
}: React.ComponentProps<"div"> & {
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex-1 overflow-y-auto scrollbar-thin scrollbar-coffee-border",
        className
      )}
      {...props}
    />
  )
}

export { ScrollArea }