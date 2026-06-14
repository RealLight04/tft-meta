# TFT 메타 분석 (KR)

Riot 공식 API로 한국 서버 상위 티어(챌린저/그랜드마스터/마스터)의 게임 데이터를 수집해
**현재 패치 기준 메타 덱 · 증강 · 챔피언 통계**를 보여주는 웹서비스입니다.

기존 사이트(tactics.tools, lolchess.gg)는 정보가 많고 복잡한 편이라,
**한국어 + 깔끔한 UI**로 핵심만 빠르게 보는 것을 목표로 합니다.

## 주요 기능

- 현재 패치 메타 덱 TOP 10 (평균 등수 · 순방률 · 1등률)
- 아이템 랭킹 (캐리 아이템 성능)
- 챔피언 랭킹
- 소환사 전적 검색 (`이름#태그` 실시간 조회)
- 6시간마다 데이터 자동 수집 (스케줄러)

> 참고: 당초 "증강 랭킹"을 계획했으나, **TFT Set 17 랭크 매치 API에는 증강(augments)
> 데이터가 포함되지 않음**을 실제 수집으로 확인했습니다. 데이터가 풍부한
> **아이템 랭킹**으로 대체했습니다.

## 기술 스택

- **백엔드:** FastAPI
- **프론트엔드:** Jinja2 템플릿 + Chart.js
- **DB:** SQLite (개발) / PostgreSQL (배포)
- **수집:** httpx + 자체 RateLimiter (개발 키 한도 준수)
- **스케줄러:** APScheduler

## 프로젝트 구조

```
tft-meta/
├── app/
│   ├── main.py          # FastAPI 라우터
│   ├── config.py        # 환경설정 (.env)
│   ├── database.py      # DB 세션
│   ├── models.py        # ORM 모델 (Match, Participant)
│   ├── riot_client.py   # Riot API 래퍼 (rate limit)
│   ├── collector.py     # 데이터 수집 파이프라인
│   ├── stats.py         # 메타 통계 계산
│   ├── scheduler.py     # 6시간 주기 자동 수집
│   └── names.py         # Riot 내부 ID → 읽기 좋은 이름
├── templates/           # base / index / summoner
├── static/style.css
├── scripts/collect.py   # 수동 수집 스크립트
└── requirements.txt
```

## 실행 방법

### 1. Riot API 키 발급

[developer.riotgames.com](https://developer.riotgames.com) 로그인 → 개발 키 발급.
**개발 키는 24시간마다 만료되므로** 매일 재발급해야 합니다.

### 2. 환경변수 설정

`.env.example`을 복사해 `.env`를 만들고 키를 넣습니다.

```bash
cp .env.example .env
# .env 파일에서 RIOT_API_KEY 수정
```

### 3. 의존성 설치

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. 데이터 수집

```bash
python -m scripts.collect
```

### 5. 서버 실행

```bash
uvicorn app.main:app --reload
```

→ http://127.0.0.1:8000

## 메타 덱 정의 방식

정확한 덱 분류(클러스터링)는 복잡하므로, MVP에서는
**가장 높이 발현된 주력 특성(trait)** 을 덱 archetype으로 보고 집계합니다.
(style → tier → 유닛 수 순으로 주력 특성 결정)

## 한계 / TODO

- 챔피언·증강 이름이 영문 ID 기반 → Data Dragon 연동으로 한글화 예정
- 덱 분류를 주력 특성 1개 → 핵심 조합 기반으로 고도화
- 아이템 조합 승률, 패치별 메타 비교 (2단계)
- PostgreSQL 전환 후 Render 배포

## 데이터 출처

Riot Games API. 본 서비스는 Riot Games가 보증하거나 후원하지 않는 비공식 서비스입니다.
