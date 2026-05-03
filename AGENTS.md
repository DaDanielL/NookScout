# AGENTS.md

This repository is a reusable AI-agent-layer template for Codex. It contains workflow definitions and documentation only.

## Project Overview

The template helps Codex-driven projects move from idea to reviewed implementation through PRDs, GitHub issue-ready stories, context priming, implementation plans, validation, and review workflows.

Do not create a demo app, product scaffold, or framework-specific sample inside this repository.

## Tech Stack

No application runtime is required. The repository is Markdown workflow content.

| Area | Tooling |
|------|---------|
| Workflow docs | Markdown files in `.agents/skills/` |
| Issue tracking | GitHub Issues via `gh` |
| Pull requests | GitHub CLI via `gh pr create` and `gh pr view` |

## Commands

```bash
# List template files
rg --files

# Check workflow command coverage
rg -n "AGENTS.md|GitHub Issue|gh issue view|gh issue create|gh pr create|gh pr view|.agents/PRDs|.agents/stories|.agents/plans" .agents README.md AGENTS.md
```

## Architecture

```text
.
|-- AGENTS.md                 # Rules for this template repository
|-- README.md                 # Root overview
`-- .agents/
    |-- README.md             # AI-layer workflow guide
    |-- AGENTS-template.md    # Template for downstream project rules
    |-- PRDs/                 # Generated PRDs
    |-- stories/              # Generated story manifests
    |-- plans/                # Generated implementation plans
    |-- reports/              # Generated implementation reports
    |-- reviews/              # Generated review reports
    `-- skills/               # Workflow definitions
```

## Workflow Order

1. `rules-interactive` or `create-rules`
2. `prd-interactive` or `create-prd`
3. `create-stories`
4. `prime`
5. `plan`
6. `implement`
7. `validate`
8. `review` / `security-review`

## Editing Rules

- Use `AGENTS.md` as the project rules file.
- Store PRDs in `.agents/PRDs/`.
- Store story manifests in `.agents/stories/`.
- Store implementation plans in `.agents/plans/`.
- Keep workflows app-neutral unless a workflow explicitly discovers project-specific context.
- Use GitHub Issues instead of external issue trackers.
- Prefer `gh issue view`, `gh issue create`, `gh pr create`, and `gh pr view` where useful.
- Do not introduce framework-specific demo code.

## Key Files

| File | Purpose |
|------|---------|
| `.agents/README.md` | Explains the AI layer and every workflow |
| `.agents/AGENTS-template.md` | Base for generated downstream `AGENTS.md` files |
| `.agents/skills/rules-interactive.md` | Greenfield interview workflow for generating `AGENTS.md` |
| `.agents/skills/create-rules.md` | Existing-codebase workflow for generating `AGENTS.md` |
| `.agents/skills/create-stories.md` | PRD-to-GitHub-Issue story manifest workflow |
