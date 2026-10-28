import asyncio
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Optional

# Настройка кодировки вывода на случай Windows-консоли (cp1251)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from vkbottle import Bot, Keyboard, Text, GroupEventType, Callback, EMPTY_KEYBOARD
from vkbottle.bot import Message, MessageEvent
from vkbottle import KeyboardButtonColor


# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = os.getenv("VK_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задана переменная окружения VK_TOKEN.")

# peer_id беседы художников.
# Например:
# ARTIST_CHAT_ID = 2000000003
ARTIST_CHAT_ID = 2000000003
TOR_BOT_GROUP_ID = 227820718

# Высший офицерский состав (ВОС)
# morohrono (706284129), motheroftor (31959523), geek_mann (208825850), pain_lolikox (629691481)
VOS_USER_IDS = {706284129, 31959523, 208825850, 629691481}

# Игроки для напоминания на РБ (вт, ср, чт)
# morohrono (706284129), pain_lolikox (629691481), jaleit (32162922), santil54rus (342456805)
RB_TARGET_USER_IDS = [706284129, 629691481, 32162922, 342456805]


# ============================================================
# BOT
# ============================================================

bot = Bot(TOKEN)


# ============================================================
# СОСТОЯНИЕ АНКЕТЫ
# ============================================================
#
# user_id: {
#     "step": "race",
#     "race": "...",
#     "gender": "...",
#     ...
# }
#
# Для небольшого бота этого достаточно.
# После перезапуска процесса данные сбросятся.
# ============================================================

orders = {}
order_records = {}
ORDER_STORE = os.path.join(os.path.dirname(__file__), "orders.json")
WISH_STORE = os.path.join(os.path.dirname(__file__), "wishes.json")
PROFILE_STORE = os.path.join(os.path.dirname(__file__), "customer_profiles.json")
CLAN_MEMBERS_STORE = os.path.join(os.path.dirname(__file__), "clan_members.json")
CLAN_SETTINGS_STORE = os.path.join(os.path.dirname(__file__), "clan_settings.json")


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_random_id() -> int:
    """Генерация уникального random_id для исключения дублирования в VK API."""
    return random.randint(1, 2**31 - 1)


def safe_save_json(file_path: str, data: dict) -> None:
    """Безопасное сохранение данных в JSON с защитой от сбоев на Windows."""
    temporary_path = f"{file_path}.tmp"
    try:
        with open(temporary_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temporary_path, file_path)
    except Exception as error:
        print(f"[ERROR] Не удалось сохранить {file_path}: {error}")
        if os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError:
                pass


def reset_order(user_id: int):
    """Полностью сбросить текущую анкету пользователя."""
    orders.pop(user_id, None)


def get_order(user_id: int) -> dict:
    """Получить анкету пользователя."""
    if user_id not in orders:
        orders[user_id] = {
            "step": "race",
            "race": None,
            "gender": None,
            "style": None,
            "mood": None,
            "description": None,
            "references": [],
        }

    return orders[user_id]


def normalize(text: Optional[str]) -> str:
    """Нормализация пользовательского текста с защитой от None."""
    if not text:
        return ""
    return text.strip().lower().replace("ё", "е")


def is_artist_orders_command(text: str) -> bool:
    normalized = normalize(text)
    normalized = re.sub(
        r"^(?:@?club\d+|\[club\d+\|[^\]]+\])\s+",
        "",
        normalized,
    )
    return normalized in {"заказы", "/заказы"}


def load_order_records() -> dict:
    """Загрузить сохранённые заказы, если файл уже создан."""
    try:
        with open(ORDER_STORE, encoding="utf-8") as order_file:
            data = json.load(order_file)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as error:
        print(f"[ERROR] Не удалось загрузить заказы: {error}")
        return {}


def save_order_records() -> None:
    """Сохранить заказы, чтобы статусы переживали перезапуск."""
    safe_save_json(ORDER_STORE, order_records)


order_records = load_order_records()


def load_wishes() -> dict:
    """Загрузить пожелания, сгруппированные по беседам."""
    try:
        with open(WISH_STORE, encoding="utf-8") as wish_file:
            data = json.load(wish_file)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as error:
        print(f"[ERROR] Не удалось загрузить пожелания: {error}")
        return {}


def save_wishes() -> None:
    """Сохранить пожелания отдельно от заказов на арт."""
    safe_save_json(WISH_STORE, wishes)


wishes = load_wishes()


def load_customer_profiles() -> dict:
    try:
        with open(PROFILE_STORE, encoding="utf-8") as profile_file:
            data = json.load(profile_file)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as error:
        print(f"[ERROR] Не удалось загрузить профили: {error}")
        return {}


def save_customer_profiles() -> None:
    safe_save_json(PROFILE_STORE, customer_profiles)


customer_profiles = load_customer_profiles()


def load_clan_members() -> dict:
    try:
        with open(CLAN_MEMBERS_STORE, encoding="utf-8") as clan_file:
            data = json.load(clan_file)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as error:
        print(f"[ERROR] Не удалось загрузить участников клана: {error}")
        return {}


def save_clan_members() -> None:
    safe_save_json(CLAN_MEMBERS_STORE, clan_members)


clan_members = load_clan_members()


def load_clan_settings() -> dict:
    defaults = {
        "clan_chat_id": None,
        "required_ore": "железо",
        "monitored_resources": ["железо"],
        "last_rb_date": None,
        "last_krb_date": None,
        "officers": [706284129, 31959523, 208825850, 629691481],
        "unhit_boss_players": [],
        "status_request_sent": False,
    }
    try:
        with open(CLAN_SETTINGS_STORE, encoding="utf-8") as settings_file:
            data = json.load(settings_file)
            if isinstance(data, dict):
                defaults.update(data)
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError) as error:
        print(f"[ERROR] Не удалось загрузить настройки клана: {error}")
    if "required_ore" not in defaults or not defaults["required_ore"]:
        defaults["required_ore"] = "железо"
    return defaults


def save_clan_settings() -> None:
    safe_save_json(CLAN_SETTINGS_STORE, clan_settings)


clan_settings = load_clan_settings()


def get_officer_ids() -> set[int]:
    """Возвращает актуальный список ID всех офицеров (основатели ВОС + назначенные офицеры)."""
    stored_officers = clan_settings.get("officers", [])
    return set(stored_officers) | VOS_USER_IDS


def extract_user_id_from_message(message: Message, arg_text: str = "") -> Optional[int]:
    """Извлекает VK ID пользователя из ответа на сообщение, пересылки, упоминания или аргумента."""
    if message.reply_message and message.reply_message.from_id > 0:
        return message.reply_message.from_id
    if message.fwd_messages:
        for fwd in message.fwd_messages:
            if fwd.from_id > 0:
                return fwd.from_id

    if arg_text:
        match = re.search(r"(?:\[id(\d+)\||\bid(\d+)\b|vk\.com/id(\d+)|@id(\d+))", arg_text, re.IGNORECASE)
        if match:
            for group in match.groups():
                if group:
                    return int(group)
        digits = re.search(r"\b\d{5,12}\b", arg_text)
        if digits:
            return int(digits.group(0))
    return None


CANONICAL_RESOURCES = {
    "железо": "железо",
    "ртуть": "ртуть",
    "сера": "сера",
    "торий": "торий",
    "torий": "торий",
    "tor": "торий",
}


def parse_zakrep_ore(text: str) -> Optional[str]:
    """
    Ищет в тексте кланового закрепа строку вида:
      Железо: добытчика ставим всегда
      Сера: добытчика ставим всегда
      TORий: добытчика ставим всегда
    Сообщение должно начинаться с #закреп (или закреп).
    Возвращает каноническое название руды ('железо', 'сера', 'торий', 'ртуть') или None.
    """
    clean = normalize(text)
    clean = re.sub(r"^(?:@?club\d+|\[club\d+\|[^\]]+\])\s*", "", clean).lstrip("\\/")
    if not clean.startswith(("#закреп", "закреп")):
        return None
    clean_after_tag = re.sub(r"^(?:#закреп|закреп)[:\s]*", "", clean)
    match = re.search(
        r"(?:^|\n|\s*)([^\n:]+?):\s*добытчика\s+ставим\s+всегда",
        clean_after_tag,
        re.IGNORECASE,
    )
    if match:
        raw_ore = match.group(1).strip()
        raw_ore = re.sub(r"^[^\wа-яa-z]+|[^\wа-яa-z]+$", "", raw_ore).strip()
        return CANONICAL_RESOURCES.get(raw_ore.lower(), raw_ore.lower())
    return None


async def send_initial_status_call(peer_id: int) -> None:
    """Отправляет призыв ко всем участникам клана вызвать свой статус для первичного сбора профилей."""
    broadcast = (
        "📢 Внимание, бойцы клана Dha’t’elle! 🏰\n\n"
        "Для настройки автоматических функций (лог босса, созыв, защита спотов ресурсов и учёт званий) "
        "каждому участнику клана необходимо отправить в этот чат команду:\n"
        "👉 статус\n\n"
        "Бот автоматически зафиксирует ваш игровой ник и текущее звание в базе клана! ⚔️"
    )
    await bot.api.messages.send(
        peer_id=peer_id,
        random_id=get_random_id(),
        message=broadcast,
    )


def is_lieutenant_or_higher(rank: Optional[str]) -> bool:
    """Проверяет, является ли звание Лейтенантом или выше."""
    if not rank:
        return False
    norm = normalize(rank)
    if "рядов" in norm:
        return False
    higher_keywords = (
        "лейтенант", "капитан", "майор", "подполковник", "полковник",
        "генерал", "маршал", "глава", "зам", "офицер", "лидер", "вос"
    )
    return any(keyword in norm for keyword in higher_keywords)


def forwarded_messages(message: Message):
    pending = []
    if message.reply_message:
        pending.append(message.reply_message)
    if message.fwd_messages:
        pending.extend(message.fwd_messages)

    while pending:
        forwarded = pending.pop(0)
        yield forwarded
        if getattr(forwarded, "reply_message", None):
            pending.append(forwarded.reply_message)
        if getattr(forwarded, "fwd_messages", None):
            pending.extend(forwarded.fwd_messages or [])


def unpack_fwd_messages(message: Message):
    """Рекурсивно извлекает только пересланные сообщения (fwd_messages), исключая цитирование/ответы (reply_message)."""
    pending = list(message.fwd_messages or [])
    while pending:
        forwarded = pending.pop(0)
        yield forwarded
        if getattr(forwarded, "fwd_messages", None):
            pending.extend(forwarded.fwd_messages or [])


def is_message_too_old(date_value, max_age_seconds: int = 600) -> bool:
    """
    Проверяет, старше ли сообщение/лог заданного количества секунд (по умолчанию 600 сек = 10 минут).
    """
    if date_value is None:
        return False

    now_ts = time.time()
    if isinstance(date_value, (int, float)):
        msg_ts = float(date_value)
    elif hasattr(date_value, "timestamp"):
        msg_ts = date_value.timestamp()
    else:
        return False

    return (now_ts - msg_ts) > max_age_seconds


def extract_guild_name(message: Message, forwarded=None) -> Optional[str]:
    if forwarded is None:
        forwarded = get_customer_tor_profile(message, message.from_id)
    if forwarded is None:
        return None

    match = re.search(
        r"(?:^|\n)\s*([^|\n]+?)\s*\|\s*ур\.?\s*\d+\s*\|",
        forwarded.text or "",
        flags=re.IGNORECASE,
    )
    if match:
        guild_name = re.sub(r"^[🏠🏡🏰🏛⛺🛡⚔👑⚜️\W_]+\s*", "", match.group(1)).strip()
        if guild_name:
            return guild_name
    return None


def extract_nickname_from_profile(forwarded_text: str, user_id: int) -> str:
    """
    Извлекает игровой никнейм персонажа из текста карточки профиля ToR.
    """
    # 1. Поиск кликабельной ссылки на конкретного игрока: [id208825850|Ярость всегда рядом]
    match_id = re.search(rf"\[id{user_id}\|([^\]]+)\]", forwarded_text, re.IGNORECASE)
    if match_id:
        return match_id.group(1).strip()

    # 2. Поиск любой ссылки на игрока в карточке: [id12345|Никнейм]
    match_any = re.search(r"\[id\d+\|([^\]]+)\]", forwarded_text)
    if match_any:
        return match_any.group(1).strip()

    # 3. Никнейм под заголовком Статус / Профиль ToR
    match_stat = re.search(
        r"(?:📜\s*(?:Статус|Профиль)|👤\s*Игрок)\s*\n\s*[🔹•👤]?\s*([^\n|]+)",
        forwarded_text,
        re.IGNORECASE,
    )
    if match_stat:
        cand = re.sub(r"^[🔹•👤⚔️🛡⚜️\W_]+\s*", "", match_stat.group(1)).strip()
        if cand:
            return cand

    return f"id{user_id}"


def get_customer_tor_profile(message: Message, customer_id: int):
    for forwarded in forwarded_messages(message):
        if forwarded.from_id != -TOR_BOT_GROUP_ID:
            continue

        profile_ids = re.findall(
            r"\[id(\d+)\||@id(\d+)(?:\b|\])|"
            r"vk\.com/id(\d+)\b|\bid(?::\s*|\s+)?(\d+)\b",
            forwarded.text or "",
            flags=re.IGNORECASE,
        )
        linked_ids = {
            int(profile_id)
            for match in profile_ids
            for profile_id in match
            if profile_id
        }
        if customer_id in linked_ids:
            return forwarded
    return None


def get_customer_tor_transfer_log(message: Message):
    """
    Проверяет пересланные сообщения на наличие чека передачи валюты из официального бота ToR (-227820718).
    """
    for forwarded in forwarded_messages(message):
        if forwarded.from_id != -TOR_BOT_GROUP_ID:
            continue
        text = forwarded.text or ""
        match = re.search(
            r"(?:✅\s*)?Вы успешно передали\s+([\d\s,.]+)\s*(ядер|ядра|ядро|rnd|рнд)\s+игроку\s+([^.\n]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            return forwarded, match
    return None, None


def sync_subscriptions_to_miniapp():
    """
    Синхронизирует активные подписки из clan_settings в miniapp/store_subscriptions.json.
    """
    subs = [{
        "userId": 208825850,
        "userNick": "geek_mann",
        "expiresAt": 253402300799000,
        "grantedBy": "root"
    }]
    store_subs = clan_settings.get("store_subscriptions", {})
    now_ts = int(datetime.now().timestamp())
    for uid_str, data in store_subs.items():
        exp = data.get("expires_at", 0)
        if exp > now_ts:
            subs.append({
                "userId": data.get("user_id"),
                "userNick": data.get("nickname"),
                "expiresAt": exp * 1000,
                "amount": data.get("amount"),
                "currency": data.get("currency")
            })
    sub_path = os.path.join(os.path.dirname(__file__), "miniapp", "store_subscriptions.json")
    try:
        safe_save_json(sub_path, subs)
    except Exception as e:
        print(f"[WARNING] Не удалось синхронизировать store_subscriptions.json: {e}")


def normalize_guild_name(guild_name: str) -> str:
    normalized = normalize(guild_name)
    for apostrophe in ("'", "’", "‘", "ʼ", "`", "´"):
        normalized = normalized.replace(apostrophe, "")
    return "".join(character for character in normalized if character.isalnum())


def get_customer_tariff(guild_name: Optional[str]) -> dict:
    """
    Определяет тариф и условия заказа арта по названию гильдии:
    - Dha't'elle: бесплатно
    - 7-я рота (Седьмая рота): бесплатно
    - Союзники (Zащитники, Красное&белое, Донные Падальщики, Zакат/Закат): скидка 50% (250 ₽)
    - Враги / Карпы (Carpe Diem, CarpeDiem Academ): заблокировано
    - Нейтралы: стандартная цена (500 ₽)
    """
    if not guild_name:
        return {
            "type": "standard",
            "price": 500,
            "label": "Нейтрал (стандартная цена: 500 ₽)",
            "blocked": False,
        }

    norm = normalize_guild_name(guild_name)
    norm_rus = norm.replace("z", "з")

    # 100% бесплатные гильдии (наш клан Dha't'elle и братская 7-я рота)
    if "dhatelle" in norm or any(k in norm_rus for k in ("7ярота", "7рота", "седьмаярота")):
        label = "Соклановец Dha't'elle (Бесплатно)" if "dhatelle" in norm else "Братская гильдия 7-я рота (Бесплатно)"
        return {
            "type": "free",
            "price": 0,
            "label": label,
            "blocked": False,
        }

    # Союзники со скидкой 50% (250 ₽)
    ally_keys = ("защитники", "красноебелое", "донныепадальщики", "закат")
    if any(ally_key in norm_rus for ally_key in ally_keys):
        return {
            "type": "ally",
            "price": 250,
            "label": "Союзник (скидка 50%: 250 ₽)",
            "blocked": False,
        }

    carp_keys = ("carpediem", "carpediemacadem")
    if any(carp_key in norm for carp_key in carp_keys):
        return {
            "type": "enemy",
            "price": 0,
            "label": "Враг (Carpe Diem)",
            "blocked": True,
        }

    return {
        "type": "standard",
        "price": 500,
        "label": "Нейтрал (стандартная цена: 500 ₽)",
        "blocked": False,
    }


def wishes_keyboard() -> str:
    """Inline-кнопка для бесед с функционалом попрошаек."""
    return make_inline_keyboard([
        (
            "📋 Попрошайки",
            KeyboardButtonColor.PRIMARY,
            {"action": "show_wishes"},
        )
    ])


def build_wishes_chunks(peer_id: int) -> list[str]:
    """Формирует список сообщений (чанков) с пожеланиями беседы."""
    chat_key = str(peer_id)
    chat_wishes = wishes.get(chat_key, [])
    report_lines = ["📋 Пожелания участников этой беседы:"]
    if chat_wishes:
        for index, entry in enumerate(chat_wishes, start=1):
            author_link = entry.get("profile_url")
            if not author_link and entry.get("user_id") is not None:
                author_link = f"https://vk.com/id{entry['user_id']}"
            if not author_link:
                author_link = "Профиль не указан"
            report_lines.append(
                f"\n{index}. {author_link} "
                f"хочет {entry['wish']}"
            )
    else:
        report_lines.append("\nПока никто ничего не пожелал.")

    report_lines.extend([
        "\nКоманды:",
        "+хочу описание — добавить желание.",
        "-нехочу — удалить своё желание.",
        "/попрошайки — показать этот список.",
        "-попрошайка номер — удалить желание по номеру "
        "(только для администратора беседы).",
    ])

    report = "\n".join(report_lines)
    chunks = []
    while len(report) > 3500:
        split_at = report.rfind("\n", 0, 3500)
        if split_at <= 0:
            split_at = 3500
        chunks.append(report[:split_at])
        report = report[split_at:].lstrip()
    chunks.append(report)
    return chunks


async def send_chat_wishes(peer_id: int) -> None:
    """Отправляет список пожеланий в беседу с кнопкой."""
    chunks = build_wishes_chunks(peer_id)
    for chunk in chunks:
        await bot.api.messages.send(
            peer_id=peer_id,
            random_id=get_random_id(),
            message=chunk,
            keyboard=wishes_keyboard(),
        )


async def answer_wishes(message: Message, text: str) -> None:
    await message.answer(text, keyboard=wishes_keyboard())


async def handle_guild_wish(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        return

    text = re.sub(
        r"^(?:@?club\d+|\[club\d+\|[^\]]+\])\s+",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    if not text:
        return

    # Поддержка команд с эмодзи (например, '📋 Попрошайки')
    clean_cmd_text = re.sub(r"^[📋\s]+", "", text).strip()
    command_parts = (clean_cmd_text or text).split(maxsplit=1)
    command = normalize(command_parts[0])
    chat_key = str(message.peer_id)
    chat_wishes = wishes.get(chat_key, [])

    if command in {"/попрошайки", "попрошайки", "-попрошайка"}:
        if command in {"/попрошайки", "попрошайки"}:
            if len(command_parts) != 1:
                await answer_wishes(message, "Используй команду отдельно: /попрошайки")
                return

            chunks = build_wishes_chunks(message.peer_id)
            for chunk in chunks:
                await answer_wishes(message, chunk)
            return

        try:
            is_admin = await message.user_is_admin(message.from_id)
        except Exception as error:
            print(f"[ERROR] Не удалось проверить права участника: {error}")
            await answer_wishes(
                message,
                "Не удалось проверить права администратора. Попробуй позже."
            )
            return

        if not is_admin:
            await answer_wishes(
                message,
                "Эта команда доступна только администраторам беседы."
            )
            return

        if len(command_parts) != 2 or not command_parts[1].strip().isdigit():
            await answer_wishes(
                message,
                "Укажи номер желания: -попрошайка 1"
            )
            return

        wish_number = int(command_parts[1].strip())
        if not 1 <= wish_number <= len(chat_wishes):
            await answer_wishes(message, "Желания с таким номером нет в списке.")
            return

        removed_wish = chat_wishes.pop(wish_number - 1)
        if not chat_wishes:
            wishes.pop(chat_key, None)
        save_wishes()
        await answer_wishes(
            message,
            f"Удалено желание №{wish_number}: {removed_wish['wish']}"
        )
        return

    if command == "-нехочу":
        if len(command_parts) != 1:
            await answer_wishes(message, "Используй команду отдельно: -нехочу")
            return

        own_index = next(
            (
                index
                for index, entry in enumerate(chat_wishes)
                if entry["user_id"] == message.from_id
            ),
            None,
        )
        if own_index is None:
            await answer_wishes(message, "У тебя нет желания в списке этой беседы.")
            return

        removed_wish = chat_wishes.pop(own_index)
        if not chat_wishes:
            wishes.pop(chat_key, None)
        save_wishes()
        await answer_wishes(message, f"Твоё желание удалено: {removed_wish['wish']}")
        return

    if command == "+хочу":
        if len(command_parts) < 2 or not command_parts[1].strip():
            await answer_wishes(message, "Напиши желание после команды: +хочу описание")
            return

        if any(entry["user_id"] == message.from_id for entry in chat_wishes):
            await answer_wishes(
                message,
                "У тебя уже есть желание в списке. Сначала удали его командой "
                "-нехочу, затем добавь новое."
            )
            return

        wish = {
            "user_id": message.from_id,
            "wish": command_parts[1].strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        wishes.setdefault(chat_key, []).append(wish)
        save_wishes()
        await answer_wishes(message, "Записала пожелание в список этой беседы.")
        return


async def handle_clan_chat(message: Message) -> None:
    """
    Обработка сообщений в беседах клана:
    1. Пожелания (попрошайки).
    2. Привязка беседы к боту (/кланчат).
    3. Призыв к первичному сбору профилей (/запроспрофилей, /статусы).
    4. Управление офицерами (/офицеры, /офицер +, /офицер -).
    5. Просмотр звания и состава клана (/ранг, /состав).
    6. Управление отслеживаемыми ресурсами (/ресурсы, /ресурсы +..., /ресурсы -...).
    7. Команда /созыв (тег не отбивших босса по сохранённому логу).
    8. Карточка статуса игрока ToR (статус) — сохранение с подтверждением в чат.
    9. Сообщения о повышении / понижении — обновление с подтверждением в чат.
    10. Лог гильд-босса — сохранение списка не отбивших без спам-тега.
    11. Лог спота ценных ресурсов — тег онлайн офицеров для повышения рядовых.
    """
    text = (message.text or "").strip()
    clean_text = normalize(text)
    clean_text_no_mention = re.sub(
        r"^(?:@?club\d+|\[club\d+\|[^\]]+\])\s*",
        "",
        clean_text,
    ).strip()

    # 1. Проверка команд попрошаек
    if any(clean_text_no_mention.startswith(cmd) for cmd in ("+хочу", "-нехочу", "/попрошайки", "попрошайки", "-попрошайка", "📋 попрошайки")):
        await handle_guild_wish(message)
        return

    # Меню команд клан-бота
    if clean_text_no_mention in {"/команды", "команды", "/помощь", "помощь", "/help", "help", "/меню", "меню"}:
        user_is_officer = message.from_id in get_officer_ids()
        role_label = "Офицер 👑" if user_is_officer else "Боец клана 🛡️"
        help_text = (
            f"📜 Список команд клан-бота Dha’t’elle\n"
            f"Ваш статус: {role_label}\n\n"
            "👥 ДОСТУПНО ВСЕМ УЧАСТНИКАМ:\n"
            "• статус — вызвать карточку ToR (бот автоматически зафиксирует ваш ник и звание в базе)\n"
            "• /состав (или /клан) — посмотреть состав клана по званиям\n"
            "• /ресурсы — текущий необходимый ресурс клана для добытчиков\n"
            "• /попрошайки — открыть список желаний участников беседы\n"
            "• +хочу [текст] — записать своё желание в список попрошаек\n"
            "• -нехочу — удалить своё желание\n"
            "• /команды — открыть это меню\n\n"
            "👑 ТОЛЬКО ДЛЯ ОФИЦЕРСКОГО СОСТАВА:\n"
            "• /созыв — созвать и тегнуть всех, кто не отбил гильд-босса по сохранённому логу (можно с текстом: /созыв [сообщение])\n"
            "• /офицеры — список офицеров с правами управления ботом\n"
            "• /офицер +[id/ссылка] (или ответом на сообщение: /офицер +) — назначить нового офицера\n"
            "• /офицер -[id/ссылка] (или ответом на сообщение: /офицер -) — разжаловать назначенного офицера\n"
            "• /запроспрофилей (или /статусы) — объявить общий сбор профилей через «статус»\n"
            "• /кланчат — привязать текущую беседу как основной клан-чат\n"
            "• -попрошайка [номер] — удалить чужое желание из списка"
        )
        await message.answer(help_text)
        return

    # 2. Привязка беседы как клан-чата
    if clean_text_no_mention in {"/кланчат", "кланчат", "/сетчат"}:
        if message.from_id not in get_officer_ids():
            await message.answer("⚠️ Эта команда доступна только офицерскому составу.")
            return
        clan_settings["clan_chat_id"] = message.peer_id
        save_clan_settings()
        await message.answer("✅ Эта беседа успешно сохранена как основной клан-чат для уведомлений и напоминаний.")
        if not clan_settings.get("status_request_sent"):
            clan_settings["status_request_sent"] = True
            save_clan_settings()
            await send_initial_status_call(message.peer_id)
        return

    # Авто-привязка ID чата, если он ещё не задан в настройках
    if clan_settings.get("clan_chat_id") is None:
        clan_settings["clan_chat_id"] = message.peer_id
        save_clan_settings()

    # 3. Принудительный запрос вызова профилей ко всем участникам
    if clean_text_no_mention in {"/запроспрофилей", "запроспрофилей", "/сборпрофилей", "/статусы"}:
        if message.from_id not in get_officer_ids():
            await message.answer("⚠️ Эта команда доступна только офицерскому составу.")
            return
        await send_initial_status_call(message.peer_id)
        clan_settings["status_request_sent"] = True
        save_clan_settings()
        return

    # 4. Управление офицерами (/офицеры, /офицер +, /офицер -)
    if clean_text_no_mention in {"/офицеры", "офицеры", "/офицер", "офицер"}:
        officers = get_officer_ids()
        lines = []
        for uid in sorted(officers):
            member_nick = clan_members.get(str(uid), {}).get("nickname")
            display_name = member_nick if member_nick else "Офицер"
            tag_type = " [ВОС/Основатель]" if uid in VOS_USER_IDS else ""
            lines.append(f"• @id{uid} ({display_name}){tag_type}")
        await message.answer(
            "👑 Офицерский состав клана (доступ к командам /созыв, /офицер):\n\n"
            + "\n".join(lines) + "\n\n"
            "⚙️ Управление (для офицеров):\n"
            "• /офицер +[id/ссылка] (или ответом на сообщение: /офицер +) — назначить\n"
            "• /офицер -[id/ссылка] (или ответом на сообщение: /офицер -) — разжаловать"
        )
        return

    if clean_text_no_mention.startswith(("/офицер +", "офицер +", "/офицеры +", "офицеры +")):
        if message.from_id not in get_officer_ids():
            await message.answer("⚠️ Управление офицерами доступно только действующим офицерам.")
            return
        arg_text = text.split("+", 1)[1].strip()
        target_uid = extract_user_id_from_message(message, arg_text)
        if not target_uid:
            await message.answer("Укажите пользователя: /офицер +[ссылка/id] или отправьте команду в ответ на его сообщение.")
            return
        if target_uid in get_officer_ids():
            await message.answer(f"Пользователь @id{target_uid} уже является офицером.")
            return
        stored = clan_settings.setdefault("officers", list(VOS_USER_IDS))
        if target_uid not in stored:
            stored.append(target_uid)
            save_clan_settings()
        await message.answer(f"✅ Пользователь @id{target_uid} успешно добавлен в список офицеров и получил доступ к командам!")
        return

    if clean_text_no_mention.startswith(("/офицер -", "офицер -", "/офицеры -", "офицеры -")):
        if message.from_id not in get_officer_ids():
            await message.answer("⚠️ Управление офицерами доступно только действующим офицерам.")
            return
        arg_text = text.split("-", 1)[1].strip()
        target_uid = extract_user_id_from_message(message, arg_text)
        if not target_uid:
            await message.answer("Укажите пользователя: /офицер -[ссылка/id] или отправьте команду в ответ на его сообщение.")
            return
        if target_uid in VOS_USER_IDS:
            await message.answer("⚠️ Нельзя снять полномочия с основателя ВОС.")
            return
        stored = clan_settings.setdefault("officers", list(VOS_USER_IDS))
        if target_uid in stored:
            stored.remove(target_uid)
            save_clan_settings()
            await message.answer(f"✅ Пользователь @id{target_uid} исключён из списка назначенных офицеров.")
        else:
            await message.answer(f"Пользователь @id{target_uid} не найден в списке назначенных офицеров.")
        return

    # 5. Просмотр состава клана (/состав, /клан)
    if clean_text_no_mention in {"/состав", "состав", "/клан", "клан"}:
        if not clan_members:
            await message.answer("В базе клана пока нет участников. Отправьте команду «статус», чтобы внести данные!")
            return
        rank_groups = {}
        for uid, data in clan_members.items():
            r = data.get("rank", "Без звания")
            rank_groups.setdefault(r, []).append((uid, data.get("nickname", f"id{uid}")))
        report_lines = [f"🏰 Состав клана Dha’t’elle ({len(clan_members)} чел. в базе):\n"]
        for rank_name, members in rank_groups.items():
            report_lines.append(f"🎖 {rank_name} ({len(members)}):")
            for m_uid, m_nick in members:
                report_lines.append(f"• @id{m_uid} ({m_nick})")
            report_lines.append("")
        await message.answer("\n".join(report_lines).strip())
        return

    # 6. Просмотр необходимого ресурса для добытчиков (/ресурсы)
    if clean_text_no_mention in {"/ресурсы", "ресурсы", "/руда", "руда"}:
        required = clan_settings.get("required_ore", "железо")
        await message.answer(
            f"⛏️ Необходимый ресурс для добытчиков клана: «{required.capitalize()}»\n\n"
            f"ℹ️ Бот отслеживает пересланные логи жил только для этого ресурса и оповещает офицеров, если боец ещё не имеет звания Лейтенант.\n"
            f"📌 Смена ресурса происходит автоматически при отправке кланового закрепа (#закреп), содержащего строку:\n"
            f"«[Руда]: добытчика ставим всегда»"
        )
        return

    # Обработка кланового закрепа (#закреп)
    if clean_text_no_mention.startswith(("#закреп", "закреп")):
        new_ore = parse_zakrep_ore(clean_text_no_mention)
        if new_ore:
            clan_settings["required_ore"] = new_ore
            clan_settings["monitored_resources"] = [new_ore]
            save_clan_settings()
            await message.answer(
                f"📌 Настройка ресурса из #закреп обновлена!\n\n"
                f"Необходимый ресурс для добытчиков: «{new_ore.capitalize()}».\n"
                f"Бот будет оповещать офицеров при нахождении жил этого ресурса. ⛏️"
            )
            return
        elif clean_text_no_mention in {"#закреп", "закреп"}:
            curr = clan_settings.get("required_ore", "железо")
            await message.answer(
                f"ℹ️ Текущий ресурс для добытчиков: «{curr.capitalize()}».\n"
                f"Чтобы изменить его через #закреп, укажите в тексте закрепа строку вида:\n"
                f"«Железо: добытчика ставим всегда» (или Торий, Сера, Ртуть)."
            )
            return

    # 7. Команда /созыв (только для офицеров)
    if clean_text_no_mention.startswith(("/созыв", "созыв")):
        if message.from_id not in get_officer_ids():
            await message.answer("⚠️ Команда /созыв доступна только офицерскому составу.")
            return

        unhit_list = clan_settings.get("unhit_boss_players", [])
        if not unhit_list:
            await message.answer("ℹ️ Список не отбивших босса пуст. Сначала перешлите актуальный лог босса из игры.")
            return

        tags = []
        missing_count = 0
        for entry in unhit_list:
            nick = entry.get("nickname", "Боец")
            uid = entry.get("user_id")
            # Пробуем найти актуальный uid в clan_members по нику
            if not uid:
                for m_uid, m_info in clan_members.items():
                    if normalize(m_info.get("nickname")) == normalize(nick):
                        uid = int(m_uid)
                        entry["user_id"] = uid
                        break
            if uid:
                tags.append(f"@id{uid} ({nick})")
            else:
                tags.append(f"{nick} (не привязан профиль)")
                missing_count += 1

        save_clan_settings()

        raw_without_bot = re.sub(r"^(?:@?club\d+|\[club\d+\|[^\]]+\])\s*", "", text).strip()
        call_parts = raw_without_bot.split(maxsplit=1)
        custom_header = call_parts[1].strip() if len(call_parts) > 1 else "Бойцы, ещё не отбившие гильд-босса, срочно зайдите в игру!"
        lines = "\n".join(f"• {t}" for t in tags)
        notice = ""
        if missing_count > 0:
            notice = f"\n\n⚠️ {missing_count} бойцов не вызвали «статус» в чате, поэтому их нельзя тегнуть кликабельной ссылкой."

        await message.answer(
            f"⚔️ ВНИМАНИЕ! СОЗЫВ НА ГИЛЬД-БОССА! ⚔️\n\n"
            f"{custom_header}\n\n"
            f"Не отбили босса ({len(tags)} чел.):\n"
            f"{lines}"
            f"{notice}\n\n"
            f"Гильдия ждёт каждого! Добиваем босса! 🔥💥"
        )
        return

    # 8. Анализ входящих и пересланных сообщений (статус, лог босса, споты ресурсов).
    # Используем только текст сообщения и реальные пересылки (fwd_messages),
    # исключая цитаты/ответы (reply_message), чтобы бот не реагировал на ответы к старому логу.
    candidate_messages = []
    if message.text:
        candidate_messages.append((message.from_id, message.text, getattr(message, "date", None)))
    for fwd in unpack_fwd_messages(message):
        if fwd.text:
            candidate_messages.append((fwd.from_id, fwd.text, getattr(fwd, "date", None)))

    for sender_id, msg_text, msg_date in candidate_messages:
        # Проверка кланового закрепа (#закреп) в тексте или пересылке
        zakrep_ore = parse_zakrep_ore(msg_text)
        if zakrep_ore:
            clan_settings["required_ore"] = zakrep_ore
            clan_settings["monitored_resources"] = [zakrep_ore]
            save_clan_settings()
            await message.answer(
                f"📌 Настройка ресурса из #закреп обновлена!\n\n"
                f"Необходимый ресурс для добытчиков: «{zakrep_ore.capitalize()}».\n"
                f"Бот будет оповещать офицеров при нахождении жил этого ресурса. ⛏️"
            )
            return

        # A. Проверка карточки статуса игрока (ToR статус)
        is_status_card = (
            ("| ур" in msg_text.lower() or "|ур" in msg_text.lower())
            and ("статус" in msg_text.lower() or "dha’t’elle" in msg_text.lower() or "dha't'elle" in msg_text.lower())
        )
        if is_status_card:
            stat_match = re.search(
                r"(?:^|\n)\s*([^\n|]+?)\s*\|\s*Ур\.?\s*\d+\s*\|\s*([^\n|]+)",
                msg_text,
                re.IGNORECASE,
            )
            if stat_match:
                raw_guild = stat_match.group(1)
                raw_rank = stat_match.group(2)
                clean_guild = re.sub(r"^[🏠🏡🏰🏛⛺🛡⚔👑⚜️\W_]+\s*", "", raw_guild).strip()
                clean_rank = re.sub(r"^[🏠🏡🏰🏛⛺🛡⚔👑⚜️\W_]+\s*", "", raw_rank).strip()

                target_user_id = None
                target_nickname = None

                # Никнейм из карточки ToR (строка сразу под 📜 Статус)
                nick_match = re.search(
                    r"📜\s*Статус\s*\n\s*[🔹•👤]?\s*(?:\[id(\d+)\|([^\]]+)\]|([^\n|]+))",
                    msg_text,
                    re.IGNORECASE,
                )
                if nick_match:
                    if nick_match.group(1):
                        target_user_id = int(nick_match.group(1))
                        target_nickname = nick_match.group(2).strip()
                    else:
                        candidate_nick = nick_match.group(3).strip()
                        target_nickname = re.sub(r"^[🔹•👤⚔️🛡⚜️\W_]+\s*", "", candidate_nick).strip()

                # Если UID ещё не определён, ищем [id...|...] в тексте
                if not target_user_id:
                    id_match = re.search(r"\[id(\d+)\|([^\]]+)\]", msg_text)
                    if id_match:
                        target_user_id = int(id_match.group(1))
                        if not target_nickname:
                            target_nickname = id_match.group(2).strip()

                # Если всё ещё нет UID, проверяем цитируемое сообщение или автора пересылки
                if not target_user_id:
                    if message.reply_message and message.reply_message.from_id > 0:
                        target_user_id = message.reply_message.from_id
                    elif message.from_id > 0:
                        target_user_id = message.from_id

                if target_user_id:
                    user_key = str(target_user_id)
                    already_recorded = user_key in clan_members
                    final_nick = target_nickname or f"id{target_user_id}"
                    clan_members[user_key] = {
                        "nickname": final_nick,
                        "guild": clean_guild or "Dha’t’elle",
                        "rank": clean_rank,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    save_clan_members()

                    # Автоматически регистрируем соклановца в базе профилей заказчиков (100% скидка)
                    customer_profiles[user_key] = {
                        "guild": clean_guild or "Dha’t’elle",
                        "nickname": final_nick,
                        "payment_type": "free",
                        "price": 0,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "source": "clan_chat_status",
                    }
                    save_customer_profiles()

                    # Если профиль уже был записан ранее — обновляем тихо, без спама в чат
                    if already_recorded:
                        return

                    # Отправляем подтверждение в чат только при первом сохранении профиля!
                    await message.answer(
                        f"✅ Профиль игрока @id{target_user_id} ({final_nick}) успешно сохранён в базе клана!\n"
                        f"🏰 Гильдия: {clean_guild}\n"
                        f"🎖 Звание: {clean_rank}"
                    )
                    return

        # B. Проверка сообщений о повышении / понижении
        promo_match = re.search(
            r"✅\s*Игрок\s+(?:\[id(\d+)\|([^\]]+)\]|@id(\d+)\s*\(([^)]+)\)|([^\n«]+?))\s+(повышен|понижен)\s+до\s+ранга\s+«([^»]+)»",
            msg_text,
            re.IGNORECASE,
        )
        if promo_match:
            promo_uid = promo_match.group(1) or promo_match.group(3)
            promo_name = (promo_match.group(2) or promo_match.group(4) or promo_match.group(5) or "").strip()
            action_word = promo_match.group(6)
            new_rank = promo_match.group(7).strip()

            if not promo_uid and promo_name:
                for uid_str, member in clan_members.items():
                    if normalize(member.get("nickname")) == normalize(promo_name):
                        promo_uid = uid_str
                        break

            if promo_uid:
                p_key = str(promo_uid)
                if p_key not in clan_members:
                    clan_members[p_key] = {
                        "nickname": promo_name or f"id{promo_uid}",
                        "guild": "Dha’t’elle",
                        "rank": new_rank,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                else:
                    clan_members[p_key]["rank"] = new_rank
                    clan_members[p_key]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_clan_members()
                await message.answer(f"🎖 Звание игрока {promo_name or f'id{promo_uid}'} обновлено в базе клана: {new_rank}.")
                return

        # C. Проверка лога гильд-босса (только при отправке/пересылке офицерами)
        if message.from_id in get_officer_ids():
            is_boss_log = (
                ("— не бил" in msg_text or "— бил" in msg_text)
                and ("гильдия" in msg_text.lower() or "били " in msg_text.lower())
            )
            if is_boss_log:
                if is_message_too_old(msg_date, max_age_seconds=600):
                    await message.answer(
                        "⚠️ Этот лог гильд-босса старше 10 минут и не принимается.\n"
                        "Пожалуйста, отправьте свежий лог из игры."
                    )
                    return

                unhit_matches = re.finditer(
                    r"[·•\u00b7*]\s*(?:\[id(\d+)\|([^\]]+)\]|@id(\d+)\s*\(([^)]+)\)|([^\n—–-]+?))\s*[—–-]\s*не\s+бил[аи]?",
                    msg_text,
                    re.IGNORECASE,
                )
                unhit_records = []
                for m in unhit_matches:
                    uid = m.group(1) or m.group(3)
                    name = (m.group(2) or m.group(4) or m.group(5) or "").strip()
                    if not uid and name:
                        for m_uid, m_info in clan_members.items():
                            if normalize(m_info.get("nickname")) == normalize(name):
                                uid = int(m_uid)
                                break
                    unhit_records.append({
                        "nickname": name or (f"id{uid}" if uid else "Боец"),
                        "user_id": int(uid) if uid else None,
                    })

                clan_settings["unhit_boss_players"] = unhit_records
                clan_settings["last_boss_log_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_clan_settings()

                if unhit_records:
                    await message.answer(
                        f"📋 Лог гильд-босса успешно сохранён!\n"
                        f"Не отбили босса: {len(unhit_records)} чел.\n\n"
                        f"📢 Чтобы созвать и тегнуть всех не отбивших, используйте команду:\n"
                        f"👉 /созыв\n"
                        f"(доступно только офицерам)"
                    )
                else:
                    await message.answer(
                        "🎉 По логу все члены гильдии успешно отбили босса! Отличная работа! 👏"
                    )
                return

        # D. Проверка лога натыкания на место добычи ресурсов
        res_match = re.search(r"место\s+добычи\s+«([^»]+)»", msg_text, re.IGNORECASE)
        if res_match:
            resource_name = res_match.group(1).strip()
            norm_res = normalize(resource_name)
            canonical_res = CANONICAL_RESOURCES.get(norm_res)
            required_ore = clan_settings.get("required_ore", "железо")

            if canonical_res and canonical_res == required_ore:
                if is_message_too_old(msg_date, max_age_seconds=600):
                    await message.answer(
                        f"⚠️ Пересланный лог с жилой «{resource_name}» старше 10 минут и не принимается.\n"
                        "Жила уже могла быть занята или истощена."
                    )
                    return

                player_id = message.from_id
                player_info = clan_members.get(str(player_id))
                player_rank = player_info.get("rank") if player_info else None

                if is_lieutenant_or_higher(player_rank):
                    # Уже Лейтенант или выше — тегать офицеров не требуется!
                    return

                try:
                    all_officers = list(get_officer_ids())
                    vos_users = await bot.api.users.get(user_ids=all_officers, fields=["online"])
                    online_vos = [u for u in vos_users if getattr(u, "online", 0) == 1]
                    target_vos = online_vos if online_vos else vos_users
                    officer_tags = " ".join(f"@id{u.id} ({u.first_name})" for u in target_vos)
                except Exception as err:
                    print(f"[ERROR] Не удалось запросить онлайн офицеров: {err}")
                    officer_tags = "@id706284129 (Глава) @id31959523 (Даша) @id208825850 (Миша) @id629691481 (Денис)"

                player_nick = player_info.get("nickname") if player_info else "Боец"
                rank_str = player_rank or "Рядовой"

                await message.answer(
                    f"🚨 Внимание, Офицерский Состав!\n\n"
                    f"🔩 Найдено ценное место добычи: «{resource_name}»!\n"
                    f"Игрок: @id{player_id} ({player_nick}) [Звание: {rank_str}]\n"
                    f"Необходимо повысить бойца до ранга Лейтенант для установки добытчика! ⛏️\n\n"
                    f"Офицеры: {officer_tags}"
                )
                return


async def initial_chat_setup() -> None:
    """Проверяет необходимость отправки начального призыва к вызову «статус» при старте бота."""
    await asyncio.sleep(2)
    chat_id = clan_settings.get("clan_chat_id")
    if chat_id and not clan_settings.get("status_request_sent"):
        try:
            await send_initial_status_call(chat_id)
            clan_settings["status_request_sent"] = True
            save_clan_settings()
            print(f"[INFO] Начальный запрос профилей отправлен в чат {chat_id}.")
        except Exception as err:
            print(f"[WARNING] Не удалось отправить начальный запрос профилей: {err}")


async def scheduled_reminders_worker() -> None:
    """Фоновый воркер для автоматических напоминаний в клан-чат в 15:00 по МСК."""
    while True:
        try:
            await asyncio.sleep(30)
            now_msk = datetime.now(timezone(timedelta(hours=3)))
            chat_id = clan_settings.get("clan_chat_id")
            if not chat_id:
                continue

            today_str = now_msk.strftime("%Y-%m-%d")
            weekday = now_msk.weekday()  # Пн=0, Вт=1, Ср=2, Чт=3, Пт=4, Сб=5, Вс=6

            if now_msk.hour == 15 and 0 <= now_msk.minute <= 10:
                # 1. Напоминание на РБ: вторник (1), среда (2), четверг (3) с тегами
                if weekday in (1, 2, 3) and clan_settings.get("last_rb_date") != today_str:
                    rb_tags = "@id706284129 (Артём) @id629691481 (Денис) @id32162922 (Артём) @id342456805 (Саша)"
                    rb_message = (
                        f"⚔️ РБ ТАЙМ! 📢\n\n"
                        f"{rb_tags}\n\n"
                        f"Бросайте все дела и чай с печеньками — сегодня Рейд-Босс! "
                        f"Пора настучать боссу по кумполу! 💥👊"
                    )
                    try:
                        await bot.api.messages.send(
                            peer_id=chat_id,
                            random_id=get_random_id(),
                            message=rb_message,
                        )
                        clan_settings["last_rb_date"] = today_str
                        save_clan_settings()
                    except Exception as err:
                        print(f"[ERROR] Не удалось отправить напоминание на РБ: {err}")

                # 2. Напоминание на КРБ: понедельник (0), среда (2), пятница (4) без тегов
                if weekday in (0, 2, 4) and clan_settings.get("last_krb_date") != today_str:
                    krb_message = (
                        "🛡️ ВНИМАНИЕ, КЛАН! СЕГОДНЯ КРБ! 🛡️\n\n"
                        "Не забудьте пробаффаться и отбить кланового босса! "
                        "Каждый удар на счету — покажем силу Dha’t’elle! ⚔️🔥"
                    )
                    try:
                        await bot.api.messages.send(
                            peer_id=chat_id,
                            random_id=get_random_id(),
                            message=krb_message,
                        )
                        clan_settings["last_krb_date"] = today_str
                        save_clan_settings()
                    except Exception as err:
                        print(f"[ERROR] Не удалось отправить напоминание на КРБ: {err}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[ERROR] Ошибка в scheduled_reminders_worker: {e}")
            await asyncio.sleep(5)


def make_keyboard(
    buttons: list[tuple[str, KeyboardButtonColor]],
    max_per_row: int = 2,
) -> str:
    """
    Создаёт обычную клавиатуру VK с распределением по строкам.
    """
    keyboard = Keyboard(one_time=True)

    for index, (label, color) in enumerate(buttons):
        if index > 0 and index % max_per_row == 0:
            keyboard.row()
        keyboard.add(
            Text(label),
            color=color,
        )

    return keyboard.get_json()


def main_keyboard() -> str:
    keyboard = Keyboard(one_time=False)
    keyboard.add(Text("📋 Мои заказы"), color=KeyboardButtonColor.PRIMARY)
    return keyboard.get_json()


def make_inline_keyboard(
    buttons: list[tuple[str, KeyboardButtonColor, dict]],
    max_per_row: int = 2,
) -> str:
    """
    Создаёт inline callback-клавиатуру с автоматическим распределением по строкам
    (в соответствии с лимитом VK до 5 кнопок в одной строке).
    """
    keyboard = Keyboard(inline=True)

    current_row_count = 0
    for label, color, payload in buttons:
        is_refresh_btn = isinstance(payload, dict) and payload.get("action") == "list_orders" and len(buttons) > 1
        if current_row_count > 0 and (current_row_count >= max_per_row or is_refresh_btn):
            keyboard.row()
            current_row_count = 0

        keyboard.add(
            Callback(
                label,
                payload,
            ),
            color=color,
        )
        current_row_count += 1
        if is_refresh_btn:
            current_row_count = max_per_row

    return keyboard.get_json()


async def get_user_name(user_id: int) -> Optional[tuple[str, str]]:
    """
    Получает имя и фамилию пользователя.

    ВАЖНО:
    users.get принимает user_ids=[id].
    Также защищаемся от пустого ответа VK.
    """
    try:
        users = await bot.api.users.get(
            user_ids=[user_id]
        )

        if not users:
            return None

        user = users[0]

        return user.first_name, user.last_name

    except Exception as error:
        print(
            f"[ERROR] Не удалось получить пользователя "
            f"{user_id}: {error}"
        )
        return None


def get_photo_attachments(message: Message) -> list[str]:
    """
    Ищет фото и документы (изображения/файлы артов) среди вложений
    и возвращает список стандартных строк VK (photoX_Y или docX_Y).
    """
    attachments = []

    try:
        photos = message.get_photo_attachments()
        for photo in photos or []:
            attachment = f"photo{photo.owner_id}_{photo.id}"
            access_key = getattr(photo, "access_key", None)
            if access_key:
                attachment = f"{attachment}_{access_key}"
            attachments.append(attachment)
    except Exception:
        pass

    if not attachments and message.attachments:
        try:
            for attachment in message.attachments:
                if getattr(attachment, "type", None) == "photo" and getattr(attachment, "photo", None):
                    photo = attachment.photo
                    attachment_id = f"photo{photo.owner_id}_{photo.id}"
                    access_key = getattr(photo, "access_key", None)
                    if access_key:
                        attachment_id = f"{attachment_id}_{access_key}"
                    attachments.append(attachment_id)
        except Exception as error:
            print(f"[ERROR] Ошибка обработки фото: {error}")

    # Также извлекаем документы (docs), так как художники часто отправляют результаты без сжатия документами
    try:
        docs = message.get_doc_attachments()
        for doc in docs or []:
            attachment = f"doc{doc.owner_id}_{doc.id}"
            access_key = getattr(doc, "access_key", None)
            if access_key:
                attachment = f"{attachment}_{access_key}"
            if attachment not in attachments:
                attachments.append(attachment)
    except Exception:
        pass

    if message.attachments:
        try:
            for attachment in message.attachments:
                if getattr(attachment, "type", None) == "doc" and getattr(attachment, "doc", None):
                    doc = attachment.doc
                    attachment_id = f"doc{doc.owner_id}_{doc.id}"
                    access_key = getattr(doc, "access_key", None)
                    if access_key:
                        attachment_id = f"{attachment_id}_{access_key}"
                    if attachment_id not in attachments:
                        attachments.append(attachment_id)
        except Exception as error:
            print(f"[ERROR] Ошибка обработки документов: {error}")

    return attachments


def get_photo_attachment(message: Message) -> Optional[str]:
    attachments = get_photo_attachments(message)
    return attachments[0] if attachments else None


# ============================================================
# КЛАВИАТУРЫ
# ============================================================

def race_keyboard():
    return make_keyboard([
        ("Человек", KeyboardButtonColor.PRIMARY),
        ("Эльф", KeyboardButtonColor.PRIMARY),
        ("Орк/Гоблин", KeyboardButtonColor.PRIMARY),
        ("Фурри/Животное", KeyboardButtonColor.PRIMARY),
    ])


def gender_keyboard():
    return make_keyboard([
        ("Мужской", KeyboardButtonColor.PRIMARY),
        ("Женский", KeyboardButtonColor.PRIMARY),
        ("Неважно", KeyboardButtonColor.SECONDARY),
    ])


def style_keyboard():
    return make_keyboard([
        ("Аниме", KeyboardButtonColor.PRIMARY),
        ("Реализм", KeyboardButtonColor.PRIMARY),
        ("Мультяшный", KeyboardButtonColor.PRIMARY),
        ("Пиксель-арт", KeyboardButtonColor.PRIMARY),
    ])


def mood_keyboard():
    return make_keyboard([
        ("Мрачное/Дарк", KeyboardButtonColor.PRIMARY),
        ("Яркое/Неон", KeyboardButtonColor.PRIMARY),
        ("Пастельное/Милое", KeyboardButtonColor.PRIMARY),
    ])


def reference_keyboard():
    return make_keyboard([
        ("Готово", KeyboardButtonColor.POSITIVE),
        ("Пропустить", KeyboardButtonColor.SECONDARY),
    ])


def preview_keyboard():
    return make_keyboard([
        ("✅ Отправить заказ", KeyboardButtonColor.POSITIVE),
        ("❌ Отменить и начать заново", KeyboardButtonColor.NEGATIVE),
    ], max_per_row=1)


def accept_keyboard(order_id: str):
    return make_inline_keyboard([
        (
            "✅ Принять заказ",
            KeyboardButtonColor.POSITIVE,
            {
                "action": "accept_order",
                "order_id": order_id,
            },
        ),
        (
            "📋 Заказы",
            KeyboardButtonColor.PRIMARY,
            {"action": "list_orders"},
        ),
    ])


def complete_keyboard(order_id: str):
    return make_inline_keyboard([
        (
            "✅ Отметить выполненным",
            KeyboardButtonColor.POSITIVE,
            {
                "action": "complete_order",
                "order_id": order_id,
            },
        )
    ])


def artist_orders_keyboard() -> str:
    return make_inline_keyboard([
        (
            "📋 Заказы",
            KeyboardButtonColor.PRIMARY,
            {"action": "list_orders"},
        )
    ])


def order_payment_text(order: dict) -> str:
    payment_type = order.get("payment_type")
    price = order.get("price", 0)
    if payment_type == "free":
        return "Бесплатно"
    if payment_type == "ally":
        return f"Союзная скидка 50% ({price} ₽)"
    if payment_type in ("paid", "standard"):
        return f"Стандартный тариф ({price} ₽)"
    return f"Платно, цена: {price} ₽"


async def send_open_orders(peer_id: int) -> None:
    open_orders = get_open_orders()
    if not open_orders:
        await bot.api.messages.send(
            peer_id=peer_id,
            random_id=get_random_id(),
            message="📋 Сейчас нет открытых заказов.",
            keyboard=artist_orders_keyboard(),
        )
        return

    status_labels = {
        "waiting": "Ожидает художника",
        "in_progress": "В работе",
        "completed": "Выполнено",
    }
    for page_start in range(0, len(open_orders), 8):
        page_orders = open_orders[page_start:page_start + 8]
        lines = ["📋 Открытые заказы:"]
        buttons = []
        for index, (order_id, order) in enumerate(page_orders, start=page_start + 1):
            artist = order.get("artist_name") or "не назначен"
            status_text = status_labels.get(order.get("status"), "Статус неизвестен")
            lines.append(
                f"\n{index}. Заказ {order_id[:8]} — "
                f"{status_text}\n"
                f"Художник: {artist}"
            )
            buttons.append((
                f"Подробнее {index}",
                KeyboardButtonColor.PRIMARY,
                {"action": "order_details", "order_id": order_id},
            ))
        buttons.append((
            "🔄 Обновить",
            KeyboardButtonColor.SECONDARY,
            {"action": "list_orders"},
        ))
        await bot.api.messages.send(
            peer_id=peer_id,
            random_id=get_random_id(),
            message="\n".join(lines),
            keyboard=make_inline_keyboard(buttons),
        )


def get_open_orders() -> list[tuple[str, dict]]:
    return [
        (order_id, order)
        for order_id, order in order_records.items()
        if order.get("status") in {"waiting", "in_progress"}
    ]


async def delete_artist_orders(message: Message) -> None:
    command_text = (message.text or "").strip()
    clean_cmd = re.sub(r"^(?:@?club\d+|\[club\d+\|[^\]]+\])\s*", "", command_text).strip()
    arguments = clean_cmd.split(maxsplit=1)
    try:
        is_admin = await message.user_is_admin(message.from_id)
    except Exception as error:
        print(f"[ERROR] Не удалось проверить права участника: {error}")
        await message.answer("Не удалось проверить права администратора. Убедись, что бот назначен администратором беседы.")
        return

    if not is_admin:
        await message.answer("Удалять заказы могут только администраторы беседы.")
        return

    if len(arguments) != 2 or not arguments[1].strip():
        await message.answer(
            "Использование: /удалить 1, /удалить 1-3, "
            "/удалить 1 3 5 или /удалить все."
        )
        return

    open_orders = get_open_orders()
    if not open_orders:
        await message.answer("Нет открытых заказов для удаления.")
        return

    clean_raw_selection = arguments[1].replace(",", " ")
    selection = normalize(clean_raw_selection)
    if selection == "все":
        selected_numbers = list(range(1, len(open_orders) + 1))
    elif re.fullmatch(r"\d+\s*-\s*\d+", selection):
        first_number, last_number = map(int, re.split(r"\s*-\s*", selection))
        if first_number > last_number:
            await message.answer("В диапазоне сначала укажи меньший номер.")
            return
        selected_numbers = list(range(first_number, last_number + 1))
    elif re.fullmatch(r"\d+(?:\s+\d+)*", selection):
        selected_numbers = [int(number) for number in selection.split()]
    else:
        await message.answer(
            "Номера должны быть числами. Примеры: /удалить 1-3 или /удалить 1 3 5."
        )
        return

    if len(set(selected_numbers)) != len(selected_numbers):
        await message.answer("В списке есть повторяющиеся номера. Укажи каждый номер один раз.")
        return
    if any(number < 1 or number > len(open_orders) for number in selected_numbers):
        await message.answer(
            f"Номер вне списка. Сейчас открытых заказов: {len(open_orders)}."
        )
        return

    selected_order_ids = [open_orders[number - 1][0] for number in selected_numbers]
    for order_id in selected_order_ids:
        order_records.pop(order_id, None)
    save_order_records()

    await message.answer(
        f"Удалено заказов: {len(selected_order_ids)}. "
        "Нумерация оставшихся заказов обновилась."
    )


async def publish_artist_orders_button() -> None:
    try:
        await bot.api.messages.send(
            peer_id=ARTIST_CHAT_ID,
            random_id=get_random_id(),
            message="📋 Нажмите кнопку «Заказы», чтобы посмотреть текущие заявки.",
            keyboard=artist_orders_keyboard(),
        )
    except Exception as error:
        print(f"[WARNING] Не удалось отправить кнопку заказов: {error}")


def detailed_order_text(order_id: str, order: dict) -> str:
    status_labels = {
        "waiting": "Ожидает художника",
        "in_progress": "В работе",
        "completed": "Выполнено",
    }
    artist = order.get("artist_name") or "не назначен"
    guild = order.get("guild") or "не указана"
    return (
        f"📋 Подробности заказа {order_id[:8]}\n\n"
        f"{order.get('artist_message', 'Данные заказа отсутствуют')}\n\n"
        f"Гильдия: {guild}\n"
        f"Оплата: {order_payment_text(order)}\n"
        f"Статус: {status_labels.get(order.get('status'), 'неизвестен')}\n"
        f"Художник: {artist}"
    )


def customer_orders_text(customer_id: int) -> str:
    user_orders = [
        (order_id, order)
        for order_id, order in order_records.items()
        if order.get("customer_id") == customer_id
    ]

    if not user_orders:
        return (
            "У тебя пока нет заказов художникам.\n"
            "Оформить заказ на арт можно в Мини-Приложении сообщества."
        )

    status_labels = {
        "waiting": "Ожидает художника",
        "in_progress": "В работе",
        "completed": "Выполнено",
    }
    lines = ["📋 Твои заказы:"]
    for order_id, order in user_orders:
        race = order.get("race", "Раса не указана")
        style = order.get("style", "Стиль не указан")
        status_text = status_labels.get(order.get("status"), "Статус неизвестен")
        lines.append(
            f"\nЗаказ {order_id[:8]} — {status_text}\n"
            f"{race}, {style}"
        )
    return "\n".join(lines)


# ============================================================
# ПРЕВЬЮ ЗАКАЗА
# ============================================================

def order_reference_attachments(order: dict) -> list[str]:
    references = order.get("references")
    if references is not None:
        return references
    legacy_reference = order.get("reference")
    return [legacy_reference] if legacy_reference else []


def build_preview(order: dict) -> str:
    references = order_reference_attachments(order)
    return (
        "📋 ПРЕДПРОСМОТР ЗАКАЗА\n\n"

        f"🎭 Раса: {order['race']}\n"
        f"⚧ Пол: {order['gender']}\n"
        f"🎨 Стиль: {order['style']}\n"
        f"🌈 Настроение: {order['mood']}\n\n"
        f"🏠 Гильдия: {order.get('guild', 'не указана')}\n"
        f"💰 Оплата: {order_payment_text(order)}\n\n"

        "📝 Описание:\n"
        f"{order['description']}\n\n"

        "🖼 Референс: "
        f"{f'{len(references)} изображений' if references else 'не указан'}\n\n"

        "Проверь данные перед отправкой."
    )


# ============================================================
# ФОРМАТ ЗАКАЗА ДЛЯ ХУДОЖНИКОВ
# ============================================================

def build_artist_order(
    order: dict,
    order_id: str,
    customer_id: int,
    first_name: str,
    last_name: str,
) -> str:
    references = order_reference_attachments(order)
    reference_summary = (
        f"будет отправлено отдельно ({len(references)})"
        if references
        else "отсутствует"
    )

    return (
        "🎨 НОВЫЙ ЗАКАЗ НА АРТ\n\n"

        f"🆔 Номер заказа: {order_id[:8]}\n\n"

        f"👤 Заказчик: "
        f"@id{customer_id} ({first_name} {last_name})\n\n"

        f"🎭 Раса: {order['race']}\n"
        f"⚧ Пол: {order['gender']}\n"
        f"🎨 Стиль: {order['style']}\n"
        f"🌈 Настроение: {order['mood']}\n\n"
        f"🏠 Гильдия: {order.get('guild', 'не указана')}\n"
        f"💰 Оплата: {order_payment_text(order)}\n\n"

        "📝 Описание:\n"
        f"{order['description']}\n\n"

        "🖼 Референс: "
        f"{reference_summary}"
    )


# ============================================================
# АНКЕТА
# ============================================================

@bot.on.message()
async def order_handler(message: Message):
    """
    Обрабатывает анкету в ЛС и раздельные функции в беседах.
    """

    # --------------------------------------------------------
    # Жёсткая изоляция ЛС
    # --------------------------------------------------------

    if message.peer_id != message.from_id:
        if message.peer_id == ARTIST_CHAT_ID:
            message_text = (message.text or "").strip()
            clean_artist_text = re.sub(
                r"^(?:@?club\d+|\[club\d+\|[^\]]+\])\s*",
                "",
                normalize(message_text),
            ).strip()
            if re.match(r"^/?удалить(?:\s|$)", clean_artist_text):
                await delete_artist_orders(message)
            elif is_artist_orders_command(message_text):
                await send_open_orders(message.peer_id)
            else:
                await forward_artist_result(message)
        else:
            await handle_clan_chat(message)
        return

    # --------------------------------------------------------
    # Защита от системных сообщений
    # --------------------------------------------------------

    text = message.text or ""
    clean_text = normalize(text)

    user_id = message.from_id

    # --------------------------------------------------------
    # Отмена заказа на любом этапе
    # --------------------------------------------------------
    if clean_text in {"отмена", "/cancel", "отменить", "стоп"}:
        reset_order(user_id)
        await message.answer(
            "Для оформления заказа используйте Мини-Приложение ВКонтакте.\n"
            "Текущие заявки доступны по кнопке «📋 Мои заказы».",
            keyboard=main_keyboard(),
        )
        return

    # Проверка на заказ из мини-приложения
    if "ЗАКАЗ НА АРТ ИЗ ПРИЛОЖЕНИЯ" in (message.text or "") or "Номер заказа: ord_" in (message.text or ""):
        await handle_app_order_message(message)
        return

    # Проверка на оплату Торговой Лавки (чек из ToR)
    transfer_msg, transfer_match = get_customer_tor_transfer_log(message)
    if transfer_msg is not None:
        await handle_tor_store_payment(message, transfer_msg, transfer_match)
        return

    profile_key = str(user_id)
    game_profile = get_customer_tor_profile(message, user_id)

    # Проверка нового/пересланного профиля ToR
    if game_profile is not None:
        guild_name = extract_guild_name(message, game_profile) or "Без гильдии"
        tariff = get_customer_tariff(guild_name)
        player_nick = extract_nickname_from_profile(game_profile.text or "", user_id)

        if tariff.get("blocked"):
            customer_profiles[profile_key] = {
                "guild": guild_name,
                "nickname": player_nick,
                "profile_link": f"https://vk.com/id{user_id}",
                "payment_type": tariff["type"],
                "price": tariff["price"],
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            save_customer_profiles()
            await message.answer(
                f"⛔ Гильдия определена: «{guild_name}».\n"
                "К сожалению, для представителей вашей гильдии оформление заказов заблокировано."
            )
            return

        customer_profiles[profile_key] = {
            "guild": guild_name,
            "nickname": player_nick,
            "profile_link": f"https://vk.com/id{user_id}",
            "payment_type": tariff["type"],
            "price": tariff["price"],
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save_customer_profiles()

        disclaimer = (
            f"👤 Персонаж: {player_nick} (https://vk.com/id{user_id})\n"
            f"🏰 Гильдия определена: {guild_name}\n"
            f"💰 Тариф: {tariff['label']}\n\n"
            "📜 Пользовательское соглашение и правила:\n"
            "1. Гарантом всех сделок и заказов выступает Даша (@motheroftor).\n"
            "2. Данные профиля ToR проверяются для расчета союзных скидок.\n"
            "3. Информацию профиля необходимо обновлять раз в месяц или при смене гильдии.\n\n"
            "🎨 Оформление заказов на арт теперь происходит в Мини-Приложении ВКонтакте!\n"
            "После выгрузки приложения в ВК прямо здесь появится кнопка быстрого запуска."
        )
        await message.answer(
            disclaimer,
            keyboard=main_keyboard(),
        )
        return

    # Если профиля ещё нет в базе
    if profile_key not in customer_profiles:
        await message.answer(
            "Перед использованием данного бота отправь сюда свой "
            "профиль из ToR не позднее 24 часов.\n\n"
            "⚠️ Информацию о гильдии необходимо обновлять раз в месяц или при смене гильдии. "
            "Гарант заказов — Даша (@motheroftor)."
        )
        return

    user_prof = customer_profiles.get(profile_key, {})

    # Блокировка врагов (Carpe Diem)
    if user_prof.get("payment_type") == "enemy" or get_customer_tariff(user_prof.get("guild")).get("blocked"):
        await message.answer("⛔ Доступ к боту для представителей вашей гильдии заблокирован.")
        return

    # Напоминание об обновлении профиля раз в месяц при попытке начать заказ
    if clean_text in {"начать", "привет", "заказ", "начать заказ", "/start"}:
        updated_at_str = user_prof.get("updated_at")
        if updated_at_str:
            try:
                prof_dt = datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M")
                if (datetime.now() - prof_dt).days >= 30:
                    await message.answer(
                        "⚠️ Внимание: твой профиль ToR был обновлён более 30 дней назад.\n"
                        "Пожалуйста, не забудь переслать свежий профиль из ToR для сохранения союзных скидок!"
                    )
            except Exception:
                pass

    if clean_text in {"мои заказы", "📋 мои заказы"}:
        await message.answer(
            customer_orders_text(user_id),
            keyboard=main_keyboard(),
        )
        return

    # --------------------------------------------------------
    # ОФОРМЛЕНИЕ ЗАКАЗОВ В МИНИ-ПРИЛОЖЕНИИ
    # --------------------------------------------------------
    user_prof = customer_profiles.get(profile_key, {})
    guild_name = user_prof.get("guild", "Без гильдии")
    tariff = get_customer_tariff(guild_name)

    app_message = (
        "🎨 Оформление заказов на арт перенесено в Мини-Приложение ВКонтакте!\n\n"
        f"🏰 Ваша гильдия: {guild_name}\n"
        f"💰 Ваш тариф: {tariff.get('label', 'Бесплатно')}\n"
        f"🛡️ Гарант сделок: Даша (@motheroftor)\n\n"
        "✨ В мини-приложении доступен интерактивный выбор расы, стиля, настроения, подсчет стоимости и передача описания персонажа.\n\n"
        "📱 Анкета в личных сообщениях бота отключена в пользу удобного приложения. Как только приложение будет опубликовано в сообществе, прямо здесь появится кнопка запуска «Приложение» в 1 клик!\n\n"
        "📋 Для проверки статуса ваших текущих заказов нажмите «📋 Мои заказы»."
    )
    await message.answer(app_message, keyboard=main_keyboard())
    return


# ============================================================
# ИНТЕГРАЦИЯ С МИНИ-ПРИЛОЖЕНИЕМ (API ПРИЁМА ЗАКАЗОВ)
# ============================================================

async def submit_order_from_app(customer_id: int, order_data: dict) -> tuple[bool, str]:
    """
    Создаёт заказ, поступивший из VK Mini App:
    - Отправляет заявку в чат художников ARTIST_CHAT_ID с кнопкой принятия.
    - Сохраняет в order_records и orders.json.
    - Возвращает (True, order_id) или (False, error_message).
    """
    user_data = await get_user_name(customer_id)
    first_name = user_data[0] if user_data else "Игрок"
    last_name = user_data[1] if user_data else ""
    order_id = uuid4().hex

    artist_message = build_artist_order(
        order=order_data,
        order_id=order_id,
        customer_id=customer_id,
        first_name=first_name,
        last_name=last_name,
    )

    try:
        await bot.api.messages.send(
            peer_id=ARTIST_CHAT_ID,
            random_id=get_random_id(),
            message=artist_message,
            keyboard=accept_keyboard(order_id),
        )
    except Exception as error:
        print(f"[ERROR] Не удалось отправить заказ в чат художников: {error}")
        return False, str(error)

    references = order_reference_attachments(order_data)
    if references:
        try:
            await bot.api.messages.send(
                peer_id=ARTIST_CHAT_ID,
                random_id=get_random_id(),
                message=(
                    f"🖼 Референсы к заказу {order_id[:8]} "
                    f"({len(references)} изображения)"
                ),
                attachment=",".join(references),
            )
        except Exception as error:
            print(f"[ERROR] Не удалось отправить референс заказа {order_id[:8]}: {error}")

    order_records[order_id] = {
        "customer_id": customer_id,
        "status": "waiting",
        "race": order_data.get("race", "Не указана"),
        "style": order_data.get("style", "Не указан"),
        "guild": order_data.get("guild", "не указана"),
        "payment_type": order_data.get("payment_type", "free"),
        "price": order_data.get("price", 0),
        "references": references,
        "artist_message": artist_message,
        "artist_message_cmid": None,
        "artist_id": None,
        "artist_name": None,
        "result_sent": False,
    }
    save_order_records()
    return True, order_id


async def handle_app_order_message(message: Message):
    """
    Обрабатывает заказ на арт, сформированный в Мини-Приложении и переданный в ЛС боту.
    Пересылает заявку в чат художников с фото-референсами и кнопкой 'Принять заказ'.
    """
    user_id = message.from_id
    text = message.text or ""

    # Извлекаем фото-вложения (референсы)
    refs = get_photo_attachments(message)

    # Извлекаем параметры заказа из текста
    race_m = re.search(r"Раса:\s*([^\n|]+)", text, re.IGNORECASE)
    gender_m = re.search(r"Пол:\s*([^\n|]+)", text, re.IGNORECASE)
    style_m = re.search(r"Стиль:\s*([^\n|]+)", text, re.IGNORECASE)
    mood_m = re.search(r"Настроение:\s*([^\n|]+)", text, re.IGNORECASE)
    desc_m = re.search(r"Описание персонажа:\s*([\s\S]+)", text, re.IGNORECASE)

    user_prof = customer_profiles.get(str(user_id), {})
    guild_name = user_prof.get("guild", "не указана")
    tariff = get_customer_tariff(guild_name)

    order_data = {
        "race": race_m.group(1).strip() if race_m else "Не указана",
        "gender": gender_m.group(1).strip() if gender_m else "Не указан",
        "style": style_m.group(1).strip() if style_m else "Не указан",
        "mood": mood_m.group(1).strip() if mood_m else "Не указано",
        "description": desc_m.group(1).strip() if desc_m else text,
        "guild": guild_name,
        "payment_type": tariff.get("type", "free"),
        "price": tariff.get("price", 0),
        "references": refs
    }

    success, order_id_or_err = await submit_order_from_app(user_id, order_data)

    if success:
        short_id = order_id_or_err[:8]
        await message.answer(
            f"🎨 Ваш заказ на арт #{short_id} успешно передан художникам гильдии Dha’t’elle!\n\n"
            f"👤 Заказчик: @id{user_id}\n"
            f"🏰 Гильдия: {guild_name}\n"
            f"💰 Стоимость: {tariff.get('label', 'Бесплатно')}\n"
            f"🖼 Прикреплено референсов: {len(refs)}\n"
            f"🛡️ Гарант: Даша (@motheroftor)\n\n"
            "⏳ Как только художник примет заказ в работу и нарисует арт, готовый результат придёт прямо сюда в ЛС!",
            keyboard=main_keyboard()
        )
    else:
        await message.answer(
            f"⚠️ Ошибка при передаче заказа в чат художников: {order_id_or_err}.\n"
            "Пожалуйста, свяжитесь с гарантом Дашей (@motheroftor)."
        )


async def handle_tor_store_payment(message: Message, forwarded, match):
    """
    Проверяет пересланный чек ToR (-227820718) и выдает подписку на Торговую лавку.
    """
    now_ts = int(datetime.now().timestamp())
    msg_date = getattr(forwarded, "date", 0) or now_ts
    if now_ts - msg_date > 86400:
        await message.answer(
            "⚠️ Этот чек перевода устарел (старше 24 часов).\n"
            "Пожалуйста, перешлите свежий чек передачи ядер/RND из игры ToR."
        )
        return

    raw_amount_str = re.sub(r"[\s,.]+", "", match.group(1))
    try:
        amount = int(raw_amount_str)
    except ValueError:
        amount = 0

    curr_str = match.group(2).lower()
    currency = "rnd" if ("rnd" in curr_str or "рнд" in curr_str) else "cores"

    cores_price = clan_settings.get("cores_price", 27000)
    rnd_price = clan_settings.get("rnd_price", 1000)
    required = rnd_price if currency == "rnd" else cores_price

    if amount < required:
        curr_label = "RND" if currency == "rnd" else "ядер 🔮"
        await message.answer(
            f"⚠️ Недостаточная сумма перевода!\n"
            f"Передано: {amount:,} {curr_label}.\n"
            f"Требуется минимум: {required:,} {curr_label}."
        )
        return

    recipient = match.group(3).strip().lower()
    valid_recips = ["ярость всегда рядом", "geek_mann", "208825850", "тразир"]
    if not any(vr in recipient for vr in valid_recips):
        await message.answer(
            "⛔ Ошибка получателя!\n"
            "Перевод должен быть адресован персонажу «Ярость всегда рядом» (vk.com/id208825850)."
        )
        return

    log_key = f"{msg_date}_{amount}_{currency}_{recipient}"
    used_logs = clan_settings.setdefault("used_tor_logs", [])
    if log_key in used_logs:
        await message.answer("⛔ Этот чек перевода уже был активирован ранее!")
        return
    used_logs.append(log_key)

    user_id = message.from_id
    user_key = str(user_id)
    store_subs = clan_settings.setdefault("store_subscriptions", {})
    rent_days = clan_settings.get("rent_days", 30)
    duration_sec = rent_days * 86400

    current_exp = store_subs.get(user_key, {}).get("expires_at", 0)
    base_ts = max(now_ts, current_exp)
    new_exp = base_ts + duration_sec

    user_nick = None
    if user_key in clan_members:
        user_nick = clan_members[user_key].get("nickname")
    elif user_key in customer_profiles:
        user_nick = customer_profiles[user_key].get("nickname")
    if not user_nick:
        user_info = await get_user_name(user_id)
        user_nick = f"{user_info[0]} {user_info[1]}".strip() if user_info else f"Игрок #{user_id}"

    store_subs[user_key] = {
        "user_id": user_id,
        "nickname": user_nick,
        "expires_at": new_exp,
        "activated_at": now_ts,
        "amount": amount,
        "currency": currency,
    }
    save_clan_settings()
    sync_subscriptions_to_miniapp()

    exp_date_str = datetime.fromtimestamp(new_exp).strftime("%d.%m.%Y")
    curr_label = "RND 🪙" if currency == "rnd" else "ядер 🔮"
    await message.answer(
        f"✅ Оплата аренды Торговой лавки ({amount:,} {curr_label}) подтверждена!\n\n"
        f"🏪 Ваша торговая лавка в мини-приложении Dha’t’elle успешно активирована на {rent_days} дней (до {exp_date_str})!\n\n"
        "🔥 Ваши товары на Рынке получили наивысший VIP-приоритет и будут отображаться на самом верху списка, "
        "а покупатели смогут нажать «В лавку» и открыть вашу персональную витрину.\n\n"
        "📱 Откройте мини-приложение, чтобы выставить свои товары!",
        keyboard=main_keyboard()
    )


# ============================================================
# MESSAGE EVENT — "ПРИНЯТЬ ЗАКАЗ"
# ============================================================

@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    dataclass=MessageEvent,
)
async def handle_message_event(event: MessageEvent):
    event_data = event.object
    payload = event_data.payload

    async def answer_callback(text: str) -> None:
        try:
            await bot.api.messages.send_message_event_answer(
                event_id=event_data.event_id,
                user_id=event_data.user_id,
                peer_id=event_data.peer_id,
                event_data=json.dumps({
                    "type": "show_snackbar",
                    "text": text,
                }),
            )
        except Exception as error:
            print(f"[WARNING] Не удалось ответить на MessageEvent: {error}")

    if not payload:
        return

    action = payload.get("action")

    if action == "show_wishes":
        await answer_callback("Обновляю список пожеланий.")
        await send_chat_wishes(event_data.peer_id)
        return

    if event_data.peer_id != ARTIST_CHAT_ID:
        return

    if action == "list_orders":
        await answer_callback("Обновляю список заказов.")
        await send_open_orders(event_data.peer_id)
        return

    order_id = payload.get("order_id")
    order_record = order_records.get(order_id)
    if order_record is None:
        await answer_callback("Заказ не найден.")
        return

    if action == "order_details":
        await answer_callback("Открываю подробности заказа.")
        detail_buttons = []
        if order_record.get("status") == "waiting":
            detail_buttons.append((
                "✅ Принять заказ",
                KeyboardButtonColor.POSITIVE,
                {"action": "accept_order", "order_id": order_id},
            ))
        detail_buttons.append((
            "📋 Заказы",
            KeyboardButtonColor.PRIMARY,
            {"action": "list_orders"},
        ))
        await bot.api.messages.send(
            peer_id=event_data.peer_id,
            random_id=get_random_id(),
            message=detailed_order_text(order_id, order_record),
            attachment=",".join(order_reference_attachments(order_record)) or None,
            keyboard=make_inline_keyboard(detail_buttons),
        )
        return

    artist_id = event_data.user_id

    if action == "accept_order":
        if order_record["status"] != "waiting":
            await answer_callback("Этот заказ уже принят.")
            return
        order_record["status"] = "in_progress"
        order_record["artist_id"] = artist_id
        order_record["bot_group_id"] = event.group_id
        order_record["artist_message_cmid"] = (
            event_data.conversation_message_id
        )
    elif action == "complete_order":
        if order_record.get("status") == "completed":
            await answer_callback("Этот заказ уже отмечен выполненным!")
            return
        if (
            order_record["status"] != "in_progress"
            or order_record["artist_id"] != artist_id
        ):
            await answer_callback("Этот заказ нельзя отметить выполненным.")
            return
        order_record["status"] = "completed"
        order_record["bot_group_id"] = event.group_id
        order_record["artist_message_cmid"] = (
            event_data.conversation_message_id
        )
    else:
        return

    save_order_records()

    artist_data = await get_user_name(artist_id)
    if artist_data is None:
        artist_name = "Неизвестный художник"
    else:
        artist_name = " ".join(artist_data)

    if action == "accept_order":
        order_record["artist_name"] = artist_name
        save_order_records()
        order_text = (
            f"{order_record['artist_message']}\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🔒 ЗАКАЗ ВЗЯТ В РАБОТУ\n\n"
            f"Художник: @id{artist_id} ({artist_name})"
        )
        keyboard = complete_keyboard(order_id)
        customer_message = (
            "🎉 Твой заказ принят в работу!\n\n"
            f"Художник: @id{artist_id} ({artist_name}).\n"
            "Статус можно проверить кнопкой «Мои заказы»."
        )
        snackbar = "Заказ принят!"
    else:
        order_text = (
            f"{order_record['artist_message']}\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "✅ ЗАКАЗ ВЫПОЛНЕН\n\n"
            f"Художник: @id{artist_id} ({artist_name})\n\n"
            "Чтобы отправить результат заказчику, ответьте на это "
            "сообщение фотографией или изображением."
        )
        keyboard = EMPTY_KEYBOARD
        customer_message = (
            "✅ Твой заказ выполнен!\n\n"
            f"Художник: @id{artist_id} ({artist_name})."
        )
        snackbar = "Заказ отмечен выполненным!"

    await answer_callback(snackbar)

    try:
        await bot.api.messages.edit(
            peer_id=event_data.peer_id,
            cmid=event_data.conversation_message_id,
            message=order_text,
            keyboard=keyboard,
        )
    except Exception as error:
        print(f"[ERROR] Не удалось отредактировать заказ: {error}")

    try:
        await bot.api.messages.send(
            peer_id=order_record["customer_id"],
            random_id=get_random_id(),
            message=customer_message,
        )
    except Exception as error:
        print(
            f"[ERROR] Не удалось уведомить заказчика "
            f"{order_record['customer_id']}: {error}"
        )


async def forward_artist_result(message: Message):
    if message.peer_id != ARTIST_CHAT_ID:
        return

    # Извлекаем текст из ответа, пересланного сообщения или самого сообщения
    candidate_texts = []
    if message.reply_message and message.reply_message.text:
        candidate_texts.append(message.reply_message.text)
    if message.fwd_messages:
        for fwd in message.fwd_messages:
            if fwd.text:
                candidate_texts.append(fwd.text)
    if message.text:
        candidate_texts.append(message.text)

    if not candidate_texts:
        return

    combined_text = "\n".join(candidate_texts)

    # Ищем заказ по 8-значному hex-идентификатору
    order_id = None
    order = None

    for candidate_id, record in order_records.items():
        short_id = candidate_id[:8]
        if f"Номер заказа: {short_id}" in combined_text or f"заказа {short_id}" in combined_text or short_id in combined_text:
            order_id = candidate_id
            order = record
            break

    if order_id is None or order is None:
        return

    # Проверяем художника
    if order.get("artist_id") and order["artist_id"] != message.from_id:
        await message.answer(
            "Отправить результат может только художник, принявший заказ."
        )
        return

    if order.get("status") == "waiting":
        await message.answer(
            "Этот заказ ещё не принят в работу. Сначала нажмите кнопку «Принять заказ»."
        )
        return

    if order.get("result_sent"):
        await message.answer("Результат этого заказа уже отправлен заказчику.")
        return

    result_attachments = get_photo_attachments(message)
    result_text = (message.text or "").strip()
    if not result_attachments and not result_text:
        await message.answer(
            "В ответе не найдено фото, документа или текста с результатом."
        )
        return

    customer_message = (
        f"🎨 Художник прислал результат по заказу {order_id[:8]}."
    )
    if result_text:
        customer_message += f"\n\n{result_text}"

    try:
        await bot.api.messages.send(
            peer_id=order["customer_id"],
            random_id=get_random_id(),
            message=customer_message,
            attachment=",".join(result_attachments) or None,
        )
    except Exception as error:
        print(
            f"[ERROR] Не удалось отправить результат заказчику "
            f"{order['customer_id']}: {error}"
        )
        await message.answer(
            "Не удалось передать результат заказчику. Попробуйте ещё раз."
        )
        return

    order["status"] = "completed"
    order["result_sent"] = True
    save_order_records()
    await message.answer("Результат отправлен заказчику в личные сообщения.")

    # Обновляем карточку заказа в чате художников, убирая активную кнопку
    cmid = order.get("artist_message_cmid")
    if cmid:
        try:
            artist_name = order.get("artist_name") or "Художник"
            updated_text = (
                f"{order.get('artist_message', '')}\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "✅ ЗАКАЗ ВЫПОЛНЕН И ОТПРАВЛЕН\n\n"
                f"Художник: @id{message.from_id} ({artist_name})"
            )
            await bot.api.messages.edit(
                peer_id=ARTIST_CHAT_ID,
                cmid=cmid,
                message=updated_text,
                keyboard=EMPTY_KEYBOARD,
            )
        except Exception as err:
            print(f"[WARNING] Не удалось обновить кнопку заказа в чате художников: {err}")


# ============================================================
# ЗАПУСК
# ============================================================

LOCK_FILE = os.path.join(os.path.dirname(__file__), "bot.lock")
_lock_file_handle = None


def acquire_instance_lock() -> bool:
    """Гарантирует запуск только одного экземпляра бота во избежание дублирования сообщений."""
    global _lock_file_handle
    try:
        import msvcrt
        _lock_file_handle = open(LOCK_FILE, "w")
        msvcrt.locking(_lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        return True
    except (OSError, IOError):
        return False


if __name__ == "__main__":

    if not acquire_instance_lock():
        print(
            "[WARNING] Бот уже запущен в другом окне или процессе! "
            "Второй экземпляр остановлен во избежание дублирования сообщений."
        )
        sys.exit(0)

    print("🎨 Бот для заказов на арты запущен!")

    bot.on_startup.append(publish_artist_orders_button())
    bot.startup_tasks.append(initial_chat_setup())
    bot.startup_tasks.append(scheduled_reminders_worker())
    bot.run()
