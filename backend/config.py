import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    monitor_url: str
    monitor_selector: str
    check_interval_minutes: int
    user_agent: str
    request_timeout_seconds: int
    random_delay_max_seconds: int
    max_consecutive_failures: int
    expo_push_url: str


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


def load_settings() -> Settings:
    check_interval_minutes = _get_int_env("CHECK_INTERVAL_MINUTES", 60)
    if check_interval_minutes < 60:
        raise ValueError("CHECK_INTERVAL_MINUTES must be >= 60.")

    return Settings(
        database_url=os.getenv(
            "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tdr_notify"
        ),
        monitor_url=os.getenv(
            "MONITOR_URL", "https://www.tokyodisneyresort.jp/tdr/news/update/"
        ),
        monitor_selector=os.getenv("MONITOR_SELECTOR", ".linkList6.listUpdate ul"),
        check_interval_minutes=check_interval_minutes,
        user_agent=os.getenv("USER_AGENT", "DisneyMonitorBot/1.0"),
        request_timeout_seconds=_get_int_env("REQUEST_TIMEOUT_SECONDS", 5),
        random_delay_max_seconds=_get_int_env("RANDOM_DELAY_MAX_SECONDS", 30),
        max_consecutive_failures=_get_int_env("MAX_CONSECUTIVE_FAILURES", 3),
        expo_push_url=os.getenv("EXPO_PUSH_URL", "https://exp.host/--/api/v2/push/send"),
    )


settings = load_settings()
