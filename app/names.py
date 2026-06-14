"""Riot API의 내부 ID를 사람이 읽을 수 있는 이름으로 정리한다.

예) "TFT11_Ahri" -> "Ahri", "TFT11_Augment_PandorasItems" -> "Pandoras Items"
정확한 한글 현지화는 Data Dragon 연동이 필요하므로 MVP에서는 영문 정리만 한다.
"""

import re


def _humanize(raw: str) -> str:
    # CamelCase -> "Camel Case", 언더스코어 -> 공백
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", raw)
    s = s.replace("_", " ").strip()
    return s or raw


def clean_unit(character_id: str | None) -> str:
    if not character_id:
        return "?"
    name = re.sub(r"^TFT\d*_", "", character_id)
    return _humanize(name)


def clean_trait(trait_id: str | None) -> str:
    if not trait_id:
        return "?"
    name = re.sub(r"^TFT\d*_", "", trait_id)
    return _humanize(name)


def clean_augment(augment_id: str | None) -> str:
    if not augment_id:
        return "?"
    name = re.sub(r"^TFT\d*_Augment_", "", augment_id)
    name = re.sub(r"^TFT\d*_", "", name)
    return _humanize(name)
