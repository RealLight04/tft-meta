"""UI/통계 동작 확인용 가짜(샘플) 데이터 생성기.

Riot API 키 없이도 메타 화면이 어떻게 보이는지 확인하기 위한 개발용 도구다.
실제 데이터가 아니므로 운영에는 쓰지 않는다.

사용법: python -m scripts.seed_mock
"""

import random

from app.database import SessionLocal, init_db
from app.models import Match, Participant

PATCH = "14.23"

# 그럴듯한 Set 트레이트 / 챔피언 / 증강 ID (이름 정리 유틸이 'TFT14_' 접두어를 떼어준다)
TRAITS = [
    "TFT14_Vanguard", "TFT14_Sorcerer", "TFT14_Bruiser", "TFT14_Sniper",
    "TFT14_Assassin", "TFT14_Guardian", "TFT14_Mystic", "TFT14_Rebel",
    "TFT14_Duelist", "TFT14_Invoker", "TFT14_Pyro", "TFT14_Frost",
]
UNITS = [
    "TFT14_Ahri", "TFT14_Garen", "TFT14_Jinx", "TFT14_Ekko", "TFT14_Yasuo",
    "TFT14_Lux", "TFT14_Zed", "TFT14_Leona", "TFT14_Morgana", "TFT14_Vi",
    "TFT14_Caitlyn", "TFT14_Sona", "TFT14_Sett", "TFT14_Kaisa", "TFT14_Viego",
]
AUGMENTS = [
    "TFT14_Augment_PandorasItems", "TFT14_Augment_Cybernetic", "TFT14_Augment_BuiltDifferent",
    "TFT14_Augment_TraitTracker", "TFT14_Augment_RichGetRicher", "TFT14_Augment_Ascension",
    "TFT14_Augment_PortableForge", "TFT14_Augment_ThrillOfTheHunt", "TFT14_Augment_Recombobulator",
    "TFT14_Augment_HealingOrbs", "TFT14_Augment_CalculatedLoss", "TFT14_Augment_FirstAidKit",
]

# 일부 요소에 '강함' 가중치를 줘서 평균 등수가 자연스럽게 갈리게 한다.
STRONG_TRAITS = {"TFT14_Sorcerer", "TFT14_Vanguard", "TFT14_Assassin"}
STRONG_UNITS = {"TFT14_Ahri", "TFT14_Jinx", "TFT14_Kaisa"}
STRONG_AUGMENTS = {"TFT14_Augment_PandorasItems", "TFT14_Augment_BuiltDifferent"}


def weighted_placement(is_strong: bool) -> int:
    """강한 조합이면 낮은 등수(좋음)가 더 자주 나오게."""
    if is_strong:
        return random.choices(range(1, 9), weights=[5, 5, 4, 4, 2, 2, 1, 1])[0]
    return random.choices(range(1, 9), weights=[1, 1, 2, 2, 3, 3, 4, 4])[0]


def make_participant(match_id: str) -> Participant:
    trait = random.choice(TRAITS)
    units_ids = random.sample(UNITS, k=random.randint(6, 8))
    augs = random.sample(AUGMENTS, k=3)

    is_strong = (
        trait in STRONG_TRAITS
        or any(u in STRONG_UNITS for u in units_ids)
        or any(a in STRONG_AUGMENTS for a in augs)
    )
    placement = weighted_placement(is_strong)

    units = [
        {"id": u, "tier": random.choices([1, 2, 3], weights=[5, 4, 1])[0], "items": []}
        for u in units_ids
    ]
    traits = [{"name": trait, "tier": 3, "num": 4, "style": 3}]

    return Participant(
        match_id=match_id,
        patch=PATCH,
        puuid=f"mock-{random.randint(1, 999999)}",
        placement=placement,
        primary_trait=trait,
        augments=augs,
        units=units,
        traits=traits,
    )


def seed(num_matches: int = 250):
    init_db()
    db = SessionLocal()
    try:
        for i in range(num_matches):
            mid = f"MOCK_{i:05d}"
            if db.get(Match, mid):
                continue
            db.add(Match(match_id=mid, patch=PATCH, set_number=14, game_datetime=0))
            for _ in range(8):
                db.add(make_participant(mid))
        db.commit()
        print(f"가짜 데이터 {num_matches}매치 생성 완료 (patch {PATCH})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
