import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    rag: "bg-blue-500",
    chatbot: "bg-green-500",
    agent: "bg-purple-500",
    multi_agent: "bg-pink-500",
    automation: "bg-orange-500",
    search: "bg-cyan-500",
    vision: "bg-indigo-500",
    voice: "bg-teal-500",
    coding: "bg-amber-500",
    finance: "bg-emerald-500",
    research: "bg-violet-500",
    other: "bg-slate-500",
  };
  return colors[category] || colors.other;
}

export function getComplexityBadge(complexity: string): {
  label: string;
  color: string;
} {
  const badges: Record<string, { label: string; color: string }> = {
    beginner: { label: "Beginner", color: "bg-green-100 text-green-800" },
    intermediate: {
      label: "Intermediate",
      color: "bg-yellow-100 text-yellow-800",
    },
    advanced: { label: "Advanced", color: "bg-red-100 text-red-800" },
  };
  return badges[complexity] || badges.beginner;
}

export function formatDate(dateValue: string | number): string {
  const date =
    typeof dateValue === "number" && dateValue < 10_000_000_000
      ? new Date(dateValue * 1000)
      : new Date(dateValue);

  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
