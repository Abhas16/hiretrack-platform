import { z } from "zod";

import type { PracticeSessionCreate } from "@/types/practice";

export const startSchema = z
  .object({
    applicationId: z.string(), // "" = not linked to an application
    role: z.string().trim().max(200),
    topics: z.array(z.string()).max(10),
    questionCount: z.coerce.number().int().min(3).max(8),
  })
  .refine((values) => values.role || values.applicationId, {
    path: ["role"],
    message: "Enter a role or pick an application",
  });

export type StartValues = z.input<typeof startSchema>;
export type StartOutput = z.output<typeof startSchema>;

export const START_DEFAULTS: StartValues = {
  applicationId: "",
  role: "",
  topics: [],
  questionCount: 5,
};

export function toSessionCreate(values: StartOutput): PracticeSessionCreate {
  return {
    role: values.role || undefined,
    application_id: values.applicationId || undefined,
    topics: values.topics.length ? values.topics : undefined, // empty -> API picks from the role
    question_count: values.questionCount,
  };
}
