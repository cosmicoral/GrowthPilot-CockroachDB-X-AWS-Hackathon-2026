import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-[8px] font-[family-name:var(--font-body,_'Oranienbaum',_serif)] transition-all duration-200 cursor-pointer disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        // Dark navy — primary action buttons (Sign In, Create Account, Send, etc.)
        default:
          "bg-[#0d2137] text-white border-none hover:bg-[#1a3a5c] font-bold",
        // Transparent with border — secondary actions
        outline:
          "bg-[rgba(74,122,181,0.10)] text-[#2d5a8e] border border-[rgba(74,122,181,0.25)] hover:bg-[rgba(74,122,181,0.18)]",
        // Ghost with white glass — nav pills, quick suggestion chips
        ghost:
          "bg-[rgba(255,255,255,0.45)] text-[#2d5a8e] border border-[rgba(255,255,255,0.6)] hover:bg-[rgba(255,255,255,0.7)] hover:text-[#0d2137] backdrop-blur-[4px]",
        // Transparent no border
        link: "bg-transparent border-none text-[#2d5a8e] hover:text-[#0d2137] underline-offset-4 hover:underline p-0",
      },
      size: {
        default: "px-[18px] py-[13px] text-[19px]",
        sm: "px-[14px] py-[6px] text-[15px] rounded-[6px]",
        xs: "px-[11px] py-[4px] text-[12px] rounded-[6px]",
        icon: "w-[34px] h-[34px] p-0 rounded-[9px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
