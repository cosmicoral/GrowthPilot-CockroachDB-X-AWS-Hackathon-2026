import * as React from "react"
import * as TabsPrimitive from "@radix-ui/react-tabs"
import { cn } from "@/lib/utils"

const Tabs = TabsPrimitive.Root

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn("flex w-full max-w-full gap-[6px] overflow-x-auto pb-[4px]", className)}
    {...props}
  />
))
TabsList.displayName = TabsPrimitive.List.displayName

// Matches existing ContentCreation tab button style exactly
const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      // Inactive state
      "font-[family-name:'Oranienbaum',serif] text-[17px] font-medium",
      "shrink-0 px-[18px] py-[8px] rounded-[8px] cursor-pointer transition-all duration-200",
      "bg-[rgba(255,255,255,0.45)] border-[1.5px] border-[rgba(255,255,255,0.6)] text-[#2d5a8e]",
      "hover:bg-[rgba(255,255,255,0.65)]",
      // Active state — matches: background: "#0d2137", color: "#fff", fontWeight: 700
      "data-[state=active]:bg-[#0d2137] data-[state=active]:text-white data-[state=active]:font-bold data-[state=active]:border-transparent",
      className
    )}
    {...props}
  />
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn("outline-none", className)}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName

export { Tabs, TabsList, TabsTrigger, TabsContent }
