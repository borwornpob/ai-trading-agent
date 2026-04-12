"use client";

import { useState } from "react";
import { Info, X } from "lucide-react";

interface PageInstructionsProps {
  pageId: string;
  items: string[];
}

export function PageInstructions({ items }: PageInstructionsProps) {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <Info className="size-3.5 text-muted-foreground mt-0.5 shrink-0" />
          <ul className="space-y-1 text-xs text-muted-foreground">
            {items.map((text, i) => (
              <li key={i}>{text}</li>
            ))}
          </ul>
        </div>
        <button
          type="button"
          onClick={() => setVisible(false)}
          className="text-muted-foreground/50 hover:text-muted-foreground transition-colors shrink-0"
        >
          <X className="size-4" />
        </button>
      </div>
    </div>
  );
}
