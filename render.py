"""브리핑 데이터를 HTML로 렌더링한다.

  render(briefing)             : 세계 뉴스 브리핑 페이지 (index.html)
  render_ai(briefing)          : AI 브리핑 페이지 (ai.html)
  render_email(world, ai)      : 두 브리핑을 한 문서에 담은 이메일 본문
"""

import datetime as dt
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_sources import AI_CATEGORY_META
from sources import SOURCES

TAG_LABEL = {
    "pol": "정치·외교",
    "eco": "경제·시장",
    "tec": "기술·과학",
    "soc": "사회",
}
WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def _format_date(date):
    return f"{date.year}년 {date.month}월 {date.day}일 ({WEEKDAY_KO[date.weekday()]})"


def _normalize_sources(value):
    """sources 값을 [{name, url}, ...] 형태로 정규화한다.

    허용 입력:
      - 문자열 한 개
      - 문자열 리스트
      - {"name", "url"} 객체 리스트
      - 위 형태가 섞인 리스트
    """
    if value is None:
        return []
    if isinstance(value, str):
        name = value.strip()
        return [{"name": name, "url": ""}] if name else []
    if not isinstance(value, list):
        return []

    normalized = []
    for item in value:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            url = str(item.get("url", "")).strip()
            if name:
                normalized.append({"name": name, "url": url})
        elif isinstance(item, str):
            name = item.strip()
            if name:
                normalized.append({"name": name, "url": ""})
    return normalized


def _finalize_story(story, css_tag, tag_label):
    """렌더링에 필요한 공통 필드(tag, tag_label, sources, verification)를 보정한다."""
    story = dict(story)
    story["tag"] = css_tag
    story["tag_label"] = tag_label
    story["sources"] = _normalize_sources(story.get("sources") or story.get("source"))
    verification = story.get("verification", "")
    if verification not in ("multi", "single"):
        verification = "multi" if len(story["sources"]) >= 2 else "single"
    story["verification"] = verification
    return story


def _world_regions(briefing):
    """세계 브리핑 데이터를 템플릿용 섹션 목록으로 변환한다."""
    sections = []
    for name, meta in SOURCES.items():
        raw = briefing.get("regions", {}).get(name, []) or []
        stories = [
            _finalize_story(s, s.get("tag", ""), TAG_LABEL.get(s.get("tag", ""), ""))
            for s in raw
        ]
        sections.append(
            {"name": name, "flag": meta["flag"], "en": meta["en"], "stories": stories}
        )
    return sections


def _ai_sections(briefing):
    """AI 브리핑 데이터를 템플릿용 섹션 목록으로 변환한다."""
    sections = []
    categories = briefing.get("categories", {}) or {}
    for key, meta in AI_CATEGORY_META.items():
        raw = categories.get(key, []) or []
        stories = [_finalize_story(s, key, meta["label"]) for s in raw]
        sections.append(
            {"name": meta["label"], "flag": meta["icon"], "en": meta["en"], "stories": stories}
        )
    return sections


def world_view(briefing, date=None):
    """세계 브리핑 데이터를 HTML·JSON 공용 뷰모델로 변환한다.

    HTML 렌더링과 JSON API가 같은 최종 가공 결과(tag_label·sources 정규화·
    verification 등)를 공유하도록 한곳에서 만든다.
    """
    date = date or dt.date.today()
    return {
        "date": date.isoformat(),
        "date_str": _format_date(date),
        "key5": briefing.get("key5", []),
        "regions": _world_regions(briefing),
    }


def ai_view(briefing, date=None):
    """AI 브리핑 데이터를 HTML·JSON 공용 뷰모델로 변환한다."""
    date = date or dt.date.today()
    return {
        "date": date.isoformat(),
        "date_str": _format_date(date),
        "highlights": briefing.get("highlights", []),
        "sections": _ai_sections(briefing),
    }


def render(briefing, date=None):
    """세계 뉴스 브리핑 페이지 HTML을 반환한다."""
    view = world_view(briefing, date)
    template = _env.get_template("briefing.html")
    return template.render(
        date_str=view["date_str"],
        key5=view["key5"],
        regions=view["regions"],
    )


def render_ai(briefing, date=None):
    """AI 브리핑 페이지 HTML을 반환한다."""
    view = ai_view(briefing, date)
    template = _env.get_template("ai_briefing.html")
    return template.render(
        date_str=view["date_str"],
        highlights=view["highlights"],
        sections=view["sections"],
    )


def render_email(world_briefing, ai_briefing, date=None):
    """세계 브리핑과 AI 브리핑을 한 문서에 담은 이메일 본문 HTML을 반환한다."""
    date = date or dt.date.today()
    world = world_view(world_briefing, date)
    ai = ai_view(ai_briefing, date)
    template = _env.get_template("email.html")
    return template.render(
        date_str=world["date_str"],
        key5=world["key5"],
        regions=world["regions"],
        ai_highlights=ai["highlights"],
        ai_sections=ai["sections"],
    )


if __name__ == "__main__":
    # 모의 데이터로 세 가지 렌더링을 모두 점검한다.
    world_mock = {
        "key5": [f"세계 핵심 {i}" for i in range(1, 6)],
        "regions": {
            name: [
                {"tag": "pol", "title": f"{name} 다출처 예시", "summary": "요약.",
                 "sources": [
                     {"name": "연합뉴스", "url": "https://www.yna.co.kr/"},
                     {"name": "Reuters", "url": "https://www.reuters.com/"},
                 ], "verification": "multi"},
                {"tag": "eco", "title": f"{name} 단일 예시", "summary": "요약.",
                 "sources": [{"name": "한겨레", "url": ""}], "verification": "single"},
            ]
            for name in SOURCES
        },
    }
    ai_mock = {
        "highlights": [f"AI 핵심 {i}" for i in range(1, 6)],
        "categories": {
            key: [
                {"title": f"{meta['label']} 예시", "summary": "AI 요약.",
                 "sources": [
                     {"name": "VentureBeat AI", "url": "https://venturebeat.com/"},
                     {"name": "TechCrunch AI", "url": "https://techcrunch.com/"},
                 ], "verification": "multi"}
            ]
            for key, meta in AI_CATEGORY_META.items()
        },
    }
    for label, html in [
        ("briefing", render(world_mock)),
        ("ai", render_ai(ai_mock)),
        ("email", render_email(world_mock, ai_mock)),
    ]:
        print(f"[{label}] 길이 {len(html)}")
