"use client";

import { type ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
}

export function PageHeader({ title, subtitle, children }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-4 sm:pb-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold gold-gradient-text">{title}</h2>
        {subtitle && (
          <p className="mt-0.5 text-xs sm:text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>
      {children && <div className="flex items-center gap-2 sm:gap-3 flex-wrap">{children}</div>}
    </div>
  );
}
