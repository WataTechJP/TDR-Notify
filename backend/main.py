import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import AsyncSessionLocal, get_session, init_db
from models import MonitorState, User
from scheduler import MonitorScheduler

logging.basicConfig(level=logging.INFO)

monitor_scheduler = MonitorScheduler(AsyncSessionLocal, settings)


class RegisterRequest(BaseModel):
    push_token: str = Field(min_length=1, max_length=512)


class RegisterResponse(BaseModel):
    status: str


class StatusResponse(BaseModel):
    last_checked_at: datetime | None
    last_updated_at: datetime | None


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await monitor_scheduler.start()
    try:
        yield
    finally:
        await monitor_scheduler.stop()


app = FastAPI(title="Disney Page Update Notifier API", lifespan=lifespan)


@app.post("/register", response_model=RegisterResponse)
async def register_push_token(
    payload: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> RegisterResponse:
    existing = await session.execute(select(User).where(User.push_token == payload.push_token))
    user = existing.scalar_one_or_none()
    if user is None:
        session.add(User(push_token=payload.push_token))
        await session.commit()
    return RegisterResponse(status="registered")


@app.get("/status", response_model=StatusResponse)
async def monitoring_status(session: AsyncSession = Depends(get_session)) -> StatusResponse:
    result = await session.execute(
        select(MonitorState).where(
            MonitorState.url == settings.monitor_url,
            MonitorState.selector == settings.monitor_selector,
        )
    )
    state = result.scalar_one_or_none()
    if state is None:
        return StatusResponse(last_checked_at=None, last_updated_at=None)

    return StatusResponse(
        last_checked_at=state.last_checked_at,
        last_updated_at=state.last_updated_at,
    )
