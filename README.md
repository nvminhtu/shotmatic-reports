# ShotMatic Reports — tool

One ShotMatic screenshot → one dated, sourced report on **https://shotmatic.app/reports** + an X caption.

- Run it from Claude: `/shotmatic-report` (skill at `~/.claude/skills/shotmatic-report/`).
- Posts are written into the landing worktree `Master-List-Dashboard/shotmatic-reports-section`
  (`content/reports/<type>/<date>-<slug>.md`, pages in `pages/reports/`), images into
  `app-demo/shotmatic/reports/<type>/` (served by GitHub Pages). Override with `REPORTS_LANDING` / `REPORTS_APPDEMO`.
- SEO/ASO: `keywords/bank.csv` (shotmatic.app target keywords, built by `scripts/build_keyword_bank.py`), `scripts/seo_keywords.py suggest|taken`, rules in `scripts/seo_check.py`.
- `redirects/` is the old `nvminhtu.github.io/shotmatic-reports` site, now only redirects to shotmatic.app.
- Spec + plan (first version, MkDocs on GitHub Pages): `plans/`.

## By hand

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python scripts/new_post.py create --type keyword --slug my-slug --title "…" --keyword "…" --source "…" --image shot.png
    # fill every WRITE: line + x_caption in the new post
    .venv/bin/python scripts/check_post.py

Tests: `.venv/bin/pytest -q` (`scripts/types.json` is the test copy of the landing's `content/reports/types.json`).
