import * as React from "react"
import { cn } from "cn"

function Card({
  className,
  size = "default",

}: React.ComponentProps<"div"> & { size?: "default" | "sm" }) {
  return (
    <div
      data-slot="card"
      data-size={size}
      className={cn(
        "group/card flex flex-col gap-4 overflow-hidden rounded-xl bg-coffee-surface py-4 text-sm coffee-foreground ring-1 ring-coffee-border/10 [--card-spacing:4] has-data-[slot=card-footer]:pb-0 has-[>img:first-child]:pt-0 data-[size=sm]:[--card-spacing:3] data-[size=sm]:has-data-[slot=card-footer]:pb-0 *:[img:first-child]:rounded-t-xl *:[img:last-child]:rounded-b-xl",
        className
      )}
    />
  )
}

function CardHeader(className?: string) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "group/card-header @container/card-header grid auto-rows-min items-start gap-1 rounded-t-xl px-4 has-data-[slot=card-action]:grid-cols-[1fr_auto] has-data-[slot=card-description]:grid-rows-[auto_auto] [.border-b]:pb-4",
        className
      )}
    />
  )
}

function CardTitle(className?: string) {
  return (
    <div
      data-slot="card-title"
      className={cn(
        "font-heading text-base leading-snug font-medium group-data-[size=sm]/card:text-sm",
        className
      )}
    />
  )
}

function CardDescription(className?: string) {
  return (
    <div
      data-slot="card-description"
      className={cn("text-sm coffee-muted-foreground", className)}
    />
  )
}

function CardAction(className?: string) {
  return (
    <div
      data-slot="card-action"
      className={cn(
        "col-start-2 row-span-2 row-start-1 self-start justify-self-end",
        className
      )}
    />
  )
}

function CardContent(className?: string) {
  return (
    <div
      data-slot="card-content"
      className={cn("px-4", className)}
    />
  )
}

function CardFooter(className?: string) {
  return (
    <div
      data-slot="card-footer"
      className={cn(
        "flex items-center rounded-b-xl border-t border-coffee-border/20 p-4",
        className
      )}
    />
  )
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
}