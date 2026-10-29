import { nextWeight } from "@/features/match-profile/useMatchProfileController";
import {
  splitList,
  toFormValues,
  toProfileUpdate,
} from "@/features/match-profile/matchProfileSchema";
import { makeMatch } from "@/test/matchFixtures";

import { jobMeta, kitText, postedText, scoreTone } from "./reviewQueueModel";

const NOW = new Date("2026-10-20T12:00:00Z");

describe("reviewQueueModel", () => {
  it("colours scores by band", () => {
    expect(scoreTone(91).text).toBe("text-success");
    expect(scoreTone(65).text).toBe("text-primary");
    expect(scoreTone(40).text).toBe("text-warm-ink");
  });

  it("describes when a job was posted", () => {
    expect(postedText(null, NOW)).toBeNull();
    expect(postedText("2026-10-20T08:00:00Z", NOW)).toBe("posted today");
    expect(postedText("2026-10-17T08:00:00Z", NOW)).toBe("posted 3 days ago");
  });

  it("builds the job meta line", () => {
    const match = makeMatch();
    expect(jobMeta(match.job, NOW)).toBe(
      "Acme Cloud · Remote, India · via Greenhouse · posted 3 days ago",
    );
  });

  it("puts the cover note and bullets on the clipboard", () => {
    expect(kitText(makeMatch())).toBe(
      "Hi Acme Cloud team, ...\n\nResume bullets:\n- Ran Kubernetes\n- Wrote Terraform\n",
    );
  });
});

describe("match profile form", () => {
  it("cycles a skill weight 3 -> 4 -> 5 -> removed", () => {
    expect(nextWeight(undefined)).toBe(3);
    expect(nextWeight(3)).toBe(4);
    expect(nextWeight(5)).toBeUndefined();
  });

  it("splits comma lists and drops blanks", () => {
    expect(splitList(" DevOps Engineer, ,SRE ,")).toEqual(["DevOps Engineer", "SRE"]);
  });

  it("round-trips a saved profile through the form", () => {
    const saved = {
      exists: true,
      is_active: true,
      skills: { kubernetes: 5 },
      target_roles: ["SRE", "DevOps Engineer"],
      locations: ["Pune"],
      remote_ok: false,
      years_experience: 2,
      updated_at: "2026-10-19T00:00:00Z",
    };
    const values = toFormValues(saved);
    expect(values.targetRoles).toBe("SRE, DevOps Engineer");
    expect(toProfileUpdate({ ...values, yearsExperience: Number(values.yearsExperience) })).toEqual(
      {
        is_active: true,
        skills: { kubernetes: 5 },
        target_roles: ["SRE", "DevOps Engineer"],
        locations: ["Pune"],
        remote_ok: false,
        years_experience: 2,
      },
    );
  });
});
