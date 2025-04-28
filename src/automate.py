import os
import requests
from subprocess import run

# Constants
APK_URL = 'https://apkcombo.com/instagram/com.instagram.android/download/apk'
APK_NAME = 'instagram.apk'
DECOMPILE_DIR = 'myapp-src'
SIGNED_APK = 'instagram-signed.apk'

def download_apk():
    """Download the APK from APKCombo."""
    response = requests.get(APK_URL)
    with open(APK_NAME, 'wb') as f:
        f.write(response.content)

def decompile_apk():
    """Decompile the APK using apktool."""
    run(['apktool', 'd', APK_NAME, '-o', DECOMPILE_DIR])

def recompile_apk():
    """Recompile the APK using apktool."""
    run(['apktool', 'b', DECOMPILE_DIR, '-o', 'myapp-unsigned.apk'])

def sign_apk():
    """Sign the APK using apksigner."""
    run(['apksigner', 'sign', '--ks', 'my-release-key.jks', '--out', SIGNED_APK, 'myapp-unsigned.apk'])

def upload_to_github():
    """Upload the APK to GitHub Releases."""
    run(['gh', 'release', 'create', 'v1.0.1', SIGNED_APK, '--title', 'Instagram Mod v1.0.1'])

        )

if __name__ == '__main__':
    download_apk()
    decompile_apk()
    recompile_apk()
    sign_apk()
    upload_to_github()
    send_telegram_update()
