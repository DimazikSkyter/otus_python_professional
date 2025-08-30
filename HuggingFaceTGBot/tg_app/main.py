import asyncio
import datetime as dt
import json
import os
import re
import socket
from typing import Any, Dict, Optional, Tuple

import httpx
from dateparser import parse as parse_date
from fastapi import FastAPI, HTTPException, Request
from huggingface_hub import InferenceClient

HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

RELAY_URL = os.getenv("RELAY_URL")
RELAY_TOKEN = os.getenv("RELAY_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# локальный fallback: если переменных нет, пытаемся прочитать config.json
if not TELEGRAM_TOKEN or not HF_TOKEN:
    try:
        with open(
            os.path.join(os.path.dirname(__file__), "config.json"),
            "r",
            encoding="utf-8",
        ) as f:
            cfg = json.load(f)
        TELEGRAM_TOKEN = TELEGRAM_TOKEN or cfg.get("TELEGRAM_TOKEN")
        HF_TOKEN = HF_TOKEN or cfg.get("HUGGING_FACE_TOKEN_VALUE")
        # опц.: модель из файла
        HF_MODEL = cfg.get("HF_MODEL", HF_MODEL)
    except FileNotFoundError:
        pass

if not TELEGRAM_TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN is missing: set it in HF Secrets or provide tg_app/config.json locally."
    )
if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN is missing: set it in HF Secrets or provide tg_app/config.json locally."
    )

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
client = InferenceClient(model=HF_MODEL, token=HF_TOKEN)
app = FastAPI(title="Weather Will-It-Rain Bot (HF Spaces)")


@app.get("/debug/llm")
async def debug_llm(q: str = "Будет ли дождь в Париже завтра?"):
    try:
        return hf_parse_city_date(q)
    except Exception as e:
        return {"ok": False, "err": repr(e), "model": HF_MODEL}


@app.get("/debug/dns")
async def debug_dns():
    try:
        ip = socket.gethostbyname("api.telegram.org")
        return {"ok": True, "api.telegram.org": ip}
    except Exception as e:
        return {"ok": False, "err": repr(e)}


@app.get("/debug/http")
async def debug_http():
    try:
        async with httpx.AsyncClient(timeout=10) as s:
            r1 = await s.get("https://api.telegram.org")
            r2 = await s.get("https://api.open-meteo.com")
        return {"tg": r1.status_code, "openmeteo": r2.status_code}
    except Exception as e:
        return {"ok": False, "err": repr(e)}


async def relay_call(method: str, payload: dict) -> None:
    if not RELAY_URL or not RELAY_TOKEN or not TELEGRAM_TOKEN:
        # если релея нет — просто логируем, чтобы не падал вебхук
        print("[WARN] relay not configured, skip send:", method, payload)
        return
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.post(
            RELAY_URL,
            headers={"x-relay-token": RELAY_TOKEN, "content-type": "application/json"},
            json={"method": method, "token": TELEGRAM_TOKEN, "payload": payload},
        )
        # не выбрасываем исключение, чтобы вебхук всегда вернул 200
        if r.status_code >= 400:
            print("[WARN] relay failed:", r.status_code, r.text)


async def tg_send_message(chat_id: int, text: str, **kwargs: Any) -> None:
    payload: Dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    payload.update(kwargs)
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.post(f"{TELEGRAM_API}/sendMessage", json=payload)
    r.raise_for_status()


# async def tg_action(chat_id: int, action: str = "typing") -> None:
#     async with httpx.AsyncClient(timeout=10) as s:
#         await s.post(f"{TELEGRAM_API}/sendChatAction", json={"chat_id": chat_id, "action": action})


async def tg_action(chat_id: int, action: str = "typing") -> None:
    # можно вызывать или вообще закомментить, чтобы меньше сетевых вызовов
    await relay_call("sendChatAction", {"chat_id": chat_id, "action": action})


SYSTEM = (
    "Ты извлекаешь город и дату из русского вопроса о погоде. "
    "Отвечай ТОЛЬКО JSON с ключами: city (string|nullable), date (string|nullable)."
)


FEWSHOT = (
    'Q: "Будет ли дождь в Париже завтра?"\
    '
    'A: {"city":"Париж","date":"завтра"}\
    '
    'Q: "Скажи, дождь в СПб 29 августа?"\
    '
    'A: {"city":"Санкт-Петербург","date":"29 августа"}\
    '
    'Q: "Москва дождь сегодня"\
    '
    'A: {"city":"Москва","date":"сегодня"}'
)


def _extract_json(text: str) -> Dict[str, Optional[str]]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {"city": None, "date": None}
    try:
        obj = json.loads(m.group(0))
        return {"city": obj.get("city"), "date": obj.get("date")}
    except Exception:
        return {"city": None, "date": None}


def hf_parse_city_date(user_text: str) -> Dict[str, Optional[str]]:
    messages = [
        {"role": "system", "content": SYSTEM + "\nПримеры:\n" + FEWSHOT},
        {"role": "user", "content": user_text},
    ]
    resp = client.chat_completion(messages=messages)
    content = resp.choices[0].message["content"]
    return _extract_json(content)


async def geocode_city(city: str) -> Optional[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "ru"},
        )
        r.raise_for_status()
        j = r.json()
        if not j.get("results"):
            return None
        return j["results"][0]


async def daily_precipitation(lat: float, lon: float) -> Dict[dt.date, Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_probability_max,precipitation_sum,weathercode",
                "timezone": "auto",
            },
        )
        r.raise_for_status()
        d = r.json()["daily"]
    out: Dict[dt.date, Dict[str, Any]] = {}
    for i, t in enumerate(d["time"]):
        day = dt.date.fromisoformat(t)
        out[day] = {
            "prob": d["precipitation_probability_max"][i],
            "sum": d["precipitation_sum"][i],
            "code": d["weathercode"][i],
        }
    return out


async def will_it_rain(city_text: str, when_text: str) -> Tuple[bool, str]:
    when = parse_date(when_text, languages=["ru", "en"]) if when_text else None
    if not when:
        return False, "Не понял дату. Пример: 'сегодня', 'завтра', '29 августа'."
    target = when.date()

    place = await geocode_city(city_text)
    if not place:
        return False, "Город не найден. Пришлите название иначе (например: 'Париж')."

    lat, lon = place["latitude"], place["longitude"]
    name = place["name"]
    country = place.get("country_code", "")

    table = await daily_precipitation(lat, lon)
    if target not in table:
        return False, "Эта дата вне горизонта прогноза (обычно 7–16 дней)."

    row = table[target]
    prob = row.get("prob")  # %
    mm = row.get("sum")  # мм/день

    verdict_yes = (prob is not None and prob >= 40) or (mm is not None and mm > 0)
    verdict = "Да, вероятен дождь" if verdict_yes else "Скорее нет дождя"

    text = (
        f"<b>{verdict}</b> в {name}{', ' + country if country else ''} {target:%d.%m.%Y}.\
        "
        f"Вероятность осадков: {prob}% · Ожидаемые осадки: {mm} мм."
    )
    return True, text


@app.get("/")
async def root():
    return {"ok": True, "msg": "Will-It-Rain Bot is running"}


@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != TELEGRAM_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    update = await request.json()
    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()
    if not chat_id:
        return {"ok": True}

    if text.startswith("/start"):
        await tg_send_message(
            chat_id,
            (
                "Спроси меня по‑русски:\
            "
                "<i>Будет ли дождь в Париже завтра?</i> или <i>Скажи, дождь в СПб 29 августа?</i>\
"
                "Я пойму город и дату и отвечу."
            ),
        )
        return {"ok": True}

    if not text:
        try:
            await tg_send_message(chat_id, "Пришли вопрос текстом.")
        except Exception as e:
            print("[WARN] Failed to sendMessage:", e)
        return {"ok": True}

    try:
        await tg_action(chat_id)
    except Exception:
        pass

    parsed = hf_parse_city_date(text)
    city = (parsed.get("city") or "").strip()
    when_text = (parsed.get("date") or "").strip()

    if not city:
        try:
            await tg_send_message(
                chat_id, "Не понял город. Пример: 'Будет ли дождь в Париже завтра?'"
            )
        except Exception as e:
            print("[WARN] Failed to sendMessage:", e)
        return {"ok": True}

    if not when_text:
        when_text = "сегодня"

    _, reply = await will_it_rain(city, when_text)
    try:
        await tg_send_message(chat_id, reply)
    except Exception as e:
        print("[WARN] Failed to sendMessage:", e)
    return {"ok": True}


@app.post("/send/{chat_id}/{city}/{when_text}")
async def send_weather(chat_id: int, city: str, when_text: str):
    ok, reply = await will_it_rain(city, when_text)
    if not ok:
        raise HTTPException(status_code=400, detail=reply)
    await tg_send_message(chat_id, reply)
    return {"ok": True}
