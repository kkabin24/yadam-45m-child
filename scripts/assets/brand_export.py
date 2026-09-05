#!/usr/bin/env python3
"""
채널 브랜드 이미지 규격 내보내기 — 생성된 원본을 유튜브가 요구하는 크기로 만든다.

Usage:
    python3 scripts/assets/brand_export.py channels/dalttokki/assets/brand

산출
    profile_800.png        800x800   — 채널 프로필(원형으로 잘려 보인다)
    banner_2560x1440.png   2560x1440 — 채널 배너. 가운데 가로 2560x423 이 모든 기기에서 보이는 안전영역

★배너: 생성 모델이 위아래에 어두운 띠를 그려 넣는 일이 잦다. 그 띠를 잘라내고, 잘린 자리를
  가장자리 색으로 이어 붙여 2560x1440 을 채운다. 위아래는 어차피 데스크톱에서 잘리는 영역이라
  단색에 가까워도 문제가 없고, 오히려 안전영역에 내용이 꽉 차게 된다.
"""
import argparse, pathlib, sys

try:
    from PIL import Image, ImageFilter
except ImportError:
    print("error: Pillow 가 필요합니다", file=sys.stderr)
    raise SystemExit(1)


def trim_bands(img, tol=14):
    """위아래의 거의 단색인 띠를 찾아 잘라낸다. 못 찾으면 원본 그대로."""
    px = img.convert("RGB")
    w, h = px.size

    def row_flat(y):
        row = [px.getpixel((x, y)) for x in range(0, w, max(1, w // 48))]
        r = [c[0] for c in row]; g = [c[1] for c in row]; b = [c[2] for c in row]
        return (max(r) - min(r) < tol) and (max(g) - min(g) < tol) and (max(b) - min(b) < tol)

    top = 0
    while top < h // 3 and row_flat(top):
        top += 1
    bot = h - 1
    while bot > h * 2 // 3 and row_flat(bot):
        bot -= 1
    if top == 0 and bot == h - 1:
        return img
    return img.crop((0, top, w, bot + 1))


def edge_color(img, y):
    px = img.convert("RGB")
    w = px.size[0]
    xs = range(0, w, max(1, w // 64))
    cols = [px.getpixel((x, y)) for x in xs]
    n = len(cols)
    return tuple(sum(c[i] for c in cols) // n for i in range(3))


def export_banner(src, out, w=2560, h=1440):
    img = trim_bands(Image.open(src).convert("RGB"))
    band = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
    if band.height >= h:
        top = (band.height - h) // 2
        band.crop((0, top, w, top + h)).save(out)
        print("배너 저장 → %s (%dx%d)" % (out, w, h))
        return

    canvas = Image.new("RGB", (w, h))
    top_c = edge_color(band, 0)
    bot_c = edge_color(band, band.height - 1)
    y0 = (h - band.height) // 2
    for y in range(h):                       # 잘린 위아래를 가장자리 색으로 채운다(위로 갈수록 살짝 어둡게)
        if y < y0:
            k = 1 - (y0 - y) / max(1, y0) * 0.35
            canvas.paste(tuple(int(c * k) for c in top_c), (0, y, w, y + 1))
        elif y >= y0 + band.height:
            k = 1 - (y - y0 - band.height) / max(1, h - y0 - band.height) * 0.35
            canvas.paste(tuple(int(c * k) for c in bot_c), (0, y, w, y + 1))
    canvas.paste(band, (0, y0))

    # 이음매를 부드럽게 — 접합선 위아래 40px 만 흐린 버전으로 덮는다
    blur = canvas.filter(ImageFilter.GaussianBlur(9))
    mask = Image.new("L", (w, h), 0)
    for y in range(h):
        d = min(abs(y - y0), abs(y - (y0 + band.height)))
        if d < 40:
            mask.paste(int(210 * (1 - d / 40)), (0, y, w, y + 1))
    canvas = Image.composite(blur, canvas, mask)
    canvas.save(out)
    print("배너 저장 → %s (%dx%d) · 안전영역 가운데 2560x423" % (out, w, h))


def export_profile(src, out, size=800):
    img = Image.open(src).convert("RGB")
    s = min(img.size)
    left = (img.width - s) // 2
    top = (img.height - s) // 2
    img.crop((left, top, left + s, top + s)).resize((size, size), Image.LANCZOS).save(out)
    print("프로필 저장 → %s (%dx%d)" % (out, size, size))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brand_dir", type=pathlib.Path)
    a = ap.parse_args()
    d = a.brand_dir
    if (d / "profile.png").exists():
        export_profile(d / "profile.png", d / "profile_800.png")
    if (d / "banner.png").exists():
        export_banner(d / "banner.png", d / "banner_2560x1440.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
