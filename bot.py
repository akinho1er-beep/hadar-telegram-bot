"""Telegram signal publisher for 1xGames. Python 3.10+, Windows compatible."""
from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("signal-bot")

GAMES = {
    "swamp_land": {"name": "Swamp Land", "levels": 2, "multiplier": "2.17", "minute": 0, "hour_offset": 0},
    "kamikaze": {"name": "Kamikaze", "levels": 4, "multiplier": "2.00", "minute": 20, "hour_offset": 0},
    "apple_of_fortune": {"name": "Apple of Fortune", "levels": 4, "multiplier": "2.41", "minute": 40, "hour_offset": 0},
    "dragons_gold": {"name": "Dragon's Gold", "levels": 4, "multiplier": "2.41", "minute": 0, "hour_offset": 1},
    "eastern_night": {"name": "Eastern Night", "levels": 4, "multiplier": "2.41", "minute": 30, "hour_offset": 1},
}

LINKS = (
    "1xbet : https://reffpa.com/L?tag=d_4957531m_97c_toptransfers_winter26_fr&site=4957531&ad=97&r=line/football\n"
    "Afro Pari : https://apaff.top/L?tag=d_3822237m_70055c_&site=3822237&ad=70055\n"
    "Fast Pari : https://fastpaff.top/L?tag=d_4324108m_77525c_&site=4324108&ad=77525"
)


def make_caption(game: dict, target: datetime, columns: list[int]) -> str:
    sequence = "\n".join(f"Niveau {i}: Colonne {col}" for i, col in enumerate(columns, 1))
    end = target + timedelta(minutes=5)
    return (
        f"🔔 <b>SIGNAL DÉTECTÉ — {game['name']} 🎮</b>\n\n"
        f"⏰ Tranche de jeu : {target:%H:%M} - {end:%H:%M}\n\n"
        "🔄 Tentatives conseillées : 2 tours / 2 reprises\n"
        f"🎯 Objectif : Côte {game['multiplier']}+\n\n"
        "📌 <b>SÉQUENCE À SUIVRE :</b>\n\n"
        f"{sequence}\n\n"
        "⚠️ Ce signal est généré pour les nouveaux inscrits avec le code promo <b>HADAR</b>. Jouez de façon responsable.\n\n"
        "Inscris-toi avec le code promo <b>HADAR</b> et joue avec nous\n"
        f"{LINKS}"
    )


def image_for(game_id: str) -> Path:
    for ext in (".png", ".jpg", ".jpeg"):
        candidate = BASE_DIR / "assets" / "images" / f"{game_id}{ext}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Image manquante pour {game_id} dans assets/images")


async def publish(bot: Bot, game_id: str) -> None:
    game = GAMES[game_id]
    # The scheduler fires 7 minutes before the advertised session.
    target = datetime.now(ZoneInfo(os.getenv("TIMEZONE", "Africa/Porto-Novo"))) + timedelta(minutes=7)
    target = target.replace(second=0, microsecond=0)
    columns = [random.randint(1, 5) for _ in range(game["levels"])]
    caption = make_caption(game, target, columns)
    if os.getenv("DRY_RUN", "false").lower() == "true":
        log.info("DRY_RUN %s: %s", game_id, caption.replace("\n", " | "))
        return
    await bot.send_photo(
        chat_id=os.environ["CHANNEL_ID"],
        photo=FSInputFile(image_for(game_id)),
        caption=caption,
        parse_mode=ParseMode.HTML,
    )
    log.info("Published %s for %s", game_id, target.isoformat())


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    channel = os.getenv("CHANNEL_ID")
    if not token or not channel:
        raise RuntimeError("BOT_TOKEN et CHANNEL_ID doivent être définis dans .env")
    try:
        tz = ZoneInfo(os.getenv("TIMEZONE", "Africa/Porto-Novo"))
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError("Fuseau introuvable. Installez tzdata ou corrigez TIMEZONE.") from exc

    bot = Bot(token)
    scheduler = AsyncIOScheduler(timezone=tz)
    # Each job runs at the target time minus 7 minutes; target is reconstructed from run time.
    for game_id, game in GAMES.items():
        scheduler.add_job(
            publish, "cron", args=[bot, game_id],
            minute=game["minute"] - 7 if game["minute"] >= 7 else game["minute"] + 53,
            hour="1-23/2" if game["hour_offset"] else "*/2",
            id=game_id, max_instances=1, coalesce=True,
        )
    scheduler.start()
    log.info("Bot actif dans le fuseau %s", tz)
    if os.getenv("SEND_TEST_ON_START", "false").lower() == "true":
        # One immediate test publication, then normal scheduling continues.
        test_game = os.getenv("TEST_GAME", "swamp_land")
        if test_game not in GAMES:
            raise RuntimeError(f"TEST_GAME invalide: {test_game}")
        await publish(bot, test_game)
        log.info("Test immédiat envoyé pour %s", test_game)
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
