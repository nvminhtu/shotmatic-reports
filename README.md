# ShotMatic Reports

One ShotMatic screenshot → one dated, sourced report page + an X caption.

- Site: MkDocs Material, deployed to GitHub Pages by `.github/workflows/pages.yml`.
- Run it from Claude: `/shotmatic-report` (skill at `~/.claude/skills/shotmatic-report/`).
- Spec: `plans/2026-11-23-shotmatic-reports-design.md` · Plan: `plans/2026-11-23-shotmatic-reports-plan.md`.

## By hand

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python scripts/new_post.py create --type keyword --slug my-slug --title "…" --keyword "…" --source "…" --image shot.png
    # fill every WRITE: line + x_caption in the new post
    .venv/bin/python scripts/check_post.py
    .venv/bin/mkdocs serve

Tests: `.venv/bin/pytest -q`.
