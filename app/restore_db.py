import os
import requests
from github import Github

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPO', 'dsvhub/url-short-2')
RELEASE_TAG = 'db-backup'
TARGET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'site.db'))


if not GITHUB_TOKEN:
    print("❌ GITHUB_TOKEN not set.")
    exit(2)

try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    release = repo.get_release(RELEASE_TAG)

    found = False
    for asset in release.get_assets():
        print(f"🧐 Checking asset: {asset.name}")
        if asset.name == 'site.db':
            print(f"⬇️ Downloading asset: {asset.browser_download_url}")
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            r = requests.get(asset.browser_download_url, headers=headers)
            r.raise_for_status()

            os.makedirs(os.path.dirname(TARGET_PATH), exist_ok=True)
            with open(TARGET_PATH, 'wb') as f:
                f.write(r.content)
            print("✅ Database restored successfully.")
            found = True
            break

    if not found:
        print("❌ site.db not found in GitHub release.")
        exit(2)

except Exception as e:
    print(f"❌ Exception occurred: {e}")
    exit(2)


