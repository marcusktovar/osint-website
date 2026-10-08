# ATLAS / ARCHIVE — Retro World Dossier

An interactive, retro-inspired world map with 177 clickable country / territory shapes, a searchable country index, 20 edited country briefs (including Yemen), dated statistics and outgoing research citations. Runs on **GitHub Pages**, with no framework, database, API key or paid hosting.

## Quick start / preview

Your repo should contain `site/`, `scripts/`, `sources/`, `tests/`, and `.github/workflows/` at its **root**. Run this from the root folder:

```powershell
py -m http.server 8000 --directory site
```

Open http://localhost:8000 (or use `python` instead of `py`). Do not double-click `site/index.html`—`file://` may block `fetch()` of the bundled JSON. The site works entirely **offline from its bundled data** once served locally; no live API is needed for visitors.

## Replace the current GitHub Pages website

For your existing `marcusktovar/osint-website` GitHub repository:

1. **Back up the old site** in a ZIP or a branch if you might want it later.
2. Remove the old Yemen-only `site/` folder and upload the **new `site/` folder from this project**, preserving `site/index.html`, `site/app.js`, `site/style.css`, `site/data/countries.json`, and `site/data/map.json`.
3. Upload the new `scripts/`, `sources/`, and `tests/` folders to the repo root. Replace the old project README if desired.
4. **Remove the older workflows** such as `.github/workflows/deploy.yml` or `website.yml` so two jobs do not try to publish GitHub Pages. Keep **only** `.github/workflows/atlas.yml` from this project. If GitHub's web file-upload picker won't include hidden `.github` folders, choose **Add file → Create new file** and create the path `.github/workflows/atlas.yml`, then paste the YAML from this ZIP.
5. In **Settings → Pages**, keep **Source: GitHub Actions**.
6. In the **Actions** tab, select **ATLAS - Refresh and Deploy** and choose **Run workflow**. On success, your site stays at `https://marcusktovar.github.io/osint-website/`.

Note: GitHub web uploads generally accept dragged folders from File Explorer, not the standard file picker. Hidden folders may need to be created through GitHub's web editor.

### If you want to deploy the website immediately without data automation

You can keep your existing `deploy.yml` **temporarily** provided it already publishes the `./site` folder. Upload the new `site/` files first; the new interface will run from committed JSON. Later replace that old workflow with `atlas.yml` when you are ready for scheduled data refreshes. **Don't use both deployments at once.**

## How the information works

The country viewer is intentionally a **source-combining, provenance-aware static atlas**, not a live AI improviser:

- `site/data/map.json`: 177 generalized geographic shapes, derived from the Natural Earth public-domain 1:110m dataset. Tiny islands and some small sovereign countries are not represented at this resolution; the world map is a general reference, not an official borders map.
- `sources/base_countries.json`: offline country name, capital, languages, area, currency and region. These are an **undated historical CountryInfo reference**, **not** a recent verified census or real-time government source.
- `sources/research_notes.json`: edited, original-writing topic summaries for 20 selectable countries (including Yemen), with country-specific Wikipedia source links. The rest of the map remains clickable with geographical metadata and research links but does not invent bespoke history/culture paragraphs.
- `scripts/build.py`: requests **REST Countries** country metadata, **World Bank** latest *dated* population observations, and Wikipedia intro **availability checks** for edited countries. It merges them with the edited text and links. This is not automatic LLM paraphrasing: Wikipedia checks do not silently rewrite the narratives or political claims.
- `site/data/countries.json`: prebuilt initial profiles shipped with the website. Statistics missing from the initial offline reference are marked **Awaiting dated sync** rather than guessed.

Yemen's initial population is a **World Bank 2025 observation** preserved from the original starter project. The initial offline Factbook archive is included as a linked **historical** reference for Yemen. The CIA discontinued World Factbook publication in 2026. Government and active conflicts require independently reviewed, current information; this atlas does not automatically publish political officeholders or conflict lines.

## Refresh data manually

Python 3.10+; no third-party packages are needed for the build and website.

```bash
python scripts/build.py              # Pull APIs when available
python scripts/build.py --offline    # Rebuild from committed reference data only
python scripts/validate.py
python -m unittest discover -s tests -v
```

If remote APIs are all unavailable, the generator preserves the previous saved file rather than asserting a fresh sync. Individual services may temporarily block rate-limited calls. Scheduled GitHub Actions refreshes run every Monday; the workflow also allows manual runs. Workflow permissions must allow Actions to deploy to Pages; granting repository contents write lets scheduled refreshes be committed to GitHub.

### Editorial updates

To change written briefing text or add another extended country report:

1. Edit `sources/research_notes.json` for that ISO3 code (e.g. `YEM`, `USA`, `CHN`).
2. Populate `overview`, `history`, `geography`, `culture`, and optionally `caution`. Keep the writing neutral and support claims with trusted research.
3. Run `python scripts/build.py --offline`, then `python scripts/validate.py`.
4. Commit the new JSON alongside the source notes. The site will display the report for that country and add it to the featured index.

The left-side quick-access buttons are configured in `site/app.js` via `QUICK_CODES`. The map itself can select all 177 included Natural Earth entities. Disputed borders and administrations are particularly complex; use this layer only for generalized navigation.

## Source and licensing credits

- [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/) — world political boundaries, public domain.
- [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Copyrights) — background reference links; linked text is not reproduced in the initial narrative. Any future copying of Wikipedia extracts must respect CC BY-SA attribution and its terms.
- [CountryInfo](https://github.com/porimol/countryinfo) — offline country metadata snapshot, may be old.
- [REST Countries](https://restcountries.com/) — structured country names and country metadata, refreshed if accessible.
- [World Bank](https://data.worldbank.org/indicator/SP.POP.TOTL) — dated population indicator, checked by API if available.
- [CIA World Factbook historical archive (Yemen)](https://the-world-factbook.org/the-world-factbook/countries/yemen/) — archival source, **not** a live CIA feed.
- [UNESCO Yemen heritage](https://whc.unesco.org/en/statesparties/ye/) — additional linked historical / cultural reference.

UI code and original editorial writing: MIT license in `LICENSE`. The Natural Earth map data is public domain. Third-party source material follows its original terms.

## Interface controls

- **Left panel:** quick-access flags, search, region filter, and entire country index.
- **Map:** click or keyboard-focus a country; drag to pan; use mouse wheel or +/- to zoom; **RESET** shows full globe.
- **Right panel:** statistics, history, landscape, culture, and direct research links.
- Keyboard: **/** focuses search; **Esc** clears and leaves search. Country links use `#ISO3` URLs, allowing direct links such as `#YEM` or `#JPN`.

## Limitations

This intentionally uses 1:110m coarse map geometry. At this scale, not every microstate/island appears; some disputed boundaries are simplified. Offline reference metadata may be old until an online refresh succeeds. The curated text is not an automatically updated news feed. Population is only shown with an observation year. For publication requiring official political maps or current leadership, add human editorial review and more precise sources.
