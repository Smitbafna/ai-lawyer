import * as React from "react"
import { cn } from "cn"

function Avatar({
  className,
  ...props
}: React.ComponentProps<"div"> & {
  className?: string
}) {
  return (
    <div
      className={cn(
        "rounded-full bg-coffee-surface border border-coffee-border/20",
        className
      )}
      {...props}
    />
  )
}

function AvatarImage({
  className,
  ...props
}: React.ComponentProps<"img"> & {
  className?: string
}) {
  return (
    <img
      className={cn(
        "rounded-full object-cover",
        "h-12 w-12",
        className
      )}
      {...props}
    />
  )
}

function AvatarGroup({
  className,
  ...props
}: React.ComponentProps<"div"> & {
  className?: string
}) {
  return (
    <div
      className={cn(
        "relative inline-flex rounded-full w-8 h-8",
        className
      )}
      {...props}
    />
  )
}

export { Avatar, AvatarImage, AvatarGroup }