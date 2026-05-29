"""Tavily 웹 검색 래퍼.

각 후보 사안에 대해 추가 출처를 찾아 교차 검증에 활용한다.
환경변수 TAVILY_API_KEY 가 없으면 검색을 건너뛰고 빈 결과를 반환한다
(이 경우 교차 검증은 RSS 매체만으로 수행된다).
"""

import os
from urllib.parse import urlparse

try:
    from tavily import TavilyClient
except ImportError:  # 패키지 미설치 시에도 앱이 죽지 않도록
    TavilyClient = None


def search_available():
    """Tavily 검색을 사용할 수 있는지 확인한다."""
    return bool(os.environ.get("TAVILY_API_KEY")) and TavilyClient is not None


def _domain(url):
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def search(query, max_results=5):
    """검색어로 최근 뉴스를 검색해 결과 목록을 반환한다.

    각 결과는 {title, url, domain, content} 형태. 실패 시 빈 목록.
    """
    if not search_available() or not query:
        return []
    try:
        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            topic="news",
            days=4,
        )
    except Exception as exc:
        print(f"  [경고] Tavily 검색 실패: {query!r} ({exc})")
        return []

    results = []
    for item in response.get("results", []):
        url = item.get("url", "")
        results.append(
            {
                "title": item.get("title", ""),
                "url": url,
                "domain": _domain(url),
                "content": (item.get("content", "") or "")[:800],
            }
        )
    return results
