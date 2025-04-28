import subprocess

APK_NAME = 'instagram.apk'
DECOMPILE_DIR = 'instagram_src'
RECOMPILE_DIR = 'instagram-recompiled.apk'

def decompile_apk():
    subprocess.run(['apktool', 'd', APK_NAME, '-o', DECOMPILE_DIR])
    print(f"Decompiled {APK_NAME}")

def recompile_apk():
    subprocess.run(['apktool', 'b', DECOMPILE_DIR, '-o', RECOMPILE_DIR])
    print(f"Recompiled {RECOMPILE_DIR}")

if __name__ == '__main__':
    decompile_apk()
    recompile_apk()
