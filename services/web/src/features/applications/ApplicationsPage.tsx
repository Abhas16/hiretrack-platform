import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { QueryState } from "@/components/ui/QueryState";

import { ApplicationsTable } from "./components/ApplicationsTable";
import { Pagination } from "./components/Pagination";
import { StatusFilterPills } from "./components/StatusFilterPills";
import { useApplicationsController } from "./useApplicationsController";

export function ApplicationsPage() {
  const c = useApplicationsController();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <StatusFilterPills pills={c.pills} onSelect={c.selectFilter} />
        <Button variant="secondary" onClick={c.exportCsv} disabled={c.isExporting}>
          <Icon name="download" size={18} />
          {c.isExporting ? "Exporting…" : "Export CSV"}
        </Button>
      </div>
      <QueryState isLoading={c.isLoading} error={c.error}>
        <ApplicationsTable rows={c.rows} emptyText={c.emptyText} />
        <Pagination {...c.pagination} />
      </QueryState>
    </div>
  );
}
