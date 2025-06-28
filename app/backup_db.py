import os
from github import Github

# Load environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPO', 'dsvhub/url-short-2')  # fallback if not set

# Validation
if not GITHUB_TOKEN:
    print("❌ GITHUB_TOKEN not set. Please set it in your environment.")
    exit(1)

if not REPO_NAME:
    print("❌ GITHUB_REPO not set. Please set it in your environment.")
    exit(1)

def upload_db(asset_path, release_tag='db-backup'):
    if not os.path.exists(asset_path):
        print(f"❌ File '{asset_path}' not found. Make sure the DB file exists.")
        return False

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    try:
        release = repo.get_release(release_tag)
    except:
        print("ℹ️ Release not found. Creating new release...")
        release = repo.create_git_release(release_tag, release_tag, 'DB Backup release')

    # Remove existing asset with same name
    for asset in release.get_assets():
        if asset.name == os.path.basename(asset_path):
            print(f"🗑️ Deleting existing asset: {asset.name}")
            asset.delete_asset()

    print(f"⬆️ Uploading backup: {asset_path}")
    release.upload_asset(asset_path)
    print('✅ Backup uploaded successfully.')
    return True

if __name__ == '__main__':
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'site.db'))
    upload_db(db_path)
