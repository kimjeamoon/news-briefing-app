"""기사 원문 본문 추출.

RSS 는 제목과 짧은 요약만 주므로, 선별된 사안의 기사 링크에서
본문 전문을 직접 가져와 요약 품질을 높인다.
여러 URL 을 병렬로 가져온다.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

try:
    import trafilatura
except ImportError:
    trafilatura = None

# trafilatura 의 잡다한 경고 로그를 끈다.
logging.getLogger("trafilatura").setLevel(logging.CRITICAL)

MAX_WORKERS = 8
MAX_CHARS = 6000


def fetch_fulltext(url):
    """URL 에서 기사 본문 텍스트를 추출한다. 실패하면 빈 문자열."""
    if not url or trafilatura is None:
        return ""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        text = trafilatura.extract(
            downloaded, include_comments=False, include_tables=False
        )
        return (text or "").strip()[:MAX_CHARS]
    except Exception as exc:
        print(f"  [경고] 본문 추출 실패: {url} ({exc})")
        return ""


def fetch_many(urls):
    """여러 URL 의 본문을 병렬로 가져와 {url: text} 딕셔너리로 반환한다."""
    unique = [u for u in dict.fromkeys(urls) if u]
    if not unique:
        return {}
    result = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for url, text in zip(unique, pool.map(fetch_fulltext, unique)):
            result[url] = text
    return result
