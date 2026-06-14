"""Community Dragon에서 TFT 한글 이름표를 받아 app/data/names_ko.json 으로 저장한다.

TFT는 Data Dragon보다 Community Dragon이 apiName(=매치 API의 character_id/trait/item ID)
기준으로 정확하다. latest 엔드포인트라 현재 세트(예: Set 17.5)가 반영된다.
모든 세트를 합쳐 저장하므로 이전 세트에서 넘어온 유닛도 커버된다.

사용법: python -m scripts.fetch_names
"""

import json
import os

import httpx

OUT = os.path.join(os.path.dirname(__file__), "..", "app", "data", "names_ko.json")
URL = "https://raw.communitydragon.org/latest/cdragon/tft/ko_kr.json"


def fetch():
    with httpx.Client(timeout=60) as c:
        data = c.get(URL).json()

    items = {it["apiName"]: it["name"] for it in data.get("items", []) if it.get("apiName")}

    champions, traits = {}, {}
    # 신형: setData(모든 세트 배열) / 구형: sets(딕셔너리) 둘 다 처리
    set_groups = list(data.get("setData") or [])
    set_groups += list((data.get("sets") or {}).values())
    for grp in set_groups:
        for ch in grp.get("champions", []):
            if ch.get("apiName"):
                champions[ch["apiName"]] = ch.get("name", ch["apiName"])
        for tr in grp.get("traits", []):
            if tr.get("apiName"):
                traits[tr["apiName"]] = tr.get("name", tr["apiName"])

    result = {
        "_source": "communitydragon-latest",
        "champions": champions,
        "traits": traits,
        "items": items,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"챔피언 {len(champions)} / 특성 {len(traits)} / 아이템 {len(items)}")
    print("저장 완료:", os.path.abspath(OUT))


if __name__ == "__main__":
    fetch()
