import { Button } from "@/components/ui/Button";
import type { MatchProfile } from "@/types/match";

interface Props {
  profile: MatchProfile | undefined;
  onEdit: () => void;
}

/** Without a profile the scorer has nothing to match against, so say so up front. */
export function ProfileBanner({ profile, onEdit }: Props) {
  if (!profile) return null;

  const skills = Object.keys(profile.skills).length;
  const text = !profile.exists
    ? "Set up your match profile so new jobs get scored for you."
    : profile.is_active
      ? `Matching on ${skills} skill${skills === 1 ? "" : "s"}, ${profile.years_experience} years experience${profile.remote_ok ? ", remote OK" : ""}.`
      : "Smart Apply is paused: new jobs are not scored for you.";

  return (
    <div className="border-line bg-soft flex flex-wrap items-center justify-between gap-3 rounded-[14px] border px-5 py-3">
      <span className="text-ink-3 text-sm">{text}</span>
      <Button variant="secondary" size="sm" onClick={onEdit}>
        {profile.exists ? "Edit profile" : "Set up profile"}
      </Button>
    </div>
  );
}
