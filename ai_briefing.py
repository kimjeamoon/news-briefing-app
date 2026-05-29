"""AI 전용 브리핑 생성 파이프라인.

세계 브리핑과 동일한 3단계(선별 → 근거 수집 → 교차검증·작성)를 거치되,
지역이 아니라 AI 분야(모델·제품 / 연구·논문 / 산업·투자 / 정책·안전)로 구성한다.
"""

import datetime as dt
import json
from pathlib import Path

from ai_sources import AI_FEEDS
from fetch_news import fetch_region
from pipeline import gather_evidence, index_articles
from render import ai_view, render_ai
from summarize import select_ai_stories, write_ai_briefing


def build(output_dir):
    """AI 뉴스를 수집·검증·작성하고 HTML 파일로 저장한다.

    날짜별 파일(ai-YYYY-MM-DD.html)과 최신 파일(ai.html)을 저장한다.
    (HTML 문자열, 저장 경로, 브리핑 데이터) 튜플을 반환한다.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()

    print("[AI 수집] AI 전문 매체·논문 RSS 수집...")
    articles = fetch_region(AI_FEEDS)
    print(f"  → {len(articles)}건")

    flat = index_articles(articles)
    articles_by_id = {a["id"]: a for a in flat}

    print("[AI 1단계] 사건 묶기 및 분야 선별...")
    stories = select_ai_stories(flat)
    print(f"  → {len(stories)}개 사안 선별")

    gathered = gather_evidence(stories, articles_by_id)

    print("[AI 3단계] 교차 검증 및 AI 브리핑 작성...")
    briefing = write_ai_briefing(gathered)

    html = render_ai(briefing, today)
    dated_path = output_dir / f"ai-{today.isoformat()}.html"
    latest_path = output_dir / "ai.html"
    dated_path.write_text(html, encoding="utf-8")
    latest_path.write_text(html, encoding="utf-8")

    # 모바일 앱·API 용 JSON (HTML과 동일한 뷰모델).
    view_json = json.dumps(ai_view(briefing, today), ensure_ascii=False, indent=2)
    (output_dir / f"ai-{today.isoformat()}.json").write_text(view_json, encoding="utf-8")
    (output_dir / "ai.json").write_text(view_json, encoding="utf-8")

    return html, dated_path, briefing
