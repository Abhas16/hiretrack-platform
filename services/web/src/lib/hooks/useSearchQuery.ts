import { useCallback } from "react";
import { useSearchParams } from "react-router";

import { useDebouncedValue } from "./useDebouncedValue";

/**
 * The top-bar search lives in the URL (?q=...), so it survives refresh and can be shared.
 * `query` updates instantly (for the input); `debouncedQuery` is what screens send to the API.
 */
export function useSearchQuery() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";

  const setQuery = useCallback(
    (value: string) => {
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          if (value) next.set("q", value);
          else next.delete("q");
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  return { query, debouncedQuery: useDebouncedValue(query.trim()), setQuery };
}
