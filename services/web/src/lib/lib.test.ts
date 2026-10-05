import { avatarColor } from "./avatar";
import { daysSince, firstName, formatWeekLabel, initials, percent, updatedText } from "./format";
import { isApplicationStatus, nextStatus, previousStatus } from "./status";
import { safeHttpUrl } from "./url";

describe("status helpers", () => {
  it("walks the board left to right and stops at the ends", () => {
    expect(nextStatus("WISHLIST")).toBe("APPLIED");
    expect(nextStatus("INTERVIEW")).toBe("OFFER");
    expect(nextStatus("OFFER")).toBeNull();
    expect(previousStatus("APPLIED")).toBe("WISHLIST");
    expect(previousStatus("WISHLIST")).toBeNull();
    expect(nextStatus("REJECTED")).toBeNull();
    expect(previousStatus("REJECTED")).toBeNull();
  });

  it("recognises valid statuses only", () => {
    expect(isApplicationStatus("OFFER")).toBe(true);
    expect(isApplicationStatus("offer")).toBe(false);
    expect(isApplicationStatus(42)).toBe(false);
  });
});

describe("format helpers", () => {
  const now = new Date("2026-10-05T12:00:00Z");

  it("describes how long ago something was updated", () => {
    expect(updatedText("2026-10-05T08:00:00Z", now)).toBe("Updated today");
    expect(updatedText("2026-10-04T08:00:00Z", now)).toBe("Updated yesterday");
    expect(updatedText("2026-09-26T12:00:00Z", now)).toBe("Updated 9 days ago");
    expect(daysSince("2026-10-06T00:00:00Z", now)).toBe(0); // future dates never go negative
  });

  it("formats numbers and names", () => {
    expect(percent(0.6)).toBe("60%");
    expect(percent(0.4567)).toBe("46%");
    expect(initials("Abhas Kumar Mukherjee")).toBe("AM");
    expect(initials("abhas")).toBe("A");
    expect(firstName("  Abhas Mukherjee ")).toBe("Abhas");
    expect(formatWeekLabel("2026-08-24")).toBe("Aug 24");
  });
});

describe("safeHttpUrl", () => {
  it("allows http(s) and blocks script URLs", () => {
    expect(safeHttpUrl("https://jobs.example.com/1")).toBe("https://jobs.example.com/1");
    expect(safeHttpUrl("javascript:alert(1)")).toBeNull();
    expect(safeHttpUrl("not a url")).toBeNull();
    expect(safeHttpUrl(null)).toBeNull();
  });
});

describe("avatarColor", () => {
  it("is stable for the same name", () => {
    expect(avatarColor("Atlassian")).toBe(avatarColor("Atlassian"));
    expect(avatarColor("Atlassian")).toMatch(/^#[0-9A-F]{6}$/);
  });
});
