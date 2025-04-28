#!/usr/bin/env python3
import os
import re
import sys
import json
import shutil
import logging
import requests
import subprocess
import configparser
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from github import Github
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("apk_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    config = configparser.ConfigParser()
    config_path = Path('config.ini')
    
    if not config_path.exists():
        logger.error("Config file not found. Please create config.ini")
        sys.exit(1)
        
    config.read(config_path)
    return config

config = load_config()

# Constants from config
APK_NAME = config['APK']['name']
APK_PACKAGE = config['APK']['package']
APK_SOURCE_URL = config['APK']['source_url']
GITHUB_TOKEN = config['GitHub']['token']
GITHUB_REPO = config['GitHub']['repo']
TELEGRAM_BOT_TOKEN = config['Telegram']['bot_token']
TELEGRAM_CHAT_ID = config['Telegram']['chat_id']
KEYSTORE_PATH = config['Signing']['keystore_path']
KEYSTORE_PASSWORD = config['Signing']['keystore_password']
KEY_ALIAS = config['Signing']['key_alias']
KEY_PASSWORD = config['Signing']['key_password']
WEBSITE_PATH = config['Website']['path']
WEBSITE_TEMPLATE = config['Website']['template_path']

# Create working directories
BASE_DIR = Path('apk_workspace')
DOWNLOAD_DIR = BASE_DIR / 'downloads'
DECOMPILED_DIR = BASE_DIR / 'decompiled'
RECOMPILED_DIR = BASE_DIR / 'recompiled'
SIGNED_DIR = BASE_DIR / 'signed'

for directory in [BASE_DIR, DOWNLOAD_DIR, DECOMPILED_DIR, RECOMPILED_DIR, SIGNED_DIR]:
    directory.mkdir(exist_ok=True)

def download_latest_apk():
    """Download the latest APK from the source website"""
    logger.info(f"Downloading latest {APK_NAME} APK from {APK_SOURCE_URL}")
    
    try:
        # Fetch the APK source page
        response = requests.get(APK_SOURCE_URL)
        response.raise_for_status()
        
        # Parse the page to find the download link
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This is a simplified example - you'll need to adjust the selector based on the actual website
        download_link = soup.select_one('a.download-button')['href']
        
        if not download_link:
            logger.error("Could not find download link")
            return None
            
        # Extract version from the page or link
        version_element = soup.select_one('span.version-number')
        version = version_element.text.strip() if version_element else "unknown"
        
        # Download the APK
        apk_filename = f"{APK_NAME.lower().replace(' ', '_')}_{version}.apk"
        apk_path = DOWNLOAD_DIR / apk_filename
        
        logger.info(f"Downloading APK version {version} to {apk_path}")
        
        # Stream download to file
        with requests.get(download_link, stream=True) as r:
            r.raise_for_status()
            with open(apk_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded APK to {apk_path}")
        return {"path": apk_path, "version": version}
    
    except Exception as e:
        logger.error(f"Error downloading APK: {e}")
        return None

def decompile_apk(apk_info):
    """Decompile the APK using apktool"""
    if not apk_info:
        return None
        
    apk_path = apk_info["path"]
    version = apk_info["version"]
    
    # Create a version-specific decompile directory
    decompile_dir = DECOMPILED_DIR / f"{APK_NAME.lower().replace(' ', '_')}_{version}"
    
    try:
        logger.info(f"Decompiling APK to {decompile_dir}")
        
        # Run apktool to decompile
        result = subprocess.run(
            ["apktool", "d", str(apk_path), "-o", str(decompile_dir), "-f"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Successfully decompiled APK: {result.stdout}")
        
        return {"decompile_dir": decompile_dir, "version": version}
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error decompiling APK: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during decompilation: {e}")
        return None

def modify_apk(decompile_info):
    """Modify the decompiled APK files"""
    if not decompile_info:
        return None
        
    decompile_dir = decompile_info["decompile_dir"]
    version = decompile_info["version"]
    
    try:
        logger.info(f"Modifying APK in {decompile_dir}")
        
        # Example 1: Enable developer options by modifying AndroidManifest.xml
        manifest_path = decompile_dir / "AndroidManifest.xml"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest_content = f.read()
                
            # Add debuggable flag if not present
            if 'android:debuggable="true"' not in manifest_content:
                modified_manifest = manifest_content.replace(
                    '<application ', 
                    '<application android:debuggable="true" '
                )
                
                with open(manifest_path, 'w') as f:
                    f.write(modified_manifest)
                    
                logger.info("Added debuggable flag to AndroidManifest.xml")
        
        # Example 2: Modify a string resource
        strings_path = decompile_dir / "res" / "values" / "strings.xml"
        if strings_path.exists():
            with open(strings_path, 'r') as f:
                strings_content = f.read()
                
            # Add a modified string or change an existing one
            if '<string name="app_name">' in strings_content:
                modified_strings = strings_content.replace(
                    f'<string name="app_name">{APK_NAME}</string>',
                    f'<string name="app_name">{APK_NAME} Mod</string>'
                )
                
                with open(strings_path, 'w') as f:
                    f.write(modified_strings)
                    
                logger.info("Modified app name in strings.xml")
        
        # Example 3: Modify Smali code to bypass a check
        # This is a simplified example - you'll need to adjust based on the actual code
        smali_files = list(decompile_dir.glob("smali*/**/*.smali"))
        
        # Look for a specific class that might contain a check
        target_files = [f for f in smali_files if "LoginActivity" in str(f)]
        
        for smali_file in target_files:
            with open(smali_file, 'r') as f:
                smali_content = f.read()
                
            # Look for a specific check pattern and modify it
            # This is a very simplified example - real Smali modifications require careful analysis
            if "invoke-virtual {p0}, Lcom/example/app/CheckPremium;->isPremium()Z" in smali_content:
                modified_smali = smali_content.replace(
                    "invoke-virtual {p0}, Lcom/example/app/CheckPremium;->isPremium()Z",
                    "const/4 v0, 0x1\nreturn v0"  # Always return true
                )
                
                with open(smali_file, 'w') as f:
                    f.write(modified_smali)
                    
                logger.info(f"Modified premium check in {smali_file}")
        
        # Create a changelog file to track modifications
        changelog = [
            f"# {APK_NAME} Mod v{version}",
            f"Modified on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Modifications:",
            "- Enabled developer options",
            "- Changed app name to include 'Mod'",
            "- Bypassed premium checks (if found)"
        ]
        
        changelog_path = decompile_dir / "CHANGELOG.md"
        with open(changelog_path, 'w') as f:
            f.write("\n".join(changelog))
            
        logger.info(f"Created changelog at {changelog_path}")
        
        return {"decompile_dir": decompile_dir, "version": version, "changelog": changelog}
    
    except Exception as e:
        logger.error(f"Error modifying APK: {e}")
        return None

def recompile_apk(modify_info):
    """Recompile the modified APK using apktool"""
    if not modify_info:
        return None
        
    decompile_dir = modify_info["decompile_dir"]
    version = modify_info["version"]
    
    # Define output APK path
    output_apk = RECOMPILED_DIR / f"{APK_NAME.lower().replace(' ', '_')}_mod_{version}.apk"
    
    try:
        logger.info(f"Recompiling APK from {decompile_dir} to {output_apk}")
        
        # Run apktool to recompile
        result = subprocess.run(
            ["apktool", "b", str(decompile_dir), "-o", str(output_apk), "--use-aapt2"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Successfully recompiled APK: {result.stdout}")
        
        return {
            "apk_path": output_apk, 
            "version": version, 
            "changelog": modify_info.get("changelog", [])
        }
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error recompiling APK: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during recompilation: {e}")
        return None

def sign_apk(recompile_info):
    """Sign the recompiled APK"""
    if not recompile_info:
        return None
        
    apk_path = recompile_info["apk_path"]
    version = recompile_info["version"]
    
    # Define signed APK path
    signed_apk = SIGNED_DIR / f"{APK_NAME.lower().replace(' ', '_')}_mod_{version}_signed.apk"
    
    try:
        logger.info(f"Signing APK {apk_path} to {signed_apk}")
        
        # Run apksigner to sign the APK
        result = subprocess.run([
            "apksigner", "sign",
            "--ks", KEYSTORE_PATH,
            "--ks-pass", f"pass:{KEYSTORE_PASSWORD}",
            "--ks-key-alias", KEY_ALIAS,
            "--key-pass", f"pass:{KEY_PASSWORD}",
            "--out", str(signed_apk),
            str(apk_path)
        ], capture_output=True, text=True, check=True)
        
        logger.info(f"Successfully signed APK: {result.stdout}")
        
        # Verify the signature
        verify_result = subprocess.run([
            "apksigner", "verify", "--verbose", str(signed_apk)
        ], capture_output=True, text=True, check=True)
        
        logger.info(f"Signature verification: {verify_result.stdout}")
        
        return {
            "signed_apk": signed_apk, 
            "version": version, 
            "changelog": recompile_info.get("changelog", [])
        }
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error signing APK: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during signing: {e}")
        return None

def create_github_release(sign_info):
    """Create a GitHub release with the signed APK"""
    if not sign_info:
        return None
        
    signed_apk = sign_info["signed_apk"]
    version = sign_info["version"]
    changelog = sign_info.get("changelog", [])
    
    try:
        logger.info(f"Creating GitHub release for version {version}")
        
        # Initialize GitHub client
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        # Create release tag
        tag_name = f"v{version}"
        release_name = f"{APK_NAME} Mod {version}"
        
        # Create release description from changelog
        release_description = "\n".join(changelog) if changelog else f"Release of {APK_NAME} Mod version {version}"
        
        # Create the release
        release = repo.create_git_release(
            tag=tag_name,
            name=release_name,
            message=release_description,
            draft=False,
            prerelease=False
        )
        
        # Upload the APK file
        with open(signed_apk, 'rb') as apk_file:
            release.upload_asset(
                path=str(signed_apk),
                label=f"{APK_NAME} Mod {version}",
                content_type="application/vnd.android.package-archive"
            )
        
        logger.info(f"Successfully created GitHub release: {release.html_url}")
        
        return {
            "release_url": release.html_url,
            "download_url": f"https://github.com/{GITHUB_REPO}/releases/download/{tag_name}/{signed_apk.name}",
            "version": version,
            "changelog": changelog
        }
    
    except Exception as e:
        logger.error(f"Error creating GitHub release: {e}")
        return None

def update_website(release_info):
    """Update the website with the new APK information"""
    if not release_info:
        return None
        
    version = release_info["version"]
    download_url = release_info["download_url"]
    release_url = release_info["release_url"]
    
    try:
        logger.info(f"Updating website with version {version}")
        
        # Load the website template
        with open(WEBSITE_TEMPLATE, 'r') as f:
            template = f.read()
        
        # Replace placeholders with actual values
        current_date = datetime.now().strftime("%Y-%m-%d")
        updated_html = template.replace("{{VERSION}}", version)
        updated_html = updated_html.replace("{{RELEASE_DATE}}", current_date)
        updated_html = updated_html.replace("{{DOWNLOAD_URL}}", download_url)
        updated_html = updated_html.replace("{{RELEASE_URL}}", release_url)
        
        # Update the changelog section if available
        changelog_html = ""
        if release_info.get("changelog"):
            changelog_html = "<ul>"
            for line in release_info["changelog"]:
                if line.startswith("- "):
                    changelog_html += f"<li>{line[2:]}</li>"
            changelog_html += "</ul>"
        
        updated_html = updated_html.replace("{{CHANGELOG}}", changelog_html)
        
        # Write the updated HTML to the website file
        with open(WEBSITE_PATH, 'w') as f:
            f.write(updated_html)
            
        logger.info(f"Successfully updated website at {WEBSITE_PATH}")
        
        return {
            "website_path": WEBSITE_PATH,
            "version": version,
            "download_url": download_url
        }
    
    except Exception as e:
        logger.error(f"Error updating website: {e}")
        return None

def send_telegram_notification(website_info):
    """Send a notification to Telegram about the new APK"""
    if not website_info:
        return None
        
    version = website_info["version"]
    download_url = website_info["download_url"]
    
    try:
        logger.info(f"Sending Telegram notification for version {version}")
        
        # Initialize Telegram bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Create inline keyboard with download button
        keyboard = [
            [InlineKeyboardButton("🔽 Download Now", url=download_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create message text
        message = (
            f"🚀 New {APK_NAME} Mod v{version} is out!\n\n"
            f"📱 Get the latest features and improvements.\n\n"
            f"📥 Download: {download_url}"
        )
        
        # Send the message
        sent_message = bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
        
        logger.info(f"Successfully sent Telegram notification: {sent_message.message_id}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")
        return None

def run_pipeline():
    """Run the complete APK modification pipeline"""
    logger.info("Starting APK modification pipeline")
    
    # Step 1: Download the latest APK
    apk_info = download_latest_apk()
    if not apk_info:
        logger.error("Pipeline failed at download step")
        return False
    
    # Step 2: Decompile the APK
    decompile_info = decompile_apk(apk_info)
    if not decompile_info:
        logger.error("Pipeline failed at decompile step")
        return False
    
    # Step 3: Modify the APK
    modify_info = modify_apk(decompile_info)
    if not modify_info:
        logger.error("Pipeline failed at modify step")
        return False
    
    # Step 4: Recompile the APK
    recompile_info = recompile_apk(modify_info)
    if not recompile_info:
        logger.error("Pipeline failed at recompile step")
        return False
    
    # Step 5: Sign the APK
    sign_info = sign_apk(recompile_info)
    if not sign_info:
        logger.error("Pipeline failed at sign step")
        return False
    
    # Step 6: Create GitHub release
    release_info = create_github_release(sign_info)
    if not release_info:
        logger.error("Pipeline failed at GitHub release step")
        return False
    
    # Step 7: Update website
    website_info = update_website(release_info)
    if not website_info:
        logger.error("Pipeline failed at website update step")
        return False
    
    # Step 8: Send Telegram notification
    notification_sent = send_telegram_notification(website_info)
    if not notification_sent:
        logger.error("Pipeline failed at Telegram notification step")
        return False
    
    logger.info("APK modification pipeline completed successfully!")
    return True

if __name__ == "__main__":
    run_pipeline()
