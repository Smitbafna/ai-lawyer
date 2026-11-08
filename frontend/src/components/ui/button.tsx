import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"

const buttonVariants = cva(
  [
    "group/button relative inline-flex shrink-0 items-center justify-center gap-2",
    "border border-transparent bg-clip-padding text-sm font-medium tracking-tight whitespace-nowrap",
    "select-none outline-none",
    "transition-all duration-200 ease-out",
    "hover:-translate-y-px active:translate-y-0 active:scale-[0.97]",
    "focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/40",
    "disabled:pointer-events-none disabled:translate-y-0 disabled:opacity-50",
    "aria-invalid:border-destructive aria-invalid:ring-2 aria-invalid:ring-destructive/20",
    "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  ],
  {
    variants: {
      variant: {
        default:
          "bg-linear-to-b from-coffee-primary to-coffee-primary-hover text-coffee-primary-foreground " +
          "shadow-[0_1px_2px_rgb(0_0_0/0.18),inset_0_1px_0_rgb(255_255_255/0.18)] " +
          "hover:shadow-[0_6px_16px_-4px_rgb(0_0_0/0.35),inset_0_1px_0_rgb(255_255_255/0.18)] hover:brightness-110",
        soft:
          "bg-coffee-primary/10 text-coffee-primary hover:bg-coffee-primary/20",
        outline:
          "border-border bg-background text-foreground shadow-xs hover:bg-muted hover:shadow-sm " +
          "dark:border-input dark:bg-input/30 dark:hover:bg-input/50",
        secondary:
          "bg-coffee-secondary text-coffee-secondary-hover shadow-xs hover:bg-coffee-accent hover:shadow-sm",
        ghost:
          "text-coffee-foreground hover:translate-y-0 hover:bg-coffee-surface-muted",
        destructive:
          "bg-coffee-error/10 text-coffee-error hover:bg-coffee-error/20 focus-visible:ring-coffee-error/30",
        link:
          "text-coffee-primary underline-offset-4 hover:translate-y-0 hover:underline active:scale-100",
      },
      size: {
        default: "h-9 rounded-full px-5",
        xs: "h-7 rounded-full px-3 text-xs gap-1",
        sm: "h-8 rounded-full px-4 text-xs gap-1.5",
        lg: "h-11 rounded-full px-7 text-base",
        inline: "h-auto rounded-sm p-0 text-[inherit]",
        icon: "size-9 rounded-full",
        "icon-xs": "size-6 rounded-full",
        "icon-sm": "size-8 rounded-full",
        "icon-lg": "size-10 rounded-full",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Spinner() {
  return (
    <span
      aria-hidden
      className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
    />
  )
}

type ButtonProps = ButtonPrimitive.Props &
  VariantProps<typeof buttonVariants> & {
    loading?: boolean
  }

function Button({
  className,
  variant = "default",
  size = "default",
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <ButtonPrimitive
      data-slot="button"
      aria-busy={loading || undefined}
      disabled={disabled || loading}
      className={cn(
        buttonVariants({ variant, size }),
        loading && "disabled:opacity-80",
        className
      )}
      {...props}
    >
      {loading && <Spinner />}
      {children}
    </ButtonPrimitive>
  )
}

export { Button, buttonVariants }