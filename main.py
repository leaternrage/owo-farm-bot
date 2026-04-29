import asyncio
import random
import json
import sys
import re
import time
import aiohttp
from discord.ext import commands
import discord
import logging
from datetime import datetime
from colorama import Fore, Style, init

logging.basicConfig(level=logging.CRITICAL)
for name in ['discord', 'discord.http', 'discord.gateway', 'discord.client', 'discord.ext.commands']:
    log = logging.getLogger(name); log.setLevel(logging.CRITICAL); log.propagate = False

init(autoreset=True)
OWO_ID = 408785106942164992
CHAT_MESSAGES = ["sa", "as", "selam", "merhaba", "eyw", "nasılsınız", "iyi oyunlar", "iyidir", "sen de", "lol", "xd", ":)", "evet", "hayir", "tamam", "gordum", "oha", "lan", "neyse", "hadi bakalim"]

def extract_rank(card_str):
    rank_part = re.match(r"(\d+|a|j|q|k)", card_str, re.I)
    if not rank_part: return None
    rank = rank_part.group(1).lower()
    if rank == 'a': return 'A'
    elif rank in ['j', 'q', 'k']: return 10
    return int(rank)

def hand_value(cards):
    values, aces = [], 0
    for c in cards:
        if c == 'A': aces += 1; values.append(11)
        else: values.append(c)
    total = sum(values)
    while total > 21 and aces > 0:
        total -= 10; aces -= 1
    return total, (aces > 0 and total <= 21)

def basic_strategy(p, d_up, soft):
    d = d_up if isinstance(d_up, int) else (11 if d_up == 'A' else 10)
    if soft:
        if p >= 19: return 'stand'
        if p == 18: return 'stand' if d <= 8 else 'hit'
        return 'hit'
    else:
        if p >= 17: return 'stand'
        if 13 <= p <= 16: return 'stand' if d <= 6 else 'hit'
        if p == 12: return 'stand' if d in [4, 5, 6] else 'hit'
        return 'hit'

def parse_game_state(text):
    card_pattern = r":([^:]+):\d+"
    all_values = re.findall(r"\[([^\]]+)\]", text)
    if len(all_values) < 2: raise ValueError("Eksik veri")
    d_val_str = all_values[0].replace("+", "").replace("?", "").replace("*", "").strip()
    d_rank = extract_rank(d_val_str) or 10
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    emoji_lines = [re.findall(card_pattern, l) for l in lines if re.findall(card_pattern, l)]
    if not emoji_lines: raise ValueError("Emoji yok")
    if len(emoji_lines) > 1:
        p_cards = []
        for i in range(1, len(emoji_lines)): p_cards.extend(emoji_lines[i])
    else:
        p_cards = emoji_lines[0][1:]
    p_vals = [extract_rank(c) for c in p_cards if "cardback" not in c.lower() and extract_rank(c) is not None]
    return d_rank, p_vals

def decide(text):
    try:
        d, p_vals = parse_game_state(text)
        total, soft = hand_value(p_vals)
        return basic_strategy(total, d, soft)
    except:
        return 'stand'

def get_owo_text(msg):
    parts = [msg.content or ""]
    for e in msg.embeds:
        parts.append(f"{e.author.name or ''}\n{e.title or ''}\n{e.description or ''}\n{e.footer.text or ''}")
        for f in e.fields: parts.append(f.value or "")
    return "\n".join(parts)

async def send_webhook(url, title, desc, color=0x00ff00):
    if not url: return
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"embeds": [{"title": title, "description": desc, "color": color, "timestamp": datetime.now().isoformat()}]}
            async with session.post(url, json=payload) as resp: pass
    except: pass

class FarmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.current_cash = 0
        self.initial_cash = 0
        self.last_status = "Hazir"
        self.start_time = time.time()
        self.hunt_count = 0
        self.battle_count = 0
        self.bj_wins = 0
        self.bj_losses = 0
        self.bj_ties = 0
        self.cf_wins = 0
        self.cf_losses = 0

    def start_tasks(self):
        l = self.bot.loop
        l.create_task(self.ana_dongu())
        l.create_task(self.cash_check_dongusu())
        l.create_task(self.pray_dongusu())
        l.create_task(self.satis_dongusu())

    async def satis_dongusu(self):
        await self.bot.wait_until_ready()
        periyot = self.config.get("Otomasyon", {}).get("Satis_Periyodu_Dakika", 20)
        await asyncio.sleep(periyot * 60)
        channel = self.bot.get_channel(int(self.config["Kanal_ID"]))
        webhook_url = self.config.get("Bildirim_Sistemi", {}).get("Captcha_Webhook_URL", "")
        while True:
            if not self.config["Sistem"].get("Genel_Durum_Acik", True):
                await asyncio.sleep(5); continue
            if self.config["Sistem"].get("Oto_Sell_All", True):
                try:
                    await channel.send("owo sell all")
                    await asyncio.sleep(2)
                    await channel.send("owo cash")
                    uptime_seconds = int(time.time() - self.start_time)
                    hours, remainder = divmod(uptime_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    uptime_str = f"{hours}s {minutes}dk {seconds}sn"
                    profit = self.current_cash - self.initial_cash
                    bj_total = self.bj_wins + self.bj_losses + self.bj_ties
                    bj_rate = (self.bj_wins / bj_total * 100) if bj_total > 0 else 0.0
                    cf_total = self.cf_wins + self.cf_losses
                    cf_rate = (self.cf_wins / cf_total * 100) if cf_total > 0 else 0.0
                    server_name = channel.guild.name if channel.guild else "Bilinmiyor"
                    channel_name = channel.name if hasattr(channel, 'name') else "Bilinmiyor"
                    report_desc = (
                        f"💰 **Bakiye:** Başlangıç: `{self.initial_cash:,}` | Güncel: `{self.current_cash:,}`\n"
                        f"{'📈' if profit >= 0 else '📉'} **Kar/Zarar:** `{profit:+,}` cowoncy\n\n"
                        f"🃏 **Blackjack:** {self.bj_wins}W / {self.bj_losses}L / {self.bj_ties}T (🚀 %{bj_rate:.1f})\n"
                        f"🎲 **Coinflip:** {self.cf_wins}W / {self.cf_losses}L (🚀 %{cf_rate:.1f})\n"
                        f"🏹 **Hunting:** {self.hunt_count} Hunt | {self.battle_count} Battle\n\n"
                        f"⏱ **Çalışma Süresi:** {uptime_str}\n"
                        f"⚙ **Config:** `{self.config['Bot_Prefix']}` | **Kanal:** {server_name} > #{channel_name}"
                    )
                    await send_webhook(webhook_url, f"📊 MANUEL DURUM RAPORU: {self.bot.user.name}", report_desc, 0x00ffaa)
                    periyot = self.config.get("Otomasyon", {}).get("Satis_Periyodu_Dakika", 20)
                    await asyncio.sleep(periyot * 60)
                except: await asyncio.sleep(60)
            else: await asyncio.sleep(30)

    async def pray_dongusu(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(int(self.config["Kanal_ID"]))
        target = self.config.get("Bagis_Pray", {}).get("Hedef_Kullanici_ID", "")
        while True:
            if not self.config["Sistem"].get("Genel_Durum_Acik", True):
                await asyncio.sleep(5); continue
            if self.config["Sistem"].get("Oto_Pray", True):
                try:
                    await channel.send(f"owo pray {target}")
                    await asyncio.sleep(365)
                except: await asyncio.sleep(60)
            else: await asyncio.sleep(30)

    def update_display(self, msg=""):
        if msg: self.last_status = msg
        profit = self.current_cash - self.initial_cash
        color = Fore.LIGHTGREEN_EX if profit >= 0 else Fore.LIGHTRED_EX
        line = (f"{Fore.LIGHTYELLOW_EX}CONNECTED AS: {Fore.LIGHTGREEN_EX}{self.bot.user.name}{Fore.LIGHTYELLOW_EX} | "
                f"STARTED: {Fore.LIGHTGREEN_EX}{self.initial_cash:,}{Fore.LIGHTYELLOW_EX} | "
                f"CURRENT: {Fore.LIGHTGREEN_EX}{self.current_cash:,}{Fore.LIGHTYELLOW_EX} | "
                f"PROFIT: {color}{profit:+,}{Fore.LIGHTYELLOW_EX}")
        sys.stdout.write(f"\r{Style.BRIGHT}{line}")
        sys.stdout.flush()

    async def cash_check_dongusu(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(int(self.config["Kanal_ID"]))
        while True:
            try: await channel.send("owo cash"); await asyncio.sleep(600)
            except: await asyncio.sleep(60)

    async def ana_dongu(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(int(self.config["Kanal_ID"]))
        self.update_display("Ilk bakiye kontrolu...")
        await channel.send("owo cash")
        await asyncio.sleep(5)
        while True:
            try:
                with open('ayarlar.json', 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except: pass
            if not self.config["Sistem"].get("Genel_Durum_Acik", True):
                await asyncio.sleep(5); continue
            try:
                hb_s = "AÇIK" if self.config["Sistem"].get("Oto_Hunt_Battle") else "KAPALI"
                bj_s = "AÇIK" if self.config["Sistem"].get("Oto_Blackjack") else "KAPALI"
                cf_s = "AÇIK" if self.config["Sistem"].get("Oto_Coinflip") else "KAPALI"
                self.update_display(f"Modlar: H/B:{hb_s} BJ:{bj_s} CF:{cf_s}")
                if self.config["Sistem"].get("Oto_Hunt_Battle"):
                    await channel.send("owo h")
                    self.hunt_count += 1
                    await asyncio.sleep(2)
                    await channel.send("owo b")
                    self.battle_count += 1
                    await asyncio.sleep(3)
                bet = int(self.current_cash * self.config["Kumar"].get("Dinamik_Yuzde", 0.01)) if self.current_cash > 0 else 1000
                bet = max(self.config["Kumar"].get("Min_Bet", 100), min(bet, 50000))
                bj_y = self.config["Sistem"].get("Oto_Blackjack", False)
                cf_y = self.config["Sistem"].get("Oto_Coinflip", False)
                choice = None
                if bj_y and cf_y: choice = "BJ" if random.random() < 0.75 else "CF"
                elif bj_y: choice = "BJ"
                elif cf_y: choice = "CF"
                if choice == "CF":
                    self.update_display(f"CF Atiliyor ({bet})")
                    await channel.send(f"owo cf {bet}")
                    await asyncio.sleep(8); await channel.send("owo cash")
                elif choice == "BJ":
                    self.update_display(f"BJ Atiliyor ({bet})")
                    last_id = None
                    async for m in channel.history(limit=5):
                        if m.author.id == OWO_ID: last_id = m.id; break
                    await channel.send(f"owo bj {bet}")
                    bj_msg = None
                    for _ in range(10):
                        async for m in channel.history(limit=8):
                            if m.author.id == OWO_ID and m.id != last_id and m.embeds:
                                bj_msg = m; break
                        if bj_msg: break
                        await asyncio.sleep(1.5)
                    if bj_msg: await self.play_bj(channel, bj_msg)
                if random.random() < 0.15:
                    await channel.send(random.choice(CHAT_MESSAGES))
                    await asyncio.sleep(random.uniform(2, 4))
                self.update_display("Beklemede...")
                await asyncio.sleep(random.randint(8, 12))
            except: await asyncio.sleep(10)

    async def play_bj(self, channel, msg):
        last_action = None
        while True:
            try:
                async for m in channel.history(limit=10):
                    if m.id == msg.id: msg = m; break
                text = get_owo_text(msg)
                footer = msg.embeds[0].footer.text.lower() if msg.embeds and msg.embeds[0].footer else ""
                if "game in progress" not in footer:
                    if "won" in text.lower(): self.bj_wins += 1
                    elif "lost" in text.lower(): self.bj_losses += 1
                    elif "tied" in text.lower(): self.bj_ties += 1
                    await asyncio.sleep(2); await channel.send("owo cash"); break
                action = decide(text)
                emoji = "👊" if action == "hit" else "🛑"
                if last_action != emoji:
                    if last_action:
                        try: await msg.remove_reaction(last_action, self.bot.user)
                        except: pass
                    try: await msg.add_reaction(emoji); last_action = emoji
                    except: pass
                await asyncio.sleep(2)
            except: break

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != OWO_ID: return
        cnt = message.content.lower()
        if "cowoncy" in cnt and "cash" not in cnt:
            mc = re.search(r"__?([\d,]+)__?\s*cowoncy", cnt)
            if mc:
                val = int(mc.group(1).replace(",", "")); self.current_cash = val
                if self.initial_cash == 0: self.initial_cash = val
                self.update_display()
        if "sold" in cnt and "cowoncy" in cnt:
            await asyncio.sleep(2); await message.channel.send("owo cash")
        if "you spent" in cnt and "cowoncy" in cnt:
            if "won" in cnt: self.cf_wins += 1
            elif "lost" in cnt: self.cf_losses += 1
        full_text = get_owo_text(message).lower()
        captcha_keywords = ["beedoo", "captcha", "verify that you are human", "complete your captcha", "banned for macros", "banned for botting"]
        if any(x in full_text for x in captcha_keywords):
            webhook_url = self.config.get("Bildirim_Sistemi", {}).get("Captcha_Webhook_URL", "")
            if "banned" in full_text:
                title = "🔨 HESAP BANLANDI!"
                desc = f"Hesap macro/bot tespiti nedeniyle banlandı!\n\n**Mesaj:** {message.content or '(embed)'}"
                color = 0xff0000
            else:
                import re as _re
                warn_match = _re.search(r"\((\d+/\d+)\)", full_text)
                warn_str = warn_match.group(1) if warn_match else "?"
                title = f"⚠️ CAPTCHA UYARISI! ({warn_str})"
                desc = f"OwO captcha doğrulaması istedi! Bot durduruldu.\n\n**Uyarı:** {warn_str}"
                color = 0xff8800
            await send_webhook(webhook_url, title, desc, color)
            self.config["Sistem"]["Genel_Durum_Acik"] = False
            self.update_display("🚨 CAPTCHA - BOT DURDURULDU!")
            print(f"\n\n{'='*50}\n🚨 CAPTCHA ALGILANDI! Bot durduruldu.\n{'='*50}\n")

class OwoProBot(commands.Bot):
    def __init__(self, config):
        self.config = config
        super().__init__(command_prefix=config["Bot_Prefix"], self_bot=True)
    async def on_ready(self):
        print(f"{Fore.LIGHTRED_EX}[i] OwO Farm Bot by leatern")
        print(""); cog = FarmCog(self); await self.add_cog(cog); cog.start_tasks()

if __name__ == "__main__":
    with open('ayarlar.json', 'r', encoding='utf-8') as f: cfg = json.load(f)
    bot = OwoProBot(cfg); bot.run(cfg["Hesap_Tokeni"])
