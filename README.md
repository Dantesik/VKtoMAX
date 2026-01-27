# VK to MAX Messenger Reposter Bot

Simple and robust Python bot for automatically reposting content from a VKontakte group to a MAX (VK Teams based) messenger channel.

## Features 🚀

* **Smart Queue:** Checks the last 10 posts and reposts *all* missed content in chronological order (great if the bot was offline).
* **Media Support:** Downloads and re-uploads high-quality photos.
* **Interactive Buttons:** Adds a "🔗 Open in VK" button to every message.
* **Admin Panel:** Control the bot via private messages (`/status`, `/check`, `/log`, `/stop`).
* **Security:** Whitelist system (responds only to authorized Admin IDs).
* **Backfill:** Command `/fill 10` to instantly load the last 10 posts to an empty channel.
* **Proxy Fix:** Automatically bypasses system proxies to avoid `ProxyError` on Windows.

## Setup 🛠️

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/vk-max-reposter.git](https://github.com/YOUR_USERNAME/vk-max-reposter.git)
    cd vk-max-reposter
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure:**
    Open `bot.py` and edit the SETTINGS section:
    * `VK_SERVICE_TOKEN`: Your VK App Service Token.
    * `VK_GROUP_ID`: ID of the VK group (e.g., -123456).
    * `MAX_BOT_TOKEN`: Token from @MasterBot in MAX.
    * `MAX_CHAT_ID`: ID of the target channel in MAX.
    * `ADMIN_IDS`: Your numeric User ID in MAX (for security).

4.  **Run:**
    ```bash
    python bot.py
    ```

## Admin Commands 🕹️

Send these commands to the bot in private messages:

* `/start` - Show the interactive menu button.
* `/check` - Force check for new posts immediately.
* `/log` - Show the last 15 log entries (debug).
* `/fill N` - (e.g., `/fill 5`) Repost the last N posts immediately.
* `/stop` - Stop the bot script remotely.

## License
MIT
