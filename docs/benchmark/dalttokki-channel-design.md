# 「달토끼 잠자리동화」 채널 설계서 (v0.1 · 2026-09-06)

벤치마크 분석: [hohosam-2026-09.md](hohosam-2026-09.md)
사용자 확정 사항: 브랜드=달토끼 / 화면=고정 1장 + 챕터 카드 / 1호=전래동화 4~7분 옴니버스,
낭독 60분 + 백색소음 120분 = 총 3시간.

---

## 1. 채널 정체성

| 항목 | 값 |
|---|---|
| 채널명 | **달토끼 잠자리동화** |
| 핸들 | `@달토끼동화` (영문 대체 `@moonrabbit-story`) |
| 마스코트 | 아기 달토끼 **「몽이」** (夢 — 꿈) |
| 한 줄 정의 | 달토끼가 들려주는 우리 옛이야기, 중간광고 없는 수면 오디오북 |
| 실질 타깃 | **아이를 재우는 부모** (아동용 설정 **하지 않음** — 벤치 §6) |
| 주력 소재 | 전래동화·옛날이야기 (1~5호 전래동화 단일) → 이후 이솝우화·창작 정서동화 |

### 채널 소개문 (초안)
```
달토끼가 들려주는 우리 옛이야기 🌙💤

아이부터 어른까지, 머리맡에 틀어두고 편안히 잠드세요.
중간광고 없이 끊기지 않습니다. 이야기가 끝나면 백색소음이 이어집니다.

문의: (이메일)
```
- `중간광고 없이 끊기지 않습니다` — 브랜드 약속. 제목·썸네일·소개문 3중 반복.
- `이야기가 끝나면 백색소음이 이어집니다` — 우리 포맷을 **명시**해 과장 시비를 원천 차단.
- `아이부터 어른까지` — 아동용 미설정과 짝을 이루는 문구.

---

## 2. 마스코트 「몽이」 디자인 락

캐릭터 일관성 3종 세트(CLAUDE.md 규칙)를 그대로 적용한다.

### 외형 lock (프롬프트에 항상 삽입)
```
A baby moon-rabbit named Mongi. Small round body, soft cream-white fur with a
faint warm ivory tint, long droopy ears with pale pink inner ear, tiny pink nose,
closed crescent-shaped sleeping eyes with soft pink cheek blush, short round tail.
Wears nothing. Always calm and sleepy. NOT a Western cartoon bunny, NOT anime style.
```
### 앵커 소품(anchorProp)
- **절구와 절굿공이** — 한국 달토끼의 유일무이한 식별자. 몽이 옆에 항상 둔다.
- 보조: 보름달, 감나무, 초가지붕, 댓돌.

### 표정 규칙
- **항상 눈을 감고 있다.** 벤치 썸네일 9편 전부가 '자는 캐릭터'였다. 이건 장르 문법이다.
- 입은 옅은 미소. 이빨 노출 금지.

---

## 3. 아트 스타일

벤치와 동일 계열 — **두툼한 파스텔 3D풍 그림책 일러스트**. 야담의 웹툰 스타일과 완전히 분리한다.

```
Thick soft pastel storybook illustration, gentle volumetric 3D-ish rendering with
rounded plush forms, warm rim light from a full moon, deep indigo-violet night sky
with soft star bokeh, cozy and calming, painterly soft edges.
NOT flat vector, NOT webtoon lineart, NOT Japanese anime, NOT photorealistic.
No text, no letters, no watermark.
```
문화 앵커(전래동화용):
```
Korean traditional village at night: thatched-roof and tiled-roof hanok,
stone wall, persimmon tree, wooden mortar. Korean, NOT Chinese, NOT Japanese.
```

### 컬러 팔레트

| 역할 | HEX | 용도 |
|---|---|---|
| 밤하늘 진함 | `#1B1B3A` | 배경 상단, 백색소음 구간 |
| 밤하늘 옅음 | `#2E1F5E` | 배경 하단 그라데이션 |
| 달빛 노랑 | `#FFD66B` | 달, 포인트 광원 |
| 카피 노랑 | `#FFE9A8` | 썸네일 핵심 문구 |
| 흰색 | `#FFFFFF` | 썸네일 보조 문구 |
| 외곽선 | `#1A1333` | 모든 썸네일 텍스트 외곽선 |
| 몽이 털 | `#FDF6EC` | 마스코트 |
| 볼터치 | `#F4B6B6` | 마스코트 |

폰트(상업 이용 무료): 썸네일 **배민 주아체(BM JUA)** — 둥글고 두껍다.
챕터 카드는 기존 `CapCut_ko_SourceHanSansKR-Medium.ttf` 재사용.

---

## 4. 화면 구성 (사용자 확정: 1장 + 챕터 카드)

```
[0:00]      인사말        ── 고정 배경 1장 (몽이 잠든 그림)
[0:01:00]   챕터 카드 3초 ── 배경 살짝 어둡게 + 이야기 제목
            이야기 1       ── 고정 배경으로 복귀
[0:06:30]   챕터 카드 3초
            이야기 2
            …  (전래동화 11~13편)
[1:00:00]   ── 페이드 아웃 ──
[1:00:00~3:00:00]  검은 화면 + 백색소음 120분
```
- 고정 배경 1장은 **썸네일 원본과 동일한 그림**을 쓴다(벤치 이솝우화 편과 동일 전략).
  텍스트만 얹으면 썸네일, 안 얹으면 본편 배경. **에셋 1장으로 둘 다 커버.**
- 챕터 카드는 기존 `scripts/render/insert_chapter_cards.py` 를 재사용한다.
- 백색소음은 기존 `channels/yadam/assets/intro,outro/sleep_noise_2h_quiet.mp3` 를 그대로 쓴다.
- **자막을 화면에 태우지 않는다**(벤치 §2). SRT는 챕터 타임스탬프 산출용으로만 쓴다.

---

## 5. 1호 영상 편성

| 항목 | 값 |
|---|---|
| 소재 | 전래동화 (해와 달이 된 오누이, 금도끼 은도끼, 혹부리 영감, 흥부와 놀부 …) |
| 단편 길이 | 4~7분 (평균 5.5분) |
| 편수 | 11~13편 + 인사말 1분 |
| 낭독 총량 | 약 60분 |
| 백색소음 | 120분 (검은 화면) |
| 총 길이 | **3시간** |
| 대본 분량 | 약 15,000자 (분당 250자 기준) |

### 제목 (안)
```
중간광고 없는 3시간 잠자리동화 🌙😴💤 엄마가 읽어주는 전래동화 12편 + 수면 백색소음
```
영문 제목(다국어 등록용):
```
3 Hours of Korean Folk Tales 🌙😴💤 Bedtime Stories for Kids + Sleep White Noise
```

### 설명란 서식
```
🌙 오늘의 옛이야기
0:00:00 인삿말
0:01:02 해와 달이 된 오누이
0:07:15 금도끼 은도끼
…
1:00:00 🌊 수면 백색소음 (2시간)

🎙️ 각색 및 낭독 : 달토끼
⭐ 기획 및 제작 : (이름)

#오디오북 #달토끼 #전래동화

© 2026 달토끼 잠자리동화. All Rights Reserved.
```

### 태그 — 고정 13개 + 주제 5개
고정:
`달토끼 · 잠자리동화 · 동화책읽어주기 · 잠잘때듣는동화 · 어린이동화 · 수면동화 · 자장가동화 · 꿀잠동화 · 엄마동화 · 동화책읽어주는엄마 · 소곤소곤잠자리동화 · 잠오는영상 · 백색소음`
1호 주제:
`전래동화 · 옛날이야기 · 민담 · 설화 · 어린이동화책읽어주기`

### 썸네일 문안
```
(작게)  중간광고 없는
(크게)  전래동화
(크게)  3시간
(작게)  어린이 수면동화
```
레이아웃: 좌측 텍스트 / 우측 몽이(절구 옆에서 잠듦). 다음 편은 좌우 반전.

### 업로드 설정
- **아동용: 아니오** (댓글·알림·맞춤광고 유지 — 벤치 §6)
- **미드롤 광고: 끔** — 브랜드 약속
- 다국어 제목·설명 동시 등록(한국어 + 영어)

---

## 6. 파이프라인 개조 계획

새 채널 `channels/dalttokki/` 를 `channels/_template/` 복사로 만든다.

### 제거 / 우회하는 단계
| 기존 단계 | 처리 |
|---|---|
| STORYBOARD (`storyboard/build.py`) | **건너뜀** — 씬 분할 자체가 없다 |
| SCENE_IMG | **건너뜀** — 배경 1장으로 대체 |
| SCENE_TIMING | **건너뜀** |
| 켄번스(`capcut.ken_burns`) | **끔** — 정지 화면이 이 장르의 문법 |
| VEO_HOOK | **끔** — 수면 콘텐츠에 훅 클립은 역효과 |
| ATTACH_HOOK | **끔** |

### 유지 / 재사용
- `assets/background.py` → 고정 배경 1장 생성
- `render/insert_chapter_cards.py` → 챕터 카드
- `render/attach_outro.py` + `sleep_noise_2h_quiet.mp3` → 백색소음 구간
- `render/capcut_export.py` → 최종 드래프트
- `script/check_meta.py` → 설명란 검사(챕터 개수 규격만 개정)
- `upload/upload.py` → 업로드

### 신규로 만든 것 (2026-09-06 완료)
| 파일 | 하는 일 |
|---|---|
| `scripts/render/build_sleep_video.py` | 키비주얼 1장 + 3초 챕터 카드 + 낭독 + 검은 화면 백색소음 → 최종 mp4 |
| `scripts/assets/make_thumbnail.py` | 벤치 썸네일 공식(4단 문안 · 좌우 2분할) 합성 |
| `scripts/assets/brand_export.py` | 프로필 800x800 · 배너 2560x1440 규격 내보내기 |
| `scripts/script/check_story.py` | ★단편 대본 게이트 — 분량·캐스팅·화자수·문장·금지어 |
| `scripts/tts/dialogue_tts.py` | ElevenLabs Text-to-Dialogue — 화자별 자동 캐스팅 + 챕터 타임스탬프 |
| `.claude/skills/sleep-pd/SKILL.md` | 이 채널 전용 파이프라인 스킬(상태 감지 축소판) |

`validate_script.py`(야담 45분 밴드)는 **손대지 않았다** — 이 채널은 `check_story.py` 를 따로 쓴다.
야담 검사기를 고치면 야담 쪽이 깨진다.

### TTS 트랙 변경
현행 Vrew 수동 게이트를 **ElevenLabs v3 Text-to-Dialogue**로 교체 검토(아래 §7).
`convert-with-timestamps` 가 문자 단위 타임스탬프를 주므로
**챕터 타임스탬프가 자동 산출**되고 Vrew 수동 게이트와 Whisper 정렬이 함께 사라진다.

---

## 7. TTS — 대사마다 목소리를 바꾸는 방법

### ★먼저 짚을 것: 벤치마크는 AI가 아닐 가능성이 높다
호호샘 소개문은 `호호샘의 따뜻한 목소리로`, 크레딧은 `각색 및 구연 : 호호샘` 이다.
**사람이 직접 구연한 것**으로 보는 게 타당하다. 그래서 자연스럽다.
AI로 그 수준을 노린다면 아래를 쓴다.

### 비용 비교 (편당 낭독 60분 · 약 15,000자 기준)

| 서비스 | 요금제 | 제공량 | **편당 비용** | 다화자 | 타임스탬프 |
|---|---|---|---:|---|---|
| **ElevenLabs v3** | Creator $22/월 | 100,000 크레딧 | **약 $3.3 (4,700원)** | **화자 수 무제한** | ✅ 문자 단위 |
| ElevenLabs v3 | Pro $99/월 | 500,000 크레딧 | 약 $3.0 | 무제한 | ✅ |
| **Supertone Play** (Sona 2) | Creator $10.49/월 | 100,000 (≈150분) | 약 $4.2 (6,000원) | 화자별 개별 생성 | ❌ |
| Supertone Play | Pro $55.99/월 | 500,000 (≈800분) | 약 $4.2 | 〃 | ❌ |
| **Typecast** | Business ₩99,000/월 | ≈410분 | 약 **14,500원** | 700+ 캐릭터 | ❌ |
| Typecast | Pro ₩39,000/월 | ≈150분 | 약 15,600원 | 〃 | ❌ |
| **Gemini TTS** (3.1 Flash) | 종량 $20/1M 오디오토큰 | — | **약 $1.8 (2,500원)** | 요청당 최대 2명 | ❌ |
| Gemini TTS (3.5 Flash) | 종량 $6/1M | — | 약 $0.54 (750원) | 2명 | ❌ |
| Vrew (현행) | 구독 | — | 저렴 | 수동 배정 | SRT 제공 |

> 크레딧 소모율은 모델·언어에 따라 달라진다. 위 수치는 **1크레딧 ≈ 1자** 가정 추정이며
> 첫 편에서 반드시 실측한 뒤 이 표를 갱신할 것.

### 권장안

**1순위 — ElevenLabs v3 `Text to Dialogue`**
- 화자 수 **제한 없음**. 발화마다 `voice_id` 를 지정한다.
  → 나레이션은 엄마 목소리, 호랑이는 굵은 목소리, 오누이는 아이 목소리로 갈린다.
- `[whispers]` `[sleepy]` `[gently]` 같은 **오디오 태그**로 감정을 지시한다. 수면동화에 정확히 맞다.
- `convert-with-timestamps` → 챕터 타임스탬프 자동. **Vrew 수동 게이트가 사라진다.**
- 요청당 2,000자 제한 → 청킹 필요. `generate_tts.py` 에 이미 청킹 로직이 있다.
- **이미 코드가 붙어 있다** — `scripts/tts/generate_tts.py` 가 `eleven_v3` + `with-timestamps` 를 쓴다.
  Text-to-Dialogue 엔드포인트로 바꾸는 정도의 개조면 된다.
- 약점: 한국어 억양이 간혹 어색할 수 있다.

**2순위 — Supertone Play (Sona 2)**
- 한국어 특화 품질은 국내 최상위. 성우 연기 톤이 필요하면 여기.
- 화자별로 따로 생성해 이어붙여야 하고 타임스탬프가 없다 → Whisper 정렬 필요(폴백 이미 존재).

**비용 최소 트랙 — Gemini TTS**
- 편당 2,500원. 다화자 2명 제한은 **화자별 분할 생성 후 concat** 으로 우회 가능.
- 품질이 성우급은 아니다. 백색소음이 절반인 우리 포맷에서는 충분할 수도 있다.

### ★확정된 사실 (2026-09-06 공식 문서 확인 + 실측)

**Q. 대사마다 목소리를 내가 하나씩 골라야 하나?** → **아니다.**
`POST /v1/text-to-dialogue/convert-with-timestamps` 는 `inputs: [{text, voice_id}]` 를 받는다.
즉 **발화 단위로 voice_id 를 지정**하는데, 그 지정을 사람이 아니라 **파이프라인이 대본에서 읽어 채운다.**

```
대본            채스팅 줄                        voices.json          API
호랑이: 떡 …  →  호랑이=호랑이  →  "호랑이": {voice_id: "xxx"}  →  {text:"떡 …", voice_id:"xxx"}
```
대본에 `화자:` 만 적어 두면 끝이다. Vrew처럼 구간마다 클릭할 일이 없다.
구현: `scripts/tts/dialogue_tts.py` · 규격: `channels/dalttokki/config/script-guide.md` §6

**API 제한** — 요청당 고유 voice_id **10개**, 텍스트 합계 **2,000자**. 스크립트가 자동으로 청킹한다.
한 편이 1,000~1,300자라 **이야기 하나가 요청 하나**로 끝난다.

**비용 (실측 기준)** — `eleven_v3` = **1 크레딧/자**.
`dialogue_tts.py --dry-run` 으로 20편 전체를 계산한 결과:

| 항목 | 값 |
|---|---|
| 20편 합계 | 약 24,700자 = 24,700 크레딧 |
| Creator($22 / 100,000) 기준 | **약 $5.4 (약 7,700원)** — 20편 전부 |
| 편당(약 1,200자) | 약 $0.27 (약 380원) |
| 영상 1편(이야기 12편 + 인사말) | 약 15,000 크레딧 = **약 $3.3 (약 4,700원)** |
| Creator 한 달 한도로 | 영상 **6편** 가능 |

> 크레딧 소모율은 실제 청구에서 다를 수 있다. 1호 제작 후 `CREDITS_PER_CHAR` 를 실측값으로 고칠 것.

**감정 지시** — 대사 앞 `[whispers]` `[sleepy]` `[gently]` 같은 오디오 태그가 그대로 전달된다.
우리 대본은 `[낮고 느리게]` `[아주 작게]` 형식으로 이미 전부 붙여 두었다.

### 결정 절차
1호 대본 중 **대사가 많은 한 편(예: 해와 달이 된 오누이) 3분 분량**을
ElevenLabs v3 / Supertone Sona 2 / Gemini TTS 세 곳에서 각각 뽑아 **블라인드로 듣고 고른다.**
비용 차이는 편당 최대 12,000원 수준이라, 품질이 결정 변수다.

---

## 8. 다음 할 일

1. [ ] 채널명·핸들 중복 확인 후 YouTube 채널 개설
2. [ ] 몽이 턴어라운드 + 고정 배경 1장 생성 (`gemini` 이미지 엔진)
3. [ ] 프로필/배너 제작
4. [ ] TTS 3사 블라인드 A/B (3분 샘플)
5. [ ] `channels/dalttokki/` 생성 + settings/style/workflow 작성
6. [ ] 1호 대본 (전래동화 12편, 15,000자)
7. [ ] `build_static_video.py` · `make_thumbnail.py` 작성
8. [ ] 1호 제작 → 비공개 업로드 → 지표 확인
