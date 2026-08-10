# 🤖 VK to MAX Messenger Reposter

<p align="center">
  <a href="#features"><img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python"></a>
  <a href="#features"><img src="https://img.shields.io/badge/aiohttp-async-green" alt="Async"></a>
  <a href="#features"><img src="https://img.shields.io/badge/yt--dlp-integrated-orange" alt="yt-dlp"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
</p>

<p align="center">
  <strong>Robust asynchronous bot for auto-reposting content from VKontakte groups to MAX (VK Teams) messenger channels.</strong>
</p>

<p align="center">
  <a href="README.ru.md">🇷🇺 Инструкция на русском</a>
</p>

---

## 📋 Table of Contents

- [Features](#-features)
- [How it works](#-how-it-works)
- [Quick start](#-quick-start)
- [Configuration](#%EF%B8%8F-configuration)
- [Usage](#-usage)
- [Manual repost](#-manual-repost)
- [Troubleshooting](#-troubleshooting)
- [Self-hosting (VPS)](#-self-hosting-vps)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

| Category | Feature | Description |
|----------|---------|-------------|
| 🎯 **Auto-repost** | Smart queue | Checks last 10 posts, reposts missed ones in chronological order |
| | Periodic polling | Automatic check every 5 minutes (configurable) |
| 📸 **Media** | Photos | Downloads and re-uploads in best quality |
| | Videos | Downloads directly from VK API |
| | VK Clips | Downloads via `yt-dlp` (works even for personal pages) |
| | External videos | YouTube/Rutube posted as player link buttons |
| 🎮 **Control** | Inline keyboard | Status, Logs, Tools menu with callbacks |
| | Admin whitelist | Only configured `ADMIN_ID` can control the bot |
| 🔗 **Manual repost** | URL → post | Send any VK URL to bot DM → publish to channel |
| 🛡️ **Reliability** | Async I/O | `aiohttp` — no event loop blocking |
| | Retry logic | `tenacity` for network errors |
| | Graceful shutdown | Handles SIGINT/SIGTERM correctly |
| | SSL bypass | Automatic workaround for DPI/Mintsifry certificate issues |
| 🔒 **Security** | `.env` config | Secrets never hardcoded in source code |
| | Admin-only | Only admin can trigger commands |

---

## 🔄 How it works

```
┌─────────────┐         ┌──────────┐         ┌─────────────┐
│  VKontakte  │ ──────► │   Bot    │ ──────► │ MAX Channel │
│   Group     │  API    │ (async)  │  API    │             │
└─────────────┘         └──────────┘         └─────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ yt-dlp (for  │
                       │   clips)     │
                       └──────────────┘
```

1. Bot polls VK group wall every 5 minutes via `wall.get`
2. Detects new posts (ID > last saved)
3. Downloads media (photos via API, clips via `yt-dlp`)
4. Re-uploads to MAX CDN
5. Publishes post with inline keyboard ("🔗 Read in VK" + optional "▶️ Watch")
6. Saves last post ID to `last_post_id.txt`

---

## 🚀 Quick start

### Prerequisites

- **Python 3.10+** ([download](https://www.python.org/downloads/))
- **Git** ([download](https://git-scm.com/))

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/vk-max-reposter.git
cd vk-max-reposter
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

<details>
<summary><b>📦 requirements.txt</b></summary>

```txt
aiohttp>=3.9.0
python-dotenv>=1.0.0
tenacity>=8.2.0
yt-dlp>=2024.1.0
maxapi>=2.2.4
```
</details>

### 3. Configure environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your values (see [Configuration](#%EF%B8%8F-configuration) below).

### 4. Run

```bash
python bot.py
```

You should see:
```
==================================================
🤖 BOT STARTED (photo + video + clips)
==================================================
```

---

## ⚙️ Configuration

All settings are stored in `.env` (never commit this file — it's in `.gitignore`).

| Variable | Required | Example | Description |
|----------|:--------:|---------|-------------|
| `VK_SERVICE_TOKEN` | ✅ | `b5f47704...` | VK service access token ([get it](https://dev.vk.com/apps)) |
| `VK_GROUP_ID` | ✅ | `-174162942` | Numeric ID of VK group (with leading `-`) |
| `MAX_BOT_TOKEN` | ✅ | `f9LHodD0...` | Bot token from @MasterBot in MAX |
| `MAX_CHAT_ID` | ✅ | `-69410493377140` | Target channel ID (with leading `-`) |
| `ADMIN_ID` | ✅ | `16263028` | Your numeric MAX user ID |
| `API_URL` | ❌ | `https://platform-api2.max.ru` | MAX platform endpoint |

### 🔑 How to get the keys

<details>
<summary><b>1. VK Service Token</b></summary>

1. Go to [dev.vk.com/apps](https://dev.vk.com/apps) → **Create App**
2. Choose platform **Website** or **Standalone**
3. In app settings → copy **Service access token**
</details>

<details>
<summary><b>2. VK Group ID</b></summary>

Open any post in your group. The URL looks like:
```
https://vk.com/wall-174162942_123
```
The number **with the minus** (`-174162942`) is the group ID.
</details>

<details>
<summary><b>3. MAX Bot Token</b></summary>

1. Find @MasterBot (or @Metabot) in MAX
2. Send `/newbot`
3. Choose name and username
4. Copy the issued token
</details>

<details>
<summary><b>4. MAX Channel ID</b></summary>

1. Create a channel
2. Add your bot as admin
3. Channel IDs start with `-` (e.g., `-69410493377140`)
4. Can be obtained from MAX support or bot logs on first run
</details>

<details>
<summary><b>5. Your Admin ID</b></summary>

1. Run the bot
2. Send any message to it in DM
3. Find in console logs: `[DEBUG] message from user_id=16263028`
4. That number is your ID
</details>

---

## 🎮 Usage

### Interactive menu

Send `/start` to the bot in private DM. You'll see an inline keyboard:

```
┌──────────────────┬──────────────────┐
│  🟢 Status       │  📋 Logs         │
├──────────────────┴──────────────────┤
│  🛠 Tools >>                        │
└─────────────────────────────────────┘
```

**Tools menu:**
- 🔎 **Check VK** — force immediate check for new posts
- 📥 **Load 10** — backfill the last 10 posts to the channel
- ⬅️ **Back** — return to main menu

### 🔗 Manual repost

Send any VK post URL to the bot in DM:

```
https://vk.com/wall-174162942_504
```

Bot will:
1. ✅ Find the post
2. ✅ Download all media (photos, videos, clips)
3. ✅ Publish to your channel with inline keyboard

**Works with any public post** — from your group, other groups, or personal pages.

---

## 🛠 Troubleshooting

<details>
<summary><b>❌ <code>SSL: CERTIFICATE_VERIFY_FAILED</code></b></summary>

**Status:** ✅ Already handled. Bot uses `verify_ssl=False` to bypass DPI/Mintsifry certificate issues.

If you prefer a "proper" fix — add Mintsifry root CA to trusted certificates in the system store.
</details>

<details>
<summary><b>❌ Bot is silent / no reaction to buttons</b></summary>

1. Check `ADMIN_ID` in `.env` — it must match your user ID (see logs)
2. Make sure you've sent `/start` to the bot first
3. Verify the bot is running (check console output)
</details>

<details>
<summary><b>❌ Video not uploaded: <code>attachment.not.ready</code></b></summary>

MAX needs time to process uploaded videos. The bot waits 3–15 seconds automatically (based on file size).

If needed, increase `wait_time` in `upload_video_to_max()`:
```python
wait_time = min(max(5, file_size / 1024 / 1024 * 2), 30)  # longer wait
```
</details>

<details>
<summary><b>❌ Clip not downloadable</b></summary>

Some VK clips are protected. The bot will fall back to a "▶️ Watch" button linking to the original clip.

To download protected clips, a user-token-based approach is required (not implemented — feel free to contribute!).
</details>

<details>
<summary><b>❌ <code>errors.required</code> on empty posts</b></summary>

**Status:** ✅ Bot automatically skips posts without text and attachments. No action needed.
</details>

<details>
<summary><b>❌ Buttons stopped working after MAX API update</b></summary>

Update `maxapi` library:
```bash
pip install --upgrade maxapi
```

From 15.09.2026, MAX requires `maxapi >= 2.2.4` with the new `/me/commands`
