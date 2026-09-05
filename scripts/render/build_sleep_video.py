#!/usr/bin/env python3
"""
달토끼 수면동화 영상 조립 — 고정 키비주얼 1장 + 챕터 카드 + 낭독 + 검은 화면 백색소음.

Usage:
    python3 scripts/render/build_sleep_video.py \
        --keyvisual channels/dalttokki/assets/keyvisual/keyvisual_01.png \
        --audio     channels/dalttokki/projects/01편/_video/audio.mp3 \
        --chapters  channels/dalttokki/projects/01편/_video/chapters.json \
        --noise     "channels/dalttokki/assets/intro,outro/sleep_noise_2h_quiet.mp3" \
        --out       channels/dalttokki/projects/01편/output/01편.mp4
    # 조립 계획만 보고 렌더하지 않는다
    ... --dry-run

★이 채널만 ffmpeg 직접 렌더다. 야담(story-pd)은 CapCut export 전용이지만(CLAUDE.md),
  이 채널의 영상은 정지 이미지 1장 + 3초 카드 + 오디오뿐이라 사람이 편집할 것이 없다.
  CapCut 게이트를 두면 사람이 3시간짜리 타임라인을 여는 일만 남는다.

구조
    [카드 3초][고정 이미지 …이야기1…][카드 3초][고정 이미지 …이야기2…] … + 낭독 오디오
    [검은 화면 …백색소음 전체 길이…]                                    + 백색소음
    두 덩이를 이어 붙여 최종 mp4.

★백색소음 구간은 검은 화면이다 — 화면이 밝으면 옆에서 자는 아이가 깬다.
★챕터 카드는 배경을 어둡게 깔고 제목만 얹는다. 장면 전환처럼 번쩍이지 않게 페이드는 넣지 않는다.
"""
import argparse, json, pathlib, shutil, subprocess, sys, tempfile

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("error: Pillow 가 필요합니다", file=sys.stderr)
    raise SystemExit(1)

W, H, FPS = 1920, 1080, 30
CARD_SEC = 3.0
DEFAULT_FONT = r"C:\Windows\Fonts\malgunbd.ttf"


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(" ".join(str(c) for c in cmd), file=sys.stderr)
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit("ffmpeg 실패")
    return r


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)])
    return float(r.stdout.strip())


def fit(img):
    if img.size == (W, H):
        return img
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


def make_card(base, title, out, font_path):
    """고정 배경을 어둡게 깔고 이야기 제목만 얹은 3초짜리 카드."""
    img = fit(Image.open(base).convert("RGB"))
    img = Image.blend(img, Image.new("RGB", (W, H), (12, 10, 30)), 0.62)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 96)
    except OSError:
        font = ImageFont.load_default()
    box = d.textbbox((0, 0), title, font=font)
    d.text(((W - (box[2] - box[0])) // 2, (H - (box[3] - box[1])) // 2 - 30),
           title, font=font, fill=(255, 233, 168), stroke_width=8, stroke_fill=(26, 19, 51))
    img.save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keyvisual", type=pathlib.Path, required=True)
    ap.add_argument("--audio", type=pathlib.Path, required=True, help="낭독 mp3")
    ap.add_argument("--chapters", type=pathlib.Path, help="chapters.json — 없으면 카드 없이 통짜")
    ap.add_argument("--noise", type=pathlib.Path, help="백색소음 mp3 — 없으면 붙이지 않는다")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--font", default=DEFAULT_FONT)
    ap.add_argument("--card-sec", type=float, default=CARD_SEC)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    for p in (a.keyvisual, a.audio):
        if not p.exists():
            raise SystemExit("error: 없는 파일 — %s" % p)

    narr = duration(a.audio)
    chapters = json.loads(a.chapters.read_text(encoding="utf-8")) if a.chapters else []
    noise = duration(a.noise) if (a.noise and a.noise.exists()) else 0.0

    # 각 챕터의 [카드 3초] + [고정 이미지 나머지] 로 구간을 만든다
    segs = []
    for i, ch in enumerate(chapters):
        start = float(ch["start_sec"])
        end = float(chapters[i + 1]["start_sec"]) if i + 1 < len(chapters) else narr
        span = end - start
        if span <= a.card_sec + 1:                 # 너무 짧은 챕터는 카드를 생략한다
            segs.append(("still", span, None))
            continue
        segs.append(("card", a.card_sec, ch["title"]))
        segs.append(("still", span - a.card_sec, None))
    if not segs:
        segs = [("still", narr, None)]

    total = narr + noise
    print("낭독 %.1f분 / 백색소음 %.1f분 / 합계 %.2f시간" % (narr / 60, noise / 60, total / 3600))
    print("챕터 %d개 · 구간 %d개 (카드 %.0f초)" % (len(chapters), len(segs), a.card_sec))
    if a.dry_run:
        for kind, sec, title in segs[:6]:
            print("  %-5s %6.1fs %s" % (kind, sec, title or ""))
        print("  … --dry-run — 렌더하지 않았습니다.")
        return 0

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="sleepvid_"))
    try:
        still = tmp / "still.png"
        fit(Image.open(a.keyvisual).convert("RGB")).save(still)
        black = tmp / "black.png"
        Image.new("RGB", (W, H), (0, 0, 0)).save(black)

        lines, ci = [], 0
        for kind, sec, title in segs:
            if kind == "card":
                ci += 1
                card = tmp / ("card_%03d.png" % ci)
                make_card(a.keyvisual, title, card, a.font)
                src = card
            else:
                src = still
            lines.append("file '%s'\nduration %.3f\n" % (src.resolve().as_posix(), sec))
        lines.append("file '%s'\n" % (still.resolve().as_posix()))   # concat 데먹서는 마지막 항목을 한 번 더 요구한다
        (tmp / "vlist.txt").write_text("".join(lines), encoding="utf-8")

        part1 = tmp / "part1.mp4"
        print("① 낭독 구간 렌더 중…")
        run(["ffmpeg", "-y", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(tmp / "vlist.txt"),
             "-i", str(a.audio),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-shortest", str(part1)])

        parts = [part1]
        if noise:
            part2 = tmp / "part2.mp4"
            print("② 백색소음 구간 렌더 중… (%.0f분)" % (noise / 60))
            run(["ffmpeg", "-y", "-loglevel", "error",
                 "-loop", "1", "-i", str(black), "-i", str(a.noise),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p",
                 "-r", str(FPS), "-tune", "stillimage",
                 "-c:a", "aac", "-b:a", "128k", "-shortest", str(part2)])
            parts.append(part2)

        a.out.parent.mkdir(parents=True, exist_ok=True)
        if len(parts) == 1:
            shutil.copy(parts[0], a.out)
        else:
            (tmp / "plist.txt").write_text(
                "".join("file '%s'\n" % p.resolve().as_posix() for p in parts), encoding="utf-8")
            print("③ 두 구간 이어 붙이는 중…")
            run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                 "-i", str(tmp / "plist.txt"), "-c", "copy", str(a.out)])

        print("\n완성 → %s  (%.2f시간)" % (a.out, duration(a.out) / 3600))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
