import asyncio

import requests


def send_push_notification(
    expo_push_url: str, push_token: str, title: str, body: str, timeout_seconds: int
) -> bool:
    payload = {"to": push_token, "title": title, "body": body, "sound": "default"}
    response = requests.post(
        expo_push_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=timeout_seconds,
    )
    if response.status_code != 200:
        return False

    try:
        data = response.json()
    except ValueError:
        return False

    status = data.get("data", {}).get("status")
    return status == "ok"


async def send_bulk_notifications(
    expo_push_url: str, push_tokens: list[str], title: str, body: str, timeout_seconds: int
) -> None:
    for token in push_tokens:
        await asyncio.to_thread(
            send_push_notification, expo_push_url, token, title, body, timeout_seconds
        )
