"""Download every Google Doc in the Wiki folder as HTML into src/docs/.

Runs in the GitHub Action. Needs:
  GOOGLE_SERVICE_ACCOUNT_JSON  the service account key (a repo secret)
  WIKI_FOLDER_ID               the Drive folder that holds one Doc per article
The folder must be shared with the service account's email address (Viewer is enough).
"""
import io, json, os, re, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

FOLDER = os.environ.get('WIKI_FOLDER_ID', '13Kx5mR6fTIbzby2twmcXfNQW9s9pKrSK')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'docs')


def slug(t):
    t = t.lower().replace("'", '').replace('’', '')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-') or 'untitled'


def main():
    raw = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '').strip()
    if not raw:
        sys.exit('GOOGLE_SERVICE_ACCOUNT_JSON is empty. Add the service account key as a repository secret '
                 '(Settings > Secrets and variables > Actions); see the README.')
    info = json.loads(raw)
    creds = service_account.Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/drive.readonly'])
    drive = build('drive', 'v3', credentials=creds, cache_discovery=False)
    q = "'%s' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false" % FOLDER
    files, token = [], None
    while True:
        r = drive.files().list(q=q, fields='nextPageToken, files(id, name, modifiedTime)', pageSize=200,
                               pageToken=token, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files += r.get('files', [])
        token = r.get('nextPageToken')
        if not token:
            break
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith('.html'):
            os.remove(os.path.join(OUT, f))
    kept = 0
    for f in sorted(files, key=lambda f: f['name']):
        if f['name'].startswith('_'):
            continue            # "_old draft - X" and other parked docs
        req = drive.files().export_media(fileId=f['id'], mimeType='text/html')
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        open(os.path.join(OUT, slug(f['name']) + '.html'), 'wb').write(buf.getvalue())
        kept += 1
        print('  %s' % f['name'])
    print('Fetched %d docs from the Wiki folder' % kept)
    if kept == 0:
        sys.exit('No docs found. Is the folder shared with %s?' % info.get('client_email'))


if __name__ == '__main__':
    main()
