# TFT 메타 웹서비스 요구사항 정의서

## 서비스 개요

Riot 공식 API로 한국 서버 상위 티어(챌린저/그랜드마스터/마스터) 게임 데이터를 수집해
현재 패치 기준 메타 덱, 증강 승률을 보여주는 웹서비스.

**차별화 포인트:** 기존 사이트(tactics.tools, lolchess.gg)는 정보가 너무 많고 복잡함 → 한국어 + 깔끔한 UI로 승부

---

## 제약사항

| 항목 | 내용 |
|---|---|
| Riot API 개발 키 | 100요청/2분 제한, Riot 심사 전까지 사용 |
| 프로덕션 키 | Riot 승인 필요 (심사 기간 2~4주) |
| 수집 가능 티어 | 챌린저 / 그랜드마스터 / 마스터만 |
| 패치 주기 | 약 2주마다 메타 변경 → 현재 패치 데이터만 표시 |
| 경쟁 서비스 | tactics.tools, lolchess.gg, metatft.com |

---

## 기능 요구사항

### MVP (1단계 - 반드시 구현)

- [ ] 현재 패치 기준 메타 덱 TOP 10 (평균 순위 기준)
- [ ] 증강(Augment) 승률 랭킹
- [ ] 소환사명 검색 → 최근 전적 요약 (순위, 덱 구성)
- [ ] 6시간마다 데이터 자동 수집 및 갱신

### 2단계 (여유 있을 때)

- [ ] 아이템 조합 승률 랭킹
- [ ] 덱 상세 페이지 (최적 챔피언 성 수, 아이템 추천)
- [ ] 패치별 메타 변화 비교

### 3단계 (선택)

- [ ] 챔피언 시너지 조합 분석
- [ ] 증강 픽률 vs 승률 2차원 차트

---

## 기술 스택

| 역할 | 기술 | 이유 |
|---|---|---|
| 백엔드 | FastAPI | finance-tracker에서 이미 경험 있음 |
| 프론트엔드 | Jinja2 + Chart.js | React는 오버킬, Python으로 서버사이드 렌더링 |
| DB | SQLite (개발) → PostgreSQL (배포) | 수집 데이터 저장 |
| 스케줄러 | APScheduler | 주기적 데이터 수집 자동화 |
| 배포 | Render | 이미 경험 있음 |

---

## 데이터 흐름

```
Riot API
  │
  ├─ 1. 챌린저/그마/마스터 소환사 목록 수집
  ├─ 2. 각 소환사 최근 20게임 매치 ID 수집
  ├─ 3. 매치 상세 데이터 수집 (덱 구성, 증강, 아이템, 최종 순위)
  │
  ↓
DB 저장 (matches, augments, units 테이블)
  │
  ↓
통계 계산 (평균 순위, 승률, 픽률)
  │
  ↓
FastAPI → Jinja2 템플릿 → 브라우저
```

---

## DB 테이블 설계 (초안)

### matches
| 컬럼 | 타입 | 설명 |
|---|---|---|
| match_id | TEXT PK | Riot 매치 ID |
| patch | TEXT | 패치 버전 (예: 14.10) |
| collected_at | DATETIME | 수집 시각 |

### placements (게임 내 개인 결과)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | INT PK | |
| match_id | TEXT FK | |
| placement | INT | 최종 순위 (1~8) |
| augments | TEXT | 선택한 증강 목록 (JSON) |
| units | TEXT | 배치한 챔피언 목록 (JSON) |

---

## 화면 구성 (페이지)

| 페이지 | URL | 내용 |
|---|---|---|
| 메인 | `/` | 메타 덱 TOP 10, 증강 랭킹 |
| 전적 검색 | `/summoner/{name}` | 소환사 최근 20게임 요약 |
| 덱 상세 | `/deck/{id}` | 덱 구성 상세 정보 (2단계) |

---

## 개발 순서

1. Riot API 키 발급 + 데이터 수집 스크립트 작성
2. DB 모델 설계 및 저장 로직
3. 통계 계산 로직 (평균 순위, 증강 승률)
4. FastAPI 라우터 + Jinja2 템플릿 기본 화면
5. Chart.js로 시각화
6. APScheduler로 자동 수집 연결
7. Render 배포

---

## 참고

- Riot API 문서: https://developer.riotgames.com/apis
- TFT 관련 엔드포인트: `/tft/league/v1`, `/tft/match/v1`, `/tft/summoner/v1`
- 한국 서버 리전 코드: `kr` (소환사), `asia` (매치 데이터)
