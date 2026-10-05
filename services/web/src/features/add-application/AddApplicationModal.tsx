import { Button } from "@/components/ui/Button";
import { SelectField, TextField } from "@/components/ui/fields";
import { Modal } from "@/components/ui/Modal";

import {
  SOURCE_OPTIONS,
  STAGE_OPTIONS,
  useAddApplicationController,
} from "./useAddApplicationController";

export function AddApplicationModal({ onClose }: { onClose: () => void }) {
  const c = useAddApplicationController(onClose);

  return (
    <Modal title="Add application" onClose={c.onCancel}>
      <form onSubmit={c.onSubmit} noValidate className="flex flex-col gap-4">
        <TextField
          id="add-company"
          label="Company"
          placeholder="e.g. Atlassian"
          autoFocus
          error={c.errors.company?.message}
          {...c.register("company")}
        />
        <TextField
          id="add-role"
          label="Role"
          placeholder="e.g. Junior DevOps Engineer"
          error={c.errors.role?.message}
          {...c.register("role")}
        />
        <TextField
          id="add-location"
          label="Location"
          placeholder="e.g. Bhubaneswar"
          error={c.errors.location?.message}
          {...c.register("location")}
        />
        <div className="grid grid-cols-2 gap-3">
          <SelectField
            id="add-status"
            label="Stage"
            options={STAGE_OPTIONS}
            {...c.register("status")}
          />
          <SelectField
            id="add-source"
            label="Source"
            options={SOURCE_OPTIONS}
            {...c.register("source")}
          />
        </div>
        <TextField
          id="add-url"
          label="Job URL (optional)"
          placeholder="https://…"
          error={c.errors.jobUrl?.message}
          {...c.register("jobUrl")}
        />
        <div className="flex justify-end gap-2.5">
          <Button variant="secondary" size="lg" onClick={c.onCancel}>
            Cancel
          </Button>
          <Button type="submit" size="lg" disabled={c.isSaving}>
            {c.isSaving ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
