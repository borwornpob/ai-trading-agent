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
  // Map -1..1 to 0..180 degrees (left to right arc)
  const angle = ((clampedValue + 1) / 2) * 180;
  const r = size * 0.38;
  const cx = size / 2;
  const cy = size * 0.55;
  const startAngle = Math.PI;
  const endAngle = 0;

  // Arc path (semicircle from left to right)
  const arcStart = {
    x: cx + r * Math.cos(startAngle),
    y: cy - r * Math.sin(startAngle),
  };
  const arcEnd = {
    x: cx + r * Math.cos(endAngle),
    y: cy - r * Math.sin(endAngle),
  };
  const arcPath = `M ${arcStart.x} ${arcStart.y} A ${r} ${r} 0 0 1 ${arcEnd.x} ${arcEnd.y}`;

  // Needle position
  const needleAngle = Math.PI - (angle * Math.PI) / 180;
  const needleLen = r * 0.85;
  const needleX = cx + needleLen * Math.cos(needleAngle);
  const needleY = cy - needleLen * Math.sin(needleAngle);

  const getColor = () => {
    if (clampedValue > 0.2) return { stroke: "#4ade80", text: "text-green-400" };
    if (clampedValue < -0.2) return { stroke: "#f87171", text: "text-red-400" };
    return { stroke: "oklch(0.80 0.15 85)", text: "text-primary" };
  };

  const colors = getColor();

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <svg width={size} height={size * 0.65} viewBox={`0 0 ${size} ${size * 0.65}`}>
        {/* Background arc */}
        <path
          d={arcPath}
          fill="none"
          stroke="oklch(0.22 0.008 250)"
          strokeWidth={8}
          strokeLinecap="round"
        />
        {/* Colored arc up to needle */}
        <path
          d={arcPath}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={`${(angle / 180) * Math.PI * r} ${Math.PI * r}`}
          className="transition-all duration-700 ease-out"
        />
        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={needleX}
          y2={needleY}
          stroke={colors.stroke}
          strokeWidth={2.5}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
        {/* Center dot */}
        <circle cx={cx} cy={cy} r={4} fill={colors.stroke} />
        {/* Labels */}
        <text x={arcStart.x - 4} y={cy + 16} fill="oklch(0.60 0.01 250)" fontSize={10} textAnchor="middle">-1</text>
        <text x={cx} y={cy - r - 8} fill="oklch(0.60 0.01 250)" fontSize={10} textAnchor="middle">0</text>
        <text x={arcEnd.x + 4} y={cy + 16} fill="oklch(0.60 0.01 250)" fontSize={10} textAnchor="middle">+1</text>
      </svg>
      <p className={cn("text-3xl font-bold font-mono mt-1", colors.text)}>
        {clampedValue > 0 ? "+" : ""}
        {clampedValue.toFixed(2)}
      </p>
      <p className="text-xs uppercase tracking-wider text-muted-foreground mt-1">
        {label}
      </p>
    </div>
  );
}
