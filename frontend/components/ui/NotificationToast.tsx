"use client";

/**
 * Phase 9 — NotificationToast
 * Lightweight in-app notification for important events:
 *   - buyer request sent / accepted / rejected
 *   - forecast updated
 *   - quality assessment completed
 *
 * Usage:
 *   import { useNotifications, NotificationContainer } from "@/components/ui/NotificationToast";
 *   const { notify } = useNotifications();
 *   notify("success", "Request sent to Ahmedabad Textile Corp");
 */

import { useCallback, useEffect, useState, createContext, useContext } from "react";

export type NotificationType = "success" | "info" | "warning" | "error";

export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  duration?: number; // ms, default 4000
}

interface NotificationContextType {
  notify: (type: NotificationType, message: string, duration?: number) => void;
}

const NotificationContext = createContext<NotificationContextType>({
  notify: () => {},
});

export function useNotifications() {
  return useContext(NotificationContext);
}

const TYPE_STYLES: Record<NotificationType, string> = {
  success: "bg-green-600  text-white",
  info:    "bg-blue-600   text-white",
  warning: "bg-amber-500  text-white",
  error:   "bg-red-600    text-white",
};

const TYPE_ICONS: Record<NotificationType, string> = {
  success: "✓",
  info:    "ℹ",
  warning: "⚠",
  error:   "✕",
};

function Toast({ notification, onDismiss }: {
  notification: Notification;
  onDismiss: (id: string) => void;
}) {
  useEffect(() => {
    const t = setTimeout(() => onDismiss(notification.id), notification.duration ?? 4000);
    return () => clearTimeout(t);
  }, [notification, onDismiss]);

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-center gap-2 px-4 py-3 rounded-2xl shadow-lg text-sm font-medium max-w-sm animate-fade-in ${TYPE_STYLES[notification.type]}`}
    >
      <span className="text-base leading-none" aria-hidden="true">{TYPE_ICONS[notification.type]}</span>
      <span className="flex-1">{notification.message}</span>
      <button
        onClick={() => onDismiss(notification.id)}
        className="ml-1 opacity-70 hover:opacity-100 transition-opacity text-lg leading-none"
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  );
}

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const notify = useCallback((type: NotificationType, message: string, duration = 4000) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setNotifications(prev => [...prev.slice(-3), { id, type, message, duration }]);
  }, []);

  const dismiss = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  return (
    <NotificationContext.Provider value={{ notify }}>
      {children}
      {notifications.length > 0 && (
        <div
          className="fixed bottom-24 sm:bottom-6 right-4 z-50 flex flex-col gap-2 items-end"
          aria-label="Notifications"
        >
          {notifications.map(n => (
            <Toast key={n.id} notification={n} onDismiss={dismiss} />
          ))}
        </div>
      )}
    </NotificationContext.Provider>
  );
}
