import type { Application } from "@/types/application";

import { ApplicationRow, CELL } from "./ApplicationRow";

const HEADERS = ["Company", "Role", "Location", "Source", "Status", "Last update"];

export function ApplicationsTable({ rows, emptyText }: { rows: Application[]; emptyText: string }) {
  return (
    <div className="border-line bg-surface overflow-x-auto rounded-[14px] border">
      <table className="w-full min-w-[760px] border-collapse text-sm">
        <thead>
          <tr className="text-muted text-left text-xs tracking-[0.6px] uppercase">
            {HEADERS.map((header) => (
              <th key={header} className={`${CELL} font-semibold`}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((app) => (
            <ApplicationRow key={app.id} app={app} />
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p className="text-muted m-0 px-5 py-6 text-sm">{emptyText}</p>}
    </div>
  );
}
