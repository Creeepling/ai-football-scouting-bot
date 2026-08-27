import io
import json
import requests
from config import TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_ID


def build_menu_buttons(labels: list[str], ids: list[str]) -> list[list[dict]]:
    """Builds inline keyboard menu structure from lists of labels and callback ids."""
    menu = []
    for label, callback_id in zip(labels, ids):
        menu.append([{"text": label, "callback_data": callback_id}])
    return menu


def direct_message(chat_id: int, text: str | object) -> None:
    """Sends a text message to Telegram, splitting into chunks if exceeding limit."""
    if not TELEGRAM_BOT_TOKEN:
        print(f"Warning: TELEGRAM_BOT_TOKEN not set. Message to {chat_id}: {text}")
        return
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        text = str(text)
        if not text.strip():
            print(f"Empty text provided to direct_message for chat_id {chat_id}")
            return
        else:
            MAX_LENGTH = 4000
            while len(text) > 0:
                split_index = text.rfind('\n', 0, MAX_LENGTH)
                if split_index == -1 or len(text) <= MAX_LENGTH:
                    split_index = min(MAX_LENGTH, len(text))
                segment = text[:split_index].strip()
                if segment:
                    payload = {
                        "chat_id": chat_id,
                        "text": segment
                    }
                    try:
                        requests.post(url, json=payload, timeout=10)
                    except Exception as e:
                        print(f"Failed to send Telegram message to {chat_id}: {e}")
                else:
                    pass
                text = text[split_index:].strip()


def send_menu(chat_id: int, text: str, menu: list[list[dict]]) -> None:
    """Sends a message with an inline keyboard menu."""
    if not TELEGRAM_BOT_TOKEN:
        print(f"Warning: TELEGRAM_BOT_TOKEN not set for send_menu ({chat_id})")
        return
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        reply_markup = {"inline_keyboard": menu}
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": json.dumps(reply_markup)
        }
        try:
            requests.post(url, data=payload, timeout=10)
        except Exception as e:
            print(f"Failed to send Telegram menu to {chat_id}: {e}")


def send_photo(chat_id: int, image_buffer: io.BytesIO, filename: str = "plot.png") -> None:
    """Sends a photo buffer to a Telegram chat."""
    if not TELEGRAM_BOT_TOKEN:
        print(f"Warning: TELEGRAM_BOT_TOKEN not set for send_photo ({chat_id})")
        return
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        image_buffer.seek(0)
        files = {"photo": (filename, image_buffer, "image/png" if filename.endswith(".png") else "image/jpeg")}
        data = {"chat_id": chat_id}
        try:
            requests.post(url, data=data, files=files, timeout=20)
        except Exception as e:
            print(f"Failed to send Telegram photo to {chat_id}: {e}")


def delete_message(chat_id: int, message_id: int) -> None:
    """Deletes a message from a Telegram chat."""
    if not TELEGRAM_BOT_TOKEN:
        return
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
        params = {"chat_id": chat_id, "message_id": message_id}
        try:
            requests.get(url, params=params, timeout=5)
        except Exception as e:
            print(f"Failed to delete Telegram message {message_id} in {chat_id}: {e}")


def notify_admin_error(error_message: str | Exception) -> None:
    """Sends an error alert directly to the admin Telegram account."""
    direct_message(ADMIN_TELEGRAM_ID, f"⚠️ LLM Bot Error:\n{str(error_message)}")
