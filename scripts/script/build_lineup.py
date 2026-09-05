#!/usr/bin/env python3
"""
달토끼 편성 배치 — 이야기 은행에서 한 편(영상)에 넣을 목록을 골라 순서를 잡는다.

Usage:
    python3 scripts/script/build_lineup.py channels/dalttokki/stories \
        --count 12 --target-min 60 --out channels/dalttokki/projects/01편/lineup.json
    # 이미 쓴 이야기를 빼고 다음 편을 짠다
    python3 scripts/script/build_lineup.py channels/dalttokki/stories \
        --exclude channels/dalttokki/projects/01편/lineup.json --count 8

배치 규칙 (sleep-pd SKILL LINEUP 절)
  ① 웃음 편을 앞쪽에, 잔잔한 유래담을 뒤쪽에 — 뒤로 갈수록 조용해져야 한다
  ② 같은 결(꾀·보답·욕심…)이 연달아 오지 않게 섞는다
  ③ 합계 낭독 시간이 목표 ±10% 안에 들어오게 고른다
  ④ 첫 편은 가장 널리 아는 이야기로 — 부모가 제목을 보고 튼다

★"뒤로 갈수록 조용해진다"가 이 편성의 전부다. 마지막 편에 사건이 터지면
  아이가 다시 깨고, 그 편은 시청 지속시간에서 손해를 본다.
"""
import argparse, json, pathlib, re, sys

LINE = re.compile(r"^([^\s:\[][^:]{0,15}):\s*(.+)$")
TAG = re.compile(r"\[[^\]]*\]")
GENRE = re.compile(r"^-\s*갈래\s*:\s*(.+)$", re.M)
CHARS_PER_MIN = 210

# 각성도 — 낮을수록 조용하다. 뒤쪽에 배치한다.
CALM = {"유래담": 0, "보답": 1, "우정": 1, "약속": 1, "도움": 2, "협동": 2,
        "정직": 2, "지혜": 3, "깨달음": 3, "욕심": 3, "형제": 3, "도깨비": 4, "꾀": 4, "웃음": 5}
# 널리 아는 이야기 — 첫 편 후보(제목 검색량이 높다)
FAMOUS = ("금도끼", "흥부", "해와 달", "호랑이와 곶감", "혹부리", "콩쥐", "선녀")


def scan(path):
    raw = path.read_text(encoding="utf-8")
    head, _, body = raw.partition("\n---\n")
    m = GENRE.search(head)
    tags = [x.strip() for x in (m.group(1) if m else "").split("·")]
    genre = tags[-1] if tags else ""
    n = 0
    for ln in body.splitlines():
        ln = ln.strip()
        lm = LINE.match(ln) if ln else None
        if lm:
            n += len(TAG.sub("", lm.group(2)).replace(" ", ""))
    title = path.stem.split("_", 1)[-1].replace("-", " ")
    return {"file": path.name, "title": title, "genre": genre,
            "chars": n, "min": round(n / CHARS_PER_MIN, 2),
            "calm": CALM.get(genre, 3),
            "famous": any(f in title for f in FAMOUS)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stories", type=pathlib.Path)
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--target-min", type=float, default=60.0, help="낭독 목표 길이(분)")
    ap.add_argument("--exclude", type=pathlib.Path, action="append", default=[],
                    help="이미 쓴 lineup.json (여러 번 줄 수 있다)")
    ap.add_argument("--out", type=pathlib.Path)
    a = ap.parse_args()

    used = set()
    for ex in a.exclude:
        if ex.exists():
            used |= {r["file"] for r in json.loads(ex.read_text(encoding="utf-8"))}

    rows = [scan(f) for f in sorted(a.stories.glob("*.md")) if not f.name.startswith("_")]
    rows = [r for r in rows if r["file"] not in used]
    if len(rows) < a.count:
        print("warning: 은행에 %d편뿐입니다 — %d편을 요청했습니다" % (len(rows), a.count), file=sys.stderr)
        a.count = len(rows)

    # ③ 목표 시간에 맞춰 고른다: 널리 아는 것 우선, 그다음 결이 겹치지 않게
    pick, seen_genre, total = [], {}, 0.0
    for r in sorted(rows, key=lambda r: (not r["famous"], seen_genre.get(r["genre"], 0))):
        if len(pick) >= a.count:
            break
        pick.append(r)
        seen_genre[r["genre"]] = seen_genre.get(r["genre"], 0) + 1
        total += r["min"]

    # ① 뒤로 갈수록 조용하게. ② 같은 결이 연달아 오지 않게 한 번 훑어 자리를 바꾼다
    pick.sort(key=lambda r: -r["calm"])
    for i in range(1, len(pick)):
        if pick[i]["genre"] == pick[i - 1]["genre"]:
            for j in range(i + 1, len(pick)):
                if pick[j]["genre"] != pick[i - 1]["genre"]:
                    pick[i], pick[j] = pick[j], pick[i]
                    break
    # ④ 첫 자리는 널리 아는 이야기로
    for i, r in enumerate(pick):
        if r["famous"]:
            pick.insert(0, pick.pop(i))
            break

    print("%-30s %-8s %6s %5s" % ("제목", "갈래", "분", "각성"))
    for r in pick:
        print("%-30s %-8s %6.1f %5d" % (r["title"], r["genre"], r["min"], r["calm"]))
    print("\n%d편 / 낭독 %.1f분 (목표 %.0f분) / 백색소음 120분을 더하면 총 %.2f시간"
          % (len(pick), total, a.target_min, (total + 120) / 60))
    off = abs(total - a.target_min) / a.target_min
    if off > 0.10:
        print("warning: 목표에서 %.0f%% 벗어났습니다 — --count 를 조정하세요" % (off * 100), file=sys.stderr)

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(pick, ensure_ascii=False, indent=1), encoding="utf-8")
        print("편성 저장 → %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
