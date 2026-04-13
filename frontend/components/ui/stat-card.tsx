"use client";

import { type LucideIcon } from "lucide-react";
import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  icon?: LucideIcon;
  iconNode?: ReactNode;
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: { direction: "up" | "down" | "flat"; label: string };
  variant?: "default" | "success" | "danger" | "warning" | "gold";
  className?: string;
}

const variantStyles = {
  default: "text-foreground",
  success: "text-success dark:text-green-400",
  danger: "text-destructive",
  warning: "text-amber-600 dark:text-amber-400",
  gold: "text-primary-foreground dark:text-primary",
};

const iconVariantStyles = {
  default: "bg-muted text-muted-foreground",
  success: "bg-success/10 text-success dark:bg-green-400/10 dark:text-green-400",
  danger: "bg-destructive/10 text-destructive",
  warning: "bg-amber-100 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400",
  gold: "bg-primary/10 text-primary-foreground dark:text-primary",
};

export function StatCard({
  icon: Icon,
  iconNode,
  label,
  value,
  subtitle,
  trend,
  variant = "default",
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border p-3 card-hover",
        "bg-card",
        className
      )}
    >
      <div
        className={cn(
          "size-6 rounded-lg flex items-center justify-center mb-1.5",
          iconVariantStyles[variant]
        )}
      >
        {iconNode ? iconNode : Icon ? <Icon className="size-3" /> : null}
      </div>
      <p className="text-[11px] text-muted-foreground font-medium">{label}</p>
      <p
        className={cn(
          "mt-0.5 text-sm font-bold font-mono tracking-tight truncate",
          variantStyles[variant]
        )}
      >
        {value}
      </p>
      {subtitle && (
        <p className="mt-0.5 text-[10px] text-muted-foreground font-medium truncate">{subtitle}</p>
      )}
    </div>
  );
}
