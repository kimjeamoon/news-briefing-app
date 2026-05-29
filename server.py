#!/usr/bin/env python3
"""브리핑 웹 서버 (독립 실행 진입점).

- 세계 뉴스 브리핑(/)과 AI 브리핑(/ai)을 웹 페이지로 제공한다.
- 매일 정해진 시각(기본 07:00)에 두 브리핑을 자동으로 갱신한다.
- 이메일 설정이 있으면 두 브리핑을 한 통에 담아 발송한다.

이 파일 하나만 실행하면 웹 서버와 스케줄러가 함께 동작한다:
  python server.py
"""

import datetime as dt
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request, send_from_directory

load_dotenv()

import ai_briefing  # noqa: E402
import briefing as world_briefing  # noqa: E402
from emailer import email_configured, send_email  # noqa: E402
from render import render_email  # noqa: E402

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output"))
RUN_HOUR = int(os.environ.get("RUN_HOUR", "7"))
RUN_MINUTE = int(os.environ.get("RUN_MINUTE", "0"))

app = Flask(__name__)


def _serve(filename, empty_message):
    if not (OUTPUT_DIR / filename).exists():
        return (
            f"<h1 style='font-family:sans-serif'>{empty_message}</h1>"
            "<p style='font-family:sans-serif'>잠시 후 다시 확인해 주세요.</p>",
            200,
        )
    return send_from_directory(OUTPUT_DIR, filename)


@app.route("/")
@app.route("/index.html")
def index():
    """세계 뉴스 브리핑 페이지."""
    return _serve("index.html", "아직 생성된 브리핑이 없습니다.")


@app.route("/ai")
@app.route("/ai.html")
def ai_page():
    """AI 브리핑 페이지."""
    return _serve("ai.html", "아직 생성된 AI 브리핑이 없습니다.")


@app.route("/archive/<name>")
def archive(name):
    """과거 브리핑 (예: /archive/briefing-2026-05-25.html, /archive/ai-2026-05-25.html)."""
    valid = (name.startswith("briefing-") or name.startswith("ai-")) and name.endswith(".html")
    if not valid or not (OUTPUT_DIR / name).exists():
        abort(404)
    return send_from_directory(OUTPUT_DIR, name)


@app.route("/healthz")
def healthz():
    """헬스 체크용 엔드포인트."""
    return {"status": "ok"}


# ---- PWA (모바일 앱) 자산 ----

@app.route("/manifest.webmanifest")
def manifest():
    """웹 앱 매니페스트 (홈 화면 설치용)."""
    return send_from_directory(
        app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json"
    )


@app.route("/sw.js")
def service_worker():
    """서비스 워커 — 루트 스코프(/)에서 동작하도록 루트 경로에서 직접 서빙한다."""
    resp = send_from_directory(
        app.static_folder, "sw.js", mimetype="application/javascript"
    )
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


# ---- JSON API (모바일 앱·향후 네이티브 앱의 기반) ----

def _serve_json(filename):
    if not (OUTPUT_DIR / filename).exists():
        return jsonify({"error": "아직 생성된 브리핑이 없습니다."}), 404
    return send_from_directory(OUTPUT_DIR, filename, mimetype="application/json")


def _serve_json_dated(prefix, date_str):
    try:
        dt.date.fromisoformat(date_str)  # 형식 검증 겸 경로 조작 방지
    except ValueError:
        abort(404)
    return _serve_json(f"{prefix}-{date_str}.json")


@app.route("/api/world")
def api_world():
    """최신 세계 뉴스 브리핑 (JSON)."""
    return _serve_json("index.json")


@app.route("/api/ai")
def api_ai():
    """최신 AI 브리핑 (JSON)."""
    return _serve_json("ai.json")


@app.route("/api/world/<date>")
def api_world_date(date):
    """날짜별 세계 뉴스 브리핑 (예: /api/world/2026-05-28)."""
    return _serve_json_dated("briefing", date)


@app.route("/api/ai/<date>")
def api_ai_date(date):
    """날짜별 AI 브리핑 (예: /api/ai/2026-05-28)."""
    return _serve_json_dated("ai", date)


@app.after_request
def _api_cors(resp):
    """API 응답에만 CORS 허용 — 향후 별도 출처의 네이티브 앱이 읽을 수 있도록."""
    if request.path.startswith("/api/"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


def run_job(send_mail=True):
    """세계 브리핑과 AI 브리핑을 생성하고, 설정돼 있으면 한 통의 이메일로 발송한다."""
    try:
        print(f"[{dt.datetime.now():%Y-%m-%d %H:%M}] 브리핑 생성 시작")
        _, world_path, world_data = world_briefing.build(OUTPUT_DIR)
        print(f"세계 브리핑 생성 완료: {world_path}")
        _, ai_path, ai_data = ai_briefing.build(OUTPUT_DIR)
        print(f"AI 브리핑 생성 완료: {ai_path}")

        if send_mail and email_configured():
            email_html = render_email(world_data, ai_data)
            subject = f"[아침 뉴스 브리핑] {dt.date.today().isoformat()}"
            send_email(email_html, subject)
            print("이메일 발송 완료 (세계 + AI 브리핑)")
    except Exception as exc:
        print(f"[오류] 브리핑 생성 실패: {exc}")


def scheduler_loop():
    """매일 RUN_HOUR:RUN_MINUTE 에 run_job 을 1회 실행한다."""
    last_run_date = None
    while True:
        now = dt.datetime.now()
        if (
            now.hour == RUN_HOUR
            and now.minute == RUN_MINUTE
            and last_run_date != now.date()
        ):
            last_run_date = now.date()
            run_job(send_mail=True)
        time.sleep(30)


def main():
    # 시작 시 브리핑이 없으면 즉시 한 번 생성한다(이메일은 발송하지 않음).
    if not (OUTPUT_DIR / "index.html").exists() or not (OUTPUT_DIR / "ai.html").exists():
        print("초기 브리핑을 생성합니다...")
        run_job(send_mail=False)

    scheduler = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler.start()

    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("SERVER_PORT", "8080"))
    print(f"웹 서버 시작: http://{host}:{port}  (/ 세계 · /ai AI · 매일 {RUN_HOUR:02d}:{RUN_MINUTE:02d} 자동 갱신)")
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
