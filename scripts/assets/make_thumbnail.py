#!/usr/bin/env python3
"""
달토끼 썸네일 합성 — 고정 키비주얼 1장에 4단 문안을 얹는다.

Usage:
    python3 scripts/assets/make_thumbnail.py \
        channels/dalttokki/assets/keyvisual/keyvisual_01.png out.png \
        --top "중간광고 없는" --big1 "전래동화" --big2 "3시간" --bottom "어린이 수면동화"
    # 캐릭터가 왼쪽에 있는 그림이면 --side right 로 문안을 오른쪽에 놓는다
    python3 scripts/assets/make_thumbnail.py in.png out.png --side right ...

벤치마크(호호샘) 썸네일 9편 전수 분석에서 뽑은 공식을 그대로 구현한다
(docs/benchmark/hohosam-2026-09.md §4):
  ① 좌우 2분할 — 한쪽 캐릭터, 반대쪽 문안. 편마다 좌우를 뒤집어 단조로움을 피한다
  ② 4단 문안 — 작은 윗줄 / 큰 줄 / 큰 줄(분량) / 작은 아랫줄
  ③ 노랑(핵심) + 흰색(보조), 굵은 외곽선 + 그림자
  ④ ★'장르 + N시간' 이 썸네일의 핵심 정보다. 최상위 2편이 모두 분량을 박았다

★폰트: 기본값은 Malgun Gothic Bold(윈도우 기본)다. 벤치의 두툼한 라운드체와는 결이 다르므로,
  상업 이용 무료 라운드체(배민 주아체 등)를 받으면 --font 로 바꾸고 이 기본값도 고칠 것.
"""
import argparse, pathlib, sys

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("error: Pillow 가 필요합니다 — pip install Pillow", file=sys.stderr)
    raise SystemExit(1)

W, H = 1920, 1080
DEFAULT_FONT = r"C:\Windows\Fonts\malgunbd.ttf"

YELLOW = (255, 233, 168)      # 핵심 문구
WHITE = (255, 255, 255)       # 보조 문구
OUTLINE = (26, 19, 51)        # 외곽선 — style.json 팔레트와 동일


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        print("warning: 폰트를 열 수 없습니다 (%s) — 기본 폰트로 진행합니다" % path, file=sys.stderr)
        return ImageFont.load_default()


def text_w(draw, s, font):
    box = draw.textbbox((0, 0), s, font=font)
    return box[2] - box[0]


def draw_line(draw, xy, s, font, fill, stroke):
    """굵은 외곽선 + 아래로 살짝 떨어지는 그림자. 밤 배경 위에서 글자가 뜨게 한다."""
    x, y = xy
    draw.text((x + 6, y + 8), s, font=font, fill=(0, 0, 0, 120),
              stroke_width=stroke, stroke_fill=(0, 0, 0, 120))
    draw.text((x, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=OUTLINE)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=pathlib.Path, help="키비주얼 png")
    ap.add_argument("out", type=pathlib.Path)
    ap.add_argument("--top", default="중간광고 없는")
    ap.add_argument("--big1", default="전래동화")
    ap.add_argument("--big2", default="3시간")
    ap.add_argument("--bottom", default="어린이 수면동화")
    ap.add_argument("--side", choices=["left", "right"], default="left",
                    help="문안을 놓을 쪽. 캐릭터 반대쪽에 둔다 (기본 left = 캐릭터가 오른쪽)")
    ap.add_argument("--font", default=DEFAULT_FONT)
    a = ap.parse_args()

    img = Image.open(a.src).convert("RGB")
    if img.size != (W, H):
        # 16:9 로 가운데를 잘라 맞춘다 — 생성 이미지가 1376x768 등으로 나올 수 있다
        scale = max(W / img.width, H / img.height)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        left = (img.width - W) // 2
        top = (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))

    # 문안 쪽에 어두운 그라데이션을 깔아 글자 대비를 확보한다(그림은 거의 가리지 않는다)
    veil = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(veil)
    span = int(W * 0.62)
    for i in range(span):
        alpha = int(120 * (1 - i / span) ** 1.4)
        x = i if a.side == "left" else W - 1 - i
        vd.line([(x, 0), (x, H)], fill=alpha)
    img = Image.composite(Image.new("RGB", (W, H), (10, 8, 26)), img,
                          veil.filter(ImageFilter.GaussianBlur(2)))

    draw = ImageDraw.Draw(img)
    f_small = load_font(a.font, 62)
    f_big = load_font(a.font, 158)
    f_bottom = load_font(a.font, 54)

    lines = [(a.top, f_small, WHITE, 6),
             (a.big1, f_big, YELLOW, 12),
             (a.big2, f_big, WHITE, 12),
             (a.bottom, f_bottom, WHITE, 5)]
    gaps = [18, 8, 26]

    total = sum(f.getbbox("가")[3] - f.getbbox("가")[1] + s * 2 for _t, f, _c, s in lines) \
        + sum(gaps) + 60
    y = (H - total) // 2
    margin = 110
    for i, (s, font, fill, stroke) in enumerate(lines):
        if not s:
            continue
        w = text_w(draw, s, font)
        x = margin if a.side == "left" else W - margin - w
        draw_line(draw, (x, y), s, font, fill, stroke)
        h = font.getbbox("가")[3] - font.getbbox("가")[1]
        y += h + stroke * 2 + (gaps[i] if i < len(gaps) else 0) + 24

    a.out.parent.mkdir(parents=True, exist_ok=True)
    img.save(a.out, quality=95)
    print("썸네일 저장 → %s (%dx%d)" % (a.out, W, H))
    return 0


if __name__ == "__main__":
    sys.exit(main())
