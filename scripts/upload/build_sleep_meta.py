#!/usr/bin/env python3
"""
달토끼 업로드 메타 생성 — chapters.json 으로 제목·설명·태그를 만든다.

Usage:
    python3 scripts/upload/build_sleep_meta.py \
        --chapters channels/dalttokki/projects/01편/_video/chapters.json \
        --noise-min 120 --genre 전래동화 --speaker 엄마 \
        --out channels/dalttokki/projects/01편/output/meta.txt

벤치마크(호호샘) 18편 전수 분석에서 뽑은 서식을 그대로 따른다
(docs/benchmark/hohosam-2026-09.md §3):
  ① 제목 = [후킹구] + [분량] + [장르] + 🌙😴💤 + [화자 프레이밍]
  ② 설명 = "🌙 오늘의 옛이야기" + 전체 목차 타임스탬프 + 크레딧 + 해시태그 + 저작권
  ③ 태그 = 고정 13개 + 주제 5개
  ④ ★영어 제목·설명을 함께 낸다 — 벤치는 다국어 메타로 해외 노출을 먹고 있다

★"중간광고 없는" 은 브랜드 약속이다. 제목에 넣었으면 업로드에서 미드롤을 반드시 꺼야 한다
  (settings.json upload.mid_roll_ads=false). 말만 하고 광고를 켜면 그 한 번으로 신뢰가 끝난다.
"""
import argparse, json, pathlib, sys

FIXED_TAGS = ["달토끼", "잠자리동화", "동화책읽어주기", "잠잘때듣는동화", "어린이동화",
              "수면동화", "자장가동화", "꿀잠동화", "엄마동화", "동화책읽어주는엄마",
              "소곤소곤잠자리동화", "잠오는영상", "백색소음"]
GENRE_TAGS = {
    "전래동화": ["전래동화", "옛날이야기", "민담", "설화", "어린이동화책읽어주기"],
    "이솝우화": ["이솝우화", "이솝이야기", "우화", "어린이동화책읽어주기", "교훈동화"],
    "명작동화": ["명작동화", "세계명작", "동화모음", "어린이동화책읽어주기", "창작동화"],
}
GENRE_EN = {"전래동화": "Korean Folk Tales", "이솝우화": "Aesop's Fables",
            "명작동화": "Classic Fairy Tales"}


def hms(sec):
    sec = int(round(sec))
    return "%d:%02d:%02d" % (sec // 3600, sec % 3600 // 60, sec % 60)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chapters", type=pathlib.Path, required=True)
    ap.add_argument("--noise-min", type=int, default=120, help="뒤에 붙는 백색소음 길이(분)")
    ap.add_argument("--genre", default="전래동화", choices=sorted(GENRE_TAGS))
    ap.add_argument("--speaker", default="엄마", help="화자 프레이밍 — 엄마 / 아빠 / 달토끼")
    ap.add_argument("--producer", default="", help="기획·제작자 이름(선택)")
    ap.add_argument("--out", type=pathlib.Path)
    a = ap.parse_args()

    chapters = json.loads(a.chapters.read_text(encoding="utf-8"))
    if not chapters:
        print("error: chapters.json 이 비어 있습니다", file=sys.stderr)
        return 1

    narr_sec = float(chapters[-1]["start_sec"]) + 300      # 마지막 편은 길이를 모르니 5분으로 잡는다
    total_h = (narr_sec + a.noise_min * 60) / 3600
    hours = int(round(total_h))
    # 인삿말은 "이야기 N편" 에서 세지 않는다 — 목차에는 넣되 편수에는 빼야 과장이 안 된다
    n = sum(1 for c in chapters if c["title"].strip() not in ("인삿말", "인사말"))

    title = ("중간광고 없는 %d시간 잠자리동화 🌙😴💤 %s가 읽어주는 %s %d편 + 수면 백색소음"
             % (hours, a.speaker, a.genre, n))
    title_en = ("%d Hours of %s 🌙😴💤 Bedtime Stories for Kids + Sleep White Noise"
                % (hours, GENRE_EN.get(a.genre, "Bedtime Stories")))

    lines = ["🌙 오늘의 옛이야기"]
    for ch in chapters:
        lines.append("%s %s" % (hms(ch["start_sec"]), ch["title"]))
    lines.append("%s 🌊 수면 백색소음 (%d시간)" % (hms(narr_sec), a.noise_min // 60))
    lines += ["",
              "이야기가 끝나면 백색소음이 이어집니다.",
              "중간광고 없이 끝까지 끊기지 않아요. 머리맡에 편안히 틀어 두세요.",
              "",
              "🎙️ 각색 및 낭독 : 달토끼"]
    if a.producer:
        lines.append("⭐ 기획 및 제작 : %s" % a.producer)
    lines += ["", "#오디오북 #달토끼 #%s" % a.genre, "",
              "© 2026 달토끼 잠자리동화. All Rights Reserved."]
    desc = "\n".join(lines)

    tags = FIXED_TAGS + GENRE_TAGS[a.genre]

    out = []
    out.append("[제목]\n%s\n" % title)
    out.append("[제목 EN]\n%s\n" % title_en)
    out.append("[설명]\n%s\n" % desc)
    out.append("[태그]\n%s\n" % ", ".join(tags))
    out.append("[업로드 설정]\n아동용: 아니오 (댓글·알림·맞춤광고 유지)\n"
               "미드롤 광고: 끔 (제목의 '중간광고 없는' 약속)\n"
               "다국어: 한국어 + 영어 동시 등록\n")
    out.append("[썸네일 문안]\n중간광고 없는 / %s / %d시간 / 어린이 수면동화\n" % (a.genre, hours))
    text = "\n".join(out)

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8")
        print("메타 저장 → %s" % a.out)
    print(text)

    if len(title) > 100:
        print("warning: 제목이 %d자입니다 — 유튜브 한도 100자를 넘습니다" % len(title), file=sys.stderr)
    if len(", ".join(tags)) > 500:
        print("warning: 태그 합계가 500자를 넘습니다", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
