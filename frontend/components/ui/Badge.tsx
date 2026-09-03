import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  variant?: "green" | "amber" | "red" | "blue" | "gray" | "purple";
  className?: string;
}

const variants = {
  green:  "bg-green-100 text-green-800",
  amber:  "bg-amber-100 text-amber-800",
  red:    "bg-red-100 text-red-800",
  blue:   "bg-blue-100 text-blue-800",
  gray:   "bg-gray-100 text-gray-700",
  purple: "bg-purple-100 text-purple-800",
};

export function Badge({ children, variant = "gray", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
