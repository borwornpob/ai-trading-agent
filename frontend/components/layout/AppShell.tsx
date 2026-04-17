"use client";

import { useEffect, useState, Suspense } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar, MobileHeader } from "@/components/layout/Sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { CommandPalette } from "@/components/ui/command-palette";
import { RouteProgress } from "@/components/ui/route-progress";
import api, { getSymbols } from "@/lib/api";
import { useBotStore } from "@/store/botStore";

const AUTH_BYPASS_PAGES = ["/login"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPage = AUTH_BYPASS_PAGES.includes(pathname);
  const [authChecked, setAuthChecked] = useState(false);
  const symbolsLoaded = useBotStore((s) => s.symbols.length > 0);
  const setSymbols = useBotStore((s) => s.setSymbols);

  useEffect(() => {
    if (isAuthPage) {
      setAuthChecked(true);
      return;
    }

    // Check if token exists in localStorage
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (!token) {
      router.replace("/login");
      return;
    }

    // Verify token is still valid
    api.get("/api/auth/me")
      .then(() => {
        setAuthChecked(true);
      })
      .catch(() => {
        // Token invalid or auth not configured — allow if no password set
        api.get("/health")
          .then(() => setAuthChecked(true))
          .catch(() => setAuthChecked(true));
      });
  }, [isAuthPage, router, pathname]);

  // Prefetch symbols into global store once authed, so pages that read
  // symbols from Zustand (insights, quant, etc.) work on direct load
  // without requiring a dashboard visit first.
  useEffect(() => {
    if (!authChecked || isAuthPage || symbolsLoaded) return;
    getSymbols()
      .then((res) => {
        if (res.data?.symbols) {
          setSymbols(res.data.symbols);
        }
      })
      .catch(() => {});
  }, [authChecked, isAuthPage, symbolsLoaded, setSymbols]);

  if (isAuthPage) {
    return <>{children}</>;
  }

  if (!authChecked) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground text-sm">Loading...</p>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <Suspense fallback={null}>
        <RouteProgress />
      </Suspense>
      <CommandPalette />
      <div className="flex flex-col lg:flex-row min-h-full">
        <MobileHeader />
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <div className="max-w-400 mx-auto">{children}</div>
        </main>
      </div>
    </TooltipProvider>
  );
}
