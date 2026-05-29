"""세계 뉴스 브리핑 생성 파이프라인.

  수집 → 후보 선별 → 근거 수집(원문 본문 + 웹 검색) → 교차검증·작성 → 렌더링·저장
"""

import datetime as dt
import json
from pathlib import Path

from fetch_news import fetch_all
from pipeline import flatten_regions, gather_evidence
from render import render, world_view
from summarize import select_stories, write_briefing


def build(output_dir):
    """세계 뉴스를 수집·검증·작성하고 HTML 파일로 저장한다.

    날짜별 파일(briefing-YYYY-MM-DD.html)과 최신 파일(index.html)을 저장한다.
    (HTML 문자열, 저장 경로, 브리핑 데이터) 튜플을 반환한다.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()

    articles_by_region = fetch_all()
    flat = flatten_regions(articles_by_region)
    articles_by_id = {a["id"]: a for a in flat}

    print("[1단계] 사건 묶기 및 후보 선별...")
    stories = select_stories(flat)
    print(f"  → {len(stories)}개 사안 선별")

    gathered = gather_evidence(stories, articles_by_id)

    print("[3단계] 교차 검증 및 브리핑 작성...")
    briefing = write_briefing(gathered)

    html = render(briefing, today)
    dated_path = output_dir / f"briefing-{today.isoformat()}.html"
    latest_path = output_dir / "index.html"
    dated_path.write_text(html, encoding="utf-8")
    latest_path.write_text(html, encoding="utf-8")

    # 모바일 앱·API 용 JSON (HTML과 동일한 뷰모델).
    view_json = json.dumps(world_view(briefing, today), ensure_ascii=False, indent=2)
    (output_dir / f"briefing-{today.isoformat()}.json").write_text(view_json, encoding="utf-8")
    (output_dir / "index.json").write_text(view_json, encoding="utf-8")

    return html, dated_path, briefing
