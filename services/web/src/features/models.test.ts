import { makeSummary } from "@/test/fixtures";

import {
  buildAnalyticsKpis,
  toFunnelRows,
  toSourceRows,
  toVariantRows,
} from "./analytics/analyticsModel";
import {
  buildFilterPills,
  parsePage,
  parseStatusFilter,
  rangeText,
} from "./applications/applicationsModel";
import { buildKpis, buildPipeline } from "./dashboard/dashboardModel";

describe("dashboardModel", () => {
  it("builds the four KPI cards from the summary", () => {
    expect(buildKpis(makeSummary())).toEqual([
      { label: "Total applications", value: "12", hint: "10 sent, 2 on wishlist" },
      { label: "Active pipeline", value: "9", hint: "Not yet offered or rejected" },
      { label: "Interviews", value: "3", hint: "Currently in interview stage" },
      { label: "Response rate", value: "60%", hint: "6 of 10 sent got a reply" },
    ]);
  });

  it("sizes pipeline segments as a share of all applications", () => {
    const pipeline = buildPipeline(makeSummary());
    expect(pipeline.map((s) => s.status)).toEqual([
      "WISHLIST",
      "APPLIED",
      "INTERVIEW",
      "OFFER",
      "REJECTED",
    ]);
    expect(pipeline[1]?.widthPercent).toBeCloseTo((4 / 12) * 100);
  });

  it("handles an empty account without dividing by zero", () => {
    const empty = makeSummary({
      total: 0,
      by_status: { WISHLIST: 0, APPLIED: 0, INTERVIEW: 0, OFFER: 0, REJECTED: 0 },
    });
    expect(buildPipeline(empty).every((s) => s.widthPercent === 0)).toBe(true);
  });
});

describe("applicationsModel", () => {
  it("labels filter pills with counts and marks the active one", () => {
    const pills = buildFilterPills(makeSummary(), "APPLIED");
    expect(pills[0]).toEqual({ value: "ALL", label: "All · 12", active: false });
    expect(pills.find((p) => p.active)?.label).toBe("Applied · 4");
  });

  it("shows plain labels while the summary is loading", () => {
    expect(buildFilterPills(undefined, "ALL")[0]?.label).toBe("All");
  });

  it("parses URL params defensively", () => {
    expect(parseStatusFilter("OFFER")).toBe("OFFER");
    expect(parseStatusFilter("<script>")).toBe("ALL");
    expect(parsePage("3")).toBe(3);
    expect(parsePage("-1")).toBe(1);
    expect(parsePage(null)).toBe(1);
  });

  it("describes the visible range", () => {
    expect(rangeText(2, 25, 40)).toBe("Showing 26–40 of 40");
    expect(rangeText(1, 25, 0)).toBe("No results");
  });
});

describe("analyticsModel", () => {
  it("builds KPIs, showing a dash when there is no interview data yet", () => {
    const kpis = buildAnalyticsKpis(makeSummary(), {
      average_days: null,
      median_days: null,
      sample_size: 0,
    });
    expect(kpis.map((k) => k.value)).toEqual(["—", "40%", "1"]);
    expect(
      buildAnalyticsKpis(makeSummary(), { average_days: 6.6, median_days: 6, sample_size: 2 })[0]
        ?.value,
    ).toBe("7d");
  });

  it("sizes funnel bars relative to the first stage", () => {
    const rows = toFunnelRows([
      { stage: "Saved", count: 10 },
      { stage: "Applied", count: 5 },
    ]);
    expect(rows.map((r) => r.widthPercent)).toEqual([100, 50]);
  });

  it("labels sources and variants for display", () => {
    const sources = toSourceRows(
      [{ source: "COMPANY_SITE", applications: 3, interviews: 1, offers: 0, interview_rate: 0.5 }],
      12,
    );
    expect(sources[0]).toMatchObject({ label: "Company site", count: 3, widthPercent: 25 });

    const variants = toVariantRows([
      {
        resume_variant_id: null,
        name: "No resume variant",
        applications: 2,
        interviews: 1,
        offers: 0,
        interview_rate: 0.5,
      },
    ]);
    expect(variants[0]).toEqual({
      name: "No resume variant",
      detail: "2 applications · 1 interviews · 0 offers",
      interviewRate: "50%",
    });
  });
});
