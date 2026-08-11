import json
import asyncio
import logging
import os
import signal
import re
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Any

import aiohttp
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import yt_dlp

# ==========================================
# ⚙️ ЗАГРУЗКА НАСТРОЕК
# ==========================================
load_dotenv()

VK_SERVICE_TOKEN = os.getenv("VK_SERVICE_TOKEN")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
MAX_CHAT_ID = int(os.getenv("MAX_CHAT_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID_MAX", "0"))  # или ADMIN_ID, как у тебя
API_URL = os.getenv("API_URL", "https://platform-api2.max.ru")

# ==========================================
# 🔢 КОНСТАНТЫ
# ==========================================
VK_VERSION = "5.131"
LOG_BUFFER_SIZE = 15
POST_SEND_DELAY_SEC = 3
CHECK_INTERVAL_SEC = 300
DEFAULT_POSTS_COUNT = 10
LAST_POST_FILE = "last_post_id.txt"
MAX_VIDEO_SIZE_MB = 500
DOWNLOAD_CHUNK_SIZE = 1024 * 1024

VK_POST_PATTERN = re.compile(r"wall(-?\d+)_(\d+)")

VIDEO_QUALITY_KEYS = [
    "mp4_2160", "mp4_1440", "mp4_1080", "mp4_720",
    "mp4_480", "mp4_360", "mp4_240"
]

MIME_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}

# ==========================================
# 📝 ЛОГИРОВАНИЕ
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logs_buffer: deque = deque(maxlen=LOG_BUFFER_SIZE)
shutdown_event = asyncio.Event()

# ==========================================
# 📦 ИМПОРТ MAXAPI
# ==========================================
try:
    from maxapi import Bot, Dispatcher
    from maxapi.types import Command, MessageCreated, MessageCallback, CallbackButton
    from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
except ImportError as e:
    logger.critical(f"Не удалось импортировать maxapi: {e}")
    raise


def log(text: str) -> None:
    logger.info(text)
    logs_buffer.append(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")


# ==========================================
# 🔧 HTTP-КЛИЕНТ
# ==========================================
class HttpClient:
    def __init__(self, verify_ssl: bool = True):
        self.verify_ssl = verify_ssl
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        connector = aiohttp.TCPConnector(ssl=self.verify_ssl, limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=600)
        self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("HTTP-сессия не инициализирована.")
        return self._session


http = HttpClient(verify_ssl=False)
vk_http = HttpClient(verify_ssl=False)


# ==========================================
# 📤 ОТПРАВКА В MAX
# ==========================================
async def send_content_to_max(chat_id: int, text: str, attachments: List[Dict[str, Any]]) -> bool:
    url = f"{API_URL}/messages"
    headers = {"Authorization": MAX_BOT_TOKEN, "Content-Type": "application/json"}
    payload = {"text": text, "attachments": attachments}
    params = {"chat_id": chat_id}

    try:
        async with http.session.post(url, headers=headers, params=params, json=payload) as r:
            if r.status != 200:
                body = await r.text()
                log(f"Max API ошибка: {r.status} {body}")
                return False
            return True
    except aiohttp.ClientError as e:
        log(f"Max сетевая ошибка: {e}")
        return False


# ==========================================
# 🖼️ ФОТО
# ==========================================
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    reraise=True,
)
async def upload_photo_to_max(vk_photo_url: str) -> Optional[str]:
    async with vk_http.session.get(vk_photo_url) as img_resp:
        if img_resp.status != 200:
            return None
        image_bytes = await img_resp.read()
        content_type = img_resp.headers.get("Content-Type", "image/jpeg")
        ext = MIME_MAP.get(content_type, "jpg")

    headers = {"Authorization": MAX_BOT_TOKEN}
    async with http.session.post(
        f"{API_URL}/uploads", params={"type": "image"}, headers=headers
    ) as req:
        data = await req.json()
        upload_url = data.get("url") or (data.get("payload") or {}).get("url")
        if not upload_url:
            return None

    form = aiohttp.FormData()
    form.add_field("data", image_bytes, filename=f"photo.{ext}", content_type=content_type)

    async with http.session.post(upload_url, data=form, headers=headers) as file_resp:
        if file_resp.status != 200:
            return None
        file_data = await file_resp.json()

    if "photos" in file_data:
        for key in file_data["photos"]:
            if "token" in file_data["photos"][key]:
                return file_data["photos"][key]["token"]
    if "token" in file_data:
        return file_data["token"]
    return None


# ==========================================
# 🎬 ЗАГРУЗКА ВИДЕО В MAX
# ==========================================
async def upload_video_to_max(video_path: str, title: str = "video") -> Optional[str]:
    """Загружает видео в Max API с ожиданием обработки."""
    try:
        headers = {"Authorization": MAX_BOT_TOKEN}
        
        # 1. Получаем URL для загрузки и токен (сразу!)
        async with http.session.post(
            f"{API_URL}/uploads", params={"type": "video"}, headers=headers
        ) as req:
            if req.status != 200:
                log(f"Max uploads video: статус {req.status}")
                return None
            
            response_text = await req.text()
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                log(f"[DEBUG] Не удалось распарсить ответ от /uploads")
                return None
            
            upload_url = data.get("url")
            video_token = data.get("token")
            
            if not upload_url or not video_token:
                log(f"[DEBUG] Нет url или token в ответе: {data}")
                return None
            
            log(f"✅ Получен токен: {video_token[:30]}...")

        # 2. Загружаем файл на CDN
        file_size = os.path.getsize(video_path)
        log(f"Загружаю видео на CDN ({file_size / 1024 / 1024:.1f} МБ)...")

        form = aiohttp.FormData()
        with open(video_path, "rb") as f:
            form.add_field("data", f, filename=f"{title}.mp4", content_type="video/mp4")
            
            async with http.session.post(upload_url, data=form) as file_resp:
                log(f"[DEBUG] Статус загрузки на CDN: {file_resp.status}")
                
                if file_resp.status != 200:
                    body = await file_resp.text()
                    log(f"Загрузка на CDN не удалась: {body[:200]}")
                    return None

        # 3. Ждём обработки видео на сервере Max
        # Для больших видео нужно больше времени, для маленьких — меньше
        wait_time = min(max(3, file_size / 1024 / 1024), 15)  # от 3 до 15 секунд
        log(f"Жду обработки видео ({wait_time:.1f} сек)...")
        await asyncio.sleep(wait_time)
        
        # 4. Возвращаем токен
        log(f"✅ Видео готово к отправке: {video_token[:30]}...")
        return video_token

    except Exception as e:
        log(f"upload_video_to_max ошибка: {type(e).__name__}: {e}")
        return None


# ==========================================
# 📥 СКАЧИВАНИЕ ЧЕРЕЗ YT-DLP (главное изменение)
# ==========================================
async def download_vk_video(url: str, output_path: str) -> bool:
    """Скачивает видео с VK через yt-dlp (работает и для обычных видео, и для клипов)."""
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4][vcodec!=none]/best[ext=mp4]/best',  # Только видео с видео-кодеком
        'merge_output_format': 'mp4',  # Принудительно объединять в MP4
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'retries': 3,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
    }

    try:
        log(f"[yt-dlp] Начинаю скачивание: {url}")
        loop = asyncio.get_event_loop()

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await loop.run_in_executor(None, _download)

        # yt-dlp может добавить расширение, проверяем варианты
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024 / 1024
            log(f"[yt-dlp] ✅ Скачано: {file_size:.1f} МБ")
            return True
        
        # yt-dlp мог сохранить с другим расширением
        for ext in ['.mp4', '.mkv', '.webm']:
            candidate = output_path.replace('.mp4', ext)
            if os.path.exists(candidate):
                os.rename(candidate, output_path)
                log(f"[yt-dlp] ✅ Переименовано: {ext} → .mp4")
                return True

        log("[yt-dlp] ❌ Файл не найден после скачивания")
        return False

    except Exception as e:
        log(f"[yt-dlp] ❌ Ошибка: {e}")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        return False


async def download_and_upload_video(video_url: str, title: str = "video") -> Optional[str]:
    """Скачивает видео через yt-dlp и загружает в Max."""
    timestamp = int(datetime.now().timestamp() * 1000)
    temp_video_path = f"temp_video_{timestamp}.mp4"

    try:
        success = await download_vk_video(video_url, temp_video_path)
        if not success:
            return None

        # Проверяем размер
        file_size = os.path.getsize(temp_video_path) / 1024 / 1024
        if file_size > MAX_VIDEO_SIZE_MB:
            log(f"Видео слишком большое: {file_size:.1f} МБ")
            return None

        token = await upload_video_to_max(temp_video_path, title)
        return token

    finally:
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except OSError:
                pass


# ==========================================
# 📺 РАБОТА С VK VIDEO API (для обычных видео)
# ==========================================
async def get_vk_video_files(
    owner_id: int, video_id: int, access_key: Optional[str] = None, is_clips: bool = False
) -> Optional[Dict[str, str]]:
    url = "https://api.vk.com/method/video.get"
    video_ref = f"{owner_id}_{video_id}"
    if access_key:
        video_ref = f"{video_ref}_{access_key}"

    params = {"access_token": VK_SERVICE_TOKEN, "videos": video_ref, "v": VK_VERSION}

    attempts = [params]
    if is_clips and access_key:
        attempts.append({
            "access_token": VK_SERVICE_TOKEN,
            "videos": f"{owner_id}_{video_id}",
            "v": VK_VERSION,
        })

    for attempt_params in attempts:
        try:
            async with vk_http.session.get(url, params=attempt_params) as r:
                response = await r.json()

            if "response" not in response:
                continue
            if response["response"].get("count", 0) == 0:
                continue

            video_item = response["response"]["items"][0]
            files = video_item.get("files", {})
            player = video_item.get("player")

            if files:
                media_type = "клипа" if is_clips else "видео"
                log(f"VK: получены файлы для {media_type} {owner_id}_{video_id}")
                return files
            if player:
                return {"player": player}
        except Exception as e:
            log(f"VK video.get ошибка: {e}")
            continue

    return None


def select_best_video_url(files: Dict[str, str]) -> Optional[str]:
    for key in VIDEO_QUALITY_KEYS:
        if key in files and files[key]:
            return files[key]
    return files.get("player")


def is_clip_attachment(attachment: Dict[str, Any]) -> bool:
    if attachment.get("type") != "video":
        return False
    video = attachment.get("video", {})
    return (
        video.get("type") == "short_video"
        or video.get("is_clips_video", False)
        or video.get("is_clips", False)
        or "is_clips_video" in video
        or (video.get("width", 0) > 0 and video.get("height", 0) > 0 and video.get("height", 0) > video.get("width", 0))
    )


# ==========================================
# 📰 VK API
# ==========================================
async def get_vk_posts(count: int = DEFAULT_POSTS_COUNT) -> List[Dict[str, Any]]:
    url = "https://api.vk.com/method/wall.get"
    params = {"access_token": VK_SERVICE_TOKEN, "owner_id": VK_GROUP_ID, "count": count + 5, "v": VK_VERSION}
    try:
        async with vk_http.session.get(url, params=params) as r:
            response = await r.json()
        if "response" not in response:
            return []
        items = response["response"]["items"]
        real_posts = [p for p in items if not p.get("is_pinned")]
        return (real_posts or items)[:count]
    except Exception as e:
        log(f"VK ошибка: {e}")
        return []


async def get_last_vk_post() -> Optional[Dict[str, Any]]:
    posts = await get_vk_posts(count=1)
    return posts[0] if posts else None


async def get_vk_post_by_id(owner_id: int, post_id: int) -> Optional[Dict[str, Any]]:
    url = "https://api.vk.com/method/wall.getById"
    params = {"access_token": VK_SERVICE_TOKEN, "posts": f"{owner_id}_{post_id}", "v": VK_VERSION}
    try:
        async with vk_http.session.get(url, params=params) as r:
            response = await r.json()
        if "response" not in response:
            return None
        resp = response["response"]
        items = resp if isinstance(resp, list) else resp.get("items", [])
        return items[0] if items else None
    except Exception as e:
        log(f"VK wall.getById ошибка: {e}")
        return None


# ==========================================
# ⌨️ КЛАВИАТУРЫ
# ==========================================
def get_main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        CallbackButton(text="🟢 Статус", payload="/status"),
        CallbackButton(text="📋 Логи", payload="/log"),
    )
    kb.row(CallbackButton(text="🛠 Инструменты >>", payload="/menu_tools"))
    return kb.as_markup()


def get_tools_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text="🔎 Проверить ВК", payload="/check"))
    kb.row(CallbackButton(text="📥 Загрузить 10", payload="/fill_10"))
    kb.row(CallbackButton(text="<< Назад", payload="/menu_main"))
    return kb.as_markup()


# ==========================================
# 🤖 ОБРАБОТЧИКИ
# ==========================================
dp = Dispatcher()


@dp.message_created(Command("start"))
async def start_handler(event: MessageCreated) -> None:
    try:
        if event.from_user.user_id != ADMIN_ID:
            return
        await event.bot.send_message(
            user_id=event.from_user.user_id,
            text="🏠 **Главное меню**",
            attachments=[get_main_kb()],
        )
    except Exception as e:
        log(f"start_handler ошибка: {e}")


@dp.message_created()
async def manual_repost_handler(event: MessageCreated) -> None:
    try:
        user_id = getattr(event.from_user, "user_id", None)
        if user_id != ADMIN_ID:
            return

        body = getattr(getattr(event, "message", None), "body", None)
        text = getattr(body, "text", "") or ""
        if not text or text.strip().startswith("/"):
            return

        match = VK_POST_PATTERN.search(text)
        if not match:
            return

        owner_id = int(match.group(1))
        post_id = int(match.group(2))
        log(f"Ручной репост: {owner_id}_{post_id}")

        await event.bot.send_message(user_id=user_id, text="🔎 Ищу пост...")

        post = await get_vk_post_by_id(owner_id, post_id)
        if not post:
            await event.bot.send_message(user_id=user_id, text="❌ Пост не найден.")
            return

        success = await publish_post(post)
        if success:
            await event.bot.send_message(user_id=user_id, text=f"✅ Пост {post_id} опубликован!")
        else:
            await event.bot.send_message(user_id=user_id, text="❌ Не удалось опубликовать.")
    except Exception as e:
        log(f"manual_repost ошибка: {e}")


@dp.message_callback()
async def callback_handler(callback: MessageCallback) -> None:
    try:
        user_id = None
        from_user = getattr(callback, "from_user", None)
        if from_user is not None:
            user_id = getattr(from_user, "user_id", None) or getattr(from_user, "id", None)
        if user_id is None:
            user_id = getattr(callback, "user_id", None)

        if user_id != ADMIN_ID:
            try:
                await callback.answer(text="⛔ Доступ запрещен", show_alert=True)
            except Exception:
                pass
            return

        try:
            await callback.answer()
        except Exception:
            pass

        payload = getattr(getattr(callback, "callback", None), "payload", None)
        log(f"Команда: {payload}")

        if payload == "/status":
            await callback.message.edit(
                text=f"🤖 В сети.\n🕒 {datetime.now().strftime('%H:%M:%S')}",
                attachments=[get_main_kb()],
            )
        elif payload == "/log":
            log_text = "📋 **Логи:**\n" + "\n".join(logs_buffer)
            await callback.message.edit(text=log_text, attachments=[get_main_kb()])
        elif payload == "/menu_tools":
            await callback.message.edit(text="🛠 Меню инструментов", attachments=[get_tools_kb()])
        elif payload == "/menu_main":
            await callback.message.edit(text="🏠 **Главное меню**", attachments=[get_main_kb()])
        elif payload == "/check":
            await callback.message.edit(text="🔎 Проверяю...", attachments=[get_tools_kb()])
            new_count = await run_vk_check()
            await callback.message.edit(
                text=f"✅ Проверка завершена. Новых: {new_count}",
                attachments=[get_tools_kb()],
            )
        elif payload == "/fill_10":
            await callback.message.edit(text="🚀 Загружаю...", attachments=[get_tools_kb()])
            loaded = await run_vk_check(force_count=10)
            await callback.message.edit(
                text=f"✅ Загружено: {loaded}", attachments=[get_tools_kb()]
            )
    except Exception as e:
        log(f"Callback ошибка: {e}")


# ==========================================
# 📮 ПУБЛИКАЦИЯ ПОСТОВ
# ==========================================
def read_last_id() -> int:
    if not os.path.exists(LAST_POST_FILE):
        return 0
    try:
        with open(LAST_POST_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (ValueError, OSError) as e:
        log(f"Ошибка чтения {LAST_POST_FILE}: {e}")
        return 0


def write_last_id(post_id: int) -> None:
    try:
        with open(LAST_POST_FILE, "w", encoding="utf-8") as f:
            f.write(str(post_id))
    except OSError as e:
        log(f"Ошибка записи {LAST_POST_FILE}: {e}")


async def process_attachment(attachment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    att_type = attachment.get("type")

    # --- ФОТО ---
    if att_type == "photo":
        sizes = attachment.get("photo", {}).get("sizes", [])
        if not sizes:
            return None
        best = sorted(sizes, key=lambda x: x.get("width", 0))[-1]
        try:
            token = await upload_photo_to_max(best["url"])
            if token:
                return {"type": "image", "payload": {"token": token}}
        except Exception as e:
            log(f"Ошибка загрузки фото: {e}")
        return None

    # --- ВИДЕО / КЛИП (через yt-dlp) ---
    elif att_type == "video":
        video = attachment.get("video", {})
        owner_id = video.get("owner_id")
        video_id = video.get("id")
        title = video.get("title", "video")
        access_key = video.get("access_key")
        is_clips = is_clip_attachment(attachment)

        if not owner_id or not video_id:
            return None

        media_type = "клип" if is_clips else "видео"
        log(f"Обрабатываю {media_type}: {owner_id}_{video_id} «{title}»")

        # СНАЧАЛА пробуем получить прямые ссылки (быстро для обычных видео)
        if not is_clips:
            files = await get_vk_video_files(owner_id, video_id, access_key=access_key)
            video_url = select_best_video_url(files) if files else None
            
            if video_url and "player" not in video_url:
                # Прямая ссылка есть — скачиваем напрямую
                log(f"Прямая ссылка доступна, скачиваю напрямую")
                try:
                    token = await download_and_upload_video(video_url, title)
                    if token:
                        return {"type": "video", "payload": {"token": token}}
                except Exception as e:
                    log(f"Ошибка прямой загрузки: {e}")
                return None

        # Для клипов или если прямых ссылок нет — используем yt-dlp
        video_page_url = f"https://vk.com/video{owner_id}_{video_id}"
        log(f"{media_type}: использую yt-dlp ({video_page_url})")
        
        try:
            token = await download_and_upload_video(video_page_url, title)
            if token:
                return {"type": "video", "payload": {"token": token}}
        except Exception as e:
            log(f"yt-dlp ошибка: {e}")

        # Fallback — кнопка со ссылкой
        log(f"{media_type} не удалось скачать — шлю ссылку")
        return {
            "type": "extra_buttons",
            "buttons": [[{
                "type": "link",
                "text": f"▶️ Смотреть {media_type}",
                "url": video_page_url,
            }]]
        }

    # --- ССЫЛКА ---
    elif att_type == "link":
        link_data = attachment.get("link", {})
        url = link_data.get("url")
        if url:
            return {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": [[{
                        "type": "link",
                        "text": f"🔗 {link_data.get('title', 'Ссылка')}",
                        "url": url,
                    }]]
                },
            }
        return None

    return None

def is_repost(post: Dict[str, Any]) -> bool:
    """Проверяет, является ли пост репостом."""
    return bool(post.get("copy_history"))
async def publish_post(post: Dict[str, Any]) -> bool:
    text = post.get("text", "")
    post_owner = post.get("owner_id", VK_GROUP_ID)
    link = f"https://vk.com/wall{post_owner}_{post['id']}"

    attachments: List[Dict[str, Any]] = []
    extra_buttons: List[List[Dict[str, Any]]] = []

    raw_attachments = post.get("attachments", [])
    if raw_attachments:
        tasks = [process_attachment(att) for att in raw_attachments]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                log(f"Ошибка вложения: {result}")
            elif result:
                if result.get("type") == "extra_buttons":
                    extra_buttons.extend(result.get("buttons", []))
                else:
                    attachments.append(result)

    all_buttons = extra_buttons.copy()
    all_buttons.append([{
        "type": "link",
        "text": "🔗 Читать в ВК",
        "url": link,
    }])

    attachments.append({
        "type": "inline_keyboard",
        "payload": {"buttons": all_buttons}
    })

    #if not text.strip():
        #text = f"📮 Пост из ВК: {link}"

    return await send_content_to_max(MAX_CHAT_ID, text, attachments)


async def run_vk_check(force_count: Optional[int] = None) -> int:
    last_id = read_last_id()
    count = force_count or DEFAULT_POSTS_COUNT

    posts = await get_vk_posts(count)
    if not posts:
        return 0

    new_posts = sorted([p for p in posts if p["id"] > last_id], key=lambda p: p["id"])

    if not new_posts:
        if force_count:
            log("Нет новых постов.")
        return 0

    sent_count = 0
    for post in new_posts:
        # Пропускаем репосты
        if is_repost(post):
            log(f"Пост {post['id']} пропущен (это репост)")
            # Но обновляем last_id, чтобы не зацикливаться
            write_last_id(post["id"])
            continue
        
        # Пропускаем полностью пустые посты (без текста и вложений)
        if not post.get("text", "").strip() and not post.get("attachments"):
            log(f"Пост {post['id']} пропущен (пустой)")
            write_last_id(post["id"])
            continue

        success = await publish_post(post)
        if success:
            sent_count += 1
            log(f"Пост {post['id']} отправлен.")
            write_last_id(post["id"])
            await asyncio.sleep(POST_SEND_DELAY_SEC)
        else:
            log(f"Пост {post['id']} НЕ отправлен!")
            # Обновляем last_id даже при ошибке, чтобы не зацикливаться
            # (но можно убрать эту строку, если хочешь переотправлять)
            write_last_id(post["id"])

    return sent_count


async def periodic_check() -> None:
    while not shutdown_event.is_set():
        try:
            await asyncio.sleep(CHECK_INTERVAL_SEC)
            if shutdown_event.is_set():
                break
            await run_vk_check()
        except asyncio.CancelledError:
            break
        except Exception as e:
            log(f"Периодическая проверка: {e}")
            await asyncio.sleep(30)


async def check_internet() -> bool:
    """Проверяет доступность интернета через DNS-запрос."""
    import socket
    try:
        socket.setdefaulttimeout(3)
        socket.getaddrinfo("platform-api2.max.ru", 443)
        return True
    except socket.gaierror:
        return False


async def wait_for_internet(max_wait: int = 300) -> None:
    """Ждёт появления интернета до max_wait секунд."""
    waited = 0
    while not await check_internet():
        if waited >= max_wait:
            log(f"⚠️ Нет интернета {max_wait} секунд. Продолжаю запуск...")
            break
        log(f"🌐 Нет интернета. Жду 10 сек... ({waited}/{max_wait})")
        await asyncio.sleep(10)
        waited += 10


async def main() -> None:
    print("=" * 50)
    print("🤖 БОТ ЗАПУЩЕН (с yt-dlp для видео и клипов)")
    print("=" * 50)

    # Проверяем наличие обязательных настроек
    required = [VK_SERVICE_TOKEN, MAX_BOT_TOKEN, VK_GROUP_ID, MAX_CHAT_ID, ADMIN_ID]
    if any(not v for v in required):
        logger.critical("Отсутствуют переменные окружения")
        return

    # Ждём появления интернета перед запуском
    await wait_for_internet()

    # Инициализируем HTTP-сессии
    await http.start()
    await vk_http.start()

    # Инициализируем файл last_post_id, если его ещё нет
    if not os.path.exists(LAST_POST_FILE):
        first_post = await get_last_vk_post()
        if first_post:
            write_last_id(first_post["id"])

    # Создаём бота
    try:
        bot = Bot(token=MAX_BOT_TOKEN, base_url=API_URL)
    except TypeError:
        bot = Bot(token=MAX_BOT_TOKEN)

    # Обработка сигналов остановки
    loop = asyncio.get_running_loop()

    def _request_shutdown():
        log("Остановка...")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_shutdown)
        except (NotImplementedError, ValueError):
            pass

    # Запускаем фоновую проверку с retry при сетевых ошибках
    periodic_task = asyncio.create_task(periodic_check())

    # Запускаем бота с retry при ошибках подключения
    bot_running = False
    while not shutdown_event.is_set() and not bot_running:
        try:
            log("Попытка подключения к MAX API...")
            await dp.start_polling(bot)
            bot_running = True
        except Exception as e:
            log(f"❌ Ошибка подключения к MAX: {e}")
            if "getaddrinfo" in str(e) or "Cannot connect" in str(e):
                log("🔄 Жду 30 секунд перед повторной попыткой...")
                await asyncio.sleep(30)
                # Пересоздаём сессию (DNS мог "залипнуть")
                await http.close()
                await vk_http.close()
                await http.start()
                await vk_http.start()
            else:
                log("💥 Неизвестная ошибка, завершение...")
                break

    # Корректное завершение
    log("Завершение...")
    shutdown_event.set()
    periodic_task.cancel()
    try:
        await periodic_task
    except asyncio.CancelledError:
        pass
    await http.close()
    await vk_http.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановлено.")