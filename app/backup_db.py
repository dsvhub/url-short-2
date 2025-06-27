import os
import requests
from github import Github

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPO')  # e.g. 'youruser/url-short-2'

def upload_db(asset_path, release_tag='db-backup'):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    # Create or get the release
    try:
        release = repo.get_release(release_tag)
    except:
        release = repo.create_git_release(release_tag, release_tag, 'DB Backup release')
    # Remove existing asset
    for asset in release.get_assets():
        if asset.name == os.path.basename(asset_path):
            asset.delete_asset()
    # Upload
    release.upload_asset(asset_path)
    print('Backup uploaded.')

if __name__ == '__main__':
    upload_db('site.db')
