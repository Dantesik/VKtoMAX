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


Конечно! Вот подробная, пошаговая инструкция на русском языке. Она написана так, чтобы понял даже человек, который первый раз видит код.

Вы можете сохранить этот текст в файл **`README.ru.md`** (или просто `Инструкция.txt`) и положить рядом с ботом.

---

# 🤖 Бот-Репостер из ВКонтакте в MAX (VK Teams)

**Инструкция по установке и настройке**

Этот бот автоматически копирует посты из вашей группы ВК и публикует их в канал мессенджера MAX (или VK Teams). Он умеет переносить текст, картинки, видео и даже имеет защиту от чужих рук.

---

### ШАГ 0. Подготовка компьютера

Перед началом убедитесь, что у вас установлен **Python**.

1. Скачайте Python с официального сайта: [python.org](https://www.python.org/downloads/).
2. **ВАЖНО:** При установке обязательно поставьте галочку **"Add Python to PATH"** (Добавить в путь).
3. Нажимайте "Install Now".

---

### ШАГ 1. Сбор секретных ключей 🔑

Чтобы бот заработал, нужно получить 5 "ключей". Скопируйте их куда-нибудь в блокнот.

**1. Токен ВКонтакте (VK Service Token):**

* Зайдите на [dev.vk.com/apps](https://www.google.com/search?q=https://dev.vk.com/apps) и нажмите "Создать приложение".
* Напишите любое название (например, "Мой Репостер"), выберите платформу "Сайт" (или Standalone).
* Зайдите в настройки созданного приложения -> раздел **"Настройки"**.
* Найдите поле **"Сервисный ключ доступа"**. Это длинная строка символов. Скопируйте её.

**2. ID группы ВКонтакте:**

* Откройте любой пост в вашей группе.
* В адресной строке будет ссылка вида `vk.com/wall-174162942_123`.
* Число с минусом (`-174162942`) — это и есть ID. Обязательно копируйте вместе с минусом!

**3. Токен бота MAX:**

* В мессенджере MAX найдите главного бота (обычно `@MasterBot` или `@Metabot`).
* Напишите ему команду `/newbot`.
* Придумайте имя и никнейм. Бот выдаст вам длинный токен. Скопируйте его.

**4. ID канала в MAX:**

* Создайте канал, куда бот будет писать.
* Добавьте созданного бота в администраторы канала.
* (Лайфхак: ID канала можно узнать, если запустить бота, и он попытается отправить сообщение. Но проще всего спросить у админов вашего корпоративного мессенджера, как узнать `chat_id`).

**5. Ваш ID (для защиты):**

* Это нужно, чтобы бот слушался только вас.
* Запустите бота (см. шаг 3), напишите ему любое сообщение.
* В черном окне консоли появится надпись: `⛔ Unauthorized access attempt (ID: 12345678)`.
* Число `12345678` — это ваш ID.

---

### ШАГ 2. Настройка файла ⚙️

1. Скачайте файл с кодом бота (`bot.py`).
2. Откройте его с помощью любого текстового редактора (Блокнот, Notepad++, VS Code).
3. В самом начале файла найдите блок настроек и вставьте свои данные внутрь кавычек:

```python
# ==========================================
# ⚙️ SETTINGS (НАСТРОЙКИ)
# ==========================================

VK_SERVICE_TOKEN = "ВСТАВЬТЕ_ТУТ_СЕРВИСНЫЙ_КЛЮЧ_ВК"
VK_GROUP_ID = -174162942  # Не забудьте минус!

MAX_BOT_TOKEN = "ВСТАВЬТЕ_ТУТ_ТОКЕН_БОТА_MAX"
MAX_CHAT_ID = -69410493377140 # ID канала (обычно начинается с минуса)

ADMIN_IDS = [12345678] # Ваш цифровой ID (без кавычек)

```

4. Сохраните файл (`Ctrl + S`).

---

### ШАГ 3. Запуск 🚀

1. Создайте папку (например, `Bot`) и положите туда файл `bot.py`.
2. Нажмите правой кнопкой мыши внутри папки (на пустом месте) -> **"Открыть в терминале"** (или запустите командную строку `cmd` и перейдите в папку).
3. Установите библиотеку (нужно один раз):
```bash
pip install requests

```


4. Запустите бота:
```bash
python bot.py

```



Если появилось черное окно и надпись `=== 🤖 VK TO MAX REPOSTER ===` — поздравляем, бот работает!

---

### ШАГ 4. Как пользоваться (Команды) 🎮

Напишите боту в личные сообщения (в мессенджере MAX):

* **/start** — Вызовет красивое меню с кнопками.
* **Кнопка "🔎 Check Now"** — Бот немедленно проверит группу ВК на новые посты.
* **Кнопка "🟢 Status"** — Проверка, что бот жив и не завис.
* **Кнопка "📋 Logs"** — Покажет последние действия (что скачал, где ошибся).

**Полезная фишка "Заполнение канала":**
Если вы только создали канал, напишите команду:
`/fill 10`
Бот возьмет 10 последних постов из ВК и загрузит их в канал по порядку.

---

### Частые вопросы ❓

**Q: Бот выключился, когда я закрыл черное окно!**
A: Да, бот работает, только пока запущено окно консоли. Если хотите, чтобы он работал всегда — его нужно запускать на сервере (VDS).

**Q: Бот пишет "Unauthorized access attempt" и не отвечает.**
A: Вы забыли вписать свой цифровой ID в список `ADMIN_IDS` в файле `bot.py`. Посмотрите, какое число пишет бот в консоли, и впишите его в код.

**Q: Ошибка "ProxyError".**
A: В коде уже встроена защита от этого. Если ошибка есть — попробуйте полностью отключить VPN на компьютере.
