import asyncio
import logging
import random
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from config import Settings
from models import MonitorState, User
from notifier import send_bulk_notifications
from scraper import get_section_hash, is_allowed_by_robots

logger = logging.getLogger(__name__)


class MonitorScheduler:
    def __init__(self, session_factory: async_sessionmaker, settings: Settings) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.scheduler = AsyncIOScheduler()
        self.consecutive_failures = 0
        self._lock = asyncio.Lock()
        self._started = False

    async def start(self) -> None:
        if self._started:
            return

        self.scheduler.add_job(
            self.run_monitoring_check,
            "interval",
            minutes=self.settings.check_interval_minutes,
            jitter=self.settings.random_delay_max_seconds,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        self._started = True
        asyncio.create_task(self.run_monitoring_check())
        logger.info("monitor scheduler started")

    async def stop(self) -> None:
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False
        logger.info("monitor scheduler stopped")

    async def run_monitoring_check(self) -> None:
        if self._lock.locked():
            logger.info("monitor check skipped: previous run still active")
            return

        async with self._lock:
            try:
                if self.consecutive_failures >= self.settings.max_consecutive_failures:
                    logger.error("monitor check halted: reached consecutive failure limit")
                    return

                if self.settings.random_delay_max_seconds > 0:
                    delay = random.randint(0, self.settings.random_delay_max_seconds)
                    await asyncio.sleep(delay)

                allowed = await asyncio.to_thread(
                    is_allowed_by_robots,
                    self.settings.monitor_url,
                    self.settings.user_agent,
                    self.settings.request_timeout_seconds,
                )
                if not allowed:
                    raise PermissionError("robots.txt disallows monitoring this URL.")

                content_hash = await asyncio.to_thread(
                    get_section_hash,
                    self.settings.monitor_url,
                    self.settings.monitor_selector,
                    self.settings.user_agent,
                    self.settings.request_timeout_seconds,
                )

                now = datetime.now(timezone.utc)
                changed, push_tokens = await self._persist_state_and_get_tokens(content_hash, now)
                if changed and push_tokens:
                    await send_bulk_notifications(
                        self.settings.expo_push_url,
                        push_tokens,
                        "✨ TDRサイト更新情報が更新されました",
                        "東京ディズニーリゾート公式サイトの更新情報を確認してください。",
                        self.settings.request_timeout_seconds,
                    )
                self.consecutive_failures = 0
                logger.info("monitor check completed changed=%s tokens=%s", changed, len(push_tokens))
            except Exception:
                self.consecutive_failures += 1
                logger.exception(
                    "monitor check failed (%s/%s)",
                    self.consecutive_failures,
                    self.settings.max_consecutive_failures,
                )
                if self.consecutive_failures >= self.settings.max_consecutive_failures:
                    logger.error("stopping monitor scheduler due to repeated failures")
                    await self.stop()

    async def _persist_state_and_get_tokens(
        self, content_hash: str, checked_at: datetime
    ) -> tuple[bool, list[str]]:
        async with self.session_factory() as session:
            state = await self._get_or_create_state(session)
            changed = state.last_hash is not None and state.last_hash != content_hash

            state.last_hash = content_hash
            state.last_checked_at = checked_at
            if changed:
                state.last_updated_at = checked_at

            push_tokens = []
            if changed:
                result = await session.execute(select(User.push_token))
                push_tokens = [row[0] for row in result.all()]

            await session.commit()
            return changed, push_tokens

    async def _get_or_create_state(self, session) -> MonitorState:
        result = await session.execute(
            select(MonitorState).where(
                MonitorState.url == self.settings.monitor_url,
                MonitorState.selector == self.settings.monitor_selector,
            )
        )
        state = result.scalar_one_or_none()
        if state is not None:
            return state

        state = MonitorState(
            url=self.settings.monitor_url,
            selector=self.settings.monitor_selector,
            last_hash=None,
            last_checked_at=None,
            last_updated_at=None,
        )
        session.add(state)
        await session.flush()
        return state
