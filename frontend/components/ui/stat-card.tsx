"use client";

import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  trend?: { direction: "up" | "down" | "flat"; label: string };
  variant?: "default" | "success" | "danger" | "warning" | "gold";
  className?: string;
}

const variantStyles = {
  default: "text-foreground",
  success: "text-green-400",
  danger: "text-red-400",
  warning: "text-amber-400",
  gold: "text-primary",
};

const iconVariantStyles = {
  default: "bg-muted text-muted-foreground",
  success: "bg-green-400/10 text-green-400",
  danger: "bg-red-400/10 text-red-400",
  warning: "bg-amber-400/10 text-amber-400",
  gold: "bg-primary/10 text-primary",
};

export function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  variant = "default",
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "glass glass-border rounded-xl p-3 sm:p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div
          className={cn(
            "size-7 sm:size-9 rounded-lg flex items-center justify-center",
            iconVariantStyles[variant]
          )}
        >
          <Icon className="size-3.5 sm:size-4" />
        </div>
        {trend && (
          <span
            className={cn(
              "text-[10px] sm:text-xs font-medium px-1.5 sm:px-2 py-0.5 rounded-full",
              trend.direction === "up" && "bg-green-400/10 text-green-400",
              trend.direction === "down" && "bg-red-400/10 text-red-400",
              trend.direction === "flat" && "bg-muted text-muted-foreground"
            )}
          >
            {trend.direction === "up" && "+"}
            {trend.label}
          </span>
        )}
      </div>
      <div className="mt-2 sm:mt-3">
        <p className="text-[10px] sm:text-xs text-muted-foreground">{label}</p>
        <p
          className={cn(
            "mt-0.5 sm:mt-1 text-base sm:text-xl font-bold font-mono tracking-tight truncate",
            variantStyles[variant]
          )}
        >
          {value}
        </p>
      </div>
    </div>
  );
}
