"""Riot 내부 ID를 한글 이름으로 변환한다.

Community Dragon에서 받은 app/data/names_ko.json(scripts.fetch_names)을 먼저 쓰고,
매핑에 없는 ID는 영문 ID를 정리(_humanize)해서 보여준다.
"""

import json
import os
import re

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "names_ko.json")

try:
    with open(_DATA_PATH, encoding="utf-8") as f:
        _NAMES = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    _NAMES = {}

_CHAMPS = _NAMES.get("champions", {})
_TRAITS = _NAMES.get("traits", {})
_ITEMS = _NAMES.get("items", {})


def _humanize(raw: str) -> str:
    # CamelCase -> "Camel Case", 언더스코어 -> 공백
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", raw)
    s = s.replace("_", " ").strip()
    return s or raw


def clean_unit(character_id: str | None) -> str:
    if not character_id:
        return "?"
    if character_id in _CHAMPS:
        return _CHAMPS[character_id]
    return _humanize(re.sub(r"^TFT\d*_", "", character_id))


def clean_trait(trait_id: str | None) -> str:
    if not trait_id:
        return "?"
    if trait_id in _TRAITS:
        return _TRAITS[trait_id]
    return _humanize(re.sub(r"^TFT\d*_", "", trait_id))


def clean_item(item_id: str | None) -> str:
    if not item_id:
        return "?"
    if item_id in _ITEMS:
        return _ITEMS[item_id]
    name = re.sub(r"^TFT\d*_Item_", "", item_id)
    name = re.sub(r"^TFT\d*_", "", name)
    return _humanize(name)


def clean_augment(augment_id: str | None) -> str:
    if not augment_id:
        return "?"
    name = re.sub(r"^TFT\d*_Augment_", "", augment_id)
    name = re.sub(r"^TFT\d*_", "", name)
    return _humanize(name)
