#!/usr/bin/env python3
"""달토끼 배경 루프 — 잠든 몽이 그림 1장을 pjn(i2v)로 "새근새근 숨 쉬는" 클립으로 만들고,
앞뒤로 이어 붙여(핑퐁) 끝없이 반복해도 튀지 않는 루프 mp4 로 만든다.

★영상은 pjn(로컬 5090, 무료)으로만 만든다 — CLAUDE.md 「절대 금지」. gemini 영상 API 를 쓰지 않는다.

절차
  1. pjn i2v: 첫 프레임 = 입력 그림 그대로, 카메라 고정, 숨 쉬는 동작만. H3 가 붙이는 오디오는 버린다.
  2. 렌더 규격(1920x1080/30fps)으로 변환, 무음.
  3. 핑퐁 루프: 정방향 + 역방향 concat. 숨은 들숨/날숨이 대칭이라 역재생이 자연스럽고,
     첫 프레임과 끝 프레임이 같아져 반복 지점이 보이지 않는다.

사용
  python3 scripts/render/sleep_loop.py <start_frame.png> <out_loop.mp4> [--duration 10] [--quality 1.0]
      [--config channels/dalttokki/config/settings.json] [--raw-only]
  --raw-only: pjn 원본(<out>_raw.mp4)만 받고 루프 가공은 생략
"""
import argparse
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "image"))
from veo_hook import veo_pjn, conform_to_render, find_env_key  # noqa: E402

# ★프롬프트에 한글을 넣지 않는다 — H3 는 한글을 소리 내어 읽는다(veo_hook 실측). 대사도 없다.
PROMPT = """Soft pastel storybook illustration, 2D hand-painted picture-book style — keep the exact look, \
colours and composition of the first frame; do not redraw or restyle anything.
The scene comes gently alive while the baby rabbit stays FAST ASLEEP.
[0s-{d}s] The rabbit breathes slowly and peacefully: its round tummy and chest rise and fall in a soft, \
slow rhythm, about one breath every four seconds. The long floppy ears sway a tiny bit. \
Its eyes stay closed the whole time, mouth closed, no talking, no waking up, no head turning. \
Stars twinkle faintly in the night sky. The warm lamplight from the paper door flickers very softly.
Camera is completely static, locked off — no pan, no zoom, no push-in, no cuts.
Everything is extremely subtle, slow and calm; this is a bedtime video for a small child.
Audio: silence or the faintest ambient night sound only. No speech, no music.
Strictly no subtitles, no captions, no on-screen text of any kind."""


def run(cmd: list[str], what: str) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"✗ ffmpeg {what} 실패: {r.stderr[-600:]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frame", type=pathlib.Path)
    ap.add_argument("out", type=pathlib.Path)
    ap.add_argument("--duration", type=int, default=10, help="pjn 클립 길이(초, 5~15). 핑퐁 후 2배")
    ap.add_argument("--quality", type=float, default=None, help="pjn quality 0.4~1.0 (기본 settings)")
    ap.add_argument("--config", type=pathlib.Path, default=pathlib.Path("channels/dalttokki/config/settings.json"))
    ap.add_argument("--raw-only", action="store_true")
    ap.add_argument("--reuse-raw", action="store_true", help="이미 받은 _raw.mp4 가 있으면 다시 생성하지 않음")
    a = ap.parse_args()

    settings = json.loads(a.config.read_text(encoding="utf-8")) if a.config.exists() else {}
    render = settings.get("render", {})
    W, H, FPS = int(render.get("width", 1920)), int(render.get("height", 1080)), int(render.get("fps", 30))
    quality = a.quality or float((settings.get("image", {}).get("veo", {}).get("pjn") or {}).get("quality") or 1.0)

    raw = a.out.with_name(a.out.stem + "_raw.mp4")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if not (a.reuse_raw and raw.exists()):
        key = find_env_key(a.frame.resolve().parent, "PJN_API_KEY")
        if not key:
            sys.exit("✗ PJN_API_KEY 없음 (.env)")
        prompt = PROMPT.format(d=a.duration)
        (a.out.with_suffix(".prompt.txt")).write_text(prompt, encoding="utf-8")
        print(f"pjn i2v 생성 시작 (무료, minimax-h3, {a.duration}s, q{quality}) ← {a.frame.name}")
        if veo_pjn(prompt, a.frame, raw, key, "16:9", quality, a.duration) != 0:
            sys.exit("✗ pjn 생성 실패")
    if a.raw_only:
        print(f"✓ {raw}")
        return 0

    # 렌더 규격 + 무음
    conf = a.out.with_name(a.out.stem + "_conform.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-an",
         "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", str(conf)], "규격 변환")

    # 핑퐁: 정방향 + 역방향(첫/끝 프레임 중복 1장씩 잘라 이음새 정지 방지)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(conf),
         "-filter_complex",
         f"[0:v]trim=start_frame=1,setpts=PTS-STARTPTS[f];"
         f"[0:v]reverse,trim=start_frame=1,setpts=PTS-STARTPTS[r];"
         f"[f][r]concat=n=2:v=1:a=0[v]",
         "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
         "-movflags", "+faststart", str(a.out)], "핑퐁 루프")
    conf.unlink(missing_ok=True)

    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(a.out)], capture_output=True, text=True).stdout.strip()
    print(f"✓ {a.out}  루프 {float(dur):.1f}초 ({W}x{H}/{FPS}fps, 무음)  원본: {raw.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
