"use client";

import { useEffect, useRef, useCallback, useState } from "react";

type WSMessage = {
  channel: string;
  data: unknown;
};

type UseWebSocketReturn = {
  isConnected: boolean;
  subscribe: (channel: string, callback: (data: unknown) => void) => void;
  unsubscribe: (channel: string) => void;
};

export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const subscribersRef = useRef<Map<string, (data: unknown) => void>>(
    new Map()
  );
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    // Don't create duplicate connections
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    const baseWsUrl =
      process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
    const token = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";
    const wsUrl = token ? `${baseWsUrl}?token=${token}` : baseWsUrl;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);
          const callback = subscribersRef.current.get(msg.channel);
          if (callback) {
            callback(msg.data);
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        const delay = Math.min(
          1000 * 2 ** reconnectAttemptsRef.current,
          30000
        );
        reconnectAttemptsRef.current++;
        reconnectTimerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // connection failed
    }
  }, []);

  useEffect(() => {
    connect();

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        reconnectAttemptsRef.current = 0;
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          connect();
        }
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const subscribe = useCallback(
    (channel: string, callback: (data: unknown) => void) => {
      subscribersRef.current.set(channel, callback);
    },
    []
  );

  const unsubscribe = useCallback((channel: string) => {
    subscribersRef.current.delete(channel);
  }, []);

  return { isConnected, subscribe, unsubscribe };
}
