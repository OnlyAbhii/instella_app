import requests

APK_URL = 'https://apkcombo.com/instagram/com.instagram.android/download/apk'
APK_NAME = 'instagram.apk'

def download_apk():
    response = requests.get(APK_URL)
    with open(APK_NAME, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded {APK_NAME}")

if __name__ == '__main__':
    download_apk()
