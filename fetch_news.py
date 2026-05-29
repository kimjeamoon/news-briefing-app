"""RSS 피드에서 최근 기사를 수집한다."""

import datetime as dt
import re
import time

import feedparser

from sources import SOURCES

# 수집 대상 기사의 최대 경과 시간(시간 단위). 이보다 오래된 기사는 제외.
MAX_AGE_HOURS = 36
# 피드 하나에서 가져올 최대 기사 수.
MAX_PER_FEED = 12
# 일부 사이트가 기본 봇 UA를 차단하므로 브라우저 UA를 사용한다.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

_TAG_RE = re.compile(r"<[^>]+>")


def _entry_time(entry):
    """기사의 발행 시각을 UTC datetime으로 반환. 없으면 None."""
    for key in ("published_parsed", "updated_parsed"):
        parsed_time = entry.get(key)
        if parsed_time:
            return dt.datetime.fromtimestamp(time.mktime(parsed_time), tz=dt.timezone.utc)
    return None


def _clean(text):
    """HTML 태그를 제거하고 공백을 정리한다."""
    text = _TAG_RE.sub("", text or "")
    return re.sub(r"\s+", " ", text).strip()


def fetch_region(feeds):
    """한 지역의 피드 목록에서 기사를 수집한다."""
    articles = []
    seen_titles = set()
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=MAX_AGE_HOURS)

    for source_name, url in feeds:
        try:
            parsed = feedparser.parse(url, agent=USER_AGENT)
        except Exception as exc:  # 네트워크/파싱 오류는 건너뛴다.
            print(f"  [경고] 피드 수집 실패: {url} ({exc})")
            continue

        if parsed.bozo and not parsed.entries:
            print(f"  [경고] 피드가 비어 있음: {url}")
            continue

        count = 0
        for entry in parsed.entries:
            title = _clean(entry.get("title", ""))
            if not title or title in seen_titles:
                continue

            published = _entry_time(entry)
            if published and published < cutoff:
                continue

            summary = _clean(entry.get("summary") or entry.get("description") or "")
            articles.append(
                {
                    "source": source_name,
                    "title": title,
                    "summary": summary[:600],
                    "link": entry.get("link", ""),
                    "published": published.isoformat() if published else "",
                }
            )
            seen_titles.add(title)
            count += 1
            if count >= MAX_PER_FEED:
                break

    return articles


def fetch_all():
    """모든 지역의 기사를 수집해 {지역명: [기사, ...]} 형태로 반환한다."""
    result = {}
    for region, meta in SOURCES.items():
        print(f"[수집] {region} ...")
        articles = fetch_region(meta["feeds"])
        result[region] = articles
        print(f"  → {len(articles)}건")
    total = sum(len(v) for v in result.values())
    print(f"[수집 완료] 총 {total}건")
    return result


if __name__ == "__main__":
    import json

    data = fetch_all()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
