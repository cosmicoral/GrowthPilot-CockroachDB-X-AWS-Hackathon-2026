import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          // Matches existing Figma dashed-border input style exactly
          "w-full px-[14px] py-[12px] rounded-[8px]",
          "border-[1.5px] border-dashed border-[rgba(74,122,181,0.4)]",
          "bg-[rgba(255,255,255,0.6)]",
          "font-[family-name:'Oranienbaum',serif] text-[14px] text-[#0d2137]",
          "outline-none transition-[border-color] duration-200",
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
Input.displayName = "Input"

export { Input }
