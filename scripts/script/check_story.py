#!/usr/bin/env python3
"""
달토끼 단편 대본 검사기 — stories/*.md 를 규격(config/script-guide.md)에 맞춰 검사한다.

Usage:
    python3 scripts/script/check_story.py channels/dalttokki/stories [--json]
    python3 scripts/script/check_story.py channels/dalttokki/stories/001_*.md

★게이트다. 하나라도 ERROR면 종료코드 2 — 낭독(TTS)으로 넘어가지 않는다.
   WARN은 종료코드 0이지만 리뷰 회전에서 반드시 다룬다.

검사 항목
  E1 캐스팅 줄이 있고, 모든 화자가 캐스팅에 등록돼 있는가
  E2 캐스팅이 가리키는 베이스 보이스가 voices.json 에 있는가
  E3 고유 화자 수 <= _max_per_story
  E4 낭독 글자 수가 밴드 안인가 (기본 1000~1750자)
  E5 대립 인물이 같은 베이스 보이스를 쓰지 않는가 (같은 보이스 2회 이상 배정 시 경고→에러)
  W1 문장 평균 25자 이하 / 최대 45자
  W2 나레이션 비중 >= 70%
  W3 첫 문장이 옛이야기 시작구인가
  W4 마지막 문장이 잠으로 잇는가
  W5 금지 표현 — 큰 소리 의성어, 설교체, 청자 질문
"""
import argparse, json, pathlib, re, sys

BAND_MIN, BAND_MAX = 900, 1500
CHARS_PER_MIN = 210   # ★추정치. 수면동화는 느리게 읽고 문단마다 여백이 붙는다.
                      #   1호 낭독 실측 후 여기와 settings.json format.chars_per_min 을 함께 고친다.
SENT_AVG_MAX, SENT_MAX = 25, 45
NARRATION_MIN_RATIO = 0.70

OPENERS = ("옛날 옛날", "옛날에", "아주 먼 옛날", "옛적에", "옛날 옛적")
SLEEP_WORDS = ("잠", "꿈", "달빛", "눈을 감", "새근새근", "스르르")

# 큰 소리·각성 유발 의성어. 수면동화에서 쓰지 않는다.
LOUD = ("쾅", "우당탕", "으악", "꽥", "빽", "왁", "쿵쾅", "우르르쾅", "펑", "탕탕")
# 설교체 / 청자에게 던지는 질문 — 생각하면 잠이 깬다.
PREACHY = ("여러분", "그러니까 우리는", "해야 해요", "안 되겠지요", "알겠지요",
           "어떻게 생각하나요", "어떨까요", "그렇지요?")

CAST_RE = re.compile(r"^-\s*캐스팅\s*:\s*(.+)$", re.M)
# ★변신담 지원 — 같은 인물이 이름을 바꿔 등장하면(우렁이→각시, 젊은이→소) 같은 목소리를
#   써야 옳다. 그런 짝은 머리말에 `- 동일인물: 우렁이=각시` 로 선언하고 E5에서 면제한다.
SAME_RE = re.compile(r"^-\s*동일인물\s*:\s*(.+)$", re.M)
LINE_RE = re.compile(r"^([^\s:\[][^:]{0,15}):\s*(.+)$")
TAG_RE = re.compile(r"\[[^\]]*\]")


def find_config(start: pathlib.Path, name: str):
    cur = start.resolve()
    for _ in range(8):
        p = cur / "config" / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def parse(path: pathlib.Path):
    raw = path.read_text(encoding="utf-8")
    head, _, body = raw.partition("\n---\n")
    cast = {}
    m = CAST_RE.search(head)
    if m:
        for pair in m.group(1).split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                cast[k.strip()] = v.strip()
    same = []
    ms = SAME_RE.search(head)
    if ms:
        for grp in ms.group(1).split(","):
            same.append({x.strip() for x in grp.split("=") if x.strip()})

    lines = []
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        lm = LINE_RE.match(ln)
        if lm:
            lines.append((lm.group(1).strip(), TAG_RE.sub("", lm.group(2)).strip()))
        else:
            lines.append((None, ln))       # 화자 표기가 없는 줄
    return head, cast, lines, same


def check(path: pathlib.Path, voices_cfg: dict):
    head, cast, lines, same = parse(path)
    errs, warns = [], []
    pool = (voices_cfg or {}).get("voices", {})
    max_speakers = (voices_cfg or {}).get("_max_per_story", 6)

    if not cast:
        errs.append("E1 캐스팅 줄이 없다 — `- 캐스팅: 나레이션=나레이션, …`")

    unlabeled = [t for s, t in lines if s is None]
    if unlabeled:
        errs.append(f"E1 화자 표기가 없는 줄 {len(unlabeled)}개 (예: {unlabeled[0][:30]}…)")

    speakers = [s for s, _ in lines if s]
    uniq = sorted(set(speakers))
    for s in uniq:
        if s not in cast:
            errs.append(f"E1 화자 '{s}' 가 캐스팅에 없다")
    for k, v in cast.items():
        if v not in pool:
            errs.append(f"E2 캐스팅 '{k}={v}' — '{v}' 는 voices.json 에 없는 베이스 보이스")
    if len(uniq) > max_speakers:
        errs.append(f"E3 고유 화자 {len(uniq)}명 (최대 {max_speakers}명): {', '.join(uniq)}")

    used = {}
    for k, v in cast.items():
        used.setdefault(v, []).append(k)
    for v, ks in used.items():
        if len(ks) > 1 and not any(set(ks) <= g for g in same):
            errs.append(f"E5 베이스 보이스 '{v}' 를 {len(ks)}명이 함께 쓴다 ({', '.join(ks)}) "
                        f"— 아이가 누가 말했는지 놓친다. 같은 인물이면 '- 동일인물:' 로 선언할 것")

    spoken = " ".join(t for _, t in lines)   # ★줄을 공백으로 잇는다 — 붙여 이으면 서로 다른 두 문장이 한 문장으로 읽혀 W1이 헛경보를 낸다
    n = len(spoken.replace(" ", ""))
    if not (BAND_MIN <= n <= BAND_MAX):
        errs.append(f"E4 낭독 글자 수 {n}자 (밴드 {BAND_MIN}~{BAND_MAX})")

    sents = [s.strip() for s in re.split(r"[.!?…]\s*", spoken) if s.strip()]
    if sents:
        avg = sum(len(s) for s in sents) / len(sents)
        longest = max(sents, key=len)
        if avg > SENT_AVG_MAX:
            warns.append(f"W1 평균 문장 {avg:.1f}자 (권장 {SENT_AVG_MAX}자 이하)")
        if len(longest) > SENT_MAX:
            warns.append(f"W1 최장 문장 {len(longest)}자: {longest[:40]}…")

    nar = sum(1 for s, _ in lines if s == "나레이션")
    ratio = nar / len(lines) if lines else 0
    if ratio < NARRATION_MIN_RATIO:
        warns.append(f"W2 나레이션 비중 {ratio:.0%} (권장 {NARRATION_MIN_RATIO:.0%} 이상) — 라디오드라마가 된다")

    first = next((t for _, t in lines if t), "")
    if not any(first.startswith(o) for o in OPENERS):
        warns.append(f"W3 첫 문장이 옛이야기 시작구가 아니다: {first[:30]}…")

    last = next((t for _, t in reversed(lines) if t), "")
    if not any(w in last for w in SLEEP_WORDS):
        warns.append(f"W4 마지막 문장이 잠으로 이어지지 않는다: {last[:40]}…")

    for w in LOUD:
        if w in spoken:
            warns.append(f"W5 큰 소리 의성어 '{w}' — 아이가 깬다")
    for w in PREACHY:
        if w in spoken:
            warns.append(f"W5 설교체/청자 질문 '{w}'")

    return {"file": path.name, "chars": n, "minutes": round(n / CHARS_PER_MIN, 1),
            "speakers": uniq, "errors": errs, "warnings": warns}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", type=pathlib.Path, help="stories 폴더 또는 개별 .md")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    files = sorted(a.target.glob("*.md")) if a.target.is_dir() else [a.target]
    files = [f for f in files if not f.name.startswith("_")]
    if not files:
        print("검사할 대본이 없습니다", file=sys.stderr)
        return 1
    voices = find_config(files[0].parent, "voices.json")
    if voices is None:
        print("warning: voices.json 을 찾지 못했습니다 — 캐스팅 검사를 건너뜁니다", file=sys.stderr)

    rows = [check(f, voices) for f in files]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            mark = "ERR " if r["errors"] else ("warn" if r["warnings"] else "  ok")
            print(f"[{mark}] {r['file']}  {r['chars']}자 / 약 {r['minutes']}분 / 화자 {len(r['speakers'])}")
            for e in r["errors"]:
                print(f"        ✗ {e}")
            for w in r["warnings"]:
                print(f"        · {w}")
        tot = sum(r["chars"] for r in rows)
        print(f"\n{len(rows)}편 / 합계 {tot:,}자 / 약 {tot/250/60:.2f}시간 "
              f"/ ERROR {sum(len(r['errors']) for r in rows)} "
              f"/ WARN {sum(len(r['warnings']) for r in rows)}")
    return 2 if any(r["errors"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
