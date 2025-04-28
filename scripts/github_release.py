import subprocess

SIGNED_APK = 'instagram-signed.apk'
VERSION = 'v1.0.1'

def create_github_release():
    subprocess.run(['gh', 'release', 'create', VERSION, SIGNED_APK, '--title', 'Instagram Mod v1.0.1'])
    print(f"Release {VERSION} created on GitHub")

if __name__ == '__main__':
    create_github_release()
