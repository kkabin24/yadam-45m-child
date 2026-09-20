#!/usr/bin/env python3
"""달토끼 CHAPTERS — Vrew 낭독 SRT에서 이야기별 시작 시각을 뽑아 {P}/_video/chapters.json 을 만든다.

입력
  {P}/lineup.json            영상 순서 (file, title)
  {C}/stories/{file}         각 이야기 대본 (export_vrew_stories.render 와 같은 규칙으로 발화 텍스트 복원)
  {P}/_video/subtitle.srt    ingest_vrew.py 가 파트 병합·프레임 스냅한 자막

방법
  대본 전체를 이야기 순서로 이어 붙인 비공백·비구두점 글자열에서 각 이야기의 시작 오프셋을 재고,
  자막 큐를 같은 방식으로 이어 붙여 그 오프셋이 떨어지는 큐의 start 를 이야기 시작 시각으로 삼는다.
  (Vrew 는 자막에서 마침표를 지우므로 구두점을 뺀 글자 수로 맞춘다 — ingest_vrew.norm 과 동일)

출력
  {P}/_video/chapters.json   [{"start_sec": 0.0, "title": "해와 달이 된 오누이", "file": …, "chars": …}, …]
  화면에 유튜브 설명란용 목차(0:00 제목)도 함께 찍는다. --intro-sec 를 주면 그만큼 밀어서 찍는다.

사용
  python3 scripts/tts/sleep_chapters.py channels/dalttokki/projects/01편 [--intro-sec 0]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from export_vrew_stories import parse_story, render  # noqa: E402

SRT_TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


def norm(s: str) -> str:
    return re.sub(r"\s+", "", re.sub(r"[^\w가-힣]", "", s))


def parse_srt(text: str) -> list[dict]:
    cues, cur = [], None
    for ln in text.splitlines():
        ln = ln.strip()
        m = SRT_TIME.match(ln)
        if m:
            h, mi, s, ms = (int(x) for x in m.groups()[:4])
            cur = {"start": h * 3600 + mi * 60 + s + ms / 1000, "text": ""}
            cues.append(cur)
        elif cur is not None and ln and not ln.isdigit():
            cur["text"] += ln
    return cues


def hms(sec: float) -> str:
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=pathlib.Path)
    ap.add_argument("--intro-sec", type=float, default=0.0, help="설명란 목차 출력 때 앞에 붙는 인트로 길이(초)")
    a = ap.parse_args()

    P = a.project
    C = P.parent.parent
    lineup = json.loads((P / "lineup.json").read_text(encoding="utf-8"))
    srt_path = P / "_video" / "subtitle.srt"
    cues = parse_srt(srt_path.read_text(encoding="utf-8-sig"))
    if not cues:
        sys.exit(f"자막 큐가 없다: {srt_path}")

    # 큐 누적 글자 오프셋 → 큐 start
    cue_off = []  # (누적 시작 오프셋, start_sec)
    acc = 0
    for c in cues:
        cue_off.append((acc, c["start"]))
        acc += len(norm(c["text"]))
    total_cue_chars = acc

    chapters, off = [], 0
    for row in lineup:
        story = parse_story(C / "stories" / row["file"])
        n = len(norm(render(story, tagged=False)))
        # off 가 떨어지는 큐 — 큐 시작 오프셋이 off 이하인 마지막 큐
        idx = max(i for i, (o, _) in enumerate(cue_off) if o <= off)
        o, start = cue_off[idx]
        if o != off:
            print(f"  ! {row['title']}: 이야기 경계가 큐 중간에 떨어짐 (큐 #{idx + 1}, {off - o}자 어긋남) — 큐 시작으로 잡음", file=sys.stderr)
        chapters.append({"start_sec": round(start, 3), "title": row["title"], "file": row["file"], "chars": n})
        off += n

    if abs(off - total_cue_chars) > max(5, off * 0.01):
        print(f"⚠️ 대본 {off}자 vs 자막 {total_cue_chars}자 — Vrew에서 문장이 빠지거나 더해졌는지 확인", file=sys.stderr)

    out = P / "_video" / "chapters.json"
    out.write_text(json.dumps(chapters, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ {out} ({len(chapters)}챕터)\n")
    print("설명란 목차" + (f" (인트로 {a.intro_sec:.0f}초 포함)" if a.intro_sec else "") + ":")
    if a.intro_sec:
        print(f"  0:00 인사말")
    for ch in chapters:
        print(f"  {hms(ch['start_sec'] + a.intro_sec)} {ch['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
