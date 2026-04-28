import os
import requests
import re

 
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
                
                 if os.path.exists(save_path):
                    print(f"[!] Skipped: '{asset_name}' already exists (No new update).")
                else:
                    download_file(download_url, save_path)

if __name__ == "__main__":
    main()
