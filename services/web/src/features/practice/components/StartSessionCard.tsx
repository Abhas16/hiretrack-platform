import type { FieldErrors, UseFormRegister } from "react-hook-form";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SelectField, TextField } from "@/components/ui/fields";
import type { PracticeTopic } from "@/types/practice";

import type { StartValues } from "../startSchema";

import { TopicPicker } from "./TopicPicker";

interface Props {
  providerText: string;
  topics: PracticeTopic[];
  selectedTopics: string[];
  onToggleTopic: (id: string) => void;
  applicationOptions: { value: string; label: string }[];
  onApplicationChange: (id: string) => void;
  questionCounts: { value: string; label: string }[];
  register: UseFormRegister<StartValues>;
  errors: FieldErrors<StartValues>;
  onSubmit: () => void;
  isStarting: boolean;
}

export function StartSessionCard(p: Props) {
  const application = p.register("applicationId");

  return (
    <Card title="Start a mock interview" subtitle={p.providerText}>
      <form onSubmit={p.onSubmit} noValidate className="flex flex-col gap-4">
        <SelectField
          id="practice-application"
          label="Practise for an application"
          options={p.applicationOptions}
          {...application}
          onChange={(event) => p.onApplicationChange(event.target.value)}
        />
        <TextField
          id="practice-role"
          label="Role"
          placeholder="e.g. Junior DevOps Engineer"
          error={p.errors.role?.message}
          {...p.register("role")}
        />
        <TopicPicker topics={p.topics} selected={p.selectedTopics} onToggle={p.onToggleTopic} />
        <SelectField
          id="practice-count"
          label="Length"
          options={p.questionCounts}
          {...p.register("questionCount")}
        />
        <Button type="submit" size="lg" disabled={p.isStarting}>
          {p.isStarting ? "Preparing your questions…" : "Start interview"}
        </Button>
      </form>
    </Card>
  );
}
