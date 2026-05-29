"""뉴스 소스(RSS 피드) 정의.

각 지역별로 신뢰할 수 있는 매체의 RSS 피드를 등록한다.
같은 지역에 매체가 많을수록 '여러 매체가 같은 사건을 보도했는가'를 따지는
교차 검증의 정확도가 올라간다.
피드 일부가 실패해도 나머지로 브리핑이 생성되도록 설계되어 있다.
새 매체를 추가하려면 (표시이름, RSS URL) 튜플을 feeds 목록에 넣으면 된다.
"""

SOURCES = {
    "한국": {
        "flag": "\U0001F1F0\U0001F1F7",
        "en": "KOREA",
        "feeds": [
            ("연합뉴스", "https://www.yna.co.kr/rss/news.xml"),
            ("연합뉴스 정치", "https://www.yna.co.kr/rss/politics.xml"),
            ("연합뉴스 경제", "https://www.yna.co.kr/rss/economy.xml"),
            ("한겨레", "https://www.hani.co.kr/rss/"),
            ("경향신문", "https://www.khan.co.kr/rss/rssdata/total_news.xml"),
            ("The Korea Herald", "https://www.koreaherald.com/rss/020000000000.xml"),
        ],
    },
    "미국": {
        "flag": "\U0001F1FA\U0001F1F8",
        "en": "UNITED STATES",
        "feeds": [
            ("The New York Times", "https://rss.nytimes.com/services/xml/rss/nyt/US.xml"),
            ("NYT Business", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"),
            ("BBC US & Canada", "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"),
            ("NPR", "https://feeds.npr.org/1001/rss.xml"),
            ("The Guardian (US)", "https://www.theguardian.com/us-news/rss"),
        ],
    },
    "중국·일본": {
        "flag": "\U0001F1E8\U0001F1F3",
        "en": "CHINA & JAPAN",
        "feeds": [
            ("The Japan Times", "https://www.japantimes.co.jp/feed/"),
            ("NHK World", "https://www3.nhk.or.jp/nhkworld/en/news/rss/all.xml"),
            ("South China Morning Post", "https://www.scmp.com/rss/91/feed"),
            ("Nikkei Asia", "https://asia.nikkei.com/rss/feed/nar"),
        ],
    },
    "유럽": {
        "flag": "\U0001F1EA\U0001F1FA",
        "en": "EUROPE",
        "feeds": [
            ("BBC Europe", "https://feeds.bbci.co.uk/news/world/europe/rss.xml"),
            ("The Guardian (World)", "https://www.theguardian.com/world/rss"),
            ("Euronews", "https://www.euronews.com/rss"),
            ("Politico Europe", "https://www.politico.eu/feed/"),
        ],
    },
    "기술·과학": {
        "flag": "\U0001F52C",
        "en": "TECH & SCIENCE",
        "feeds": [
            ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
            ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
            ("ScienceDaily", "https://www.sciencedaily.com/rss/top/science.xml"),
            ("The Verge", "https://www.theverge.com/rss/index.xml"),
        ],
    },
}
