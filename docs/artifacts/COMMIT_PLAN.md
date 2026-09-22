# Commit Plan

Git status: `minimal`

## Current Audit Findings

- Current branch: `main`.
- Latest commit: `c09a5c5` from 2026-05-26: `Phase E - multi-vault support`.
- Remote is configured.
- `.gitignore` exists and now includes recovery safety additions.
- Working tree contains generated recovery docs and operating files.

## Recommended Commit Groups

### 1. Curated Recovery Docs

Review and commit:

```bash
git add .gitignore PROJECT_RECOVERY.md PROJECT_STORY.md PROJECT_STORY_LLM_BRIEF.md COMMIT_PLAN.md DASHBOARD.md BUILD-PACKET.md BRAINSWEEP.md mkdocs.yml docs/
git commit -m "docs: add project recovery packet"
```

### 2. Raw Recovery Evidence

Do not commit by default. These files may contain private conversation content and noisy unrelated matches:

- `project-recovery-evidence.json`
- `project-recovery-transcripts.html`
- `MIGRATION_MANIFEST.json`
- `MIGRATION_MANIFEST.md`

Keep them local for audit, or explicitly review and redact before committing.

### 3. Application Baseline

No application source changes were made in this recovery pass. Do not create an app baseline commit unless you intentionally update project code or README content.

## Do Not Commit Without Explicit Review

- `config.toml`
- `data/`
- `notes/`
- `sources/`
- `todos/`
- `project-recovery-evidence.json`
- `project-recovery-transcripts.html`
- `MIGRATION_MANIFEST.json`
- `MIGRATION_MANIFEST.md`
- `site/`
- `.venv-mkdocs/`
- private keys, tokens, logs, and local backups

## Raw Git Status Command

Run:

```bash
git status --short
```
