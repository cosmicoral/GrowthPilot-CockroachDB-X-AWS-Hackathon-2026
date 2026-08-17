import * as React from "react"
import { cn } from "@/lib/utils"

// ── Card ──────────────────────────────────────────────────────────────────────
// Matches the existing frosted-glass card style used throughout the dashboard:
//   background: rgba(255,255,255,0.5)
//   border: 1.5px solid rgba(255,255,255,0.65)
//   borderRadius: 16
//   padding: 20px
//   backdropFilter: blur(6px)

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "bg-[rgba(255,255,255,0.5)] border-[1.5px] border-[rgba(255,255,255,0.65)] rounded-[16px] p-[20px] backdrop-blur-[6px]",
        className
      )}
      {...props}
    />
  )
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 mb-[16px]", className)} {...props} />
  )
)
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        "font-[family-name:'Playfair_Display',serif] text-[17px] font-bold text-[#0d2137] leading-none tracking-tight",
        className
      )}
      {...props}
    />
  )
)
CardTitle.displayName = "CardTitle"

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("", className)} {...props} />
  )
)
CardContent.displayName = "CardContent"

export { Card, CardHeader, CardTitle, CardContent }
