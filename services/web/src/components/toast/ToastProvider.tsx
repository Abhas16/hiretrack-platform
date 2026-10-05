import { useCallback, useMemo, useRef, useState, type ReactNode } from "react";

import { describeError } from "@/lib/api/ApiError";

import { ToastContext, type Toast, type ToastApi, type ToastKind } from "./ToastContext";

const VISIBLE_MS = 3400;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);

  const show = useCallback((kind: ToastKind, text: string) => {
    const id = nextId.current++;
    setToasts((current) => [...current.slice(-2), { id, kind, text }]); // keep at most 3
    setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), VISIBLE_MS);
  }, []);

  const api = useMemo<ToastApi>(
    () => ({
      success: (text) => show("ok", text),
      error: (text) => show("error", text),
      fromError: (error) => show("error", describeError(error)),
    }),
    [show],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="fixed top-5 right-5 z-50 flex max-w-[420px] flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className={`rounded-xl px-[18px] py-3.5 font-mono text-[13px] leading-normal text-white shadow-[0_10px_30px_rgba(18,21,28,0.25)] ${
              toast.kind === "error" ? "bg-danger" : "bg-success"
            }`}
          >
            {toast.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
