import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/ApiError";

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        // Retry network blips and 5xx, never 4xx (a 404 won't fix itself).
        retry: (failureCount, error) =>
          !(error instanceof ApiError && error.status < 500) && failureCount < 2,
      },
    },
  });
}
