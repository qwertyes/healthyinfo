export function DisclaimerNote({ className }: { className?: string }) {
  return (
    <p className={`text-xs leading-relaxed text-muted-foreground ${className ?? ""}`}>
      이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다. 기저질환이 있다면
      전문의와 상담하세요.
    </p>
  );
}
