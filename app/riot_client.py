"""Riot API 래퍼.

개발 키 rate limit(초당 20회, 2분당 100회)을 넘지 않도록
간단한 토큰 윈도우 방식의 RateLimiter를 둔다.
"""

import logging
import threading
import time
from collections import deque

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """슬라이딩 윈도우로 요청 속도를 제한한다 (스레드 안전)."""

    def __init__(self, short_limit: int = 18, long_limit: int = 95):
        # 개발 키 한도(20/1s, 100/120s)보다 살짝 낮게 잡아 여유를 둔다.
        self._short_limit = short_limit
        self._long_limit = long_limit
        self._short = deque()   # 최근 1초 요청 시각
        self._long = deque()    # 최근 120초 요청 시각
        self._lock = threading.Lock()

    def acquire(self):
        with self._lock:
            while True:
                now = time.time()
                while self._short and now - self._short[0] > 1:
                    self._short.popleft()
                while self._long and now - self._long[0] > 120:
                    self._long.popleft()

                if len(self._short) < self._short_limit and len(self._long) < self._long_limit:
                    self._short.append(now)
                    self._long.append(now)
                    return

                waits = []
                if len(self._short) >= self._short_limit:
                    waits.append(1 - (now - self._short[0]))
                if len(self._long) >= self._long_limit:
                    waits.append(120 - (now - self._long[0]))
                time.sleep(max(max(waits, default=0.05), 0.05))


_limiter = RateLimiter()


class RiotApiError(Exception):
    pass


class RiotClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.riot_api_key
        self.platform = settings.platform_routing   # kr
        self.regional = settings.regional_routing   # asia
        self._client = httpx.Client(
            timeout=15,
            headers={"X-Riot-Token": self.api_key},
        )

    def _get(self, url: str, params: dict | None = None):
        last = None
        for attempt in range(4):
            _limiter.acquire()
            resp = self._client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                retry = int(resp.headers.get("Retry-After", "5"))
                logger.warning("429 rate limit, %s초 대기", retry)
                time.sleep(retry)
                continue
            if resp.status_code in (500, 502, 503, 504):
                time.sleep(2 * (attempt + 1))
                last = resp
                continue
            # 그 외(403 키만료, 404 없음 등)는 즉시 에러
            raise RiotApiError(f"{resp.status_code} {resp.text[:200]} ({url})")
        raise RiotApiError(f"요청 실패(재시도 초과): {url} / {last}")

    # ---- 리그 (상위 티어 목록) ----
    def league(self, tier: str) -> dict:
        # tier: challenger / grandmaster / master
        url = f"https://{self.platform}.api.riotgames.com/tft/league/v1/{tier}"
        return self._get(url)

    # ---- 소환사 (summonerId -> puuid, 구 스키마 대비) ----
    def summoner_by_id(self, summoner_id: str) -> dict:
        url = f"https://{self.platform}.api.riotgames.com/tft/summoner/v1/summoners/{summoner_id}"
        return self._get(url)

    # ---- 계정 (Riot ID <-> puuid) ----
    def account_by_riot_id(self, game_name: str, tag_line: str) -> dict:
        url = (
            f"https://{self.regional}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        return self._get(url)

    def account_by_puuid(self, puuid: str) -> dict:
        url = f"https://{self.regional}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
        return self._get(url)

    # ---- 매치 ----
    def match_ids_by_puuid(self, puuid: str, count: int = 20) -> list:
        url = f"https://{self.regional}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids"
        return self._get(url, params={"count": count})

    def match(self, match_id: str) -> dict:
        url = f"https://{self.regional}.api.riotgames.com/tft/match/v1/matches/{match_id}"
        return self._get(url)

    def close(self):
        self._client.close()
