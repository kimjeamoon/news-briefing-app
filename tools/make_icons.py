#!/usr/bin/env python3
"""PWA 앱 아이콘 PNG 생성기 (빌드타임 전용).

static/icon.svg 와 같은 디자인을 Pillow 도형만으로 그려
static/icons/ 아래 PNG 들을 만든다. 한글 폰트가 필요 없도록 텍스트 대신 도형을 쓴다.

사용:
    pip install Pillow
    python tools/make_icons.py

런타임(requirements.txt)에는 Pillow 를 넣지 않는다 — 생성된 PNG 만 커밋하면 된다.
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parent.parent / "static" / "icons"

BG = (26, 26, 26)           # #1a1a1a
ACCENT = (192, 57, 43)      # #c0392b
HEADLINE = (244, 245, 247)  # #f4f5f7
BODY = (154, 160, 166)      # #9aa0a6
BODY_DIM = (107, 114, 128)  # #6b7280

SS = 4  # 안티에일리어싱용 슈퍼샘플링 배율


def draw_icon(size, maskable=False):
    """size×size 아이콘 이미지를 반환한다 (512 좌표계 기준으로 그린 뒤 축소)."""
    canvas = size * SS
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if maskable:
        # 플랫폼이 모서리를 마스킹하므로 배경을 꽉 채우고 콘텐츠는 안전영역 안으로 축소.
        d.rectangle([0, 0, canvas, canvas], fill=BG)
        content_scale = 0.72
    else:
        d.rounded_rectangle(
            [0, 0, canvas - 1, canvas - 1], radius=int(canvas * 0.21875), fill=BG
        )
        content_scale = 1.0

    s = (canvas / 512) * content_scale

    def X(x):
        return canvas / 2 + (x - 256) * s

    def Y(y):
        return canvas / 2 + (y - 256) * s

    def L(v):
        return v * s

    def bar(x, y, w, h, fill):
        d.rounded_rectangle([X(x), Y(y), X(x + w), Y(y + h)], radius=L(h / 2), fill=fill)

    # 헤드라인: 빨강 액센트 점 + 제목 바
    r = L(15)
    d.ellipse([X(148) - r, Y(190) - r, X(148) + r, Y(190) + r], fill=ACCENT)
    bar(182, 176, 190, 26, HEADLINE)
    # 본문 라인
    bar(128, 240, 256, 18, BODY)
    bar(128, 282, 224, 18, BODY)
    bar(128, 324, 256, 18, BODY)
    bar(128, 366, 168, 18, BODY_DIM)

    return img.resize((size, size), Image.LANCZOS)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-512.png", 512, True),
        ("apple-touch-icon.png", 180, True),
    ]
    for name, size, maskable in targets:
        img = draw_icon(size, maskable=maskable)
        if name == "apple-touch-icon.png":
            # 애플 터치 아이콘은 투명 영역 없이 불투명해야 한다.
            img = img.convert("RGB")
        img.save(OUT_DIR / name)
        print(f"생성: {OUT_DIR / name}  ({size}×{size}{' · maskable' if maskable else ''})")


if __name__ == "__main__":
    main()
