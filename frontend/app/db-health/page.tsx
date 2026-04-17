"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageInstructions } from "@/components/layout/PageInstructions";

interface PoolStats {
  size: number;
  checked_out: number;
  checked_in: number;
  overflow: number;
  total_capacity: number;
  utilization: number;
}

interface PoolSample extends PoolStats {
  ts: number;
}

interface SlowQuery {
  sql: string;
  duration_ms: number;
  timestamp: number;
}

interface LongHold {
  path: string;
  method: string;
  duration_ms: number;
  checkouts: number;
  timestamp: number;
}

interface PoolHealthResponse {
  pool: PoolStats;
  samples: PoolSample[];
  slow_queries: SlowQuery[];
  long_holds: LongHold[];
  thresholds: {
    alert_utilization: number;
    alert_sustained_seconds: number;
    slow_query_ms: number;
    request_warn_ms: number;
    request_error_ms: number;
  };
}

function fmtTs(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString();
}

function utilizationColor(u: number): string {
  if (u >= 0.85) return "text-red-600 dark:text-red-400";
  if (u >= 0.7) return "text-orange-600 dark:text-orange-400";
  if (u >= 0.5) return "text-amber-600 dark:text-amber-400";
  return "text-green-600 dark:text-green-400";
}

export default function DbHealthPage() {
  const [data, setData] = useState<PoolHealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await api.get<PoolHealthResponse>("/health/pool");
        setData(res.data);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      }
    };
    fetchHealth();
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") fetchHealth();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader title="DB Health" subtitle="PostgreSQL pool + slow queries" />
      <PageInstructions
        items={[
          "Live PostgreSQL connection-pool metrics, slow queries, and requests holding DB connections too long.",
          "Refreshes every 10s when tab is visible.",
          `Telegram alert fires when utilization ≥ ${data ? Math.round(data.thresholds.alert_utilization * 100) : 70}% sustained for ${data ? data.thresholds.alert_sustained_seconds : 60}s.`,
        ]}
      />

      {error && <div className="rounded border border-red-300 bg-red-50 p-3 text-red-700 dark:border-red-700 dark:bg-red-950 dark:text-red-300">{error}</div>}

      {data && (
        <>
          <section className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <Stat label="Utilization" value={`${Math.round(data.pool.utilization * 100)}%`} cls={utilizationColor(data.pool.utilization)} />
            <Stat label="Checked out" value={`${data.pool.checked_out}/${data.pool.total_capacity}`} />
            <Stat label="Checked in" value={String(data.pool.checked_in)} />
            <Stat label="Overflow" value={String(data.pool.overflow)} />
            <Stat label="Pool size" value={String(data.pool.size)} />
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold">Utilization (last {data.samples.length} samples × 10s)</h2>
            <Sparkline samples={data.samples} threshold={data.thresholds.alert_utilization} />
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold">Top slow queries ({'>'} {data.thresholds.slow_query_ms}ms)</h2>
            {data.slow_queries.length === 0 ? (
              <p className="text-sm text-muted-foreground">No slow queries recorded.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead className="bg-muted/40">
                    <tr>
                      <th className="border-b p-2 text-left">Duration</th>
                      <th className="border-b p-2 text-left">When</th>
                      <th className="border-b p-2 text-left">SQL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.slow_queries.map((q, i) => (
                      <tr key={i} className="border-b">
                        <td className="p-2 font-mono text-red-600 dark:text-red-400">{q.duration_ms.toFixed(0)}ms</td>
                        <td className="p-2">{fmtTs(q.timestamp)}</td>
                        <td className="p-2 font-mono text-xs">{q.sql}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold">Long-hold requests ({'>'} {data.thresholds.request_warn_ms}ms)</h2>
            {data.long_holds.length === 0 ? (
              <p className="text-sm text-muted-foreground">No long-hold requests recorded.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead className="bg-muted/40">
                    <tr>
                      <th className="border-b p-2 text-left">Duration</th>
                      <th className="border-b p-2 text-left">Method</th>
                      <th className="border-b p-2 text-left">Path</th>
                      <th className="border-b p-2 text-left">Checkouts</th>
                      <th className="border-b p-2 text-left">When</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.long_holds.map((h, i) => (
                      <tr key={i} className="border-b">
                        <td className="p-2 font-mono text-orange-600 dark:text-orange-400">{h.duration_ms.toFixed(0)}ms</td>
                        <td className="p-2 font-mono">{h.method}</td>
                        <td className="p-2 font-mono text-xs">{h.path}</td>
                        <td className="p-2">{h.checkouts}</td>
                        <td className="p-2">{fmtTs(h.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function Stat({ label, value, cls }: { label: string; value: string; cls?: string }) {
  return (
    <div className="rounded border bg-card p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${cls ?? ""}`}>{value}</div>
    </div>
  );
}

function Sparkline({ samples, threshold }: { samples: PoolSample[]; threshold: number }) {
  if (samples.length === 0) {
    return <p className="text-sm text-muted-foreground">No samples yet.</p>;
  }
  const width = 600;
  const height = 80;
  const maxN = Math.max(samples.length, 1);
  const points = samples
    .map((s, i) => `${(i / maxN) * width},${height - Math.min(s.utilization, 1) * height}`)
    .join(" ");
  const thresholdY = height - threshold * height;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full max-w-2xl border rounded bg-card">
      <line x1="0" y1={thresholdY} x2={width} y2={thresholdY} stroke="#f97316" strokeDasharray="4 4" strokeWidth="1" />
      <polyline fill="none" stroke="#3b82f6" strokeWidth="2" points={points} />
    </svg>
  );
}
