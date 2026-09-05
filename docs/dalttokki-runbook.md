# 달토끼 1호 영상 실행 순서

설계 근거는 [benchmark/dalttokki-channel-design.md](benchmark/dalttokki-channel-design.md),
단계별 규칙은 `.claude/skills/sleep-pd/SKILL.md` 에 있다. 이 문서는 **손으로 뭘 치면 되는지**만 적는다.

전제: 저장소 루트에서 실행. `.venv` 가 있어야 한다.
```bash
python3 -m venv .venv
.venv/Scripts/python.exe -m pip install google-genai Pillow requests python-dotenv numpy certifi
```
★`certifi` 는 선택이 아니다 — 이 PC의 윈도우 인증서 저장소가 깨져 있어
`ssl.create_default_context()` 가 죽는다. 없으면 이미지 생성과 TTS가 전량 실패한다.

---

## 0. 지금 없는 것 (사람이 채워야 진행된다)

| 없는 것 | 어디에 | 없으면 |
|---|---|---|
| **ElevenLabs 보이스 선정** | `channels/dalttokki/config/voices.json` 의 `voice_id` 12칸 | 낭독 단계에서 멈춘다 |
| **`ELEVENLABS_API_KEY`** | 루트 `.env` | 〃 |
| **백색소음 2시간** | `channels/dalttokki/assets/intro,outro/sleep_noise_2h_quiet.mp3` | 뒤 2시간이 안 붙는다 (야담 채널 것을 복사하면 된다) |
| **채널 개설** | YouTube | 업로드 불가 |

`GEMINI_API_KEY` 는 이미 `.env` 에 있다(이미지 생성 완료).

---

## 1. 보이스 고르기 (사람, 20분)

ElevenLabs Voice Library 에서 한국어 보이스를 고르고 `voices.json` 에 id를 채운다.
**같은 편에 함께 나오는 짝은 반드시 다른 사람 목소리로** 고른다:

| 칸 | 어떤 목소리 | 함께 나오는 짝 |
|---|---|---|
| `나레이션` | 엄마 톤. 낮고 느리고 따뜻하게. **전체의 70%** | — |
| `어른남자` / `어른남자2` | 주인공 / 대립 인물 | 001·008·010·011 에서 나란히 나온다 |
| `어른여자` / `어른여자2` | 주인공 / 대립 인물 | 012 |
| `할아버지` / `할머니` | 느리고 인자하게 | 009·014·018 |
| `아이` / `아이2` | 밝지만 크지 않게 | 005(오빠·동생)·012(콩쥐·팥쥐) |
| `호랑이` | 굵고 낮게. **위협적으로 만들지 않는다** | 002·005·017 |
| `동물` / `동물2` | 가볍지만 빠르지 않게 | 007(자라·토끼)·019(개·고양이)·020(쥐·소) |
| `도깨비` | 장난꾸러기. 무섭게 만들지 않는다 | 003·011 |

★**A/B 를 먼저 하라** — 대사가 많은 `005_해와-달이-된-오누이.md` 한 편만
ElevenLabs / Supertone Sona 2 / Gemini TTS 세 곳에서 뽑아 블라인드로 들어 보고 정한다.
편당 비용 차이가 최대 1.2만 원이라 품질이 결정 변수다(설계서 §7).

---

## 2. 편성 짜기

```bash
.venv/Scripts/python.exe scripts/script/build_lineup.py channels/dalttokki/stories \
    --count 12 --target-min 60 \
    --out channels/dalttokki/projects/01편/lineup.json
```
각성도가 높은 편부터 낮은 편 순으로 정렬된다 — **뒤로 갈수록 조용해지는 것이 이 편성의 전부다.**
2호는 `--exclude channels/dalttokki/projects/01편/lineup.json` 을 붙여 겹치지 않게 뽑는다.

---

## 3. 낭독

```bash
# 먼저 비용을 본다 (키 없이도 된다)
.venv/Scripts/python.exe scripts/tts/dialogue_tts.py channels/dalttokki/stories --dry-run

# 실제 낭독
.venv/Scripts/python.exe scripts/tts/dialogue_tts.py channels/dalttokki/stories \
    --out channels/dalttokki/projects/01편/_video
```
- 대본의 `화자:` 표기를 읽어 **voice_id 를 자동으로 배정한다.** 사람이 대사마다 고르지 않는다.
- 산출: `audio.mp3` + `chapters.json`(이야기별 시작 시각) + `parts/`(청크별 mp3와 정렬)
- **재실행해도 이미 만든 청크는 다시 과금하지 않는다**(`parts/part_NNN.mp3` 가 있으면 건너뛴다).
- 12편만 낭독하려면 `--out` 은 그대로 두고 `stories` 대신 편성에 든 파일만 인자로 준다.

낭독이 끝나면 **실측 낭독 속도를 확인**하고 두 곳을 함께 고친다:
`settings.json format.chars_per_min` / `scripts/script/check_story.py` 의 `CHARS_PER_MIN`.
현재 값 210자/분은 **추정치**다.

---

## 4. 영상 조립

```bash
# 구간 계획과 총 길이만 확인
.venv/Scripts/python.exe scripts/render/build_sleep_video.py \
  --keyvisual channels/dalttokki/assets/keyvisual/keyvisual_01.png \
  --audio channels/dalttokki/projects/01편/_video/audio.mp3 \
  --chapters channels/dalttokki/projects/01편/_video/chapters.json \
  --noise "channels/dalttokki/assets/intro,outro/sleep_noise_2h_quiet.mp3" \
  --out channels/dalttokki/projects/01편/output/01편.mp4 --dry-run

# --dry-run 을 빼면 렌더한다 (3시간 분량은 시간이 걸린다)
```
CapCut을 열 일이 없다. 챕터마다 3초 카드가 들어가고, 나머지는 고정 이미지,
뒤에 검은 화면 + 백색소음이 붙는다.

---

## 5. 썸네일

```bash
.venv/Scripts/python.exe scripts/assets/make_thumbnail.py \
  channels/dalttokki/assets/keyvisual/keyvisual_01.png \
  channels/dalttokki/projects/01편/output/thumbnail.png \
  --top "중간광고 없는" --big1 "전래동화" --big2 "3시간" --bottom "어린이 수면동화"
```
2호부터는 `--flip --side right` 를 붙여 좌우를 뒤집는다(벤치가 편마다 뒤집는다).

---

## 6. 제목·설명·태그

```bash
.venv/Scripts/python.exe scripts/upload/build_sleep_meta.py \
  --chapters channels/dalttokki/projects/01편/_video/chapters.json \
  --noise-min 120 --genre 전래동화 --speaker 엄마 \
  --out channels/dalttokki/projects/01편/output/meta.txt
```

---

## 7. 업로드 — ★이 셋을 확인하고 올린다

1. **아동용: 아니오.** 아동용으로 지정하면 댓글·알림·맞춤광고가 전부 꺼진다.
   벤치도 아동용이 아니다(댓글 276개가 근거). 실질 시청 주체는 아이가 아니라 재우는 부모다.
2. **미드롤 광고: 끔.** 제목에 "중간광고 없는"을 넣었으면 반드시 꺼야 한다.
   말만 하고 광고를 켜면 그 한 번으로 신뢰가 끝난다.
3. **다국어: 한국어 + 영어 제목·설명 동시 등록.** 벤치는 이걸로 해외 노출을 먹고 있다.

---

## 8. 1호를 올린 뒤 확인할 것

| 지표 | 왜 |
|---|---|
| 평균 시청 지속시간 | 백색소음 2시간이 실제로 체류를 끌어올리는지. 이게 이 포맷의 핵심 가설이다 |
| 챕터 클릭 분포 | 설명란 목차가 실제로 쓰이는지. 안 쓰이면 목차 서식을 손봐야 한다 |
| 이탈 지점 | 특정 이야기에서 이탈이 몰리면 그 편의 각성도가 잘못 매겨진 것이다 |
| 낭독 실측 속도 | `chars_per_min` 갱신 (3절) |
| ElevenLabs 실청구 크레딧 | `dialogue_tts.py` 의 `CREDITS_PER_CHAR` 갱신 |
