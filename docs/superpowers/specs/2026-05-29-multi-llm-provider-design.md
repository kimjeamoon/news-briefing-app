# 멀티 LLM 제공자 지원 설계

날짜: 2026-05-29

## 목표

뉴스 브리핑 파이프라인의 LLM 호출을 `LLM_PROVIDER` 환경변수로
Anthropic / Gemini / OpenAI 중 선택할 수 있게 한다.
`LLM_PROVIDER` 가 없으면 기존 Anthropic 동작을 그대로 유지한다(하위 호환).

## 변경 범위

모든 LLM 호출은 `summarize.py` 의 `_call()` 한 곳으로 모인다.
따라서 `_client()` / `_model()` / `_call()` 만 교체하면 된다.

- `select_stories`, `write_briefing`, `select_ai_stories`, `write_ai_briefing`
  (4개 공개 함수): **수정 불필요**
- `briefing.py`, `ai_briefing.py` (소비자): **수정 불필요**
- JSON 추출 `_extract_json()`: 코드펜스를 이미 처리하므로 세 제공자 공통으로 재사용

## 동작

```
LLM_PROVIDER:  anthropic (기본) | gemini | openai
```

`_call(prompt, max_tokens)` 가 `LLM_PROVIDER` 를 읽어 분기한다.
세 경우 모두 system 프롬프트(`_SYSTEM`) + user 프롬프트(`prompt`)를 보내고
응답 텍스트를 반환한다.

```python
def _call(prompt, max_tokens):
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "gemini":
        return _call_gemini(prompt, max_tokens)
    if provider == "openai":
        return _call_openai(prompt, max_tokens)
    return _call_anthropic(prompt, max_tokens)
```

## 환경변수

| 변수 | 기본값 | 비고 |
|------|--------|------|
| `LLM_PROVIDER` | `anthropic` | `anthropic` / `gemini` / `openai` |
| `ANTHROPIC_API_KEY` | (필수, anthropic 사용 시) | 기존 |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | 기존 |
| `GEMINI_API_KEY` (또는 `GOOGLE_API_KEY`) | (필수, gemini 사용 시) | |
| `GEMINI_MODEL` | `gemini-2.5-flash` | |
| `OPENAI_API_KEY` | (필수, openai 사용 시) | |
| `OPENAI_MODEL` | `gpt-4o` | |

API 키는 각 SDK 표준 변수에서 읽는다.

## 구현 방식

각 제공자별 공식 SDK 사용:

- **Anthropic** (`anthropic`): 기존 코드 그대로.
- **Gemini** (`google-genai`): `system_instruction` 에 `_SYSTEM`,
  `max_output_tokens` 설정.
- **OpenAI** (`openai`): system/user 역할로 messages 구성, `max_tokens` 설정.

SDK import 는 선택한 제공자에서만 수행한다(lazy import — `search.py` 의
`TavilyClient` 패턴과 동일). 미설치 패키지 때문에 앱이 죽지 않도록 한다.

## 에러 처리

선택한 제공자의 SDK 가 미설치면 명확한 한국어 안내와 함께 `ImportError` 를
다시 던진다. 예:
`"gemini 사용에는 google-genai 패키지가 필요합니다: pip install google-genai"`

## 패키지 / 설정 파일

- `requirements.txt`: `google-genai`, `openai` 추가
- `.env.example`: `LLM_PROVIDER` 및 세 제공자의 키·모델 변수 설명 추가

## 검증

- 기존 동작 회귀: `LLM_PROVIDER` 미설정 시 Anthropic 경로로 진입하는지
- 분기 정확성: 각 `LLM_PROVIDER` 값에 대해 올바른 `_call_*` 가 호출되는지
- SDK 미설치 시 명확한 한국어 에러 메시지
