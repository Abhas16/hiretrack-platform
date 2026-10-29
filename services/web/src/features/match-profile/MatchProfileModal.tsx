import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/fields";
import { Modal } from "@/components/ui/Modal";
import { QueryState } from "@/components/ui/QueryState";

import { CheckboxField } from "./components/CheckboxField";
import { SkillWeightPicker } from "./components/SkillWeightPicker";
import { useMatchProfileController } from "./useMatchProfileController";

export function MatchProfileModal({ onClose }: { onClose: () => void }) {
  const c = useMatchProfileController(onClose);

  return (
    <Modal title="Match profile" onClose={c.onCancel}>
      <QueryState isLoading={c.isLoading} error={c.error}>
        <form onSubmit={c.onSubmit} noValidate className="flex flex-col gap-4">
          <SkillWeightPicker
            skills={c.allSkills}
            selected={c.selected}
            onCycle={c.cycleSkill}
            error={c.skillsError}
          />
          <TextField
            id="profile-roles"
            label="Target roles (comma-separated)"
            placeholder="DevOps Engineer, Platform Engineer"
            error={c.errors.targetRoles?.message}
            {...c.register("targetRoles")}
          />
          <TextField
            id="profile-locations"
            label="Locations (comma-separated, empty = anywhere)"
            placeholder="Pune, Bengaluru"
            error={c.errors.locations?.message}
            {...c.register("locations")}
          />
          <TextField
            id="profile-years"
            label="Years of experience"
            type="number"
            min={0}
            max={50}
            error={c.errors.yearsExperience?.message}
            {...c.register("yearsExperience")}
          />
          <div className="flex flex-wrap gap-5">
            <CheckboxField id="profile-remote" label="Remote is fine" {...c.register("remoteOk")} />
            <CheckboxField
              id="profile-active"
              label="Score new jobs for me"
              {...c.register("isActive")}
            />
          </div>
          <div className="flex justify-end gap-2.5">
            <Button variant="secondary" size="lg" onClick={c.onCancel}>
              Cancel
            </Button>
            <Button type="submit" size="lg" disabled={c.isSaving}>
              {c.isSaving ? "Saving…" : "Save profile"}
            </Button>
          </div>
        </form>
      </QueryState>
    </Modal>
  );
}
