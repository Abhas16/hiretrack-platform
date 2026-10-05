import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { authApi } from "@/lib/api/auth";
import { setUnauthorizedHandler } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/queryKeys";
import { tokenStorage } from "@/lib/auth/tokenStorage";

import { AuthContext, type AuthState } from "./AuthContext";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() => tokenStorage.get());

  const signIn = useCallback((accessToken: string) => {
    tokenStorage.set(accessToken);
    setToken(accessToken);
  }, []);

  const signOut = useCallback(() => {
    tokenStorage.clear();
    setToken(null);
    queryClient.clear(); // drop the previous user's cached data
  }, [queryClient]);

  // Any 401 from the API (e.g. expired token) signs the user out.
  useEffect(() => {
    setUnauthorizedHandler(signOut);
    return () => setUnauthorizedHandler(null);
  }, [signOut]);

  const me = useQuery({
    queryKey: queryKeys.me,
    queryFn: authApi.me,
    enabled: token !== null,
    staleTime: Infinity,
  });

  const value = useMemo<AuthState>(
    () => ({ isAuthenticated: token !== null, user: me.data ?? null, signIn, signOut }),
    [token, me.data, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
