/**
 * Where the JWT lives. sessionStorage: survives a page refresh, cleared when the tab closes
 * (a smaller window than localStorage if the token ever leaks). The API also expires it.
 */
const KEY = "hiretrack.accessToken";

export const tokenStorage = {
  get(): string | null {
    return sessionStorage.getItem(KEY);
  },
  set(token: string): void {
    sessionStorage.setItem(KEY, token);
  },
  clear(): void {
    sessionStorage.removeItem(KEY);
  },
};
