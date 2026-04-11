"use client";

import { usePathname } from "next/navigation";
import { Sidebar, MobileHeader } from "@/components/layout/Sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  if (isLoginPage) {
    return <>{children}</>;
  }

  return (
    <TooltipProvider>
      <div className="flex flex-col lg:flex-row min-h-full">
        <MobileHeader />
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <div className="max-w-[1600px] mx-auto animate-fade-in">{children}</div>
        </main>
      </div>
    </TooltipProvider>
  );
}
