"use client";

import { cn } from "@/lib/utils";

interface GoldGaugeProps {
  value: number; // -1 to 1
  label: string;
  size?: number;
  className?: string;
}

export function GoldGauge({
  value,
  label,
  size = 180,
  className,
}: GoldGaugeProps) {
  const clampedValue = Math.max(-1, Math.min(1, value));
  const angle = ((clampedValue + 1) / 2) * 180;
  const r = size * 0.38;
  const cx = size / 2;
  const cy = size * 0.55;
  const startAngle = Math.PI;
  const endAngle = 0;

  const arcStart = {
    x: cx + r * Math.cos(startAngle),
    y: cy - r * Math.sin(startAngle),
  };
  const arcEnd = {
    x: cx + r * Math.cos(endAngle),
    y: cy - r * Math.sin(endAngle),
  };
  const arcPath = `M ${arcStart.x} ${arcStart.y} A ${r} ${r} 0 0 1 ${arcEnd.x} ${arcEnd.y}`;

  const needleAngle = Math.PI - (angle * Math.PI) / 180;
  const needleLen = r * 0.85;
  const needleX = cx + needleLen * Math.cos(needleAngle);
  const needleY = cy - needleLen * Math.sin(needleAngle);

  const getColor = () => {
    if (clampedValue > 0.2) return { stroke: "#054d28", text: "text-success dark:text-green-400", darkStroke: "#4ade80" };
    if (clampedValue < -0.2) return { stroke: "#d03238", text: "text-destructive", darkStroke: "#f87171" };
    return { stroke: "#9fe870", text: "text-primary-foreground dark:text-primary", darkStroke: "#9fe870" };
  };

  const colors = getColor();

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <svg width={size} height={size * 0.65} viewBox={`0 0 ${size} ${size * 0.65}`}>
        {/* Background arc */}
        <path
          d={arcPath}
          fill="none"
          className="stroke-muted"
          strokeWidth={8}
          strokeLinecap="round"
        />
        {/* Colored arc */}
        <path
          d={arcPath}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={`${(angle / 180) * Math.PI * r} ${Math.PI * r}`}
          className="transition-all duration-700 ease-out dark:hidden"
        />
        <path
          d={arcPath}
          fill="none"
          stroke={colors.darkStroke}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={`${(angle / 180) * Math.PI * r} ${Math.PI * r}`}
          className="transition-all duration-700 ease-out hidden dark:block"
        />
        {/* Needle */}
        <line
          x1={cx} y1={cy} x2={needleX} y2={needleY}
          stroke={colors.stroke}
          strokeWidth={2.5}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out dark:hidden"
        />
        <line
          x1={cx} y1={cy} x2={needleX} y2={needleY}
          stroke={colors.darkStroke}
          strokeWidth={2.5}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out hidden dark:block"
        />
        {/* Center dot */}
        <circle cx={cx} cy={cy} r={4} fill={colors.stroke} className="dark:hidden" />
        <circle cx={cx} cy={cy} r={4} fill={colors.darkStroke} className="hidden dark:block" />
        {/* Labels */}
        <text x={arcStart.x - 4} y={cy + 16} className="fill-muted-foreground" fontSize={10} textAnchor="middle">-1</text>
        <text x={cx} y={cy - r - 8} className="fill-muted-foreground" fontSize={10} textAnchor="middle">0</text>
        <text x={arcEnd.x + 4} y={cy + 16} className="fill-muted-foreground" fontSize={10} textAnchor="middle">+1</text>
      </svg>
      <p className={cn("text-3xl font-bold font-mono mt-1", colors.text)}>
        {clampedValue > 0 ? "+" : ""}
        {clampedValue.toFixed(2)}
      </p>
      <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold mt-1">
        {label}
      </p>
    </div>
  );
}
