#!/usr/bin/env python3
"""
ElevenLabs Text-to-Dialogue 낭독 — 대본의 `화자:` 표기를 그대로 캐스팅으로 읽어
대사마다 다른 목소리로 낭독한다. ★사람이 대사를 하나씩 클릭해 목소리를 고르지 않는다.

Usage:
    # 비용·청크만 계산하고 호출하지 않는다 (키 없이도 된다)
    python3 scripts/tts/dialogue_tts.py channels/dalttokki/stories --dry-run
    # 실제 낭독 (ELEVENLABS_API_KEY 필요)
    python3 scripts/tts/dialogue_tts.py channels/dalttokki/stories --out channels/dalttokki/projects/01편/_video
    # 특정 편만
    python3 scripts/tts/dialogue_tts.py channels/dalttokki/stories/001_금도끼-은도끼.md --out /tmp/t

동작
  1. 대본 머리말의 `- 캐스팅: 나레이션=나레이션, 나무꾼=어른남자, …` 를 읽는다
  2. 본문 `화자: 대사` 줄을 순서대로 모아 voices.json 의 voice_id 로 치환한다
  3. API 제한(요청당 2,000자 / 고유 voice_id 10개)에 맞춰 자동으로 청크를 나눈다
  4. /v1/text-to-dialogue/convert-with-timestamps 로 호출해 mp3 + 문자단위 정렬을 받는다
  5. 청크 mp3를 ffmpeg 로 이어 붙이고, 이야기별 시작 시각을 chapters.json 으로 낸다

★타임스탬프가 함께 오므로 챕터 목차를 손으로 재지 않는다. Vrew 수동 게이트가 사라진다.
"""
import argparse, base64, json, os, pathlib, re, ssl, subprocess, sys, urllib.request

API = "https://api.elevenlabs.io/v1/text-to-dialogue/convert-with-timestamps"
MAX_CHARS = 1900          # 문서 권장 2,000자 — 여유를 둔다
MAX_VOICES = 10
CREDITS_PER_CHAR = 1.0    # eleven_v3 = 1 크레딧/자 (2026-09 확인). 실측 후 고칠 것.

CAST_RE = re.compile(r"^-\s*캐스팅\s*:\s*(.+)$", re.M)
LINE_RE = re.compile(r"^([^\s:\[][^:]{0,15}):\s*(.+)$")


def ssl_ctx():
    """Windows 인증서 저장소가 깨진 환경 우회 — generate_image.py 와 같은 이유."""
    cafile = os.environ.get("SSL_CERT_FILE")
    if not cafile:
        try:
            import certifi
            cafile = certifi.where()
        except Exception:
            return None
    try:
        return ssl.create_default_context(cafile=cafile)
    except Exception:
        return None


def find_config(start, name):
    cur = pathlib.Path(start).resolve()
    for _ in range(8):
        p = cur / "config" / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        if cur.parent == cur:
            break
        cur = cur.parent
    raise FileNotFoundError("config/%s 을 %s 상위에서 찾지 못했습니다" % (name, start))


def find_env_key(start, name="ELEVENLABS_API_KEY"):
    cur = pathlib.Path(start).resolve()
    for _ in range(8):
        env = cur / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        if cur.parent == cur:
            break
        cur = cur.parent
    return os.environ.get(name)


def parse_story(path, pool):
    """→ [(voice_id, 베이스보이스, 대사)].

    ★캐스팅에 없는 화자를 만나면 즉시 멈춘다. 조용히 나레이션으로 떨어뜨리면
      한 인물이 통째로 나레이터 목소리로 낭독되는데, 다 만들고 나서야 귀로 알게 된다.
    """
    raw = path.read_text(encoding="utf-8")
    head, _, body = raw.partition("\n---\n")
    m = CAST_RE.search(head)
    if not m:
        raise SystemExit("error: %s 에 '- 캐스팅:' 줄이 없습니다" % path.name)
    cast = {}
    for pair in m.group(1).split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            cast[k.strip()] = v.strip()

    turns = []
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        lm = LINE_RE.match(ln)
        if not lm:
            raise SystemExit("error: %s — 화자 표기가 없는 줄: %s" % (path.name, ln[:40]))
        who, text = lm.group(1).strip(), lm.group(2).strip()
        if who not in cast:
            raise SystemExit("error: %s — 화자 '%s' 가 캐스팅에 없습니다" % (path.name, who))
        base = cast[who]
        if base not in pool:
            raise SystemExit("error: %s — 베이스 보이스 '%s' 가 voices.json 에 없습니다" % (path.name, base))
        turns.append(((pool[base] or {}).get("voice_id") or "", base, text))
    return turns


def chunk(turns):
    """2,000자 / 고유 voice 10개 제한에 맞춰 나눈다. 한 발화는 쪼개지 않는다."""
    out, cur, n, voices = [], [], 0, set()
    for t in turns:
        tl = len(t[2])
        if cur and (n + tl > MAX_CHARS or (t[0] not in voices and len(voices) >= MAX_VOICES)):
            out.append(cur)
            cur, n, voices = [], 0, set()
        cur.append(t)
        n += tl
        voices.add(t[0])
    if cur:
        out.append(cur)
    return out


def call(chunk_turns, key, model, settings):
    body = json.dumps({
        "inputs": [{"text": t[2], "voice_id": t[0]} for t in chunk_turns],
        "model_id": model,
        "settings": settings,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600, context=ssl_ctx()) as r:
        return json.loads(r.read().decode("utf-8"))


def mp3_seconds(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", type=pathlib.Path, help="stories 폴더 또는 개별 .md")
    ap.add_argument("--out", type=pathlib.Path, help="산출 폴더 (audio.mp3 · chapters.json)")
    ap.add_argument("--dry-run", action="store_true", help="비용·청크만 계산하고 호출하지 않는다")
    a = ap.parse_args()

    files = sorted(a.target.glob("*.md")) if a.target.is_dir() else [a.target]
    files = [f for f in files if not f.name.startswith("_")]
    if not files:
        print("대본이 없습니다", file=sys.stderr)
        return 1

    settings_cfg = find_config(files[0].parent, "settings.json")
    voices_cfg = find_config(files[0].parent, "voices.json")
    pool = voices_cfg.get("voices", {})
    tts = settings_cfg.get("tts", {})
    model = tts.get("model_id", "eleven_v3")
    call_settings = dict((k, tts[k]) for k in ("stability", "similarity_boost", "speed") if k in tts)

    total_chars, total_chunks, plan = 0, 0, []
    for f in files:
        turns = parse_story(f, pool)
        chunks = chunk(turns)
        n = sum(len(t[2]) for t in turns)
        total_chars += n
        total_chunks += len(chunks)
        plan.append((f, turns, chunks))
        missing = sorted(set(t[1] for t in turns if not t[0]))
        tail = ("  ★voice_id 미설정: " + ", ".join(missing)) if missing else ""
        print("%-34s %5d자 / 청크 %d / 화자 %d%s"
              % (f.name, n, len(chunks), len(set(t[1] for t in turns)), tail))

    credits = int(total_chars * CREDITS_PER_CHAR)
    print("\n합계 %s자 / 요청 %d회 / 예상 %s 크레딧" % (format(total_chars, ","), total_chunks, format(credits, ",")))
    print("  Creator($22 = 100,000크레딧) 기준 약 $%.2f · Pro($99 = 500,000) 기준 약 $%.2f"
          % (credits / 100000 * 22, credits / 500000 * 99))
    if a.dry_run:
        print("\n--dry-run — API를 호출하지 않았습니다.")
        return 0

    if not a.out:
        print("error: --out 이 필요합니다", file=sys.stderr)
        return 1
    key = find_env_key(files[0])
    if not key:
        print("error: ELEVENLABS_API_KEY 가 .env 에도 환경변수에도 없습니다", file=sys.stderr)
        return 1
    if any(not t[0] for _f, turns, _c in plan for t in turns):
        print("error: voice_id 가 비어 있는 화자가 있습니다 — config/voices.json 을 먼저 채우세요",
              file=sys.stderr)
        return 2

    a.out.mkdir(parents=True, exist_ok=True)
    parts_dir = a.out / "parts"
    parts_dir.mkdir(exist_ok=True)
    chapters, elapsed, idx = [], 0.0, 0
    for f, _turns, chunks in plan:
        chapters.append({"title": f.stem.split("_", 1)[-1].replace("-", " "),
                         "start_sec": round(elapsed, 2), "file": f.name})
        for ck in chunks:
            idx += 1
            part = parts_dir / ("part_%03d.mp3" % idx)
            if not part.exists():                       # 재실행 시 이미 만든 청크는 다시 과금하지 않는다
                res = call(ck, key, model, call_settings)
                part.write_bytes(base64.b64decode(res["audio_base64"]))
                part.with_suffix(".align.json").write_text(
                    json.dumps(res.get("alignment", {}), ensure_ascii=False), encoding="utf-8")
            elapsed += mp3_seconds(part)
            print("  %s  누적 %.1f분" % (part.name, elapsed / 60))

    lst = a.out / "parts.txt"
    lst.write_text("".join("file '%s'\n" % p.resolve().as_posix()
                           for p in sorted(parts_dir.glob("part_*.mp3"))), encoding="utf-8")
    audio = a.out / "audio.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(audio)], check=True)
    (a.out / "chapters.json").write_text(json.dumps(chapters, ensure_ascii=False, indent=1),
                                         encoding="utf-8")

    print("\n낭독 완료 → %s  (%.1f분)" % (audio, elapsed / 60))
    print("챕터 %d개 → %s" % (len(chapters), a.out / "chapters.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
