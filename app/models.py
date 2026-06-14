from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)

from .database import Base


class Match(Base):
    """수집한 매치 한 판."""

    __tablename__ = "matches"

    match_id = Column(String, primary_key=True)
    patch = Column(String, index=True)          # 예: "14.23"
    set_number = Column(Integer)                 # TFT 시즌 번호
    game_datetime = Column(BigInteger)           # 게임 시작 시각 (epoch ms)
    collected_at = Column(DateTime, default=datetime.utcnow)


class Participant(Base):
    """한 매치 안의 플레이어 1명 결과 (한 판당 8명)."""

    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"), index=True)
    patch = Column(String, index=True)           # 조회 편의를 위해 비정규화
    puuid = Column(String, index=True)
    placement = Column(Integer)                   # 최종 등수 1~8
    primary_trait = Column(String, index=True)    # 덱 archetype (주력 특성)
    augments = Column(JSON)                        # 증강 id 목록
    units = Column(JSON)                           # [{id, tier, items}]
    traits = Column(JSON)                          # [{name, tier, num, style}]
