import asyncio
import random
import time
import os
from pathlib import Path
import shutil
import tempfile

import edge_tts
from playsound import playsound

# -------- Buyer-focused Hype Phrases (same meaning, stream-friendly) --------
PHRASES = [
    "A brave buyer steps in — it's {name}! Can they grab the bounty?",
    "The shop just got hotter — {name} is here to take the bounty!",
    "New order alert — {name} just joined the game! Will they win it all?",
    "Fresh packs on deck! {name} is taking the challenge!",
    "Big play coming — {name} is in! Can they hit the bounty tonight?",
    "Here comes {name}! The hunt for the bounty is on!",
    "A fresh challenger is buying in — {name} wants that prize!",
    "Get ready — {name} just placed an order! Can they pull the winner?",
    "New buyer hype! {name} is up next to rip some packs!",
    "All eyes on {name}! Their order might just crack the bounty!",
    "The bounty just got real — {name} is hunting for it!",
    "Order confirmed! {name} is on the board!",
    "Time to rip! {name} is stepping up with a fresh order!",
    "Watch closely — {name} could end the bounty streak right here!",
    "New order incoming — {name} is ready to play!",
    "Let’s cheer for {name}! Will this be the winning pull?",
    "The queue just got hotter — {name} is next to rip!",
    "Fresh hands, fresh luck — {name} might take the prize!",
    "Buy-in complete! {name} is officially in the game!",
    "The bounty is shaking — {name} is coming for it!",
    "New buyer detected — {name} is on a bounty hunt!",
    "Another shot at glory — {name} is here to rip!",
    "Let’s go! {name} just entered the bounty challenge!",
    "The shop bell rings — {name} is ready to rip packs!",
    "Who’s next? It’s {name}, here to chase the bounty!",
    "We have fresh action — {name} is buying in now!",
    "Can {name} pull the big card and take the bounty?",
    "Big moment for {name} — can this be the winning order?",
    "The hunt is live — {name} is in the race for the prize!",
    "Crowd, make some noise — {name} is next on the bounty quest!",
    "Rip it, ship it — {name} is in the hot seat!",
    "Lucky vibes incoming — {name} is ready to rip!",
    "Brand-new entry — {name} could end the bounty tonight!",
    "Who’s chasing the bounty? It’s {name}!",
    "Heat alert — {name} is cracking packs right now!",
    "The bounty counter is ticking — {name} just joined!",
    "This is the order that could change it — {name} is up!",
    "Everyone watch — {name} is challenging the bounty streak!",
    "It’s go time! {name} is ripping packs to claim the prize!",
    "A fresh buyer joins the hunt — welcome {name}!",
    "The stage is set — {name} could be our bounty breaker!",
    "This is the big moment — {name} is ripping next!",
    "Get hyped — {name} is hunting the bounty tonight!",
    "Brand new buyer energy — {name} is here to play!",
    "This could be the bounty hit — {name} is in play!",
    "Another contender steps up — {name} is ripping!",
    "Big energy in the shop — {name} is chasing the bounty!",
    "All bets are on {name}! Can they take the prize?",
    "The rip begins — {name} is going for the bounty!",
    "This might be it — {name} could finish the chase!",
]

# Files live next to this script
BASE_DIR = Path(__file__).parent.resolve()
RING_SRC = BASE_DIR / "ring.mp3"           # your existing ring.mp3 in the same folder
# Create an ASCII-only temp dir to avoid Windows MCI unicode issues
TMP_DIR = Path(tempfile.gettempdir()) / "tcf_audio"
TMP_DIR.mkdir(parents=True, exist_ok=True)
RING_TMP = TMP_DIR / "ring.mp3"
TTS_TMP  = TMP_DIR / "announcement.mp3"

async def casino_speak(name: str):
    # sanity checks + copy ring to ASCII path
    if not RING_SRC.exists():
        raise FileNotFoundError(f"ring.mp3 not found at {RING_SRC}")
    try:
        shutil.copyfile(RING_SRC, RING_TMP)
    except Exception as e:
        raise RuntimeError(f"Failed to copy ring.mp3 to temp: {e}")

    intro = "We have a new challenger!"
    phrase = random.choice(PHRASES).format(name=name)
    text   = f"{intro} {phrase}"

    # 1) Generate TTS to ASCII temp path
    tts = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="+15%", pitch="+10Hz")
    await tts.save(str(TTS_TMP))

    # 2) Play ring (~4s), then announcement
    print(f"🔊 Playing ring from: {RING_TMP}  (exists={RING_TMP.exists()})")
    playsound(str(RING_TMP))
    time.sleep(4)
    print(f"🗣️ Playing TTS from:  {TTS_TMP}   (exists={TTS_TMP.exists()})")
    playsound(str(TTS_TMP))

    print("🎰", text)

if __name__ == "__main__":
    asyncio.run(casino_speak("Andy"))

