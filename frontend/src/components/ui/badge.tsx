import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

// Matches the existing memory source badge styling in AIPartner.tsx
const badgeVariants = cva(
  "inline-flex items-center rounded-[3px] px-[5px] py-[1px] text-[10px] font-bold leading-none tracking-[0.04em] uppercase",
  {
    variants: {
      variant: {
        // "you" badge — blue
        user: "bg-[rgba(74,122,181,0.12)] text-[#4a7ab5]",
        // "reflection" badge — purple
        reflection: "bg-[rgba(109,40,217,0.10)] text-[#6d28d9]",
        // saved-as-reflection memory badge
        memoryTag:
          "bg-[rgba(109,40,217,0.10)] border border-[rgba(109,40,217,0.22)] rounded-[12px] px-[10px] py-[4px] text-[11px] text-[#6d28d9] normal-case font-[family-name:'Oranienbaum',serif] tracking-normal",
        // category tags like "AI & SaaS", "B2B Marketing"
        tag: "bg-[rgba(74,122,181,0.15)] text-[#2d5a8e] rounded-[4px] px-[7px] py-[2px] text-[15px] normal-case font-bold tracking-normal",
      },
    },
    defaultVariants: {
      variant: "user",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
