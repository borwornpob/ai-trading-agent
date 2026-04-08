"use client";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Brain, Play, Zap, BarChart3, Target, TrendingUp, Database } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatCard } from "@/components/ui/stat-card";
import { trainModel, getModelStatus, mlPredict, getDataStatus, collectData } from "@/lib/api";

export default function MLPage() {
  const [modelStatus, setModelStatus] = useState<Record<string, unknown> | null>(null);
  const [dataStatus, setDataStatus] = useState<Record<string, unknown>[]>([]);
  const [prediction, setPrediction] = useState<Record<string, unknown> | null>(null);
  const [trainResult, setTrainResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [collecting, setCollecting] = useState(false);

  // Train params
  const [timeframe, setTimeframe] = useState("M15");
  const [forwardBars, setForwardBars] = useState(10);
  const [tpPips, setTpPips] = useState(5.0);
  const [slPips, setSlPips] = useState(5.0);

  // Collect params
  const [collectFrom, setCollectFrom] = useState("2025-04-01");
  const [collectTo, setCollectTo] = useState(new Date().toISOString().split("T")[0]);

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, dataRes] = await Promise.all([
        getModelStatus().catch(() => null),
        getDataStatus().catch(() => null),
      ]);
      if (statusRes) setModelStatus(statusRes.data);
      if (dataRes) setDataStatus(Array.isArray(dataRes.data) ? dataRes.data : []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCollect = async () => {
    setCollecting(true);
    try {
      await collectData({ timeframe, from_date: collectFrom, to_date: collectTo });
      await fetchData();
    } catch (e) { console.error(e); }
    finally { setCollecting(false); }
  };

  const handleTrain = async () => {
    setTraining(true);
    setTrainResult(null);
    try {
      const res = await trainModel({ timeframe, forward_bars: forwardBars, tp_pips: tpPips, sl_pips: slPips });
      setTrainResult(res.data);
      await fetchData();
    } catch (e) { console.error(e); }
    finally { setTraining(false); }
  };

  const handlePredict = async () => {
    setPredicting(true);
    try {
      const res = await mlPredict();
      setPrediction(res.data);
    } catch (e) { console.error(e); }
    finally { setPredicting(false); }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-60 rounded-xl" />
          <Skeleton className="h-60 rounded-xl" />
        </div>
      </div>
    );
  }

  const hasModel = modelStatus?.status === "ready";
  const fi = (modelStatus?.feature_importance_top10 || {}) as Record<string, number>;
  const fiEntries = Object.entries(fi).sort(([, a], [, b]) => b - a);
  const fiMax = fiEntries.length > 0 ? fiEntries[0][1] : 1;

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="ML Model" subtitle="Train and manage LightGBM signal model" />

      {/* Data Status */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Database className="size-4 text-primary" />
            Historical Data
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {dataStatus.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {dataStatus.map((d, i) => (
                <div key={i} className="glass glass-border rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">{d.symbol as string} / {d.timeframe as string}</span>
                    <Badge variant="outline" className="text-[10px]">{(d.bar_count as number).toLocaleString()} bars</Badge>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">
                    {d.first_bar as string} — {d.last_bar as string}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No historical data collected yet.</p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">From</label>
              <Input type="date" value={collectFrom} onChange={(e) => setCollectFrom(e.target.value)} />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">To</label>
              <Input type="date" value={collectTo} onChange={(e) => setCollectTo(e.target.value)} />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Timeframe</label>
              <Select value={timeframe} onValueChange={(v) => v && setTimeframe(v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="M5">M5</SelectItem>
                  <SelectItem value="M15">M15</SelectItem>
                  <SelectItem value="H1">H1</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleCollect} disabled={collecting} className="gold-gradient text-gold-foreground font-semibold hover:opacity-90">
              <Database className="size-4 mr-1.5" />
              {collecting ? "Collecting..." : "Collect Data"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Train */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Brain className="size-4 text-primary" />
              Train Model
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Forward Bars</label>
                <Input type="number" value={forwardBars} onChange={(e) => setForwardBars(parseInt(e.target.value) || 10)} />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">TP (pips)</label>
                <Input type="number" step="0.5" value={tpPips} onChange={(e) => setTpPips(parseFloat(e.target.value) || 5)} />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">SL (pips)</label>
                <Input type="number" step="0.5" value={slPips} onChange={(e) => setSlPips(parseFloat(e.target.value) || 5)} />
              </div>
            </div>
            <Button onClick={handleTrain} disabled={training || dataStatus.length === 0} className="w-full gold-gradient text-gold-foreground font-semibold hover:opacity-90">
              <Play className="size-4 mr-1.5" />
              {training ? "Training..." : "Train Model"}
            </Button>
            {dataStatus.length === 0 && (
              <p className="text-xs text-muted-foreground text-center">Collect historical data first</p>
            )}
          </CardContent>
        </Card>

        {/* Model Status */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Zap className="size-4 text-primary" />
              Model Status
              {hasModel && <Badge className="ml-auto bg-success/20 text-success text-[10px]">Ready</Badge>}
              {!hasModel && <Badge className="ml-auto" variant="outline">No Model</Badge>}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {hasModel ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="glass glass-border rounded p-2">
                    <span className="text-muted-foreground">Timeframe</span>
                    <p className="font-medium">{modelStatus.timeframe as string}</p>
                  </div>
                  <div className="glass glass-border rounded p-2">
                    <span className="text-muted-foreground">Train Period</span>
                    <p className="font-medium text-[10px]">{modelStatus.train_period as string}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">Top Features</p>
                  {fiEntries.slice(0, 8).map(([name, val]) => (
                    <div key={name} className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground w-28 truncate">{name}</span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div className="h-full gold-gradient rounded-full" style={{ width: `${(val / fiMax) * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">Train a model to see status</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Train Result */}
      {trainResult && !trainResult.error && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard icon={Target} label="Accuracy" value={`${((trainResult.accuracy as number) * 100).toFixed(1)}%`} variant={(trainResult.accuracy as number) > 0.4 ? "success" : "warning"} />
          <StatCard icon={BarChart3} label="Train Size" value={(trainResult.train_size as number).toLocaleString()} />
          <StatCard icon={TrendingUp} label="Test Size" value={(trainResult.test_size as number).toLocaleString()} />
          <StatCard icon={Brain} label="Top Feature" value={Object.keys((trainResult.feature_importance_top15 as Record<string, number>) || {})[0] || "N/A"} />
        </div>
      )}
      {trainResult?.error ? (
        <Card className="bg-card border-border">
          <CardContent className="py-4">
            <p className="text-sm text-destructive">{String(trainResult.error)}</p>
          </CardContent>
        </Card>
      ) : null}

      {/* Live Predict */}
      {hasModel && (
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Zap className="size-4 text-primary" />
              Live Prediction
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Button onClick={handlePredict} disabled={predicting} variant="outline">
                <Zap className="size-4 mr-1.5" />
                {predicting ? "Predicting..." : "Predict Now"}
              </Button>
              {prediction && !prediction.error && (
                <div className="flex items-center gap-3">
                  <Badge className={
                    prediction.signal === "BUY" ? "bg-success/20 text-success" :
                    prediction.signal === "SELL" ? "bg-destructive/20 text-destructive" :
                    "bg-muted text-muted-foreground"
                  }>
                    {prediction.signal as string}
                  </Badge>
                  <span className="text-sm">
                    Confidence: <strong>{((prediction.confidence as number) * 100).toFixed(1)}%</strong>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(prediction.timestamp as string).toLocaleTimeString()}
                  </span>
                </div>
              )}
              {prediction?.error ? (
                <span className="text-sm text-destructive">{String(prediction.error)}</span>
              ) : null}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
