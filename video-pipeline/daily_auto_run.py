"""WSL cron으로 매일 새벽 실행되는 완전 무인 진입점.

python pipeline.py처럼 옆에서 결과를 봐줄 사람이 없는 걸 전제로 한다 — 예기치 않은 예외가
나도 트레이스백을 출력하고 0이 아닌 코드로 종료할 뿐, 크론 자체는 다음날 다시 정상 실행된다.

크론이 도는 시각(예: 새벽 5시, 노트북이 켜져 있을 가능성이 높은 시간)과 실제 유튜브 공개
시각(오후 7시, run_and_upload()의 scheduled_publish_at 기본값)은 서로 다르다 — 노트북이
저녁까지 켜져 있지 않아도 유튜브 서버가 예약 시각에 알아서 공개해준다.

설치(WSL): crontab -e 로 아래 한 줄 추가 (경로는 실제 WSL 마운트 경로로)
  0 5 * * * cd /mnt/d/AI/HealthyInfo/video-pipeline && /usr/bin/python3 daily_auto_run.py >> logs/daily_run.log 2>&1
"""

import sys
import traceback
from datetime import datetime

import pipeline


def main() -> None:
    print(f"\n=== {datetime.now().isoformat()} daily_auto_run 시작 ===")
    try:
        result = pipeline.run_and_upload()
    except Exception:
        print("=== 예기치 않은 오류 ===")
        traceback.print_exc()
        sys.exit(1)

    if result is None:
        print("오늘은 영상이 만들어지지 않았습니다 (자동 차단되었거나 콘텐츠 캘린더 큐가 비어있음).")
        print("캘린더가 비었다면: python topic_calendar.py")
        return

    if not result.get("success"):
        print(f"업로드 실패: {result}")
        sys.exit(1)

    print(f"오늘의 영상 예약 완료: video_id={result.get('video_id')}, comment_id={result.get('comment_id')}")


if __name__ == "__main__":
    main()
