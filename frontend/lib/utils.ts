import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number): string {
  return `₹${price.toLocaleString("en-IN")}`;
}

export function formatQuantity(qty: number): string {
  return `${qty.toLocaleString("en-IN")} qtl`;
}

export function getTrendColor(trend?: string): string {
  if (trend === "up") return "text-green-600";
  if (trend === "down") return "text-red-600";
  return "text-gray-500";
}

export function getTrendIcon(trend?: string): string {
  if (trend === "up") return "↑";
  if (trend === "down") return "↓";
  return "→";
}
