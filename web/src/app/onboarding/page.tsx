import { OnboardingQuiz } from "@/components/onboarding/onboarding-quiz";

export const metadata = {
  title: "맞춤 식단 온보딩 — HealthyInfo",
};

export default function OnboardingPage() {
  return (
    <main className="flex flex-1 flex-col items-center px-6 py-16 sm:py-24">
      <div className="w-full max-w-xl space-y-6">
        <div className="space-y-2 text-center sm:text-left">
          <h1 className="text-2xl font-semibold tracking-tight">나에게 맞는 식단 찾기</h1>
          <p className="text-muted-foreground">6가지 질문이면 충분합니다.</p>
        </div>
        <OnboardingQuiz />
      </div>
    </main>
  );
}
