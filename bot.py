# -*- coding: utf-8 -*-
import requests
import time
import os
import io
import datetime
from collections import deque

# === FIX: Отключение системного прокси (для Windows) ===
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# ==========================================
# ⚙️ SETTINGS (НАСТРОЙКИ)
# ==========================================

# 1. VKONTAKTE SETTINGS
# Получить сервисный токен в настройках приложения VK
VK_SERVICE_TOKEN = "ВАШ_СЕРВИСНЫЙ_ТОКЕН_VK" 
# ID группы (обычно начинается с минуса)
VK_GROUP_ID = -000000000  
VK_VERSION = "5.131"

# 2. MAX (VK TEAMS) SETTINGS
# Токен бота (от @MasterBot)
MAX_BOT_TOKEN = "ВАШ_ТОКЕН_БОТА_MAX"
# ID канала или чата, куда делать репосты
MAX_CHAT_ID = -00000000000000 

# 3. SECURITY (БЕЗОПАСНОСТЬ)
# ID администратора (число), которому бот будет отвечать на команды
# Узнать свой ID можно, написав боту любое сообщение (он выведет ID в консоль)
ADMIN_IDS = [12345678] 

# 4. BOT LOGIC
CHECK_INTERVAL = 300  # Проверка раз в 5 минут
BATCH_SIZE = 10       # Проверять 10 последних постов за раз

# ==========================================

LAST_POST_FILE = "last_post_id.txt"
MAX_HEADERS = {"Authorization": MAX_BOT_TOKEN.strip()}
API_URL = "https://platform-api.max.ru" # Или ваш API URL

logs_buffer = deque(maxlen=15)

def clean_log_text(text):
    """Скрывает токен в логах для безопасности"""
    if not text: return ""
    text = str(text)
    if VK_SERVICE_TOKEN in text and "ВАШ_" not in VK_SERVICE_TOKEN:
        return text.replace(VK_SERVICE_TOKEN, "***TOKEN_HIDDEN***")
    return text

def log(text):
    safe_text = clean_log_text(text)
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    msg = f"[{timestamp}] {safe_text}"
    print(msg)
    logs_buffer.append(msg)

def get_vk_posts_batch(count=10):
    url = "https://api.vk.com/method/wall.get"
    params = {
        "access_token": VK_SERVICE_TOKEN,
        "owner_id": VK_GROUP_ID,
        "count": count + 5,
        "v": VK_VERSION
    }
    try:
        response = requests.get(url, params=params).json()
        if 'response' in response:
            items = response['response']['items']
            # Игнорируем закрепы, берем только хронологию
            real_posts = [p for p in items if 'is_pinned' not in p]
            if not real_posts: real_posts = items
            return real_posts[:count]
    except Exception as e:
        log(f"Err VK Batch: {e}")
    return []

def get_last_vk_post():
    posts = get_vk_posts_batch(count=1)
    return posts[0] if posts else None

def upload_photo_to_max(vk_photo_url):
    try:
        img_response = requests.get(vk_photo_url)
        if img_response.status_code != 200: return None
        image_data = io.BytesIO(img_response.content)

        upload_req = requests.post(f"{API_URL}/uploads", params={"type": "image"}, headers=MAX_HEADERS)
        data = upload_req.json()
        upload_url = data.get('url') or (data.get('payload') or {}).get('url')
        if not upload_url: return None

        files = {'data': ('photo.jpg', image_data, 'image/jpeg')}
        file_req = requests.post(upload_url, files=files, headers=MAX_HEADERS)
        
        if file_req.status_code == 200:
            file_data = file_req.json()
            # Поиск токена в разных структурах ответа
            if "photos" in file_data:
                for key in file_data["photos"]:
                    if "token" in file_data["photos"][key]:
                        return file_data["photos"][key]["token"]
            elif "token" in file_data:
                return file_data["token"]
        return None
    except:
        return None

def get_admin_keyboard():
    return {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {"type": "callback", "text": "🔎 Check Now", "callbackData": "/check", "payload": "/check", "style": "primary"},
                    {"type": "callback", "text": "📋 Logs", "callbackData": "/log", "payload": "/log", "style": "attention"}
                ],
                [
                    {"type": "callback", "text": "🟢 Status", "callbackData": "/status", "payload": "/status", "style": "base"},
                    {"type": "callback", "text": "🛑 Stop", "callbackData": "/stop", "payload": "/stop", "style": "base"}
                ],
                [
                    {"type": "callback", "text": "🔄 Refresh Menu", "callbackData": "/help", "payload": "/help", "style": "base"}
                ]
            ]
        }
    }

def send_message(chat_id, text, attachments=None):
    url = f"{API_URL}/messages"
    params = {"chat_id": chat_id}
    payload = {"text": text}
    if attachments: payload["attachments"] = attachments

    try:
        r = requests.post(url, params=params, json=payload, headers=MAX_HEADERS)
        return r.status_code == 200
    except Exception as e:
        log(f"Net Err: {e}")
        return False

def answer_callback(query_id, text="", show_alert=False):
    url = f"{API_URL}/events/answer"
    payload = {"queryId": query_id, "text": text, "showAlert": show_alert}
    try: requests.post(url, json=payload, headers=MAX_HEADERS)
    except: pass

def process_post_and_send(post):
    text = post.get('text', '')
    atts = post.get('attachments', [])
    link = f"https://vk.com/wall{VK_GROUP_ID}_{post['id']}"
    
    max_atts = []
    extra = ""
    
    # Обработка вложений
    if atts:
        for a in atts:
            att_type = a.get('type')
            if att_type == 'photo':
                photo = a.get('photo', {})
                sizes = photo.get('sizes') or []
                if not sizes:
                    log(f"⚠️ Skipped photo in post {post['id']}: no sizes found")
                    continue

                best = max(sizes, key=lambda x: x.get('width', 0) * x.get('height', 0))
                photo_url = best.get('url')
                if not photo_url:
                    log(f"⚠️ Skipped photo in post {post['id']}: no URL in best size")
                    continue

                token = upload_photo_to_max(photo_url)
                if token:
                    max_atts.append({"type": "image", "payload": {"token": token}})
                else:
                    log(f"⚠️ Photo upload failed for post {post['id']}")
            elif att_type == 'video':
                video = a.get('video', {})
                extra += f"\n🎥 Video: {video.get('title', 'Video')}"

    # Добавление кнопки-ссылки
    button_attachment = {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [[{"type": "link", "text": "🔗 Open in VK", "url": link, "style": "primary"}]]
        }
    }
    max_atts.append(button_attachment)

    full_text = f"{text}{extra}"
    if send_message(MAX_CHAT_ID, full_text, max_atts):
        log(f"✅ Post {post['id']} sent successfully")
        return True
    return False

def check_for_new_posts(last_id):
    """Умная очередь: проверяет N постов и отправляет все пропущенные по порядку"""
    posts = get_vk_posts_batch(BATCH_SIZE)
    if not posts: return last_id
    
    new_posts = []
    for p in posts:
        if p['id'] > last_id:
            new_posts.append(p)
    
    if not new_posts: return last_id
        
    log(f"🔔 Found {len(new_posts)} new posts")
    new_posts.reverse() # Отправляем от старых к новым
    
    current_last_id = last_id
    for p in new_posts:
        if process_post_and_send(p):
            current_last_id = p['id']
            with open(LAST_POST_FILE, "w") as f: f.write(str(current_last_id))
            time.sleep(3) # Анти-спам задержка
            
    return current_last_id

def get_updates(marker=None):
    url = f"{API_URL}/updates"
    params = {"timeout": 10}
    if marker: params["marker"] = marker
    try:
        r = requests.get(url, params=params, headers=MAX_HEADERS)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def main():
    print("=== 🤖 VK TO MAX REPOSTER ===")
    print(f"Admin ID Protection: {ADMIN_IDS}")
    
    if os.path.exists(LAST_POST_FILE):
        try:
            with open(LAST_POST_FILE, "r") as f: last_id = int(f.read().strip())
        except: last_id = 0
    else:
        last_id = 0
        p = get_last_vk_post()
        if p: 
            last_id = p['id']
            with open(LAST_POST_FILE, "w") as f: f.write(str(last_id))

    last_vk_check = 0
    current_marker = None
    
    while True:
        try:
            updates_data = get_updates(current_marker)
            
            if updates_data:
                if 'marker' in updates_data: current_marker = updates_data['marker']
                
                events = updates_data.get('updates', [])
                for event in events:
                    text_command = None
                    dialog_id = None
                    query_id = None
                    
                    # Парсинг события (сообщение или кнопка)
                    if event.get('update_type') == 'message_created':
                        msg = event.get('message', {})
                        text_command = msg.get('body', {}).get('text', '').strip()
                        dialog_id = msg.get('recipient', {}).get('chat_id') or msg.get('sender', {}).get('user_id')

                    elif event.get('update_type') == 'message_callback':
                        callback = event.get('callback', {})
                        query_id = callback.get('callback_id')
                        payload_data = callback.get('payload')
                        if isinstance(payload_data, dict):
                            text_command = payload_data.get('callbackData') or payload_data.get('payload')
                        else:
                            text_command = payload_data
                        if not text_command: text_command = event.get('payload', {}).get('callbackData')
                        msg = event.get('message', {})
                        dialog_id = msg.get('recipient', {}).get('chat_id')
                        if query_id: answer_callback(query_id)

                    # Проверка прав доступа (Security)
                    if dialog_id:
                        try: sender_check_id = int(dialog_id)
                        except: sender_check_id = dialog_id
                        if sender_check_id not in ADMIN_IDS:
                            if text_command:
                                print(f"⛔ Unauthorized access attempt (ID: {sender_check_id})")
                            continue

                    # Выполнение команд
                    if text_command and dialog_id:
                        log(f"📩 Admin: {text_command}")
                        
                        if text_command in ['/help', '/start']:
                            send_message(dialog_id, "🛠 **Admin Panel**", [get_admin_keyboard()])
                        elif text_command == '/status':
                            send_message(dialog_id, "🤖 Online.", [get_admin_keyboard()])
                        elif text_command == '/log':
                            send_message(dialog_id, "📋 Logs:\n" + "\n".join(logs_buffer), [get_admin_keyboard()])
                        elif text_command == '/check':
                            send_message(dialog_id, "🔎 Checking...", [get_admin_keyboard()])
                            last_id = check_for_new_posts(last_id)
                            send_message(dialog_id, "✅ Done.", [get_admin_keyboard()])
                        elif text_command == '/stop':
                            send_message(dialog_id, "🛑 Stopping bot.")
                            return
                        elif text_command.startswith('/fill'):
                            try:
                                parts = text_command.split()
                                count = int(parts[1]) if len(parts) > 1 else 10
                                if count > 20: count = 20
                                send_message(dialog_id, f"🚀 Backfilling {count} posts...")
                                posts = get_vk_posts_batch(count)
                                posts.reverse()
                                succ = 0
                                for p in posts:
                                    if process_post_and_send(p):
                                        succ += 1
                                        if p['id'] > last_id:
                                            last_id = p['id']
                                            with open(LAST_POST_FILE, "w") as f: f.write(str(last_id))
                                        time.sleep(3)
                                send_message(dialog_id, f"✅ Backfill complete: {succ}", [get_admin_keyboard()])
                            except: pass

            # Автоматическая проверка
            if time.time() - last_vk_check > CHECK_INTERVAL:
                last_id = check_for_new_posts(last_id)
                last_vk_check = time.time()
            
            if not updates_data: time.sleep(1)

        except KeyboardInterrupt:
            print("Bot stopped manually.")
            break
        except Exception as e:
            log(f"Fatal Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
