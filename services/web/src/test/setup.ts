import "@testing-library/jest-dom/vitest";

import { setConfigForTests } from "@/lib/config";

setConfigForTests({ apiBaseUrl: "http://api.test", environment: "test", version: "test" });

afterEach(() => {
  sessionStorage.clear();
  vi.restoreAllMocks();
});
