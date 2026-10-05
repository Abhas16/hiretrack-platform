import { Button } from "@/components/ui/Button";

interface Props {
  text: string;
  hasPrevious: boolean;
  hasNext: boolean;
  previous: () => void;
  next: () => void;
}

export function Pagination({ text, hasPrevious, hasNext, previous, next }: Props) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted text-[13px]">{text}</span>
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" disabled={!hasPrevious} onClick={previous}>
          Previous
        </Button>
        <Button variant="secondary" size="sm" disabled={!hasNext} onClick={next}>
          Next
        </Button>
      </div>
    </div>
  );
}
