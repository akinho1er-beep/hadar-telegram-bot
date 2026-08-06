"""One-shot publisher for GitHub Actions."""
import asyncio, os, random
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

ROOT = Path(__file__).resolve().parent
GAMES = {
    "swamp_land": ("Swamp Land", 2, "2.17", 0, 0),
    "kamikaze": ("Kamikaze", 4, "2.00", 20, 0),
    "apple_of_fortune": ("Apple of Fortune", 4, "2.41", 40, 0),
    "dragons_gold": ("Dragon's Gold", 4, "2.41", 0, 1),
    "eastern_night": ("Eastern Night", 4, "2.41", 30, 1),
}
LINKS = ("1xbet : https://reffpa.com/L?tag=d_4957531m_97c_toptransfers_winter26_fr&site=4957531&ad=97&r=line/football\n"
         "Afro Pari : https://apaff.top/L?tag=d_3822237m_70055c_&site=3822237&ad=70055\n"
         "Fast Pari : https://fastpaff.top/L?tag=d_4324108m_77525c_&site=4324108&ad=77525")

def captions(name, target, mult, cols):
    nl = chr(10)

    sequence_fr = nl.join(
        f"<b>Niveau {i} : Colonne {c}</b>"
        for i, c in enumerate(cols, 1)
    )

    sequence_en = nl.join(
        f"<b>Level {i}: Column {c}</b>"
        for i, c in enumerate(cols, 1)
    )

    links = (
        "1xbet : https://reffpa.com/L?tag=d_4957531m_97c_toptransfers_winter26_fr&site=4957531&ad=97&r=line/football" + nl
        + "Afro Pari : https://apaff.top/L?tag=d_3822237m_70055c_&site=3822237&ad=70055" + nl
        + "Fast Pari : https://fastpaff.top/L?tag=d_4324108m_77525c_&site=4324108&ad=77525"
    )

    french = (
        f"🔔 <b>SIGNAL DÉTECTÉ — {name} 🎮</b>{nl}{nl}"
        f"⏰ Tranche de jeu : {target:%H:%M} - {(target + timedelta(minutes=5)):%H:%M}{nl}{nl}"
        f"🔄 Tentatives conseillées : 2 tours / 2 reprises{nl}{nl}"
        f"🎯 Objectif : Côte {mult}+{nl}{nl}"
        f"📌 <b>SÉQUENCE À SUIVRE :</b>{nl}{nl}"
        f"{sequence_fr}{nl}{nl}"
        f"⚠️ Ce signal est généré pour les nouveaux inscrits avec le code promo <b>HADAR</b>. Jouez de façon responsable.{nl}{nl}"
        f"Inscris-toi avec le code promo <b>HADAR</b> et joue avec nous{nl}{nl}"
        f"{links}"
    )

    english = (
        f"🔔 <b>SIGNAL DETECTED — {name} 🎮</b>{nl}{nl}"
        f"⏰ Game time: {target:%H:%M} - {(target + timedelta(minutes=5)):%H:%M}{nl}{nl}"
        f"🔄 Recommended attempts: 2 rounds / 2 retries{nl}{nl}"
        f"🎯 Target: Odds {mult}+{nl}{nl}"
        f"📌 <b>SEQUENCE TO FOLLOW:</b>{nl}{nl}"
        f"{sequence_en}{nl}{nl}"
        f"⚠️ This signal is generated for new players registered with the <b>HADAR</b> promo code. Please play responsibly.{nl}{nl}"
        f"Sign up with the <b>HADAR</b> promo code and play with us{nl}{nl}"
        f"{links}"
    )

    return french, english


def select_game(now):
    if os.getenv("FORCE_TEST", "false").lower() == "true":
        gid = os.getenv("TEST_GAME", "swamp_land")
        if gid not in GAMES:
            raise ValueError(f"TEST_GAME invalide: {gid}")
        return gid, now.replace(second=0, microsecond=0) + timedelta(minutes=7)

    expected = now + timedelta(minutes=7)
    base = expected.replace(second=0, microsecond=0)
    candidates = []
    for hour_offset in range(-1, 3):
        hour_base = base.replace(minute=0) + timedelta(hours=hour_offset)
        for minute in (0, 20, 30, 40):
            candidates.append(hour_base.replace(minute=minute))
    target = min(candidates, key=lambda c: abs((c - expected).total_seconds()))
    if abs((target - expected).total_seconds()) > 10 * 60:
        return None
    for gid, game in GAMES.items():
        if target.minute == game[3] and target.hour % 2 == game[4]:
            return gid, target
    return None

async def main():
    tz = ZoneInfo(os.getenv("TIMEZONE", "Africa/Porto-Novo"))
    now = datetime.now(tz)
    selected = select_game(now)
    if not selected:
        print(f"Aucun signal prévu pour {now.isoformat()}")
        return
    gid, target = selected
    name, levels, mult, _, _ = GAMES[gid]
    image = ROOT / "assets" / "images" / f"{gid}.png"
    if not image.exists():
        raise FileNotFoundError(image)
    cols = [random.randint(1, 5) for _ in range(levels)]
    bot = Bot(os.environ["BOT_TOKEN"])
    try:
        french_caption, english_caption = captions(name, target, mult, cols)

        await bot.send_photo(
            os.environ["CHANNEL_ID"],
            FSInputFile(image),
            caption=french_caption,
            parse_mode=ParseMode.HTML,
        )

        await bot.send_photo(
            os.environ["CHANNEL_ID"],
            FSInputFile(image),
            caption=english_caption,
            parse_mode=ParseMode.HTML,
        )
        print(f"Publication réussie: {gid} pour {target.isoformat()}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
