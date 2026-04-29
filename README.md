# OwO-FarmBot (Python Version)

A clean, safe, and efficient automated farming bot for the Discord OwO bot.

## 🚀 Getting Started

### 1. Requirements
Ensure you have Python installed. Then install the dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Configuration
Edit `config.json` with your details:
- `token`: Your Discord Account Token.
- `channel_id`: The ID of the channel where you want to farm.
- `random_delay_min`: Minimum wait time between rounds (Default: 15s).
- `random_delay_max`: Maximum wait time between rounds (Default: 25s).

### 3. Running the Bot
```powershell
python main.py
```

## 🛡️ Safety Features
- **Auto-Stop on Captcha**: The bot monitors OwO bot's messages. If it detects "beedoo" or any mention of a captcha/verification, it shuts down instantly to protect your account.
- **Natural Delays**: Uses randomized floating-point intervals to mimic human typing patterns.
- **Self-Bot Logic**: Built on `discord.py-self` for authentic user-like connection.

## ⚠️ Important Warning
Automating user accounts is a violation of Discord's TOS.
1. **Use an Alt Account** if possible.
2. **Don't run it 24/7**. This is an easy way to get flagged.
3. **If the bot stops**, check your Discord immediately for a captcha!

## ❓ How to get Token/Channel ID?
1. **Token**: Open Discord in browser -> F12 -> Network -> Type `/api/v9` in filter -> Send a message -> Click on any entry -> Look for `authorization` in Request Headers.
2. **Channel ID**: Enable Developer Mode in Discord Settings -> Appearance/Advanced -> Right click on a channel -> Copy ID.
