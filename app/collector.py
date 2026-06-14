"""Riot API에서 상위 티어 매치를 수집해 DB에 저장한다."""

import logging

from .config import settings
from .database import SessionLocal, init_db
from .models import Match, Participant
from .riot_client import RiotClient

logger = logging.getLogger(__name__)


def parse_patch(game_version: str) -> str:
    """'Version 14.23.643.9418 (...)' -> '14.23'"""
    try:
        v = game_version.split("Version ")[-1]
        parts = v.split(".")
        return f"{parts[0]}.{parts[1]}"
    except Exception:
        return game_version or "unknown"


def primary_trait(traits: list) -> str | None:
    """덱 archetype 추정: 활성화된 특성 중 가장 높이 발현된 것을 주력으로 본다.

    style(브론즈<실버<골드<프리즘) -> tier_current -> num_units 순으로 비교.
    """
    active = [t for t in (traits or []) if t.get("tier_current", 0) >= 1]
    if not active:
        return None
    best = max(
        active,
        key=lambda t: (
            t.get("style", 0),
            t.get("tier_current", 0),
            t.get("num_units", 0),
        ),
    )
    return best.get("name")


def collect(api_key: str | None = None) -> dict:
    """전체 수집 파이프라인. 수집 요약 dict를 반환한다."""
    init_db()
    client = RiotClient(api_key)
    db = SessionLocal()
    summary = {"summoners": 0, "match_ids": 0, "new_matches": 0}

    try:
        # 1. 상위 티어 소환사 puuid 수집
        puuids: list[str] = []
        for tier in ("challenger", "grandmaster", "master"):
            if len(puuids) >= settings.collect_summoner_count:
                break
            try:
                data = client.league(tier)
            except Exception as e:
                logger.warning("league %s 실패: %s", tier, e)
                continue
            entries = data.get("entries", [])
            entries.sort(key=lambda e: e.get("leaguePoints", 0), reverse=True)
            for entry in entries:
                if len(puuids) >= settings.collect_summoner_count:
                    break
                puuid = entry.get("puuid")
                # 구 스키마(puuid 없음) 대비: summonerId로 한 번 더 조회
                if not puuid and entry.get("summonerId"):
                    try:
                        puuid = client.summoner_by_id(entry["summonerId"]).get("puuid")
                    except Exception:
                        puuid = None
                if puuid:
                    puuids.append(puuid)
        summary["summoners"] = len(puuids)
        logger.info("소환사 %d명 수집", len(puuids))

        # 2. 매치 ID 수집 (중복 제거)
        match_ids: set[str] = set()
        for puuid in puuids:
            try:
                ids = client.match_ids_by_puuid(puuid, settings.collect_matches_per_summoner)
                match_ids.update(ids)
            except Exception as e:
                logger.warning("match ids 실패: %s", e)
        summary["match_ids"] = len(match_ids)
        logger.info("매치 ID %d개 수집", len(match_ids))

        # 3. 이미 저장된 매치는 건너뛴다
        existing = {row[0] for row in db.query(Match.match_id).all()}
        to_fetch = [mid for mid in match_ids if mid not in existing]
        logger.info("신규 매치 %d개 저장 시작", len(to_fetch))

        # 4. 매치 상세 수집 및 저장
        for mid in to_fetch:
            try:
                data = client.match(mid)
            except Exception as e:
                logger.warning("match %s 실패: %s", mid, e)
                continue

            info = data.get("info", {})
            patch = parse_patch(info.get("game_version", ""))

            db.add(Match(
                match_id=mid,
                patch=patch,
                set_number=info.get("tft_set_number"),
                game_datetime=info.get("game_datetime"),
            ))

            for p in info.get("participants", []):
                units = [
                    {
                        "id": u.get("character_id"),
                        "tier": u.get("tier"),
                        "items": u.get("itemNames", []),
                    }
                    for u in p.get("units", [])
                ]
                traits = [
                    {
                        "name": t.get("name"),
                        "tier": t.get("tier_current"),
                        "num": t.get("num_units"),
                        "style": t.get("style"),
                    }
                    for t in p.get("traits", [])
                ]
                db.add(Participant(
                    match_id=mid,
                    patch=patch,
                    puuid=p.get("puuid"),
                    placement=p.get("placement"),
                    primary_trait=primary_trait(p.get("traits", [])),
                    augments=p.get("augments", []),
                    units=units,
                    traits=traits,
                ))

            db.commit()
            summary["new_matches"] += 1

        logger.info("수집 완료: %s", summary)
        return summary
    finally:
        db.close()
        client.close()
