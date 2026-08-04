"""One-shot publisher for GitHub Actions. Accepts small scheduler delays."""
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

def caption(name, target, mult, cols):
    seq = "\n".join(f"Niveau {i}: Colonne {c}" for i, c in enumerate(cols, 1))
    return (f"🔔 <b>SIGNAL DÉTECTÉ — {name} 🎮</b>\n\n⏰ Tranche de jeu : {target:%H:%M} - {(target+timedelta(minutes=5)):%H:%M}\n\n"
            f"🔄 Tentatives conseillées : 2 tours / 2 reprises\n\n🎯 Objectif : Côte {mult}+\n\n📌 <b>SÉQUENCE À SUIVRE :</b>\n\n{seq}\n\n"
            "⚠️ Ce signal est généré pour les nouveaux inscrits avec le code promo <b>HADAR</b>. Jouez de façon responsable.\n\n"
            "Inscris-toi avec le code promo <b>HADAR</b> et joue avec nous\n\n" + LINKS)

def select_game(now):
    if os.getenv("FORCE_TEST", "false").lower() == "true":
        return "swamp_land", now.replace(second=0, microsecond=0) + timedelta(minutes=7)
    # GitHub cron can start late. Find the nearest target (00/20/40) to now+7,
    # accepting up to 10 minutes of delay, then apply the parity schedule.
    expected = now + timedelta(minutes=7)
    base = expected.replace(second=0, microsecond=0)
    candidates = [base.replace(minute=0), base.replace(minute=20), base.replace(minute=40)]
    candidates += [c + timedelta(hours=1) for c in candidates]
    target = min(candidates, key=lambda c: abs((c - expected).total_seconds()))
    if abs((target - expected).total_seconds()) > 10 * 60:
        return None
    for gid, (name, levels, mult, minute, offset) in GAMES.items():
        if target.minute == minute and target.hour % 2 == offset:
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
        await bot.send_photo(os.environ["CHANNEL_ID"], FSInputFile(image), caption=caption(name, target, mult, cols), parse_mode=ParseMode.HTML)
        print(f"Publication réussie: {gid} pour {target.isoformat()}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
