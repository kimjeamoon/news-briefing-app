"""AI 전용 브리핑의 뉴스 소스와 분야 정의.

세계 브리핑(sources.py)이 지역으로 나뉘는 것과 달리, AI 브리핑은 분야로 나뉜다.
어느 분야에 속하는지는 RSS 가 아니라 요약 단계에서 Claude 가 판단한다.
"""

# AI 전문 매체·블로그·논문 피드 (지역 구분 없는 단일 풀)
AI_FEEDS = [
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("MIT Technology Review", "https://www.technologyreview.com/feed/"),
    ("MIT News (AI)", "https://news.mit.edu/rss/topic/artificial-intelligence2"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("AI News", "https://www.artificialintelligence-news.com/feed/"),
    ("arXiv cs.AI", "https://export.arxiv.org/rss/cs.AI"),
]

# AI 브리핑의 분야. 순서대로 페이지에 노출된다.
#   key   : 내부 식별자이자 CSS 클래스명
#   label : 한국어 표시명
#   en    : 영문 부제
#   icon  : 섹션 아이콘
AI_CATEGORY_META = {
    "release": {"label": "모델·제품 출시", "en": "MODELS & PRODUCTS", "icon": "\U0001F680"},
    "research": {"label": "연구·논문", "en": "RESEARCH", "icon": "\U0001F9EA"},
    "industry": {"label": "산업·투자·기업", "en": "INDUSTRY & INVESTMENT", "icon": "\U0001F4BC"},
    "policy": {"label": "정책·규제·안전", "en": "POLICY & SAFETY", "icon": "⚖️"},
}
