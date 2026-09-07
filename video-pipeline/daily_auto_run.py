r"""Windows 작업 스케줄러로 매일 아침 실행되는 완전 무인 진입점.

python pipeline.py처럼 옆에서 결과를 봐줄 사람이 없는 걸 전제로 한다 — 예기치 않은 예외가
나도 트레이스백을 출력하고 0이 아닌 코드로 종료할 뿐, 스케줄된 작업 자체는 다음날 다시
정상 실행된다.

실행 시각(매일 05:10 1회)과 실제 유튜브 공개 시각은 서로 다르다 — 노트북이 공개 시각까지
켜져 있지 않아도 유튜브 서버가 예약 시각에 알아서 공개해준다. 이 특성을 이용해서, 실행은
하루 1번(새벽)이지만 그 안에서 영상을 2개 만들어 서로 다른 시각(PUBLISH_SLOTS)으로 각각
예약한다 — 하루 2편 발행 체제.

처음엔 WSL cron으로 스케줄했었는데, WSL 인스턴스 자체가 그 시각에 꺼져있으면 그냥 조용히
스킵되는 문제를 실제로 겪어서(cron은 놓친 시간을 따라잡지 않음) Windows 작업 스케줄러로
교체했다 — "놓친 작업을 컴퓨터가 켜지면 바로 실행"(StartWhenAvailable) 옵션이 있어서 이
문제가 없다.

Windows 작업 스케줄러는 stdout/stderr를 캡처하지 않으므로, 로그를 남기려면 python.exe를
직접 호출하지 않고 run_daily.bat(같은 폴더)을 통해 실행한다 — 거기서
`>> logs\daily_run.log 2>&1`로 리다이렉트한다.

설치(Windows, PowerShell):
  $action = New-ScheduledTaskAction -Execute "<video-pipeline 절대경로>\run_daily.bat" -WorkingDirectory "<video-pipeline 절대경로>"
  $trigger = New-ScheduledTaskTrigger -Daily -At 6:30AM
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
  Register-ScheduledTask -TaskName "Hankki Daily Video" -Action $action -Trigger $trigger -Settings $settings
"""

import sys
import traceback
from datetime import datetime

import pipeline

# (라벨, 공개 시각 hour, minute) — 하루 2편 발행 슬롯. 순서대로 캘린더 큐에서 하나씩 소비한다.
PUBLISH_SLOTS = [
    ("아침(07:30)", 7, 30),
    ("저녁(22:30)", 22, 30),
]


def _run_slot(label: str, hour: int, minute: int) -> bool:
    """한 슬롯(영상 1개) 생성·업로드. 성공하면 True."""
    scheduled_publish_at = pipeline.next_publish_time_kst(hour, minute)
    print(f"\n--- {label} 슬롯 시작 (예약 공개 시각: {scheduled_publish_at}) ---")
    try:
        result = pipeline.run_and_upload(scheduled_publish_at=scheduled_publish_at)
    except Exception:
        print(f"=== {label} 슬롯 예기치 않은 오류 ===")
        traceback.print_exc()
        return False

    if result is None:
        print(f"{label} 슬롯: 영상이 만들어지지 않았습니다 (자동 차단되었거나 콘텐츠 캘린더 큐가 비어있음).")
        print("캘린더가 비었다면: python topic_calendar.py")
        return True  # 큐가 빈 건 오류가 아니라 정상적인 종료 상태

    if not result.get("success"):
        print(f"{label} 슬롯 업로드 실패: {result}")
        return False

    print(f"{label} 슬롯 예약 완료: video_id={result.get('video_id')}, comment_id={result.get('comment_id')}")
    return True


def main() -> None:
    print(f"\n=== {datetime.now().isoformat()} daily_auto_run 시작 (하루 {len(PUBLISH_SLOTS)}편) ===")
    all_ok = True
    for label, hour, minute in PUBLISH_SLOTS:
        if not _run_slot(label, hour, minute):
            all_ok = False
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
