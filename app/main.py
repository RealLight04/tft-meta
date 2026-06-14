import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import names, stats
from .collector import primary_trait
from .config import settings
from .database import get_db, init_db
from .riot_client import RiotClient
from .scheduler import shutdown_scheduler, start_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.enable_scheduler and settings.riot_api_key:
        start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="TFT 메타 분석", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Riot 개발자 포털의 사이트 소유권 인증 토큰.
# Riot이 https://(배포주소)/riot.txt 를 읽어 이 값과 대조한다.
RIOT_VERIFICATION_TOKEN = "9d4ca169-2c15-49c9-bb29-e4d2330532ff"


@app.get("/riot.txt", response_class=PlainTextResponse)
def riot_txt():
    return RIOT_VERIFICATION_TOKEN


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    patch = stats.current_patch(db)
    data = stats.get_overview(db, patch) if patch else None
    return templates.TemplateResponse(
        request,
        "index.html",
        {"patch": patch, "data": data},
    )


@app.get("/summoner", response_class=HTMLResponse)
def summoner(request: Request, q: str | None = Query(None)):
    result = None
    error = None
    if q:
        if not settings.riot_api_key:
            error = "서버에 Riot API 키가 설정되지 않았습니다."
        else:
            try:
                result = lookup_summoner(q)
            except Exception as e:
                error = f"조회 실패: {e}"
    return templates.TemplateResponse(
        request,
        "summoner.html",
        {"q": q, "result": result, "error": error},
    )


def lookup_summoner(riot_id: str) -> dict:
    """'이름#태그'로 최근 전적을 실시간 조회한다."""
    if "#" in riot_id:
        game_name, tag = riot_id.split("#", 1)
    else:
        game_name, tag = riot_id, "KR1"  # 태그 생략 시 KR1 기본값
    game_name, tag = game_name.strip(), tag.strip()

    client = RiotClient()
    try:
        account = client.account_by_riot_id(game_name, tag)
        puuid = account["puuid"]
        match_ids = client.match_ids_by_puuid(puuid, 10)

        games = []
        for mid in match_ids:
            info = client.match(mid).get("info", {})
            me = next(
                (p for p in info.get("participants", []) if p.get("puuid") == puuid),
                None,
            )
            if not me:
                continue
            trait = primary_trait(me.get("traits", []))
            games.append({
                "placement": me.get("placement"),
                "deck": names.clean_trait(trait) if trait else "-",
                "units": [
                    {"name": names.clean_unit(u.get("character_id")), "tier": u.get("tier")}
                    for u in me.get("units", [])
                ],
                "augments": [names.clean_augment(a) for a in me.get("augments", [])],
            })

        avg = round(sum(g["placement"] for g in games) / len(games), 2) if games else None
        return {
            "name": f"{account.get('gameName')}#{account.get('tagLine')}",
            "avg": avg,
            "games": games,
        }
    finally:
        client.close()
