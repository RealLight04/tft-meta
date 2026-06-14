from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수(.env)에서 설정을 읽어온다."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    riot_api_key: str = ""
    database_url: str = "sqlite:///./tft.db"

    # 라우팅: 리그/소환사는 platform(kr), 매치/계정은 regional(asia)
    platform_routing: str = "kr"
    regional_routing: str = "asia"

    # 데이터 수집 파라미터 (개발 키 rate limit 고려해 보수적으로)
    collect_summoner_count: int = 40       # 상위 소환사 몇 명까지 수집할지
    collect_matches_per_summoner: int = 8  # 소환사당 최근 몇 게임을 볼지
    min_sample_size: int = 20              # 통계에 포함할 최소 표본 수

    enable_scheduler: bool = False         # True면 6시간마다 자동 수집


settings = Settings()
