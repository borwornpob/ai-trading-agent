"use client";

import { useEffect, useState, useCallback } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import api from "@/lib/api";

interface ServiceStatus {
  name: string;
  status: string;
  latency_ms: number;
  detail: string;
}

const SERVICE_ICONS: Record<string, string> = {
  "Anthropic API": "🤖",
  "MT5 Bridge": "📊",
  "Redis": "⚡",
  "PostgreSQL": "🗄️",
  "Binance": "💰",
};

const STATUS_STYLES: Record<string, string> = {
  connected: "bg-green-500/20 text-green-400 border-green-500/30",
  error: "bg-red-500/20 text-red-400 border-red-500/30",
  disabled: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  testing: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
};

export default function IntegrationPage() {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingService, setTestingService] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.get("/api/integration/status");
      setServices(res.data.services);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const testService = async (serviceName: string) => {
    const serviceKey = serviceName.toLowerCase().replace(/\s+/g, "").replace("api", "");
    const keyMap: Record<string, string> = {
      "anthropic": "anthropic",
      "mt5bridge": "mt5",
      "redis": "redis",
      "postgresql": "db",
      "binance": "binance",
    };
    const key = keyMap[serviceKey] || serviceKey;

    setTestingService(serviceName);
    try {
      const res = await api.get(`/api/integration/test/${key}`);
      setServices((prev) =>
        prev.map((s) => (s.name === serviceName ? res.data : s))
      );
    } catch {
      setServices((prev) =>
        prev.map((s) =>
          s.name === serviceName
            ? { ...s, status: "error", detail: "Request failed" }
            : s
        )
      );
    } finally {
      setTestingService(null);
    }
  };

  const testAll = async () => {
    setLoading(true);
    await fetchStatus();
  };

  const connectedCount = services.filter((s) => s.status === "connected").length;

  return (
    <div className="p-4 lg:p-6 space-y-6">
      <PageHeader
        title="Integration"
        subtitle={`${connectedCount}/${services.length} services connected`}
      >
        <button
          onClick={testAll}
          disabled={loading}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? "Testing..." : "Test All"}
        </button>
      </PageHeader>

      {loading && services.length === 0 ? (
        <div className="text-center text-muted-foreground py-8">Testing connections...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((s) => (
            <div
              key={s.name}
              className={`rounded-lg border p-5 ${STATUS_STYLES[s.status] || STATUS_STYLES.error}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{SERVICE_ICONS[s.name] || "🔌"}</span>
                  <div>
                    <h3 className="font-semibold text-sm">{s.name}</h3>
                    <span className={`text-xs font-medium uppercase ${
                      s.status === "connected" ? "text-green-400" :
                      s.status === "error" ? "text-red-400" :
                      "text-zinc-400"
                    }`}>
                      {s.status}
                    </span>
                  </div>
                </div>
                {s.latency_ms > 0 && (
                  <span className="text-xs text-muted-foreground">{s.latency_ms}ms</span>
                )}
              </div>

              <p className="text-xs text-muted-foreground mb-3 min-h-8">{s.detail}</p>

              <button
                onClick={() => testService(s.name)}
                disabled={testingService === s.name}
                className="text-xs px-3 py-1.5 rounded border border-current/20 hover:bg-white/5 disabled:opacity-50 w-full"
              >
                {testingService === s.name ? "Testing..." : "Test Connection"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
