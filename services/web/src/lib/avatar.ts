const PALETTE = ["#2F5BEA", "#E07A1F", "#2E9A5E", "#7A4FD6", "#C2410C", "#0F766E"];

/** Same company name -> same colour, every time (sum of character codes). */
export function avatarColor(name: string): string {
  let sum = 0;
  for (const char of name) sum += char.charCodeAt(0);
  return PALETTE[sum % PALETTE.length] ?? PALETTE[0]!;
}
