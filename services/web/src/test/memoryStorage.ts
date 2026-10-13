/**
 * A tiny in-memory Web Storage for tests.
 *
 * Node 25+ ships its own global `localStorage`, which is unusable unless Node is started with
 * `--localstorage-file`, and it hides jsdom's working one. Tests install this instead so they
 * behave the same on every Node version.
 */
export class MemoryStorage implements Storage {
  private items = new Map<string, string>();

  get length(): number {
    return this.items.size;
  }

  clear(): void {
    this.items.clear();
  }

  getItem(key: string): string | null {
    return this.items.get(key) ?? null;
  }

  key(index: number): string | null {
    return [...this.items.keys()][index] ?? null;
  }

  removeItem(key: string): void {
    this.items.delete(key);
  }

  setItem(key: string, value: string): void {
    this.items.set(key, String(value));
  }
}
