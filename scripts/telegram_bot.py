import requests

TELEGRAM_TOKEN = 'your-telegram-bot-token'
CHAT_ID = 'your-chat-id'
SIGNED_APK = 'instagram-signed.apk'

def send_telegram_update():
    with open(SIGNED_APK, 'rb') as file:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument',
            data={'chat_id': CHAT_ID},
            files={'document': file}
        )
    print("Sent update to Telegram")

if __name__ == '__main__':
    send_telegram_update()
