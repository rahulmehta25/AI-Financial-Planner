"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

interface ProgressProps
  extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  showLabel?: boolean;
  label?: string;
  steps?: Array<{ label: string; completed: boolean }>;
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value = 0, showLabel = false, label, steps, ...props }, ref) => (
  <div className="w-full">
    {(showLabel || label || steps) && (
      <div className="flex justify-between items-center mb-2">
        {label && (
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
          </span>
        )}
        {showLabel && (
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {Math.round(value || 0)}%
          </span>
        )}
      </div>
    )}
    
    {steps && (
      <div className="flex justify-between items-center mb-2">
        {steps.map((step, index) => (
          <div key={index} className="flex flex-col items-center">
            <div
              className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium",
                step.completed
                  ? "bg-primary text-primary-foreground"
                  : "bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
              )}
            >
              {step.completed ? (
                <svg
                  className="w-4 h-4"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span className="text-xs text-gray-600 dark:text-gray-400 mt-1 max-w-[80px] text-center">
              {step.label}
            </span>
          </div>
        ))}
      </div>
    )}
    
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-secondary",
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className="h-full w-full flex-1 bg-primary transition-all"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  </div>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };