#!/usr/bin/env python3
"""달토끼 썸네일 — 잠든 캐릭터 그림(왼쪽) + 오른쪽 큰 글씨.

레이아웃(벤치마크 실측): 캐릭터가 왼쪽 1/3에 있는 16:9 그림 위에
  줄1  작은 흰 글씨 + 초승달 아이콘      "마음이 편안해지는"
  줄2  아주 큰 노란 글씨                  "어린이"
  줄3  아주 큰 흰 글씨                    "수면동화"
을 오른쪽 절반에 가운데 정렬로 얹는다. 글씨는 두꺼운 어두운 외곽선 + 부드러운 그림자.

사용:
  python3 scripts/render/sleep_thumbnail.py <배경.png> <out.png> \
      [--top "마음이 편안해지는"] [--big1 "어린이"] [--big2 "수면동화"] \
      [--font channels/dalttokki/assets/fonts/BMJUA.ttf] [--center 0.70]
  --center: 텍스트 블록 중심의 가로 위치(0~1). 캐릭터가 왼쪽 1/3에 있으면 0.68~0.72.
"""
import argparse
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
DEFAULT_FONT = pathlib.Path(__file__).resolve().parents[2] / "channels/dalttokki/assets/fonts/BMJUA.ttf"
YELLOW = (250, 200, 60)
WHITE = (255, 255, 255)
OUTLINE = (30, 22, 60)


def fit_cover(img: Image.Image) -> Image.Image:
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


def text_layer(text: str, font: ImageFont.FreeTypeFont, fill, outline_w: int) -> Image.Image:
    """글자 + 외곽선 + 그림자를 투명 레이어로 그린다."""
    l, t, r, b = font.getbbox(text)
    pad = outline_w * 3 + 12
    layer = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    # 그림자
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((pad - l + 6, pad - t + 8), text, font=font, fill=(0, 0, 0, 170),
                            stroke_width=outline_w, stroke_fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    layer.alpha_composite(sh)
    ImageDraw.Draw(layer).text((pad - l, pad - t), text, font=font, fill=fill,
                               stroke_width=outline_w, stroke_fill=OUTLINE)
    return layer


def crescent(size: int) -> Image.Image:
    """초승달 아이콘 — 원에서 살짝 옮긴 원을 빼서 만든다."""
    s = size * 4  # 수퍼샘플
    m = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((0, 0, s - 1, s - 1), fill=255)
    off = int(s * 0.32)
    d.ellipse((off, -int(s * 0.12), off + s, s - int(s * 0.12) - 1), fill=0)
    m = m.resize((size, size), Image.LANCZOS)
    icon = Image.new("RGBA", (size, size), YELLOW + (0,))
    icon.putalpha(m)
    return icon


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("background", type=pathlib.Path)
    ap.add_argument("out", type=pathlib.Path)
    ap.add_argument("--top", default="마음이 편안해지는")
    ap.add_argument("--big1", default="어린이")
    ap.add_argument("--big2", default="수면동화")
    ap.add_argument("--font", type=pathlib.Path, default=DEFAULT_FONT)
    ap.add_argument("--center", type=float, default=0.70, help="텍스트 블록 가로 중심 (0~1)")
    ap.add_argument("--big-size", type=int, default=190)
    ap.add_argument("--top-size", type=int, default=64)
    a = ap.parse_args()

    bg = fit_cover(Image.open(a.background).convert("RGB")).convert("RGBA")
    # 경로에 ★ 같은 비ASCII가 있으면 Pillow가 못 열므로 바이트로 넘긴다
    import io
    font_bytes = a.font.read_bytes()
    f_big = ImageFont.truetype(io.BytesIO(font_bytes), a.big_size)
    f_top = ImageFont.truetype(io.BytesIO(font_bytes), a.top_size)

    layers = [
        ("top", text_layer(a.top, f_top, WHITE, 6)),
        ("big1", text_layer(a.big1, f_big, YELLOW, 12)),
        ("big2", text_layer(a.big2, f_big, WHITE, 12)),
    ]
    gaps = {"top": 18, "big1": -6}
    total_h = sum(l.height for _, l in layers) + sum(gaps.values())
    y = (H - total_h) // 2 + 10
    cx = int(W * a.center)
    for name, layer in layers:
        x = cx - layer.width // 2
        if name == "top":
            icon = crescent(a.top_size)
            shift = (icon.width + 16) // 2
            x += shift
            bg.alpha_composite(icon, (x - icon.width - 16, y + (layer.height - icon.height) // 2 + 4))
        bg.alpha_composite(layer, (x, y))
        y += layer.height + gaps.get(name, 0)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(a.out, quality=95)
    print(f"✓ {a.out}  ({W}x{H})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
