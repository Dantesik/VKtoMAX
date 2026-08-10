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

# 🤖 Репостер из ВКонтакте в MAX

<p align="center">
  <a href="#возможности"><img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python"></a>
  <a href="#возможности"><img src="https://img.shields.io/badge/aiohttp-async-green" alt="Async"></a>
  <a href="#возможности"><img src="https://img.shields.io/badge/yt--dlp-интегрирован-orange" alt="yt-dlp"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/лицензия-MIT-blue.svg" alt="License"></a>
</p>

<p align="center">
  <strong>Асинхронный бот для автоматического переноса постов из группы ВКонтакте в канал мессенджера MAX (VK Teams).</strong>
</p>

<p align="center">
  <a href="README.md">🇬🇧 English version</a>
</p>

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Как это работает](#-как-это-работает)
- [Быстрый старт](#-быстрый-старт)
- [Настройка](#%EF%B8%8F-настройка)
- [Использование](#-использование)
- [Ручной репост](#-ручной-репост)
- [Решение проблем](#-решение-проблем)
- [Запуск на сервере](#-запуск-на-сервере-vps)
- [Планы развития](#-планы-развития)
- [Лицензия](#-лицензия)

---

## ✨ Возможности

| Категория | Функция | Описание |
|-----------|---------|----------|
| 🎯 **Авторепост** | Умная очередь | Подтягивает пропущенные посты в хронологическом порядке |
| | Периодическая проверка | Автоматический опрос каждые 5 минут (настраивается) |
| 📸 **Медиа** | Фото | Скачивает и перезаливает в лучшем качестве |
| | Видео | Скачивает напрямую через VK API |
| | Клипы ВК | Скачивает через `yt-dlp` (даже с личных страниц) |
| | Внешние видео | YouTube/Rutube публикует как кнопку-ссылку |
| 🎮 **Управление** | Инлайн-меню | Кнопки Статус / Логи / Инструменты |
| | Белый список | Только настроенный `ADMIN_ID` может управлять ботом |
| 🔗 **Ручной репост** | URL → пост | Пришлите любую ссылку ВК → публикация в канал |
| 🛡️ **Надёжность** | Асинхронность | `aiohttp` — без блокировки event loop |
| | Retry-логика | `tenacity` для сетевых ошибок |
| | Корректное завершение | Обрабатывает SIGINT/SIGTERM |
| | Обход SSL | Автоматический обход сертификатов DPI/Минцифры |
| 🔒 **Безопасность** | Конфиг в `.env` | Секреты никогда не попадают в исходный код |
| | Только для админа | Команды доступны только администратору |

---

## 🔄 Как это работает

```
┌─────────────┐         ┌──────────┐         ┌─────────────┐
│  ВКонтакте  │ ──────► │   Бот    │ ──────► │  MAX канал  │
│   Группа    │   API   │ (async)  │   API   │             │
└─────────────┘         └──────────┘         └─────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ yt-dlp (для  │
                       │   клипов)    │
                       └──────────────┘
```

1. Бот опрашивает стену группы ВК каждые 5 минут через `wall.get`
2. Находит новые посты (ID > последнего сохранённого)
3. Скачивает медиа (фото через API, клипы через `yt-dlp`)
4. Перезаливает на CDN MAX
5. Публикует пост с инлайн-клавиатурой («🔗 Читать в ВК» + опционально «▶️ Смотреть»)
6. Сохраняет ID последнего поста в `last_post_id.txt`

---

## 🚀 Быстрый старт

### Требования

- **Python 3.10+** ([скачать](https://www.python.org/downloads/))
- **Git** ([скачать](https://git-scm.com/))

### 1. Клонируем репозиторий

```bash
git clone https://github.com/YOUR_USERNAME/vk-max-reposter.git
cd vk-max-reposter
```

### 2. Устанавливаем зависимости

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

### 3. Настраиваем окружение

Создайте файл `.env` в корне проекта:

```bash
cp .env.example .env
```

Отредактируйте `.env`, подставив свои значения (см. [Настройка](#%EF%B8%8F-настройка)).

### 4. Запускаем

```bash
python bot.py
```

В консоли должно появиться:
```
==================================================
🤖 БОТ ЗАПУЩЕН (фото + видео + клипы)
==================================================
```

---

## ⚙️ Настройка

Все настройки хранятся в `.env` (никогда не коммитьте этот файл — он в `.gitignore`).

| Переменная | Обязательно | Пример | Описание |
|------------|:-----------:|--------|----------|
| `VK_SERVICE_TOKEN` | ✅ | `b5f47704...` | Сервисный токен ВК ([получить](https://dev.vk.com/apps)) |
| `VK_GROUP_ID` | ✅ | `-174162942` | Числовой ID группы ВК (с минусом) |
| `MAX_BOT_TOKEN` | ✅ | `f9LHodD0...` | Токен бота от @MasterBot в MAX |
| `MAX_CHAT_ID` | ✅ | `-69410493377140` | ID целевого канала (с минусом) |
| `ADMIN_ID` | ✅ | `16263028` | Ваш числовой ID пользователя MAX |
| `API_URL` | ❌ | `https://platform-api2.max.ru` | Эндпоинт платформы MAX |

### 🔑 Как получить ключи

<details>
<summary><b>1. Сервисный токен ВК</b></summary>

1. Перейдите на [dev.vk.com/apps](https://dev.vk.com/apps) → **Создать приложение**
2. Выберите платформу **Сайт** или **Standalone**
3. В настройках приложения → скопируйте **Сервисный ключ доступа**
</details>

<details>
<summary><b>2. ID группы ВК</b></summary>

Откройте любой пост вашей группы. Ссылка выглядит так:
```
https://vk.com/wall-174162942_123
```
Число **с минусом** (`-174162942`) — это ID группы.
</details>

<details>
<summary><b>3. Токен бота MAX</b></summary>

1. Найдите @MasterBot (или @Metabot) в MAX
2. Отправьте `/newbot`
3. Выберите имя и username
4. Скопируйте выданный токен
</details>

<details>
<summary><b>4. ID канала MAX</b></summary>

1. Создайте канал
2. Добавьте бота в администраторы
3. ID канала начинаются с `-` (например, `-69410493377140`)
4. Можно получить через поддержку MAX или из логов при первом запуске
</details>

<details>
<summary><b>5. Ваш Admin ID</b></summary>

1. Запустите бота
2. Отправьте ему любое сообщение в личку
3. Найдите в логах консоли: `[DEBUG] сообщение от user_id=16263028`
4. Это число — ваш ID
</details>

---

## 🎮 Использование

### Интерактивное меню

Отправьте боту в личку `/start`. Появится инлайн-клавиатура:

```
┌──────────────────┬──────────────────┐
│  🟢 Статус       │  📋 Логи         │
├──────────────────┴──────────────────┤
│  🛠 Инструменты >>                  │
└─────────────────────────────────────┘
```

**Меню инструментов:**
- 🔎 **Проверить ВК** — немедленная проверка новых постов
- 📥 **Загрузить 10** — заполнить канал последними 10 постами
- ⬅️ **Назад** — вернуться в главное меню

### 🔗 Ручной репост

Пришлите боту в личку любую ссылку на пост ВК:

```
https://vk.com/wall-174162942_504
```

Бот:
1. ✅ Найдёт пост
2. ✅ Скачает все медиа (фото, видео, клипы)
3. ✅ Опубликует в ваш канал с инлайн-клавиатурой

**Работает с любым публичным постом** — из вашей группы, других групп или со страниц пользователей.

---

## 🛠 Решение проблем

<details>
<summary><b>❌ <code>SSL: CERTIFICATE_VERIFY_FAILED</code></b></summary>

**Статус:** ✅ Уже обработано. Бот использует `verify_ssl=False` для обхода проблем с сертификатами DPI/Минцифры.

Для «правильного» решения — добавьте корневой сертификат Минцифры в доверенные в системном хранилище.
</details>

<details>
<summary><b>❌ Бот молчит / не реагирует на кнопки</b></summary>

1. Проверьте `ADMIN_ID` в `.env` — должен совпадать с вашим user ID (видно в логах)
2. Убедитесь, что сначала отправили боту `/start`
3. Проверьте, что бот запущен (смотрите вывод консоли)
</details>

<details>
<summary><b>❌ Видео не загружается: <code>attachment.not.ready</code></b></summary>

MAX нужно время на обработку загруженных видео. Бот ждёт 3–15 секунд автоматически (зависит от размера).

При необходимости увеличьте `wait_time` в `upload_video_to_max()`:
```python
wait_time = min(max(5, file_size / 1024 / 1024 * 2), 30)  # более долгое ожидание
```
</details>

<details>
<summary><b>❌ Клип не скачивается</b></summary>

Некоторые клипы ВК защищены. Бот отправит кнопку «▶️ Смотреть» со ссылкой на оригинал.

Для скачивания защищённых клипов нужен user-token подход (не реализован — welcome to contribute!).
</details>

<details>
<summary><b>❌ <code>errors.required</code> на пустых постах</b></summary>

**Статус:** ✅ Бот автоматически пропускает посты без текста и вложений. Действий не требуется.
</details>

<details>
<summary><b>❌ Кнопки перестали работать после обновления MAX API</b></summary>

Обновите библиотеку `maxapi`:
```bash
pip install --upgrade maxapi
```

С 15.09.2026 MAX требует `maxapi >= 2.2.4` с новым эндпоинтом `/me/commands`.
</details>

---

## 🖥 Запуск на сервере (VPS)

Для круглосуточной работы на Linux-сервере используйте `systemd`.

### 1. Создаём файл сервиса

```bash
sudo nano /etc/systemd/system/vk-reposter.service
```

### 2. Вставляем конфигурацию

```ini
[Unit]
Description=VK to MAX Reposter Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/vk-reposter
EnvironmentFile=/opt/vk-reposter/.env
ExecStart=/usr/bin/python3 /opt/vk-reposter/bot.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/vk-reposter/bot.log
StandardError=append:/opt/vk-reposter/bot.log

[Install]
WantedBy=multi-user.target
```

### 3. Включаем и запускаем

```bash
sudo systemctl daemon-reload
sudo systemctl enable vk-reposter
sudo systemctl start vk-reposter

# Проверка статуса
sudo systemctl status vk-reposter

# Просмотр логов
tail -f /opt/vk-reposter/bot.log
```

---

## 🗺 Планы развития

- [ ] Режим пре-модерации (подтверждение постов перед публикацией)
- [ ] Тихие часы (отложенная публикация ночных постов утром)
- [ ] Стоп-лист ключевых слов (автопропуск рекламы/спама)
- [ ] Панель статистики (постов/день, ошибки, типы медиа)
- [ ] Запись логов в файл (а не только в консоль)
- [ ] Отложенные репосты («опубликовать в 18:00»)
- [ ] Режим еженедельного дайджеста
- [ ] Репост топ-комментариев вместе с постом

Полный список — в [открытых issues](../../issues).

---

## 🤝 Вклад в проект

Приветствуются любые вклады! Пожалуйста, следуйте этим шагам:

1. **Форкните** репозиторий
2. **Создайте ветку** для вашей фичи:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Внесите изменения** и протестируйте локально
4. **Закоммитьте** с понятным сообщением:
   ```bash
   git commit -m "Добавить классную функцию"
   ```
5. **Запушьте** и откройте **Pull Request**

---

## 📄 Лицензия

Проект распространяется под лицензией MIT — подробности в файле [LICENSE](LICENSE).

---

## ⭐ Понравился проект?

Поставьте звёздочку — это помогает другим найти проект!

<p align="center">
  <a href="https://github.com/YOUR_USERNAME/vk-max-reposter">
    <img src="https://img.shields.io/github/stars/YOUR_USERNAME/vk-max-reposter?style=social" alt="Stars">
  </a>
</p>

---

<p align="center">
  Сделано с ❤️ для сообщества MAX messenger
</p>
