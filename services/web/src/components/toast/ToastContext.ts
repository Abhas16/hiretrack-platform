import { createContext } from "react";

export type ToastKind = "ok" | "error";

export interface Toast {
  id: number;
  kind: ToastKind;
  text: string;
}

export interface ToastApi {
  success: (text: string) => void;
  error: (text: string) => void;
  /** Show any thrown value (ApiError -> "409 Conflict · ..."). */
  fromError: (error: unknown) => void;
}

export const ToastContext = createContext<ToastApi | null>(null);
