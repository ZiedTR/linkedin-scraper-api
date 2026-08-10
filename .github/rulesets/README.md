# Branch protection ruleset

`protect-main.json` is an importable GitHub ruleset that protects `main`:

- **Require a pull request before merging** (no direct pushes to `main`)
- **Block force pushes** (`non_fast_forward`)
- **Block branch deletion** (`deletion`)
- `required_approving_review_count: 0` — so a solo maintainer isn't blocked
- **Admins bypass** (`RepositoryRole` 5, `always`) — you can still merge/push directly

## How to import

GitHub does **not** auto-apply this file. Import it via the UI:

1. Repo → **Settings** → **Rules** → **Rulesets** → **New ruleset** → **Import a ruleset**.
2. Select `.github/rulesets/protect-main.json`.
3. Review and **Create**.

To tighten later (recommended once you have CI or a teammate):
- Set `required_approving_review_count` to `1`.
- Add a `required_status_checks` rule listing your CI checks.
- Remove the admin bypass to enforce PRs for everyone.
