import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          // Matches exactly: ContentCreation.tsx textarea style
          "w-full min-h-[380px]",
          "bg-[rgba(255,255,255,0.55)]",
          "border-[1.5px] border-dashed border-[rgba(74,122,181,0.35)] rounded-[10px]",
          "p-[16px]",
          "font-[family-name:'Oranienbaum',serif] text-[15px] leading-[1.65] text-[#0d2137]",
          "resize-vertical outline-none box-border",
          "placeholder:text-[rgba(13,33,55,0.4)]",
          "focus:border-[#4a7ab5]",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
