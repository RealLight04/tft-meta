"""DB에 저장된 매치 데이터로 메타 통계를 계산한다.

JSON 컬럼(augments/units)을 다뤄야 하므로 SQL 집계 대신
파이썬에서 집계한다. MVP 규모(수백 매치)에서는 충분히 빠르다.
"""

from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import names
from .config import settings
from .models import Participant

# 전투 성능과 무관한 아이템(빈 가방, 컴포넌트)은 통계에서 제외한다.
EXCLUDED_ITEM_MARKERS = ("EmptyBag", "Spatula", "FryingPan")


def _is_real_item(item_id: str) -> bool:
    return not any(marker in item_id for marker in EXCLUDED_ITEM_MARKERS)


def current_patch(db: Session) -> str | None:
    """표본이 가장 많은 패치를 '현재 패치'로 본다."""
    row = (
        db.query(Participant.patch, func.count(Participant.id))
        .group_by(Participant.patch)
        .order_by(func.count(Participant.id).desc())
        .first()
    )
    return row[0] if row else None


def deck_archetype(traits: list) -> str | None:
    """저장된 traits(JSON)에서 덱 주력 특성을 재계산한다.

    collector.primary_trait과 동일한 기준이지만 저장 포맷(name/tier/num/style)을 쓴다.
    이미 수집된 데이터에도 개선된 로직을 적용하기 위해 통계 시점에 다시 계산한다.
    """
    active = [t for t in (traits or []) if (t.get("tier") or 0) >= 1]
    synergy = [t for t in active if (t.get("num") or 0) >= 2] or active
    if not synergy:
        return None
    best = max(
        synergy,
        key=lambda t: (t.get("style") or 0, t.get("tier") or 0, t.get("num") or 0),
    )
    return best.get("name")


def _finalize(stats: dict, clean, min_n: int, limit: int) -> list:
    """집계 dict -> 평균 등수 오름차순 정렬된 리스트."""
    out = []
    for key, s in stats.items():
        if s["count"] < min_n:
            continue
        out.append({
            "name": clean(key),
            "count": s["count"],
            "avg": round(s["sum"] / s["count"], 2),
            "top4_rate": round(s["top4"] / s["count"] * 100, 1),
            "win_rate": round(s["win"] / s["count"] * 100, 1),
        })
    out.sort(key=lambda x: x["avg"])
    return out[:limit]


def get_overview(db: Session, patch: str) -> dict:
    """현재 패치의 메타 덱 / 증강 / 챔피언 통계를 한 번에 계산한다."""
    parts = db.query(Participant).filter(Participant.patch == patch).all()

    def new_bucket():
        return {"count": 0, "sum": 0, "top4": 0, "win": 0}

    decks = defaultdict(new_bucket)
    items = defaultdict(new_bucket)
    units = defaultdict(new_bucket)

    def add(bucket, placement):
        bucket["count"] += 1
        bucket["sum"] += placement
        if placement <= 4:
            bucket["top4"] += 1
        if placement == 1:
            bucket["win"] += 1

    for p in parts:
        placement = p.placement or 8
        deck = deck_archetype(p.traits)
        if deck:
            add(decks[deck], placement)
        for u in (p.units or []):
            uid = u.get("id")
            if uid:
                add(units[uid], placement)
            for item in (u.get("items") or []):
                if _is_real_item(item):
                    add(items[item], placement)

    min_n = settings.min_sample_size
    return {
        "matches": len({p.match_id for p in parts}),
        "participants": len(parts),
        "decks": _finalize(decks, names.clean_trait, min_n, 10),
        "item_ranking": _finalize(items, names.clean_item, min_n, 15),
        "units": _finalize(units, names.clean_unit, min_n, 15),
    }
