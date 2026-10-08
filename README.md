# Yemen / Field Notes

An accessible, responsive educational website about Yemen with six sections, source citations, and a scheduled data-refresh pipeline. **Works without an AI service, API key, database, or paid web host.**

![Yemen flag palette](https://img.shields.io/badge/Yemen-Field%20Notes-b64b38?style=flat-square)

## What is included

- `site/index.html` — semantic page structure and the decorative Yemen-inspired landscape illustration.
- `site/style.css` — mobile-friendly site styling.
- `site/app.js` — loads `site/data/sections.json`, creates sections, links supporting references. Uses `textContent` rather than executing source HTML.
- `site/data/sections.json` — **already-built initial website content**, so the site works immediately.
- `sources/editorial.json` — concise, edited contextual prose, section outlines, and attributed source links.
- `sources/factbook_archive.json` — historical CIA World Factbook snapshot, edition dated **Jan 5, 2026**. Not a maintained API.
- `scripts/build.py` — combines text and source data, checks Wikipedia context, reads Wikidata and World Bank data, and rewrites the website's JSON.
- `scripts/validate.py` — catches missing sections, broken reference IDs and unexpected content shapes.
- `.github/workflows/website.yml` — tests, updates, and deploys the website, including scheduled Monday runs.
- `tests/test_build.py` — Python unit tests for API parsing, merging and outage behavior.

## See the website on your computer

You need **Python 3.10+**. From a terminal opened in the `yemen-website` folder, run:

```bash
python -m http.server 8000 --directory site
```

Now open <http://localhost:8000> in a browser. Use `Ctrl+C` to stop the server. If `python` is not recognized on Windows, try `py` instead.

**Don't double-click `index.html`.** Browsers often block `fetch()` of JSON files when loaded using `file://`. Use the local server above.

## Refresh source data locally

```bash
python scripts/build.py
python scripts/validate.py
python -m unittest discover -s tests -v
```

No third-party Python packages are required. The command needs internet access to Wikipedia, Wikidata and World Bank public endpoints. If none of them respond, it fails **without overwriting** the existing saved site data. If some sources fail, it keeps previously dated values and labels the edition `partial`. The `--offline` option regenerates with saved facts only; it does **not** check current sources.

The startup snapshot was assembled from research references on October 7, 2026. Its population value is the World Bank's **2025** estimate (41,773,878), not a 2026 count. A checked-in copy is provided so visitors see a complete page even before the first automated refresh. The snapshot isn't being represented as a successful API fetch from the packaging environment.

## Publish to GitHub Pages

1. Sign into <https://github.com> and create a **public** repository called `yemen-website` (on GitHub Free, public repos work with Pages).
2. **Extract** the starter ZIP. Upload its contents to the **repository root**—`.github/workflows/website.yml`, `site/`, `scripts/`, and `sources/` must be in the repository, not inside an extra wrapper directory.
3. Confirm your default branch is `main`.
4. Open **Settings → Pages → Build and deployment → Source**, and select **GitHub Actions** (not “Deploy from a branch”).
5. Open the **Actions** tab. The workflow `Build and publish Yemen Field Notes` should run on the first push. If Pages was configured after the first push, run the workflow using **Run workflow**.
6. The website address will look like `https://YOUR-USERNAME.github.io/yemen-website/` once the deployment succeeds.

In repositories where Actions are restricted, enable workflows. If automated committing of refreshed JSON is blocked, verify repository **Actions → General → Workflow permissions** and organization policies. The workflow can still be adjusted to deploy the refreshed artifact without committing it.

### Automatic updating

Every Monday, the workflow (a) unit-tests the data pipeline, (b) requests the latest available Wikipedia contextual extracts, Wikidata properties, and World Bank population series, (c) validates the output, (d) saves the updated JSON back to the repo, and (e) publishes the site. You can also manually trigger updates from **Actions → Run workflow**.

GitHub may delay scheduled runs. If the sources are unavailable, the script preserves the previously published data rather than inventing new statistics. Note that a commit generated with `GITHUB_TOKEN` does not itself re-trigger a Pages branch build; this project **deploys within the same workflow run**, so it does not depend on such a trigger.

## How sources are *combined*, not copied

This starter uses a **transparent, deterministic source combiner** rather than an AI rewriting service:

1. An editor supplies brief neutral narrative in `sources/editorial.json`, with source IDs for each paragraph.
2. The generator appends explanatory sentences that interpolate **verified, dated source facts** (archived Factbook measurements; Wikidata's state-formation date; World Bank population observation).
3. It fetches Wikipedia introductions as an additional **corroboration** input, records conservative topic checks, and links the source. Wikipedia paragraphs are not automatically copied onto the site.
4. The website shows references beside each paragraph and a source library with complete outgoing links.

This keeps output legible, attribution visible and unsupported machine-generated claims out of the public site. **This is not an AI paraphraser and does not automatically rewrite every new Wikipedia edit into the summary.** If you want AI-based narrative synthesis later, add a reviewed draft/approval step before publishing; never auto-publish generated government claims.

## Updating what the website says

- Edit a section in `sources/editorial.json`; add only claims supported by its `sources` identifiers.
- Update the archived Factbook fields only if you have a different archive edition; change the edition date and URL as well.
- Update `sources/editorial.json` to add or revise references.
- Run `python scripts/build.py`, then `python scripts/validate.py`.
- Commit and push; GitHub Pages will redeploy.

### Accuracy and licenses

- The CIA Factbook copy is dated **2026-01-05** and is a historical snapshot, **not live CIA data**.
- Wikipedia and UNESCO background texts have their own attribution and licensing requirements. Our original prose is not copied verbatim, but source links are maintained so readers can inspect evidence and conditions of reuse.
- World Bank population data carries its original observation year and attribution; see the World Bank data portal for usage terms.
- **Government** is not automatically updated with officeholders. Conflict and control may change and the section requires editorial review of authoritative, dated coverage.
- No images were scraped or embedded: the hero is made from CSS geometry to avoid licensing and reliability issues.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| Site says data unavailable | Start the site with `python -m http.server 8000 --directory site` from the repository root. |
| Pages reports no deployment | Ensure **Settings → Pages → Source** is **GitHub Actions** and manually run the workflow. |
| `build.py` can't fetch APIs | Verify internet, DNS and network policy. Saved data remains in `site/data/sections.json`. |
| Scheduled workflow fails | See the Actions logs. Wikipedia/Wikidata/World Bank may temporarily block requests; retry manually later. |
| Hosted site path is wrong | Keep `site/app.js` and `site/data/sections.json` together; all asset paths are relative. |

## Reference links

- [Wikipedia / Yemen](https://en.wikipedia.org/wiki/Yemen)
- [Wikidata / Yemen (Q805)](https://www.wikidata.org/wiki/Q805)
- [CIA World Factbook archived Yemen entry](https://the-world-factbook.org/the-world-factbook/countries/yemen/)
- [World Bank / population, Yemen](https://data.worldbank.org/indicator/SP.POP.TOTL?locations=YE)
- [UNESCO World Heritage / Yemen](https://whc.unesco.org/en/statesparties/ye/)
- [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

## Project license

The original site code, art, and original editorial narrative in this starter are released under the MIT License (see `LICENSE`). Source facts and third-party texts remain subject to their own applicable terms; a project's MIT license cannot relicense them.
