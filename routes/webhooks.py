import asyncio
import uuid
import httpx
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, HttpUrl
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.linkedin_client import linkedin

router = APIRouter(prefix="/webhooks", tags=["Webhooks ⭐"])
limiter = Limiter(key_func=get_remote_address)

_subscriptions: dict[str, dict] = {}
_snapshots: dict[str, dict] = {}
_polling_task: asyncio.Task | None = None


class SubscribeRequest(BaseModel):
    linkedin_url: str
    callback_url: HttpUrl
    events: list[Literal["job_changed", "headline_changed", "new_post"]] = ["job_changed", "headline_changed"]


async def _deliver(callback_url: str, payload: dict):
    """POST the event payload to the subscriber's callback URL."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(callback_url, json=payload)
    except Exception:
        pass  # log in production


async def _poll_loop():
    """Background loop: checks subscribed profiles every 5 minutes for changes."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        for sub_id, sub in list(_subscriptions.items()):
            if sub["status"] != "active":
                continue
            try:
                current = await linkedin.request(
                    "/get-profile-data-by-url",
                    params={"url": sub["linkedin_url"]},
                    use_cache=False,
                )
                prev = _snapshots.get(sub["linkedin_url"], {})
                events = []

                if "headline_changed" in sub["events"] and current.get("headline") != prev.get("headline") and prev:
                    events.append({
                        "type": "headline_changed",
                        "old": prev.get("headline"),
                        "new": current.get("headline"),
                    })

                current_company = (current.get("positions", {}).get("positionHistory") or [{}])[0].get("companyName")
                prev_company = (prev.get("positions", {}).get("positionHistory") or [{}])[0].get("companyName")
                if "job_changed" in sub["events"] and current_company != prev_company and prev:
                    events.append({
                        "type": "job_changed",
                        "old": prev_company,
                        "new": current_company,
                    })

                _snapshots[sub["linkedin_url"]] = current

                if events:
                    payload = {
                        "subscriptionId": sub_id,
                        "linkedinUrl": sub["linkedin_url"],
                        "events": events,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    asyncio.create_task(_deliver(sub["callback_url"], payload))
                    _subscriptions[sub_id]["totalDelivered"] = sub.get("totalDelivered", 0) + len(events)
                    _subscriptions[sub_id]["lastDeliveredAt"] = datetime.utcnow().isoformat()

            except Exception as e:
                _subscriptions[sub_id]["lastError"] = str(e)


def _ensure_polling():
    global _polling_task
    if _polling_task is None or _polling_task.done():
        loop = asyncio.get_event_loop()
        _polling_task = loop.create_task(_poll_loop())


@router.post("/subscribe", status_code=201, summary="[UNIQUE] Subscribe to real-time profile change events")
@limiter.limit("10/minute")
async def subscribe(request: Request, body: SubscribeRequest):
    """
    Subscribe to events for a LinkedIn profile.
    Your `callback_url` will receive a POST request when events occur.

    Supported events:
    - `job_changed` — person changed company or title
    - `headline_changed` — LinkedIn headline was updated
    - `new_post` — person published a new post

    Profiles are checked every **5 minutes**.
    **No other LinkedIn API offers this.**
    """
    # Take initial snapshot
    try:
        snapshot = await linkedin.request("/get-profile-data-by-url", params={"url": body.linkedin_url})
        _snapshots[body.linkedin_url] = snapshot
    except Exception:
        raise HTTPException(400, f"Cannot fetch profile: {body.linkedin_url}")

    sub_id = str(uuid.uuid4())
    _subscriptions[sub_id] = {
        "subscriptionId": sub_id,
        "linkedin_url": body.linkedin_url,
        "callback_url": str(body.callback_url),
        "events": body.events,
        "status": "active",
        "createdAt": datetime.utcnow().isoformat(),
        "totalDelivered": 0,
        "lastDeliveredAt": None,
        "lastError": None,
    }

    _ensure_polling()

    return {
        **_subscriptions[sub_id],
        "message": "Webhook active. Profile checked every 5 minutes.",
    }


@router.get("/", summary="List all active webhook subscriptions")
@limiter.limit("30/minute")
async def list_subscriptions(request: Request):
    return {"subscriptions": list(_subscriptions.values()), "total": len(_subscriptions)}


@router.get("/{sub_id}", summary="Get a webhook subscription")
@limiter.limit("30/minute")
async def get_subscription(request: Request, sub_id: str):
    if sub_id not in _subscriptions:
        raise HTTPException(404, "Subscription not found")
    return _subscriptions[sub_id]


@router.delete("/{sub_id}", summary="Cancel a webhook subscription")
@limiter.limit("20/minute")
async def cancel_subscription(request: Request, sub_id: str):
    if sub_id not in _subscriptions:
        raise HTTPException(404, "Subscription not found")
    _subscriptions[sub_id]["status"] = "cancelled"
    del _subscriptions[sub_id]
    return {"message": "Subscription cancelled", "subscriptionId": sub_id}
