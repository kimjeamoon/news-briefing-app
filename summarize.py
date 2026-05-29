"""Claude API 기반 3단계 요약·교차검증 파이프라인.

  1단계 select_stories() : RSS 기사를 사건별로 묶어 지역별 후보 사안을 선별한다.
  (사이 단계) briefing.py 가 각 사안의 원문 본문과 웹 검색 결과를 모은다.
  3단계 write_briefing() : 모은 근거로 여러 매체가 같은 사실을 보도했는지
                           교차 검증하고 최종 브리핑 기사를 작성한다.

LLM 제공자는 LLM_PROVIDER 환경변수로 고른다(기본: anthropic).
  anthropic : ANTHROPIC_API_KEY,  ANTHROPIC_MODEL(기본 claude-sonnet-4-6)
  gemini    : GEMINI_API_KEY(또는 GOOGLE_API_KEY),  GEMINI_MODEL(기본 gemini-2.5-flash)
  openai    : OPENAI_API_KEY,  OPENAI_MODEL(기본 gpt-4o)
"""

import json
import os
import time

_SYSTEM = (
    "당신은 세계 주요국 뉴스를 정리하는 신뢰받는 편집자입니다. "
    "정확하고 검증 가능한 정보만 다루며, 추측성·미확인 정보나 선정적 가십은 제외합니다. "
    "한국어로, 객관적이고 중립적인 정보 전달체로 작성합니다."
)

# ── 1단계: 사건 묶기 + 후보 선별 ──────────────────────────────────────
_SELECT_PROMPT = """아래는 여러 매체에서 수집한 최근 뉴스 기사 목록입니다(JSON).
각 기사에는 고유 id, 지역(region), 매체(source), 제목(title), 짧은 요약(summary)이 있습니다.

할 일:
1. 같은 사건·이슈를 다룬 기사들을 하나로 묶습니다.
2. 각 지역에서 가장 중요한 사안을 선별합니다 (한국·미국·중국·일본·유럽은 3~4건, 기술·과학은 3건).
3. 정치·외교, 경제·시장, 기술·과학, 사회 분야가 고르게 포함되도록 합니다.

각 사안마다 다음을 작성하세요:
- region: 지역명 (한국 / 미국 / 중국·일본 / 유럽 / 기술·과학 중 하나, 입력과 동일하게)
- tag: pol(정치·외교) / eco(경제·시장) / tec(기술·과학) / soc(사회) 중 하나
- event: 사건을 설명하는 한 문장 (다음 단계 검색·작성의 기준이 됨)
- search_query: 이 사안을 웹에서 교차 확인할 검색어. 핵심 고유명사를 포함하고 영어로 작성
- article_ids: 이 사안을 다룬 기사들의 id 목록 (여러 매체일수록 좋음)

반드시 아래 JSON 형식으로만 응답하세요(코드펜스·설명 금지):
{{"stories": [
  {{"region": "한국", "tag": "pol", "event": "...", "search_query": "...", "article_ids": [1, 7]}}
]}}

수집 기사:
{articles}
"""

# ── 3단계: 교차 검증 + 최종 작성 ──────────────────────────────────────
_WRITE_PROMPT = """아래는 선별된 사안들과 각 사안의 근거 자료입니다(JSON).
각 사안에는 event(사건 설명), region, tag, 그리고 두 종류의 근거가 있습니다:
- rss_evidence: 주요 매체 기사들의 본문 (source=매체명, url=기사 URL, title, text=본문)
- search_evidence: 웹 검색으로 찾은 추가 출처들 (domain=매체 도메인, url=기사 URL, title, content=발췌)

각 사안에 대해 다음을 수행하세요:

[교차 검증]
- 핵심 사실이 서로 독립적인 언론사 2곳 이상에서 확인되면 verification = "multi"
- 한 곳에서만 확인되면 verification = "single"
- 같은 통신사(예: 연합뉴스·Reuters·AP) 기사를 여러 매체가 받아쓴 경우는 한 곳으로 셉니다.
- 근거 본문이 부실하거나 사실이 모호하면 신중하게 표현하고 verification = "single" 로 둡니다.

[기사 작성]
- title: 한국어 16~45자, 핵심이 드러나게
- summary: 2~3문장, 사실 위주로 객관적으로. 근거 자료에서 확인된 내용만 사용
- sources: 실제로 사실을 확인한 출처 2~4개. 각 출처는 {{"name": 매체명, "url": 기사 URL}} 객체로
  적습니다. URL 은 rss_evidence 의 url 또는 search_evidence 의 url 중에서 그 사실을 직접 확인한
  것을 사용합니다. URL 이 확실하지 않으면 빈 문자열("")로 둡니다.
- verification: "multi" 또는 "single"

마지막으로 그날 가장 중요한 5건을 한 줄씩 요약한 key5 를 작성합니다.

반드시 아래 JSON 형식으로만 응답하세요(코드펜스·설명 금지):
{{"key5": ["...", "...", "...", "...", "..."],
  "regions": {{
    "한국": [{{"tag": "pol", "title": "...", "summary": "...",
              "sources": [{{"name": "연합뉴스", "url": "https://..."}},
                          {{"name": "한겨레", "url": "https://..."}}],
              "verification": "multi"}}],
    "미국": [...], "중국·일본": [...], "유럽": [...], "기술·과학": [...]
  }}}}

지역명은 입력과 동일하게: 한국, 미국, 중국·일본, 유럽, 기술·과학.

선별된 사안과 근거:
{stories}
"""


def _provider():
    return os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()


def _require(module, package, provider):
    """제공자 SDK 를 지연 import 한다. 미설치 시 한국어 안내와 함께 다시 던진다."""
    try:
        return __import__(module, fromlist=["_"])
    except ImportError as exc:
        raise ImportError(
            f"{provider} 사용에는 {package} 패키지가 필요합니다: pip install {package}"
        ) from exc


def _call_anthropic(prompt, max_tokens):
    anthropic = _require("anthropic", "anthropic", "anthropic")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    message = anthropic.Anthropic().messages.create(  # ANTHROPIC_API_KEY 를 환경변수에서 읽음
        model=model,
        max_tokens=max_tokens,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if hasattr(block, "text"))


def _call_gemini(prompt, max_tokens):
    genai = _require("google.genai", "google-genai", "gemini")
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "system_instruction": _SYSTEM,
            "max_output_tokens": max_tokens,
            "response_mime_type": "application/json",  # 유효한 JSON 만 반환하도록 강제
            # 2.5 모델의 내부 추론(thinking)은 max_output_tokens 예산을 잠식해
            # JSON 이 잘리게 한다(MAX_TOKENS). 구조화 추출에는 불필요하므로 끈다.
            "thinking_config": {"thinking_budget": 0},
        },
    )
    return response.text or ""


def _call_openai(prompt, max_tokens):
    openai = _require("openai", "openai", "openai")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    client = openai.OpenAI()  # OPENAI_API_KEY 를 환경변수에서 읽음
    completion = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},  # 유효한 JSON 만 반환하도록 강제
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content or ""


def _is_transient(exc):
    """일시적 오류(과부하·속도제한·서버 오류)인지 추정한다. 이 경우 재시도한다."""
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status in (429, 500, 502, 503, 504):
        return True
    text = str(exc).lower()
    return any(k in text for k in ("503", "overload", "unavailable", "rate limit", "429", "high demand"))


def _call(prompt, max_tokens, retries=4):
    """선택된 제공자로 호출한다. 일시적 오류는 지수 백오프로 재시도한다."""
    provider = _provider()
    fn = {"gemini": _call_gemini, "openai": _call_openai}.get(provider, _call_anthropic)
    for attempt in range(retries):
        try:
            return fn(prompt, max_tokens)
        except Exception as exc:  # 마지막 시도이거나 일시적 오류가 아니면 그대로 던진다
            if attempt == retries - 1 or not _is_transient(exc):
                raise
            wait = 2 ** attempt  # 1s, 2s, 4s, ...
            print(f"  [재시도] {provider} 일시 오류 ({str(exc)[:60]}) — {wait}s 후 재시도")
            time.sleep(wait)


def _extract_json(text):
    """모델 응답에서 JSON 객체를 추출해 파싱한다."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def select_stories(flat_articles):
    """1단계: 평탄화된 기사 목록에서 후보 사안을 선별한다.

    flat_articles: [{id, region, source, title, summary}, ...]
    반환: [{region, tag, event, search_query, article_ids}, ...]
    """
    compact = [
        {
            "id": a["id"],
            "region": a["region"],
            "source": a["source"],
            "title": a["title"],
            "summary": a.get("summary", "")[:300],
        }
        for a in flat_articles
    ]
    payload = json.dumps(compact, ensure_ascii=False)
    raw = _call(_SELECT_PROMPT.format(articles=payload), max_tokens=4096)
    result = _extract_json(raw)
    stories = result.get("stories", [])
    if not stories:
        raise ValueError("1단계 선별 결과가 비어 있습니다.")
    return stories


def write_briefing(stories_with_evidence):
    """3단계: 근거가 모인 사안들로 교차 검증을 거쳐 최종 브리핑을 작성한다.

    stories_with_evidence: [{region, tag, event, rss_evidence, search_evidence}, ...]
    반환: {"key5": [...], "regions": {지역명: [기사, ...]}}
    """
    payload = json.dumps(stories_with_evidence, ensure_ascii=False)
    raw = _call(_WRITE_PROMPT.format(stories=payload), max_tokens=8192)
    briefing = _extract_json(raw)
    if "key5" not in briefing or "regions" not in briefing:
        raise ValueError("3단계 작성 결과에 key5 또는 regions 키가 없습니다.")
    return briefing


# ── AI 브리핑: 1단계 사건 묶기 + 분야 선별 ────────────────────────────
_SELECT_AI_PROMPT = """아래는 AI 전문 매체·블로그·논문에서 수집한 최근 기사 목록입니다(JSON).
각 기사에는 고유 id, 매체(source), 제목(title), 짧은 요약(summary)이 있습니다.

할 일:
1. 같은 사건·발표·연구를 다룬 기사들을 하나로 묶습니다.
2. 가장 중요한 AI 소식 10~14건을 선별합니다.
3. 각 사안을 다음 4개 분야 중 하나로 분류하되, 분야가 고르게 포함되도록 합니다
   (각 분야 3~4건 권장):
   - release  : 모델·제품 출시 (새 모델 발표, 제품 업데이트, 기능 공개)
   - research : 연구·논문 (연구 성과, 논문, 기술적 돌파)
   - industry : 산업·투자·기업 (기업 소식, 투자·인수, 시장 동향, 반도체)
   - policy   : 정책·규제·안전 (AI 규제, 정부 정책, 안전·윤리 이슈)

각 사안마다 작성하세요:
- category    : release / research / industry / policy 중 하나
- event       : 사건을 설명하는 한 문장
- search_query: 웹에서 교차 확인할 검색어. 핵심 고유명사를 포함하고 영어로 작성
- article_ids : 이 사안을 다룬 기사들의 id 목록

반드시 아래 JSON 형식으로만 응답하세요(코드펜스·설명 금지):
{{"stories": [
  {{"category": "release", "event": "...", "search_query": "...", "article_ids": [2, 9]}}
]}}

수집 기사:
{articles}
"""

# ── AI 브리핑: 3단계 교차 검증 + 최종 작성 ────────────────────────────
_WRITE_AI_PROMPT = """아래는 선별된 AI 사안들과 각 사안의 근거 자료입니다(JSON).
각 사안에는 event(사건 설명), category(분야), 그리고 두 종류의 근거가 있습니다:
- rss_evidence   : 매체 기사 본문 (source=매체명, url=기사 URL, title, text=본문)
- search_evidence: 웹 검색으로 찾은 추가 출처 (domain=매체 도메인, url=기사 URL, title, content=발췌)

각 사안에 대해:

[교차 검증]
- 핵심 사실이 서로 독립적인 출처 2곳 이상에서 확인되면 verification = "multi"
- 한 곳에서만 확인되면 verification = "single"
- 같은 발표·논문을 여러 매체가 받아쓴 경우는 한 곳으로 셉니다.
- 근거가 부실하거나 사실이 모호하면 신중히 표현하고 verification = "single" 로 둡니다.
- 논문 사전공개(arXiv 등) 단독 건은 동료평가 전임을 감안해 verification = "single".

[기사 작성]
- title       : 한국어 16~45자, 핵심이 드러나게
- summary     : 2~3문장, 사실 위주로 객관적으로. 근거에서 확인된 내용만 사용
- sources     : 실제로 확인한 출처 2~4개. 각 출처는 {{"name": 매체명, "url": 기사 URL}} 객체로
                적습니다. URL 은 rss_evidence·search_evidence 의 url 중 그 사실을 확인한 것을
                그대로 사용합니다. URL 이 확실하지 않으면 ""(빈 문자열)로 둡니다.
- verification: "multi" 또는 "single"

마지막으로 그날 가장 중요한 AI 소식 5건을 한 줄씩 요약한 highlights 를 작성합니다.

반드시 아래 JSON 형식으로만 응답하세요(코드펜스·설명 금지):
{{"highlights": ["...", "...", "...", "...", "..."],
  "categories": {{
    "release": [{{"title": "...", "summary": "...",
                  "sources": [{{"name": "VentureBeat AI", "url": "https://..."}},
                              {{"name": "TechCrunch AI", "url": "https://..."}}],
                  "verification": "multi"}}],
    "research": [...], "industry": [...], "policy": [...]
  }}}}

분야 키는 release, research, industry, policy 만 사용하세요.

선별된 사안과 근거:
{stories}
"""


def select_ai_stories(flat_articles):
    """AI 1단계: 기사 목록에서 분야별 후보 사안을 선별한다.

    반환: [{category, event, search_query, article_ids}, ...]
    """
    compact = [
        {
            "id": a["id"],
            "source": a["source"],
            "title": a["title"],
            "summary": a.get("summary", "")[:300],
        }
        for a in flat_articles
    ]
    payload = json.dumps(compact, ensure_ascii=False)
    raw = _call(_SELECT_AI_PROMPT.format(articles=payload), max_tokens=4096)
    stories = _extract_json(raw).get("stories", [])
    if not stories:
        raise ValueError("AI 1단계 선별 결과가 비어 있습니다.")
    return stories


def write_ai_briefing(stories_with_evidence):
    """AI 3단계: 근거가 모인 사안들로 교차 검증을 거쳐 AI 브리핑을 작성한다.

    반환: {"highlights": [...], "categories": {분야: [기사, ...]}}
    """
    payload = json.dumps(stories_with_evidence, ensure_ascii=False)
    raw = _call(_WRITE_AI_PROMPT.format(stories=payload), max_tokens=8192)
    briefing = _extract_json(raw)
    if "highlights" not in briefing or "categories" not in briefing:
        raise ValueError("AI 3단계 작성 결과에 highlights 또는 categories 키가 없습니다.")
    return briefing
