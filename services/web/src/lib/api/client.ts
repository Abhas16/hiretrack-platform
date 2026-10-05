/** The only place that talks HTTP. Every resource module (applications.ts, ...) goes through here. */
import { tokenStorage } from "@/lib/auth/tokenStorage";
import { getConfig } from "@/lib/config";

import { ApiError } from "./ApiError";

type QueryValue = string | number | boolean | string[] | null | undefined;
export type Query = Record<string, QueryValue>;

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Query;
}

let onUnauthorized: (() => void) | null = null;

/** AuthProvider registers a callback here so an expired token logs the user out. */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

export function buildUrl(path: string, query: Query = {}): string {
  const url = new URL(`${getConfig().apiBaseUrl}/api/v1${path}`);
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === "") continue;
    for (const item of Array.isArray(value) ? value : [value]) {
      url.searchParams.append(key, String(item));
    }
  }
  return url.toString();
}

async function send(path: string, options: RequestOptions, accept: string): Promise<Response> {
  const headers: Record<string, string> = { Accept: accept };
  const token = tokenStorage.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(buildUrl(path, options.query), {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    if (response.status === 401 && token) onUnauthorized?.();
    throw await ApiError.fromResponse(response);
  }
  return response;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(path, options, "application/json");
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function apiDownload(path: string, query?: Query): Promise<Blob> {
  const response = await send(path, { query }, "*/*");
  return response.blob();
}
