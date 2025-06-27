import os
import requests
from github import Github

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPO')
RELEASE_TAG = 'db-backup'

def download_db(dest='site.db'):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    release = repo.get_release(RELEASE_TAG)
    for asset in release.get_assets():
        if asset.name == 'site.db':
            url = asset.browser_download_url
            r = requests.get(url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
            open(dest, 'wb').write(r.content)
            print('Database restored.')
            return
    print('No backup found.')

if __name__ == '__main__':
    download_db()
