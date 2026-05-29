# 아침 뉴스 브리핑 (Morning News Briefing)

세계 주요국(한국·미국·중국·일본·유럽)의 최신 뉴스와 **AI 분야 소식**을 매일 자동으로
수집·요약해 **웹 페이지**로 보여주고 **이메일**로 발송하는 독립 실행형 앱입니다.

Cowork 같은 외부 도구 없이, 본인 서버(또는 PC)에서 혼자 돌아갑니다.

두 가지 브리핑을 만듭니다:

- **세계 뉴스 브리핑** (`/`) — 한국·미국·중국·일본·유럽·기술과학
- **AI 브리핑** (`/ai`) — 모델·제품 출시 / 연구·논문 / 산업·투자·기업 / 정책·규제·안전

매일 아침 이메일에는 두 브리핑이 한 통에 담겨 발송됩니다.

## 동작 방식 (심층 검색 + 교차 검증)

```
1) RSS 수집        여러 매체의 RSS 에서 최근 36시간 기사 수집
2) 후보 선별       Claude 가 같은 사건끼리 묶어 지역별 핵심 사안 선별
3) 근거 수집       각 사안의 기사 원문 본문 추출 + Tavily 웹 검색으로 추가 출처 확보
4) 교차 검증·작성  여러 매체가 같은 사실을 보도했는지 따져 최종 기사 작성
5) 제공            HTML 브리핑 생성 → 웹 제공 + 이메일 발송
```

신뢰할 수 있는 매체의 RSS(연합뉴스·한겨레·경향신문·Korea Herald·NYT·BBC·NPR·
The Guardian·Japan Times·NHK World·SCMP·Nikkei Asia·Euronews·Politico·Ars Technica·
ScienceDaily·The Verge 등)에서 기사를 모읍니다. 단순히 RSS 요약문만 보지 않고,
선별된 사안은 **기사 원문 본문을 직접 가져와 읽고**, **Tavily 웹 검색으로 추가
출처를 찾아 교차 확인**합니다.

각 기사에는 검증 배지가 붙습니다:

- **✓ 다출처 확인** — 둘 이상의 독립 매체에서 확인된 사안
- **단일 출처 · 확인 필요** — 한 매체에서만 확인된 사안 (제외하지 않고 표시해 포함)

## 필요한 것

- Python 3.10 이상
- Anthropic API 키 (뉴스 요약·검증용) — https://console.anthropic.com
- Tavily API 키 (웹 교차 검색용, 권장) — https://tavily.com · 무료 월 1,000회
  - 없어도 동작하며, 이 경우 교차 검증을 RSS 매체만으로 수행합니다.
- (선택) 이메일 발송용 SMTP 계정 — 예: Gmail 앱 비밀번호

## 설치

```bash
cd news-briefing-app
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # .env 파일을 열어 값 입력
```

`.env` 에서 최소한 `ANTHROPIC_API_KEY` 는 반드시 채워야 합니다.
이메일을 받으려면 `SMTP_*` 와 `EMAIL_TO` 도 입력하세요. (비워 두면 웹 페이지만 갱신)

## 실행 방법

### 방법 A — 웹 서버 + 내장 스케줄러 (권장)

`server.py` 하나만 띄우면 웹 페이지 제공과 매일 자동 갱신을 함께 합니다.

```bash
python server.py
```

- `http://localhost:8080` — 세계 뉴스 브리핑
- `http://localhost:8080/ai` — AI 브리핑
- 매일 `RUN_HOUR:RUN_MINUTE`(기본 07:00)에 두 브리핑을 자동 생성하고, 한 통의
  이메일로 발송
- 과거 브리핑: `/archive/briefing-2026-05-25.html`, `/archive/ai-2026-05-25.html`

서버를 끄지 않고 계속 켜 두어야 자동 갱신이 동작합니다. 백그라운드 상시 실행은
아래 "상시 실행" 항목을 참고하세요.

### 방법 B — cron 으로 하루 한 번만 실행

웹 페이지가 필요 없거나 OS 의 cron 을 쓰고 싶으면:

```bash
python run_daily.py             # 즉시 1회 생성 + 이메일 발송
python run_daily.py --no-email  # 이메일 없이 생성만
```

`crontab.example` 파일을 참고해 `crontab -e` 에 등록하면 매일 자동 실행됩니다.

## 모바일 앱 (PWA)

별도 앱 설치 없이, 브라우저에서 **홈 화면에 추가**하면 일반 앱처럼 전체화면으로
열리고 아이콘이 생깁니다(PWA). 오프라인일 때는 마지막으로 본 브리핑이 표시됩니다.

- **iPhone (Safari)**: 브리핑 페이지 열기 → 공유 버튼 → **홈 화면에 추가**
- **Android (Chrome)**: 브리핑 페이지 열기 → 메뉴(⋮) → **앱 설치** (또는 설치 배너)

서버는 다음 PWA 자산을 제공합니다:

- `/manifest.webmanifest` — 앱 이름·아이콘·시작 화면 정의
- `/sw.js` — 서비스 워커(오프라인 캐싱, 루트 스코프)
- `/static/icons/…`, `/static/icon.svg` — 앱 아이콘

> 아이콘은 `static/icons/` 에 PNG 로 들어 있습니다. 다시 만들려면
> `pip install Pillow` 후 `python tools/make_icons.py` 를 실행하세요
> (`static/icon.svg` 와 같은 디자인을 도형으로 생성하며, 런타임 의존성은 아닙니다).

### JSON API

브리핑 데이터는 HTML 과 동일한 내용을 JSON 으로도 제공합니다(향후 네이티브 앱·
연동의 기반). 응답에는 `Access-Control-Allow-Origin: *` 가 포함됩니다.

| 엔드포인트 | 내용 |
|------------|------|
| `GET /api/world` | 최신 세계 뉴스 브리핑 |
| `GET /api/ai` | 최신 AI 브리핑 |
| `GET /api/world/YYYY-MM-DD` | 날짜별 세계 뉴스 브리핑 |
| `GET /api/ai/YYYY-MM-DD` | 날짜별 AI 브리핑 |

같은 데이터가 `OUTPUT_DIR` 에 `index.json` / `ai.json`(최신)과
`briefing-YYYY-MM-DD.json` / `ai-YYYY-MM-DD.json`(날짜별)으로도 저장됩니다.

### 향후 푸시 알림 (아직 미구현)

매일 아침 브리핑을 푸시로 받으려면 다음을 추가하면 됩니다(현재는 토대만 마련됨):

1. 디바이스 토큰 등록 엔드포인트(예: `POST /api/devices`) 와 토큰 저장소
2. `server.py` 의 `run_job()` 말미(이메일 발송과 같은 위치)에서 푸시 발송 호출
3. 발송 채널: Web Push(VAPID) 또는 FCM/APNs 중 택1

## 상시 실행 (서버에 올리기)

### Docker (가장 간단)

```bash
docker build -t news-briefing .
docker run -d --name news-briefing \
  -p 8080:8080 \
  -v $(pwd)/data:/data \
  --env-file .env \
  --restart unless-stopped \
  news-briefing
```

`data/` 폴더에 브리핑 HTML 이 보존되고, 서버 재시작 후에도 유지됩니다.

### GitHub Actions + Pages (무료·무관리, 권장)

서버를 24시간 띄울 필요 없이, **매일 한 번 GitHub Actions 가 브리핑을
생성해 GitHub Pages 에 게시**합니다. 사용자가 적은 개인용으로 가장 안정적이고
완전 무료입니다(공개 저장소 기준). 최신 브리핑만 게시하며 아카이브는 없습니다.

워크플로 파일: [`.github/workflows/daily.yml`](.github/workflows/daily.yml)
(매일 KST 07:00 = UTC 22:00 실행, 수동 실행도 가능).

**설정 순서:**

1. 이 저장소를 GitHub 에 푸시한다(공개 저장소 권장 — 비공개는 Pro 플랜에서만 Pages 동작).
2. **Settings → Secrets and variables → Actions → Secrets** 에 키를 등록한다:
   `GEMINI_API_KEY`(필수), `TAVILY_API_KEY`(선택),
   이메일을 보낼 경우 `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD`
   `EMAIL_FROM` `EMAIL_TO`. (다른 제공자를 쓰면 `ANTHROPIC_API_KEY` /
   `OPENAI_API_KEY`.)
3. 제공자·모델을 바꾸려면 같은 화면의 **Variables** 탭에 `LLM_PROVIDER`,
   `GEMINI_MODEL` 등을 등록한다(없으면 워크플로 기본값 사용).
4. **Settings → Pages → Source** 를 `gh-pages` 브랜치로 지정한다
   (첫 워크플로 실행 후 브랜치가 생성된다).
5. **Actions** 탭에서 워크플로를 한 번 수동 실행(Run workflow)해 확인한다.

게시 후 주소: 세계 `https://<사용자>.github.io/<저장소>/`,
AI `https://<사용자>.github.io/<저장소>/ai`.

### 컨테이너 호스팅 (상시 서버가 필요할 때)

`Dockerfile` 이 있으므로 Railway, Render, Fly.io, Google Cloud Run 등
컨테이너 기반 PaaS 에 그대로 배포할 수 있습니다. 환경변수는 각 플랫폼의
설정 화면에 `.env` 내용과 동일하게 입력하세요. 포트는 8080 입니다.

> 참고: 무료 인스턴스는 트래픽이 없으면 잠들어(sleep) 내장 스케줄러가 멈추고,
> 디스크가 휘발성이라 재시작 시 `output/` 이 사라질 수 있습니다. Cloud Run
> 처럼 잠드는 환경에서는 플랫폼 스케줄러(예: Cloud Scheduler)로 `run_daily.py`
> 를 호출하거나 항상 켜져 있는 인스턴스를 쓰세요. 무료로 안정적으로 운영하려면
> 위의 GitHub Actions 방식을 권장합니다.

### Linux 서버 (systemd)

```ini
# /etc/systemd/system/news-briefing.service
[Unit]
Description=Morning News Briefing
After=network.target

[Service]
WorkingDirectory=/opt/news-briefing-app
ExecStart=/opt/news-briefing-app/.venv/bin/python server.py
EnvironmentFile=/opt/news-briefing-app/.env
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now news-briefing
```

## 설정 항목 (.env)

| 변수 | 설명 | 필수 |
|------|------|------|
| `ANTHROPIC_API_KEY` | 뉴스 요약·검증용 Claude API 키 | 필수 |
| `ANTHROPIC_MODEL` | 사용할 모델 (기본 claude-sonnet-4-6) | 선택 |
| `TAVILY_API_KEY` | 웹 교차 검색용 Tavily 키 (없으면 RSS만으로 검증) | 권장 |
| `SMTP_HOST/PORT/USER/PASSWORD` | 이메일 발송용 SMTP 정보 | 이메일 시 |
| `EMAIL_FROM` | 보내는 주소 (기본값: SMTP_USER) | 선택 |
| `EMAIL_TO` | 받는 주소 (쉼표로 여러 명) | 이메일 시 |
| `OUTPUT_DIR` | HTML 저장 폴더 (기본 ./output) | 선택 |
| `SERVER_HOST/PORT` | 웹 서버 바인딩 (기본 0.0.0.0:8080) | 선택 |
| `RUN_HOUR/RUN_MINUTE` | 자동 갱신 시각 (기본 07:00) | 선택 |
| `TZ` | 시간대 (한국은 Asia/Seoul 권장) | 권장 |

## 뉴스 매체 추가·변경

세계 브리핑 매체는 `sources.py` 의 `SOURCES`, AI 브리핑 매체는 `ai_sources.py` 의
`AI_FEEDS` 에서 `(매체이름, RSS주소)` 형태로 추가·삭제할 수 있습니다. 피드 일부가
실패해도 나머지로 브리핑이 생성됩니다. AI 브리핑의 분야 구성은 `ai_sources.py` 의
`AI_CATEGORY_META` 에서 조정합니다.

## 파일 구성

| 파일 | 역할 |
|------|------|
| `server.py` | 웹 서버 + 내장 스케줄러 (메인 실행 파일) |
| `run_daily.py` | 하루 1회 실행용 진입점 (cron 용) |
| `briefing.py` | 세계 뉴스 브리핑 파이프라인 |
| `ai_briefing.py` | AI 브리핑 파이프라인 |
| `pipeline.py` | 공용 유틸 — 기사 색인, 근거 수집(원문+웹검색) |
| `fetch_news.py` | RSS 피드 수집 |
| `summarize.py` | Claude API 후보 선별(1단계) + 교차검증·작성(3단계), 세계·AI 양쪽 |
| `extract.py` | 기사 원문 본문 추출 (병렬) |
| `search.py` | Tavily 웹 검색 (추가 출처 확보) |
| `render.py` | 브리핑 데이터 → HTML 렌더링 (세계/AI/이메일) |
| `emailer.py` | 이메일 발송 |
| `sources.py` | 세계 뉴스 매체(RSS) 목록 |
| `ai_sources.py` | AI 전문 매체(RSS) 목록 및 분야 정의 |
| `templates/briefing.html` | 세계 브리핑 페이지 템플릿 |
| `templates/ai_briefing.html` | AI 브리핑 페이지 템플릿 |
| `templates/email.html` | 두 브리핑을 합친 이메일 템플릿 |
| `templates/_style.html` · `_macros.html` | 공용 스타일·매크로 |
| `templates/_head_pwa.html` | PWA 공용 head(매니페스트·아이콘·서비스 워커 등록) |
| `static/manifest.webmanifest` · `sw.js` · `offline.html` | PWA 매니페스트·서비스 워커·오프라인 페이지 |
| `static/icon.svg` · `static/icons/*.png` | 앱 아이콘 |
| `tools/make_icons.py` | 앱 아이콘 PNG 생성기 (빌드타임 전용, Pillow 필요) |

## 참고

- 뉴스는 신뢰할 수 있는 주요 매체의 RSS 를 기준으로 하지만, 속보성 사안은
  원문 확인을 권장합니다.
- Claude API 사용에는 토큰 비용이 발생합니다(하루 1회 실행 기준 소액).
