#!/usr/bin/env python3
"""달토끼 stories/*.md → Vrew 붙여넣기용 txt.

대본은 `화자: [지시] 대사` 한 줄 형식이다. 이 스크립트는
  - 머리말(`---` 위)을 버리고
  - `[느리게]` 같은 낭독 지시 태그를 지우고
  - 화자 접두를 지운다(plain) — 또는 나레이션이 아닌 대사에만 `[베이스보이스]` 태그를 붙인다(tagged)
  - 문단(빈 줄)은 그대로 둔다 — Vrew는 줄마다 클립을 만들고 빈 줄은 무시한다.

산출 (기본 {channel}/vrew/):
  plain/NNN_제목.txt            이야기별. 나레이터 보이스 하나로 통째 낭독
  plain/bundle_partNN.txt       001→020 순서로 한도(공백 포함 9,950자) 안에서 이야기 경계로 묶음
  tagged/…                      같은 구성. 대사 앞에 `[할아버지]` 식 베이스보이스 태그 —
                                Vrew 찾기(Ctrl+F)로 태그별 클립을 한꺼번에 골라 목소리를 바꾼 뒤
                                찾기/바꾸기로 태그를 지운다(클립 텍스트를 고치면 그 클립 목소리로 재합성)
  manifest.md                   파일별 글자 수·수록 이야기

사용:
  python3 scripts/tts/export_vrew_stories.py channels/dalttokki [--limit 9950] [--lineup projects/01편/lineup.json]
  --lineup 을 주면 bundle 을 그 편성 순서로 묶고 lineup 에 없는 이야기는 뒤에 번호순으로 붙인다.

  python3 scripts/tts/export_vrew_stories.py channels/dalttokki --project channels/dalttokki/projects/01편
  → {P}/lineup.json 의 이야기만, 그 순서로 {P}/vrew/ 에 쓴다 (story-pd 옴니버스 규격):
      vrew_script_part01a.txt, part01b …          plain  — 편 번호는 폴더명(01편)에서
      vrew_script_tagged_part01a.txt …            tagged
      manifest.md
    낭독본은 narration_01a.mp3 + .srt 식으로 같은 접미사를 붙여 {P}/vrew/ 에 둔다.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

DIRECTION_RE = re.compile(r"\[[^\]]*\]\s*")
LINE_RE = re.compile(r"^([^:\s]+):\s*(.*)$")
NARRATOR = "나레이션"


def parse_story(path: pathlib.Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    head, _, body = raw.partition("\n---\n")
    if not body:
        sys.exit(f"머리말 구분선(---)이 없다: {path}")

    m = re.match(r"#\s*(\d+)\.\s*(.+)", head.strip().splitlines()[0])
    number, title = (m.group(1), m.group(2).strip()) if m else (path.stem[:3], path.stem[4:])

    casting: dict[str, str] = {}
    cm = re.search(r"^- 캐스팅:\s*(.+)$", head, re.M)
    if cm:
        for pair in cm.group(1).split(","):
            k, _, v = pair.strip().partition("=")
            if k and v:
                casting[k.strip()] = v.strip()

    # 문단 = 빈 줄로 구분된 줄 묶음. 각 줄은 (화자, 대사)
    paras: list[list[tuple[str, str]]] = []
    for block in re.split(r"\n\s*\n", body.strip()):
        lines = []
        for ln in block.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            lm = LINE_RE.match(ln)
            if not lm:
                print(f"  ! 화자 없는 줄 (그대로 둠): {path.name}: {ln[:40]}", file=sys.stderr)
                lines.append((NARRATOR, ln))
                continue
            speaker, text = lm.group(1), DIRECTION_RE.sub("", lm.group(2)).strip()
            if text:
                lines.append((speaker, text))
        if lines:
            paras.append(lines)

    return {"number": number, "title": title, "stem": path.stem, "casting": casting, "paras": paras}


def render(story: dict, tagged: bool) -> str:
    out = []
    for para in story["paras"]:
        rows = []
        for speaker, text in para:
            if tagged and speaker != NARRATOR:
                voice = story["casting"].get(speaker, speaker)
                rows.append(f"[{voice}] {text}")
            else:
                rows.append(text)
        out.append("\n".join(rows))
    return "\n\n".join(out)


def bundle(items: list[tuple[str, str]], limit: int) -> list[list[tuple[str, str]]]:
    """(stem, text) 를 순서대로 한도 안에서 묶는다. 이야기 하나는 쪼개지 않는다."""
    parts, buf, size = [], [], 0
    for stem, text in items:
        if len(text) > limit:
            sys.exit(f"이야기 하나가 한도를 넘는다 ({len(text):,}자): {stem}")
        extra = len(text) + (2 if buf else 0)
        if buf and size + extra > limit:
            parts.append(buf)
            buf, size = [], 0
            extra = len(text)
        buf.append((stem, text))
        size += extra
    if buf:
        parts.append(buf)
    return parts


def export_project(channel: pathlib.Path, project: pathlib.Path, limit: int) -> int:
    lineup_path = project / "lineup.json"
    if not lineup_path.exists():
        sys.exit(f"lineup.json 이 없다: {lineup_path}  (먼저 build_lineup.py)")
    m = re.search(r"(\d+)", project.name)
    ep = int(m.group(1)) if m else 1

    lineup = json.loads(lineup_path.read_text(encoding="utf-8"))
    stories = [parse_story(channel / "stories" / x["file"]) for x in lineup]

    vdir = project / "vrew"
    vdir.mkdir(parents=True, exist_ok=True)
    for old in vdir.glob("vrew_script*part*.txt"):
        old.unlink()

    manifest = [f"# {project.name} Vrew 대본", "",
                f"- 편성: `{lineup_path}` ({len(stories)}편, 순서 = 영상 순서)",
                f"- 한도: {limit:,}자 (공백 포함)", ""]
    for variant, tagged, prefix in (("plain", False, "vrew_script_part"), ("tagged", True, "vrew_script_tagged_part")):
        parts = bundle([(s["stem"], render(s, tagged)) for s in stories], limit)
        manifest += [f"## {variant}", "", "| 파일 | 글자 수 | 수록 |", "|---|---:|---|"]
        for i, part in enumerate(parts):
            sfx = "" if len(parts) == 1 else chr(ord("a") + i)
            name = f"{prefix}{ep:02d}{sfx}.txt"
            joined = "\n\n".join(t for _, t in part)
            (vdir / name).write_text(joined + "\n", encoding="utf-8")
            manifest.append(f"| {name} | {len(joined):,} | {' → '.join(st for st, _ in part)} |")
        manifest.append("")
        print(f"✓ {vdir}  {variant}: 파트 {len(parts)}개")
    (vdir / "manifest.md").write_text("\n".join(manifest), encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("channel", type=pathlib.Path, help="channels/dalttokki")
    ap.add_argument("--limit", type=int, default=9950, help="Vrew 붙여넣기 한도(공백 포함). 기본 9950")
    ap.add_argument("--lineup", type=pathlib.Path, help="편성 lineup.json — bundle 순서로 쓴다")
    ap.add_argument("--out", type=pathlib.Path, help="출력 폴더. 기본 {channel}/vrew")
    ap.add_argument("--project", type=pathlib.Path, help="편 폴더 {P} — lineup.json 순서로 {P}/vrew/ 에 파트 파일 생성")
    args = ap.parse_args()
    if args.project:
        return export_project(args.channel, args.project, args.limit)

    stories_dir = args.channel / "stories"
    files = sorted(p for p in stories_dir.glob("[0-9][0-9][0-9]_*.md"))
    if not files:
        sys.exit(f"이야기 파일이 없다: {stories_dir}")
    stories = [parse_story(p) for p in files]

    order = [s["stem"] for s in stories]
    if args.lineup:
        lineup = json.loads(args.lineup.read_text(encoding="utf-8"))
        first = [pathlib.Path(x["file"]).stem for x in lineup]
        order = first + [st for st in order if st not in first]
    by_stem = {s["stem"]: s for s in stories}

    out_dir = args.out or (args.channel / "vrew")
    manifest = ["# Vrew 대본 manifest", "",
                f"- 원본: `{stories_dir}` ({len(stories)}편)",
                f"- 한도: {args.limit:,}자 (공백 포함) / 글자 수는 모두 공백 포함",
                f"- bundle 순서: {'lineup ' + str(args.lineup) if args.lineup else '번호순'}", ""]

    for variant, tagged in (("plain", False), ("tagged", True)):
        vdir = out_dir / variant
        vdir.mkdir(parents=True, exist_ok=True)
        for old in vdir.glob("*.txt"):
            old.unlink()

        manifest += [f"## {variant}/", "", "| 파일 | 글자 수 |", "|---|---:|"]
        texts = {}
        for s in stories:
            text = render(s, tagged)
            texts[s["stem"]] = text
            (vdir / f"{s['stem']}.txt").write_text(text + "\n", encoding="utf-8")
            manifest.append(f"| {s['stem']}.txt | {len(text):,} |")

        parts = bundle([(st, texts[st]) for st in order], args.limit)
        manifest += ["", "| bundle | 글자 수 | 수록 |", "|---|---:|---|"]
        for i, part in enumerate(parts, 1):
            joined = "\n\n".join(t for _, t in part)
            name = f"bundle_part{i:02d}.txt"
            (vdir / name).write_text(joined + "\n", encoding="utf-8")
            manifest.append(f"| {name} | {len(joined):,} | {' → '.join(st[:3] for st, _ in part)} |")
        manifest.append("")
        print(f"✓ {vdir}  이야기 {len(stories)}편 + bundle {len(parts)}개")

    (out_dir / "manifest.md").write_text("\n".join(manifest), encoding="utf-8")
    print(f"✓ {out_dir / 'manifest.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
