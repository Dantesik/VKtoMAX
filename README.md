## 🇬🇧 README.md (English)

```markdown
# VK to MAX Messenger Reposter Bot

A robust asynchronous Python bot for automatically reposting content from a VKontakte group to a MAX (VK Teams) messenger channel. Supports photos, videos, clips, and manual reposting from any VK source.

## Features 🚀

- **Smart Queue**: Checks the last 10 posts and reposts missed content in chronological order (great after downtime).
- **Full Media Support**:
  - 📷 Photos — downloads and re-uploads in best quality
  - 🎥 Videos — downloads directly from VK API
  - 🎬 VK Clips — downloads via `yt-dlp` (even from personal pages)
  - 🌐 External videos (YouTube, Rutube) — posted as a player link button
- **Manual Repost**: Send any VK post URL (from any group or user) to the bot in DM — it will repost it to the channel.
- **Smart Filtering**:
  - Automatically skips reposts (`copy_history`)
  - Skips empty posts (no text, no attachments)
- **Interactive Inline Keyboard**:
  - 🔗 "Read in VK" button on every post
  - ▶️ "Watch" fallback button when video cannot be downloaded
- **Admin Panel**: Control via private DM with inline keyboard menu (Status, Logs, Tools).
- **Security**: Single-admin whitelist (responds only to configured `ADMIN_ID`).
- **Reliability**:
  - Async `aiohttp` client (no blocking of the event loop)
  - Retry logic via `tenacity` for network errors
  - Auto-wait for MAX video processing
  - Graceful shutdown on SIGINT/SIGTERM
- **SSL Bypass**: Built-in workaround for Mintsifry root certificate issues on some networks.

## Setup 🛠️

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/vk-max-reposter.git
cd vk-max-reposter
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
VK_SERVICE_TOKEN=b5f47704b5f47704...
VK_GROUP_ID=-174162942
MAX_BOT_TOKEN=f9LHodD0cOJNfBFU7hLtvpNV7uySDAhHEs2gFYu3-Rzyl1_UBZOoM8pyiK-nODheZFFGur4XRYKPWN0X-CKM
MAX_CHAT_ID=-69410493377140
ADMIN_ID=16263028
API_URL=https://platform-api2.max.ru
```

| Variable | Description |
|---|---|
| `VK_SERVICE_TOKEN` | VK App service access token (from `dev.vk.com`) |
| `VK_GROUP_ID` | Numeric ID of the VK group (with leading `-`) |
| `MAX_BOT_TOKEN` | Bot token from @MasterBot in MAX |
| `MAX_CHAT_ID` | Numeric ID of the target channel (with leading `-`) |
| `ADMIN_ID` | Your numeric MAX user ID |
| `API_URL` | MAX platform endpoint (optional, defaults to `platform-api2.max.ru`) |

> ⚠️ **Never commit the `.env` file!** It's already listed in `.gitignore`.

### 3. Run

```bash
python bot.py
```

## Usage 🕹️

### Interactive menu

Send `/start` to the bot in private DM. You'll get an inline keyboard:

- 🟢 **Status** — show current time and confirm the bot is alive
- 📋 **Logs** — last 15 log entries
- 🛠 **Tools** — submenu with:
  - 🔎 **Check VK** — force a check for new posts
  - 📥 **Load 10** — backfill the last 10 posts

### Manual repost

Simply paste any VK post URL into the bot's DM:

```
https://vk.com/wall-174162942_504
```

The bot will fetch the post (including photos, videos and clips) and publish it to the channel. Works with posts from **any group or personal page**.

## Dependencies

- `aiohttp` — async HTTP client
- `python-dotenv` — environment variables
- `tenacity` — retry logic
- `yt-dlp` — video/clip downloader
- `maxapi` — MAX messenger bot framework (v2.2.4+)

## Troubleshooting

| Issue | Solution |
|---|---|
| `SSL: CERTIFICATE_VERIFY_FAILED` | Already handled — bot uses `verify_ssl=False` |
| Bot is silent / no reaction to buttons | Check that `ADMIN_ID` in `.env` matches your user ID (visible in logs) |
| Video not uploaded, `attachment.not.ready` | Bot auto-waits up to 15s; increase `wait_time` in `upload_video_to_max` if needed |
| Clip not downloadable | Some clips are private — bot will fall back to a "Watch" button |
| `errors.required` on empty posts | Bot now auto-skips them |

## License

MIT
```

---

## 🇷🇺 README.ru.md (Русская инструкция)

```markdown
# 🤖 Бот-Репостер из ВКонтакте в MAX (VK Teams)

Асинхронный Python-бот для автоматического переноса постов из группы ВКонтакте в канал мессенджера MAX. Умеет переносить текст, фото, видео, клипы и поддерживает ручной репост по ссылке.

## Возможности 🚀

- **Умная очередь**: при первом запуске подтягивает последние 10 постов в хронологическом порядке.
- **Полная поддержка медиа**:
  - 📷 Фото — скачивает и перезаливает в лучшем качестве
  - 🎥 Видео — скачивает через VK API
  - 🎬 Клипы — скачивает через `yt-dlp` (работает даже с клипами с личных страниц)
  - 🌐 Внешние видео (YouTube, Rutube) — публикует как кнопку со ссылкой на плеер
- **Ручной репост**: пришлите боту в личку ссылку на пост ВК (из любой группы или личной страницы) — он опубликует его в канал.
- **Умная фильтрация**:
  - Автоматически пропускает репосты (`copy_history`)
  - Пропускает пустые посты (без текста и вложений)
- **Интерактивное меню с кнопками**:
  - 🔗 «Читать в ВК» у каждого поста
  - ▶️ «Смотреть» как фолбэк, когда видео нельзя скачать
- **Админ-панель**: управление через личную переписку (Статус, Логи, Инструменты).
- **Безопасность**: бот слушается только одного админа по `ADMIN_ID`.
- **Надёжность**:
  - Полностью асинхронный (через `aiohttp`)
  - Retry-логика для сетевых ошибок (`tenacity`)
  - Автоожидание обработки видео на сервере MAX
  - Корректное завершение по Ctrl+C (SIGINT/SIGTERM)
- **Обход сертификатов Минцифры**: бот автоматически работает через провайдеров с подменой SSL.

## Установка 🛠️

### Шаг 0. Подготовка

Установите **Python 3.10+** с официального сайта: [python.org](https://www.python.org/downloads/).
⚠️ **Обязательно** поставьте галочку «Add Python to PATH» при установке.

### Шаг 1. Сбор секретных ключей 🔑

Все ключи будут храниться в файле `.env` (а не в коде), это безопасно.

**1. Сервисный токен ВКонтакте:**
- Зайдите на [dev.vk.com/apps](https://dev.vk.com/apps) → «Создать приложение»
- Назовите его (например, «Репостер»), платформа — «Сайт» или «Standalone»
- В настройках приложения скопируйте **«Сервисный ключ доступа»**

**2. ID группы ВКонтакте:**
- Откройте любой пост вашей группы
- В адресной строке будет `vk.com/wall-174162942_123`
- Скопируйте число **с минусом** (`-174162942`)

**3. Токен бота MAX:**
- В MAX найдите @MasterBot (или @Metabot) и напишите `/newbot`
- Придумайте имя и никнейм — получите длинный токен

**4. ID канала в MAX:**
- Создайте канал и добавьте бота в администраторы
- ID канала начинается с минуса (например, `-69410493377140`)
- Узнать можно через поддержку MAX или через лог при первом запуске

**5. Ваш ID (для защиты):**
- Запустите бота, напишите ему что-нибудь в личку
- В консоли появится строка вида `[DEBUG] сообщение от user_id=16263028`
- Это и есть ваш ID

### Шаг 2. Настройка `.env`

Создайте в папке с ботом файл с именем `.env` (с точкой в начале) и заполните его:

```env
VK_SERVICE_TOKEN=b5f47704b5f47704...
VK_GROUP_ID=-174162942
MAX_BOT_TOKEN=f9LHodD0cOJNfBFU7hLtvpNV7uySDAhHEs2gFYu3-Rzyl1_UBZOoM8pyiK-nODheZFFGur4XRYKPWN0X-CKM
MAX_CHAT_ID=-69410493377140
ADMIN_ID=16263028
API_URL=https://platform-api2.max.ru
```

> ⚠️ **Никогда не выкладывайте `.env` в интернет!** В нём секретные токены.

### Шаг 3. Установка зависимостей

Откройте терминал в папке с ботом и выполните:

```bash
pip install aiohttp python-dotenv tenacity yt-dlp maxapi
```

### Шаг 4. Запуск 🚀

```bash
python bot.py
```

Если увидели `🤖 БОТ ЗАПУЩЕН` — всё работает!

## Использование 🎮

### Интерактивное меню

Напишите боту в личку `/start` — появится меню с кнопками:

- 🟢 **Статус** — проверка, что бот жив
- 📋 **Логи** — последние 15 записей из журнала
- 🛠 **Инструменты** → подменю:
  - 🔎 **Проверить ВК** — немедленная проверка новых постов
  - 📥 **Загрузить 10** — заполнить канал последними 10 постами

### Ручной репост по ссылке

Просто пришлите боту в личку ссылку на пост ВК:

```
https://vk.com/wall-174162942_504
```

Бот найдёт пост (с фото, видео, клипами) и опубликует его в канал. Работает с постами из **любой группы или со страницы пользователя**.

## Зависимости

- `aiohttp` — асинхронный HTTP-клиент
- `python-dotenv` — чтение `.env`
- `tenacity` — повторные попытки при ошибках
- `yt-dlp` — скачивание видео и клипов
- `maxapi` (v2.2.4+) — SDK для ботов MAX

## Частые вопросы ❓

| Проблема | Решение |
|---|---|
| `SSL: CERTIFICATE_VERIFY_FAILED` | Уже обработано — бот сам обходит сертификат Минцифры |
| Бот молчит / не реагирует на кнопки | Проверьте `ADMIN_ID` в `.env` — он должен совпадать с вашим user ID |
| Видео не загружается, `attachment.not.ready` | Бот сам ждёт до 15 секунд; если не хватает — увеличьте `wait_time` в `upload_video_to_max` |
| Клип не скачивается | Некоторые клипы приватные — бот отправит кнопку «▶️ Смотреть» |
| `errors.required` на пустых постах | Бот теперь автоматически их пропускает |
| Кнопки не работают | Обновите библиотеку: `pip install --upgrade maxapi` |
| Бот «завис» | Нажмите Ctrl+C в консоли и запустите снова |
| Остановка через Ctrl+C не срабатывает | Убедитесь, что в консоли видно `Завершение работы...` — это graceful shutdown |

## Автозапуск на сервере (VDS)

Чтобы бот работал 24/7 на Linux-сервере, используйте `systemd`:

```bash
sudo nano /etc/systemd/system/vk-reposter.service
```

Вставьте:

```ini
[Unit]
Description=VK to MAX Reposter
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
EnvironmentFile=/path/to/bot/.env
ExecStart=/usr/bin/python3 /path/to/bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запустите:

```bash
sudo systemctl enable vk-reposter
sudo systemctl start vk-reposter
```

## Лицензия

MIT
```

---

## 📋 Что изменилось по сравнению со старой инструкцией

| Раздел | Было | Стало |
|---|---|---|
| **Зависимости** | Только `requests` | `aiohttp`, `python-dotenv`, `tenacity`, `yt-dlp`, `maxapi` |
| **Конфигурация** | Хардкод в `bot.py` | Отдельный `.env` файл (безопасно!) |
| **Команды** | `/stop`, `/fill N`, `/check` текстом | Inline-кнопки в меню |
| **Медиа** | Только фото | + Видео, клипы, внешние видео |
| **Ручной репост** | ❌ Не было | ✅ Любая ссылка ВК → пост в канал |
| **Фильтрация** | ❌ | ✅ Пропуск репостов и пустых постов |
| **Автозапуск** | ❌ Не описано | ✅ systemd-инструкция для VDS |
| **Troubleshooting** | 3 пункта | 8+ актуальных проблем с решениями |

Обе инструкции готовы к использованию — просто замените ими старые файлы. Если захотите добавить раздел с примерами логов или скриншотами меню — пишите, помогу оформить.
