---
name: create-stories
description: Use when a PRD should be broken into small GitHub issue-ready stories and saved as a story manifest.
---

# Create GitHub Stories from PRD

Generate a structured story manifest from a Product Requirements Document. Optionally create the stories as GitHub Issues with `gh issue create`.

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

---

## Phase 1: Load

Read the PRD file provided as input. If no path is given, look for:

1. `.agents/PRDs/*.prd.md`
2. `PRD.md` at the project root
3. Ask the user which PRD to use

Extract:

- User stories already defined in the PRD
- Acceptance criteria from success criteria and requirements
- Implementation phases and deliverables
- Technical constraints and dependencies
- Open questions that may need spike stories

Parse optional flags:

- `--repo` or `-r`: GitHub repository in `OWNER/REPO` format
- `--milestone` or `-m`: GitHub milestone name
- `--label` or `-l`: Extra label to apply; may be repeated
- `--create-issues`: Offer to create GitHub Issues after writing the manifest

---

## Phase 2: Analyze

### Break Down into Stories

For each feature or requirement in the PRD:

1. **Create a user story** in this format:
   ```markdown
   As a [user type], I want to [action], so that [benefit].
   ```
2. **Define acceptance criteria** with 3-5 testable checks.
3. **Estimate complexity**: Small / Medium / Large.
   - Small: focused change, clear implementation
   - Medium: multiple files or moderate design decisions
   - Large: cross-cutting architecture, significant unknowns, or multi-day work
4. **Identify dependencies** between stories.
5. **Split large stories** until each can be implemented and reviewed independently.

### Story Categories

Group stories by type:

- **Feature**: New user-facing or operator-facing capability
- **Enhancement**: Improvement to existing behavior
- **Bug**: Fix for known incorrect behavior
- **Technical**: Infrastructure, refactoring, tooling, observability
- **Spike**: Research or validation needed before implementation

Map categories to GitHub labels:

| Story Type | Suggested Labels |
|------------|------------------|
| Feature | `type:feature` |
| Enhancement | `type:enhancement` |
| Bug | `type:bug` |
| Technical | `type:technical` |
| Spike | `type:spike` |

Add domain labels where useful, such as `frontend`, `backend`, `api`, `database`, `docs`, `testing`, or `security`.

---

## Phase 3: Structure

### Manifest Format

Save stories in this format:

```markdown
# Stories: {PRD Name}

**Source PRD**: `.agents/PRDs/{name}.prd.md`
**Generated**: {timestamp}
**Status**: draft

## Summary

| ID | Title | Type | Priority | Complexity | Phase | GitHub Issue |
|----|-------|------|----------|------------|-------|--------------|
| STORY-001 | {title} | Feature | High | Small | 1 | N/A |

---

## STORY-001: Story Title

**Type**: Feature | Enhancement | Bug | Technical | Spike
**Priority**: High | Medium | Low
**Complexity**: Small | Medium | Large
**Phase**: {from PRD implementation phase}
**Labels**: `type:feature`, `frontend`
**GitHub Issue**: N/A
**Source**: `{PRD section heading or anchor}`

### Description

As a [user type], I want to [action], so that [benefit].

### Acceptance Criteria

- [ ] {testable criterion}
- [ ] {testable criterion}
- [ ] {testable criterion}

### Technical Notes

- Key implementation details
- Files or areas likely to change
- Patterns to follow from `AGENTS.md` or current project conventions

### Dependencies

- Blocked by: STORY-000 or None
- Blocks: STORY-000 or None

### GitHub Issue Body

Use this section as the issue body if creating a GitHub Issue.
```

### Ordering

Order stories by:

1. Phase from the PRD
2. Dependencies, with blockers before blocked stories
3. Priority, with High first within each phase

---

## Phase 4: Validate

Before output, verify:

- [ ] Every PRD requirement maps to at least one story
- [ ] No story is too large; split work expected to exceed 1-2 days
- [ ] Acceptance criteria are testable and specific
- [ ] Dependencies form a DAG with no circular dependencies
- [ ] Stories cover the full delivery path: domain logic, UI/API, validation, tests, docs, and operations where relevant
- [ ] Each story can be independently reviewed and merged

---

## Phase 5: Output Manifest

Create the directory if needed:

```bash
mkdir -p .agents/stories
```

Save the manifest to:

```text
.agents/stories/{kebab-case-prd-name}.stories.md
```

---

## Phase 6: GitHub Issues (Optional)

Use GitHub Issues as the issue tracker. Only create issues when the user asks for it or confirms after seeing the generated manifest.

### Inspect Repository Context

Use these commands when useful:

```bash
gh repo view --json nameWithOwner,defaultBranchRef
gh issue list --state open --limit 20
```

If the user provided a repository, pass `--repo OWNER/REPO` to each `gh` command.

### Create Issues

For each story selected for creation:

```bash
gh issue create \
  --title "{Story title}" \
  --body-file "{temporary-story-body.md}" \
  --label "type:feature" \
  --milestone "{milestone}"
```

Use `--repo OWNER/REPO` when creating issues outside the current repository.

After each issue is created:

1. Capture the issue number and URL from the command output.
2. Update the story manifest's `GitHub Issue` field with `#{number}` and the issue URL.
3. Preserve the local story ID for traceability.

### Report Created Issues

```markdown
## GitHub Issues Created

| Story | Issue | Title | Labels |
|-------|-------|-------|--------|
| STORY-001 | #12 | Story title | `type:feature`, `frontend` |

**Manifest**: `.agents/stories/{name}.stories.md`
```

---

## Tips

- Keep stories small enough to complete in 1-2 days.
- Acceptance criteria should be verifiable without asking the author.
- Technical stories need acceptance criteria too.
- Reference the PRD section for each story so reviewers can trace back.
- Prefer fewer, clearer labels over noisy taxonomy.
- If a story is blocked by an unanswered product question, create a Spike first.
