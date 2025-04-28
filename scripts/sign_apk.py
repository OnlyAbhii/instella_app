import subprocess

SIGNED_APK = 'instagram-signed.apk'
KEYSTORE = 'assets/my-release-key.jks'
KEY_ALIAS = 'key_alias'

def sign_apk():
    subprocess.run(['apksigner', 'sign', '--ks', KEYSTORE, '--ks-key-alias', KEY_ALIAS, '--out', SIGNED_APK, 'instagram-recompiled.apk'])
    print(f"Signed APK saved as {SIGNED_APK}")

if __name__ == '__main__':
    sign_apk()
