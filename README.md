# Solar Eternal Archive

The public wiki for Solar Eternal, served at solareternal.lewisbrewer.com.

Articles live in Google Drive, one Google Doc per article, in the Wiki folder.
A GitHub Action pulls the folder, builds the static site and deploys it to GitHub Pages
on every push, by hand from the Actions tab, and every six hours.

## Layout

- `tools/fetch_docs.py` exports every Doc in the Wiki folder as HTML into `src/docs/`.
  Docs whose names start with `_` (such as "_old draft - Bounty") are skipped.
- `tools/build.py` turns `src/docs/` into the site in `out/`: articles, category pages,
  the A to Z index, the timeline, search and the home page. Lilac highlighting is stripped.
- `atlas/` is the 3D Atlas. `atlas/build_data.py` writes `atlas/atlas-data.json` from the
  194 systems traced off the 2235.12.10 reference map (`atlas/trace/systems_named.json`)
  and the ownership, worlds and events reconstructed from the Expanded Edition.
  Edit the tables in `build_data.py` to move a border or add an event.
- `static/` holds the site's CSS and scripts.

## One-time setup

1. In Google Cloud, create a project, enable the Google Drive API, and create a service
   account. Make a JSON key for it.
2. In Drive, share the Wiki folder with the service account's email address as Viewer.
3. In this repo, Settings → Secrets and variables → Actions:
   - secret `GOOGLE_SERVICE_ACCOUNT_JSON`: the whole JSON key
   - variable `WIKI_FOLDER_ID` (optional): defaults to the current Wiki folder
4. Settings → Pages → Source: GitHub Actions. Custom domain: `solareternal.lewisbrewer.com`.
5. At the DNS host for lewisbrewer.com, add a CNAME record `solareternal` → `lewisbrewer.github.io`.

## Local build

    pip install beautifulsoup4
    python atlas/build_data.py
    python tools/build.py
    cd out && python -m http.server

Open http://localhost:8000. The Atlas needs a web server; it will not run from a file:// path.
