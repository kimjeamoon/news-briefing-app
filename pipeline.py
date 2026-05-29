"""수집한 기사의 색인과 근거 수집 — 세계·AI 브리핑이 공유하는 유틸.

근거 수집(gather_evidence)은 선별된 각 사안에 대해
기사 원문 본문을 추출하고 Tavily 웹 검색으로 추가 출처를 모은다.
"""

from extract import fetch_many
from search import search, search_available

# 한 사안당 본문을 가져올 RSS 기사 최대 개수.
MAX_ARTICLES_PER_STORY = 3
# write 단계로 넘기는 본문 텍스트 최대 길이.
EVIDENCE_TEXT_LIMIT = 2800


def flatten_regions(articles_by_region):
    """{지역: [기사]} 를 id 와 region 이 붙은 평탄한 목록으로 바꾼다."""
    flat = []
    for region, articles in articles_by_region.items():
        for article in articles:
            flat.append({**article, "region": region, "id": len(flat)})
    return flat


def index_articles(articles):
    """기사 목록에 id 를 붙인다 (지역 구분이 없는 AI 브리핑용)."""
    return [{**article, "id": idx} for idx, article in enumerate(articles)]


def gather_evidence(stories, articles_by_id):
    """선별된 사안마다 원문 본문과 웹 검색 결과를 모은다.

    각 story 의 article_ids·search_query 를 사용하며,
    story 의 나머지 메타 필드(region/category/tag/event 등)는 그대로 보존한다.
    """
    # 1) 본문을 가져올 URL 을 한꺼번에 모아 병렬 추출한다.
    urls = []
    for story in stories:
        picked = []
        for art_id in story.get("article_ids", []):
            article = articles_by_id.get(art_id)
            if article:
                picked.append(article)
            if len(picked) >= MAX_ARTICLES_PER_STORY:
                break
        story["_articles"] = picked
        urls.extend(a.get("link", "") for a in picked if a.get("link"))

    print(f"[근거 수집] 기사 원문 {len({u for u in urls if u})}건 추출 중...")
    fulltext = fetch_many(urls)

    use_search = search_available()
    if not use_search:
        print("[근거 수집] TAVILY_API_KEY 없음 — 웹 추가 검색 생략, RSS 매체만으로 교차검증")

    # 2) 사안별 근거 묶음을 구성한다.
    gathered = []
    for idx, story in enumerate(stories, 1):
        rss_evidence = []
        for article in story["_articles"]:
            text = fulltext.get(article.get("link", "")) or article.get("summary", "")
            rss_evidence.append(
                {
                    "source": article["source"],
                    "url": article.get("link", ""),
                    "title": article["title"],
                    "text": (text or "")[:EVIDENCE_TEXT_LIMIT],
                }
            )

        search_evidence = []
        if use_search:
            query = story.get("search_query", "")
            print(f"  ({idx}/{len(stories)}) 웹 검색: {query}")
            search_evidence = search(query)

        # 내부 키와 처리용 키를 뺀 나머지(region/category/tag/event)는 보존한다.
        meta = {
            k: v
            for k, v in story.items()
            if not k.startswith("_") and k not in ("article_ids", "search_query")
        }
        gathered.append(
            {**meta, "rss_evidence": rss_evidence, "search_evidence": search_evidence}
        )
    return gathered
