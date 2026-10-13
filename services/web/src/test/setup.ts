import "@testing-library/jest-dom/vitest";

import { setConfigForTests } from "@/lib/config";

import { MemoryStorage } from "./memoryStorage";

setConfigForTests({ apiBaseUrl: "http://api.test", environment: "test", version: "test" });

// Replace Node's own global localStorage (Node 25+) with one that works without a backing file.
Object.defineProperty(globalThis, "localStorage", {
  value: new MemoryStorage(),
  configurable: true,
});

afterEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  vi.restoreAllMocks();
});
