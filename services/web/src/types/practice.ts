export interface PracticeTopic {
  id: string;
  label: string;
}

export interface PracticeMeta {
  /** "rule_based" (built-in question bank) or "anthropic" (Claude). */
  provider: string;
  topics: PracticeTopic[];
  min_questions: number;
  max_questions: number;
}

export interface PracticeTurn {
  position: number;
  topic: string;
  question: string;
  answer: string | null;
  score: number | null; // 0..10
  strengths: string[];
  improvements: string[];
  feedback: string | null;
  /** Empty until the question is answered (no spoilers). */
  key_points: string[];
  evaluated_by: string | null;
  answered_at: string | null;
}

export interface PracticeSessionSummary {
  id: string;
  role: string;
  topics: string[];
  provider: string;
  status: "IN_PROGRESS" | "COMPLETED";
  question_count: number;
  answered_count: number;
  average_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface PracticeSession extends PracticeSessionSummary {
  application_id: string | null;
  turns: PracticeTurn[];
}

export interface PracticeSessionCreate {
  role?: string;
  application_id?: string;
  topics?: string[];
  question_count?: number;
}
