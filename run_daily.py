#!/usr/bin/env python3
"""하루 한 번 실행하는 진입점.

세계 뉴스 브리핑과 AI 브리핑을 생성하고, 설정돼 있으면 두 브리핑을
한 통의 이메일로 발송한다. cron 등에서 이 스크립트를 직접 호출할 수 있다.

사용법:
  python run_daily.py            # 두 브리핑 생성 + 이메일 발송
  python run_daily.py --no-email # 이메일 발송 생략
"""

import datetime as dt
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import ai_briefing  # noqa: E402
import briefing as world_briefing  # noqa: E402
from emailer import email_configured, send_email  # noqa: E402
from render import render_email  # noqa: E402


def main():
    output_dir = os.environ.get("OUTPUT_DIR", "./output")
    send_mail = "--no-email" not in sys.argv

    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M}] 아침 뉴스 브리핑 생성 시작")
    _, world_path, world_data = world_briefing.build(output_dir)
    print(f"세계 브리핑 저장 완료: {world_path}")
    _, ai_path, ai_data = ai_briefing.build(output_dir)
    print(f"AI 브리핑 저장 완료: {ai_path}")

    if send_mail and email_configured():
        try:
            email_html = render_email(world_data, ai_data)
            subject = f"[아침 뉴스 브리핑] {dt.date.today().isoformat()}"
            send_email(email_html, subject)
            print("이메일 발송 완료 (세계 + AI 브리핑)")
        except Exception as exc:
            print(f"[경고] 이메일 발송 실패: {exc}")
    else:
        print("이메일 발송 생략 (설정 없음 또는 --no-email)")

    print("\n오늘의 핵심 5 (세계)")
    for idx, item in enumerate(world_data.get("key5", []), 1):
        print(f"  {idx}. {item}")
    print("\n오늘의 AI 핵심")
    for idx, item in enumerate(ai_data.get("highlights", []), 1):
        print(f"  {idx}. {item}")


if __name__ == "__main__":
    main()
