import { Link } from "react-router";

import { Card } from "@/components/ui/Card";

interface Props {
  averageScore: string;
  studyNext: string[];
}

export function SessionSummary({ averageScore, studyNext }: Props) {
  return (
    <Card title="Interview complete">
      <div className="flex flex-wrap items-end gap-6">
        <div className="flex flex-col gap-1">
          <span className="text-muted text-[13px] font-semibold">Average score</span>
          <span className="font-mono text-[32px] font-bold">{averageScore}</span>
        </div>
        {studyNext.length > 0 && (
          <div className="flex flex-col gap-1">
            <span className="text-muted text-[13px] font-semibold">Study next</span>
            <span className="text-sm font-semibold">{studyNext.join(" · ")}</span>
          </div>
        )}
      </div>
      <Link
        to="/practice"
        className="bg-primary hover:bg-primary-dark inline-flex min-h-10 w-fit items-center rounded-[10px] px-4 text-sm font-semibold text-white no-underline"
      >
        Start another interview
      </Link>
    </Card>
  );
}
