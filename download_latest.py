import os
import requests
import re
import glob

CONFIG = {
    "android_arm64": True,
    "android_universal": False,
    "windows_amd64": True
}

DOWNLOAD_DIR = "downloads"
LINKS_FILE = "links.txt"

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def should_download(asset_name):
    name = asset_name.lower()
    
    if CONFIG["android_arm64"] and "arm64-v8a" in name and name.endswith(".apk"):
        return True
    if CONFIG["android_universal"] and "universal" in name and name.endswith(".apk"):
        return True
    if CONFIG["windows_amd64"] and "windows-amd64" in name and name.endswith(".zip"):
        return True
        
    return False

def get_latest_release(repo_url):
    match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        print(f"[-] Invalid URL: {repo_url}")
        return None
    
    owner, repo = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[-] Failed to fetch release for {repo}. Status: {response.status_code}")
        return None

def download_file(url, save_path):
    print(f"[*] Downloading {os.path.basename(save_path)}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("[+] Download complete.")
    else:
        print("[-] Download failed.")

def clean_previous_versions(asset_name, directory):
    file_ext = os.path.splitext(asset_name)[1]
    
    patterns = []
    
    if 'arm64' in asset_name:
        patterns.append('*arm64*' + file_ext)
    elif 'universal' in asset_name:
        patterns.append('*universal*' + file_ext)
    
    if 'windows' in asset_name or 'amd64' in asset_name:
        patterns.append('*windows*' + file_ext)
    
    for pattern in patterns:
        old_files = glob.glob(os.path.join(directory, pattern))
        for old_file in old_files:
            old_name = os.path.basename(old_file)
            if old_name != asset_name:
                try:
                    os.remove(old_file)
                    print(f"[✓] Removed previous: {old_name}")
                except Exception as e:
                    print(f"[!] Could not remove {old_name}: {e}")

def keep_only_latest_version(directory):
    apk_files = glob.glob(os.path.join(directory, "*.apk"))
    zip_files = glob.glob(os.path.join(directory, "*.zip"))
    
    for file_list in [apk_files, zip_files]:
        if len(file_list) > 1:
            file_list.sort(key=os.path.getmtime)
            for old_file in file_list[:-1]:
                os.remove(old_file)
                print(f"[✓] Removed old version: {os.path.basename(old_file)}")

def main():
    if not os.path.exists(LINKS_FILE):
        print(f"[-] File '{LINKS_FILE}' not found!")
        return

    ensure_dir(DOWNLOAD_DIR)

    with open(LINKS_FILE, "r") as file:
        links = [line.strip() for line in file.readlines() if line.strip()]

    for link in links:
        print(f"\n>>> Checking repository: {link}")
        release_data = get_latest_release(link)
        
        if not release_data:
            continue
            
        tag_name = release_data.get("tag_name", "Unknown")
        print(f"[*] Latest version found: {tag_name}")
        
        assets = release_data.get("assets", [])
        
        for asset in assets:
            asset_name = asset["name"]
            download_url = asset["browser_download_url"]
            
            if should_download(asset_name):
                save_path = os.path.join(DOWNLOAD_DIR, asset_name)
                
                clean_previous_versions(asset_name, DOWNLOAD_DIR)
                
                if os.path.exists(save_path):
                    print(f"[!] Skipped: '{asset_name}' already exists.")
                else:
                    download_file(download_url, save_path)
    
    keep_only_latest_version(DOWNLOAD_DIR)

if __name__ == "__main__":
    main()
