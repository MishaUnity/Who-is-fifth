import requests

from fastapi import APIRouter
from datetime import datetime, timezone
import requests


BASE_URL = "https://pro.sirius-ft.ru"

def get_events(
    begin_date: str = None,
    end_date: str = None,
    search: str = "",
    type_visit_id: int = None,
    inner_event_type_id: int = None,
    is_free_slots: bool = None,
    begin_age: int = None,
    end_age: int = None,
    limit: int = 12,
    offset: int = 0
) -> dict:
    common_filters = {"search": search}
    if begin_date:
        common_filters["beginDate"] = begin_date
    if end_date:
        common_filters["endDate"] = end_date

    inner_filters = {}
    if type_visit_id is not None:
        inner_filters["typeVisitId"] = type_visit_id
    if inner_event_type_id is not None:
        inner_filters["innerEventTypeId"] = inner_event_type_id
    if is_free_slots is not None:
        inner_filters["isFreeSlots"] = is_free_slots
    if begin_age is not None:
        inner_filters["beginAge"] = begin_age
    if end_age is not None:
        inner_filters["endAge"] = end_age

    payload = {
        "commonFilters": common_filters,
        "pagination": {"limit": limit, "offset": offset}
    }
    if inner_filters:
        payload["innerEventsFilters"] = inner_filters

    response = requests.post(
        f"{BASE_URL}/api/afisha/event/list",
        headers={"Content-Type": "application/json"},
        json=payload
    )

    data = response.json()
    code = data.get("code")

    if code == 200:
        return data["payload"]
    elif code == 416:
        raise ValueError("Недопустимый диапазон дат")
    elif code == 417:
        raise ValueError("Недопустимый диапазон возраста")
    else:
        raise RuntimeError(f"Ошибка {code}: {data.get('description')}")
    
def format_events_for_llm(payload: dict) -> str:
    lines = [f"Найдено мероприятий: {payload['count']}\n"]
    for e in payload["events"]:
        name = e.get("eventName") or e.get("bandName", "—")
        time_range = ""
        if e.get("eventStartTime"):
            time_range = f"{e['eventStartTime']}–{e.get('eventEndTime', '?')}"
        elif e.get("isAllDay"):
            time_range = "весь день"

        lines.append(
            f"[ID:{e['eventId']}] {name}\n"
            f"  Тип: {e['afishaTypeName']}\n"
            f"  Дата: {e['eventStartDate']} {time_range}\n"
            f"  Место: {e.get('eventPlace') or e.get('venueName', '—')}\n"
        )
    return "\n".join(lines)


router = APIRouter()

def get_today_range():
    now = datetime.now(timezone.utc)
    begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999000)
    return (
        begin.isoformat().replace("+00:00", "Z"),
        end.isoformat().replace("+00:00", "Z"),
    )


@router.get("/api/events/get")
def get_today_events():
    begin_date, end_date = get_today_range()
    payload = get_events(begin_date=begin_date, end_date=end_date, limit=50)
    return payload["events"]
