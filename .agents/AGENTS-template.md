# AGENTS.md Template

A flexible template for project rules. Adapt sections based on the project type, stack, and maturity.

---

# AGENTS.md

This file gives Codex and other AI agents the operating context for this repository.

## Project Overview

{What this project is, who it serves, and what the MVP is trying to prove.}

## Product Context

- **Primary users**: {users}
- **Core problem**: {problem}
- **MVP outcome**: {outcome}
- **Source PRD**: `.agents/PRDs/{name}.prd.md` or N/A

## Tech Stack

| Technology | Purpose |
|------------|---------|
| {tech} | {why it is used} |

## Commands

Use exact commands. Mark unknown commands as TBD until the project is scaffolded.

```bash
# Install dependencies
{install-command}

# Start local development
{dev-command}

# Type check
{typecheck-command}

# Lint
{lint-command}

# Test
{test-command}

# Build
{build-command}
```

## Architecture

{Describe the architecture: modular monolith, vertical slices, layered app, packages, service boundaries, event-driven flow, etc.}

## Folder Structure

```text
{root}/
|-- {dir}/     # {description}
|-- {dir}/     # {description}
`-- {dir}/     # {description}
```

## Key Files

| File | Purpose |
|------|---------|
| `{path}` | {description} |

## Code Patterns

### Naming

- {convention}

### File Organization

- {pattern}

### Data and State

- {pattern}

### Error Handling

- {pattern}

### Configuration

- {environment variables, config files, secret handling}

## Testing

- **Unit tests**: {where and how}
- **Integration tests**: {where and how}
- **End-to-end or smoke tests**: {where and how}
- **Fixtures/test data**: {pattern}

## Validation

Run these before reporting work complete:

```bash
{validation-commands}
```

## GitHub Workflow

- **Issues**: Use GitHub Issues for trackable stories and bugs.
- **Issue creation**: Use `gh issue create` when turning story manifests into issues.
- **Issue inspection**: Use `gh issue view {number}` before planning linked work.
- **Branches**: `{branch-naming-pattern}`
- **Pull requests**: Use `gh pr create` for PRs and `gh pr view` to inspect PR context.
- **PR expectation**: include summary, validation run, screenshots or recordings when UI changes, and linked issue.

## AI Layer

Generated artifacts live under `.agents/`:

| Artifact | Path |
|----------|------|
| PRDs | `.agents/PRDs/` |
| Story manifests | `.agents/stories/` |
| Implementation plans | `.agents/plans/` |
| Implementation reports | `.agents/reports/` |
| Reviews | `.agents/reviews/` |

Recommended workflow:

1. `rules-interactive` or `create-rules`
2. `prd-interactive` or `create-prd`
3. `create-stories`
4. `prime`
5. `plan`
6. `implement`
7. `validate`
8. `review` / `security-review`

## Security Notes

- {auth/authorization expectations}
- {secret handling}
- {input validation}
- {dependency or supply-chain checks}

## On-Demand Context

| Topic | File |
|-------|------|
| {topic} | `{path}` |

## Agent Notes

- Preserve user changes; do not revert unrelated work.
- Prefer existing patterns over new abstractions.
- Keep generated plans and reports in `.agents/`.
- Document deviations from plans in implementation reports.
