import { cn } from "cn"

interface BadgeProps {
  className?: string
  variant?: "default" | "primary" | "secondary" | "success" | "warning" | "destructive" | "outline"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "coffee-primary",
    primary: "coffee-primary",
    secondary: "coffee-secondary",
    success: "coffee-success",
    warning: "coffee-warning",
    destructive: "coffee-error",
    outline: "coffee-border",
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium coffee-foreground [&:not([data-state=hidden])]:visible [&:not([data-state=hidden])]:focus-visible:outline-none [&:not([data-state=hidden])]:focus-visible:ring-2 [&:not([data-state=hidden])]:focus-visible:ring-coffee-primary [&>:not(svg)]:shrink-0 [&>svg]:h-4 [&>svg]:w-4 [&>svg]:stroke-current [&>svg]:opacity-50",
        `bg-${variants[variant]}`,
        className
      )}
      {...props}
    />
  )
}

export { Badge }