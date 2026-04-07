"use client";

import { Newspaper } from "lucide-react";
import SentimentBadge from "./SentimentBadge";
import { cn } from "@/lib/utils";

type Props = {
  headline: string;
  source: string;
  time: string;
  sentimentLabel: string;
  sentimentScore: number;
};

const borderColorMap: Record<string, string> = {
  bullish: "border-l-green-500/50",
  bearish: "border-l-red-500/50",
  neutral: "border-l-muted-foreground/30",
};

export default function NewsCard({ headline, source, time, sentimentLabel, sentimentScore }: Props) {
  const timeAgo = getTimeAgo(time);

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg glass glass-border border-l-2 p-3 transition-colors hover:bg-secondary/50",
        borderColorMap[sentimentLabel] || borderColorMap.neutral
      )}
    >
      <Newspaper className="size-4 mt-0.5 text-muted-foreground shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{headline}</p>
        <div className="flex items-center gap-2 mt-1.5">
          <span className="text-[11px] text-muted-foreground">{source}</span>
          <span className="text-[11px] text-muted-foreground/40">·</span>
          <span className="text-[11px] text-muted-foreground">{timeAgo}</span>
        </div>
      </div>
      <SentimentBadge label={sentimentLabel} score={sentimentScore} size="sm" />
    </div>
  );
}

function getTimeAgo(isoTime: string): string {
  const diff = Date.now() - new Date(isoTime).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
