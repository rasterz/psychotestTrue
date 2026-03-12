import os
import requests


BOT_TOKEN = "8511304607:AAF-xowv-aKbw9wQ-vK6_AP2x_nYjDiU2Mw"
CHAT_IDS = ["1311184426", "778609143"]


def send_pdf_to_telegram(pdf_path: str, caption: str = ""):
    url = f"https://api.telegram.org/bot8511304607:AAF-xowv-aKbw9wQ-vK6_AP2x_nYjDiU2Mw/sendDocument"

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Файл не найден: {pdf_path}")

    results = []

    for chat_id in CHAT_IDS:
        with open(pdf_path, "rb") as pdf_file:
            files = {
                "document": pdf_file
            }
            data = {
                "chat_id": chat_id,
                "caption": caption
            }

            response = requests.post(url, data=data, files=files, timeout=60)

        if response.status_code != 200:
            raise Exception(
                f"Ошибка Telegram API для chat_id {chat_id}: "
                f"{response.status_code} | {response.text}"
            )

        result = response.json()
        if not result.get("ok"):
            raise Exception(f"Telegram вернул ошибку для chat_id {chat_id}: {result}")

        results.append(result)

    return results

    if response.status_code != 200:
        raise Exception(f"Ошибка Telegram API: {response.status_code} | {response.text}")

    result = response.json()
    if not result.get("ok"):
        raise Exception(f"Telegram вернул ошибку: {result}")

    return result