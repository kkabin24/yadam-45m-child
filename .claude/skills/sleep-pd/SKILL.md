---
name: sleep-pd
description: 어린이 수면동화 오디오북 PD(달토끼 채널). "달토끼 영상 만들어줘" 한마디로 이야기 선정→대본(외부 리뷰 4회전)→고정 키비주얼→챕터 카드→TTS→백색소음 결합→업로드를 상태 기반으로 오케스트레이션. 야담(story-pd)과 달리 씬 이미지·스토리보드·훅 클립이 없고 화면은 정지 1장이다. 수면동화·전래동화·이솝우화·잠자리동화 요청 시 사용.
---

# sleep-pd — 어린이 수면동화 오디오북 PD

story-pd(야담)의 자매 스킬이다. **겹치는 규칙은 story-pd를 따르고, 아래는 다른 점만 적는다.**
전역 원칙은 `CLAUDE.md`, 채널 정체성은 `channels/dalttokki/config/profile.md`,
집필 규격은 `channels/dalttokki/config/script-guide.md`, 벤치마크 근거는 `docs/benchmark/hohosam-2026-09.md`.

## 이 채널이 story-pd와 다른 점 (핵심)

| 항목 | story-pd(야담) | **sleep-pd(달토끼)** |
|---|---|---|
| 한 편 길이 | 45분 단편 | **4~7분 단편 × 12편 옴니버스** |
| 화면 | 씬 이미지 수백 장 + 켄번스 | **고정 1장 + 챕터 카드 3초.** 켄번스 끔 |
| 스토리보드 | 있음 | **없음** — STORYBOARD·SCENE_IMG·SCENE_TIMING 단계 자체가 없다 |
| 훅 클립 | VEO_HOOK | **없음** — 수면 콘텐츠에 훅은 역효과 |
| 자막 | 화면에 태움 | **태우지 않음.** SRT는 챕터 타임스탬프 산출용 |
| 뒤에 붙는 것 | 백색소음 아웃트로 | **검은 화면 + 백색소음 120분** (총 3시간) |
| 대본 게이트 | 사용자와 대화하며 집필 | **★외부 리뷰어 4회전 후 최종본만 보고** (아래) |

## ★대본 게이트 — 초고를 사용자에게 가져가지 않는다

`CLAUDE.md` 「대본 품질 게이트」 절이 이 채널의 최우선 규칙이다. 요약:

1. 이야기 20편 안팎을 **먼저 다 쓴다.** 한 편씩 승인받지 않는다.
2. `python3 scripts/script/check_story.py channels/dalttokki/stories` 로 **ERROR 0**을 만든다.
3. **에이전트를 외부 리뷰어로 세워 4회전**을 돈다. 회전마다 렌즈를 바꾼다:
   1회전 대상 적합성(만 4~7세) → 2회전 수면 정서 → 3회전 낭독/TTS → 4회전 완성도·다양성
4. 회전 결과는 `channels/dalttokki/stories/_review/roundN_*.md` 에 남기고, **지적을 실제로 반영한 뒤** 다음 회전으로 간다.
5. 사용자에게는 **최종본과 회전별 요약만** 보고한다. "이대로 진행할까요?"라고 묻지 않는다.

## 상태 감지 (위→아래 첫 매칭)

`{C}` = `channels/dalttokki` · `{P}` = `{C}/projects/{프로젝트}`

```
{C}/stories/ 에 대본이 12편 미만                  → STORY_BANK (대본 집필 + 리뷰 4회전)
{C}/assets/characters/mongi_turnaround.png 없음    → MASCOT ★검수 게이트
{P}/ 없음 or {P}/lineup.json 없음                  → LINEUP (이번 편에 넣을 이야기 12편 선정)
{P}/keyvisual.png 없음                             → KEYVISUAL ★검수 게이트 (썸네일 원본 겸용)
{P}/thumbnail.png 없음                             → THUMBNAIL
{P}/_video/audio.mp3 없음                          → TTS
{P}/_video/chapters.json 없음                      → CHAPTERS (타임스탬프 산출)
{P}/output/*.mp4 없음                              → RENDER (build_sleep_video.py — 카드·낭독·백색소음까지 한 번에)
{P}/output/upload_result.json 없음                 → UPLOAD
그 외                                              → DONE
```

**사람 게이트는 하나뿐이다** — 마스코트/키비주얼 이미지 검수.
★렌더 게이트가 없다. 야담은 CapCut export 후 사람이 마무리하지만(CLAUDE.md), 이 채널의 영상은
정지 이미지 1장 + 3초 카드 + 오디오뿐이라 **사람이 편집할 것이 없다.** `build_sleep_video.py` 가
ffmpeg로 최종 mp4까지 만든다. CapCut 게이트를 두면 3시간짜리 타임라인을 여는 일만 남는다.
대본은 사람 게이트가 **아니다**(위 대본 게이트 절).

## 단계별 요점

### STORY_BANK
- `{C}/config/script-guide.md` 를 그대로 따른다. 4~7분(900~1,500자), 만 4~7세, 존댓말 구연체.
- **순화 규칙을 반드시 적용**한다 — 잡아먹힘·죽음·잔혹한 벌·공포 묘사는 예외 없이 고친다.
- 대사는 `화자: 대사` 한 줄, 감정은 `[...]`. 파일 머리말에 `- 캐스팅:` 줄 필수.
- 소재 중복은 `{C}/research/topic_log.json` 으로 막는다(story-pd와 동일).

### LINEUP
- `stories/` 에서 12편을 골라 `{P}/lineup.json` 에 순서대로 적는다.
- **배치 규칙**: 웃음 편을 앞쪽에, 유래담·잔잔한 편을 뒤쪽에. 마지막 편은 가장 조용한 것.
- 같은 결(꾀 이야기 / 보답 이야기)이 연달아 오지 않게 섞는다.
- 합계 낭독 시간이 55~65분인지 `check_story.py` 로 확인한다.

### KEYVISUAL ★검수 게이트
- `{C}/assets/characters/mongi_turnaround.png` 를 ref로 넘겨 `scripts/image/generate_image.py` 로 1장 생성.
- 밤하늘 + 잠든 몽이 + 절구. **이 1장이 본편 배경이자 썸네일 원본**이다(에셋 1장으로 둘 다 커버).
- 생성 후 반드시 사용자에게 띄우고 OK를 받는다.

### TTS
- `settings.json tts.engine` 이 `elevenlabs` 면 `scripts/tts/dialogue_tts.py` 를 쓴다.
  대본의 `화자:` 표기 + 파일 머리말 `캐스팅:` 줄 + `config/voices.json` 을 합쳐
  Text-to-Dialogue `inputs[]` 를 자동으로 만든다. **사람이 목소리를 하나씩 고르지 않는다.**
- API 제한: 요청당 고유 voice_id 10개 / 2,000자. 스크립트가 알아서 청킹한다.
- `vrew` 면 story-pd의 vrew 절차와 같다(수동 게이트).

### CHAPTERS
- ElevenLabs 경로면 `convert-with-timestamps` 의 문자 단위 정렬에서 **이야기 시작 시각을 그대로 뽑는다.**
- 설명란 목차는 `0:00:00 인삿말` 부터 시작해 이야기 12편, 마지막 줄에 백색소음 구간을 적는다.

### RENDER
```bash
python3 scripts/render/build_sleep_video.py   --keyvisual {C}/assets/keyvisual/keyvisual_01.png   --audio {P}/_video/audio.mp3 --chapters {P}/_video/chapters.json   --noise "{C}/assets/intro,outro/sleep_noise_2h_quiet.mp3"   --out {P}/output/{편}.mp4
```
- 챕터마다 3초 카드를 얹고, 나머지는 고정 이미지, 뒤에 **검은 화면 + 백색소음 120분**을 붙인다.
- 먼저 `--dry-run` 으로 구간 계획과 총 길이를 확인한다.
- **백색소음 구간에는 광고를 넣지 않는다.**

### UPLOAD
- `settings.json upload` 를 그대로 따른다: **아동용 아니오 / 미드롤 끔 / 한국어+영어 제목 동시 등록.**
- 업로드 전 `scripts/script/check_meta.py` 로 설명란 서식·챕터·해시태그를 검사한다.

## 하지 않는 것
- 씬 이미지를 뽑지 않는다. 스토리보드를 만들지 않는다.
- 켄번스·줌·전환 효과를 넣지 않는다. **정지 화면이 이 장르의 문법이다.**
- 훅 클립을 만들지 않는다. 인트로 효과음을 넣지 않는다.
- 대본 초고를 사용자에게 보여 주지 않는다.
