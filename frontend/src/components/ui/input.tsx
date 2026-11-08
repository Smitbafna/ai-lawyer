import * as React from "react"
import { cn } from "cn"

function Input({
  id,
  type = "text",
  placeholder = "Enter text",
  className,
  ...props
}: React.ComponentProps<"input"> & {
  placeholder?: string
}) {
  return (
    <input
      id={id}
      type={type}
      placeholder={placeholder}
      className={cn(
        "block w-full rounded-md border-coffee-border bg-coffee-input px-3 py-2 coffee-text placeholder-coffee-muted focus:border-coffee-primary focus:outline-none focus:ring-2 focus:ring-coffee-primary/20 transition-colors",
        className
      )}
      {...props}
    />
  )
}

function Textarea({
  id,
  placeholder = "Enter text",
  className,
  ...props
}: React.ComponentProps<"textarea"> & {
  placeholder?: string
}) {
  return (
    <textarea
      id={id}
      placeholder={placeholder}
      className={cn(
        "block w-full rounded-md border-coffee-border bg-coffee-input py-3 px-3 coffee-text placeholder-coffee-muted resize-y focus:border-coffee-primary focus:outline-none focus:ring-2 focus:ring-coffee-primary/20 transition-colors",
        className
      )}
      {...props}
    />
  )
}

export { Input, Textarea }