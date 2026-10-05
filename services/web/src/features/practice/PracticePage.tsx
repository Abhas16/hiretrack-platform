import { SessionHistory } from "./components/SessionHistory";
import { StartSessionCard } from "./components/StartSessionCard";
import { usePracticeController } from "./usePracticeController";

export function PracticePage() {
  const c = usePracticeController();

  return (
    <div className="flex flex-col gap-4">
      <p className="text-muted m-0 text-sm">
        Answer interview questions in your own words. Each answer is scored with what you covered,
        what you missed, and what a strong answer includes.
      </p>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(340px,1fr))] items-start gap-4">
        <StartSessionCard
          providerText={c.providerText}
          topics={c.topics}
          selectedTopics={c.selectedTopics}
          onToggleTopic={c.toggleTopic}
          applicationOptions={c.applicationOptions}
          onApplicationChange={c.onApplicationChange}
          questionCounts={c.questionCounts}
          register={c.register}
          errors={c.errors}
          onSubmit={c.onSubmit}
          isStarting={c.isStarting}
        />
        <SessionHistory {...c.history} />
      </div>
    </div>
  );
}
