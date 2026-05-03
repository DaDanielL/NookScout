---
name: prime
description: Use before planning, implementation, validation, or review when Codex needs concise project, issue, or PR context.
---

# Prime: Load Project Context

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

## Objective

Build a concise working understanding of the project before planning, implementing, validating, or reviewing.

---

## Step 0: Load External Context

If the input includes a GitHub issue number or URL, fetch it:

```bash
gh issue view {NUMBER} --json number,title,body,labels,state,url
```

If the input includes a GitHub PR number or URL, fetch it:

```bash
gh pr view {NUMBER} --json number,title,body,author,baseRefName,headRefName,files,state,url
```

Use the issue or PR body to understand acceptance criteria, constraints, and expected behavior.

---

## Step 1: Read Project Rules

Read these files when present:

1. `AGENTS.md`
2. `.agents/README.md`
3. `README.md`
4. Package, build, or workspace files such as `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `Makefile`, or `Taskfile.yml`

---

## Step 2: Analyze the Codebase

Use targeted searches and file reads to identify:

- Project purpose and main user workflows
- Tech stack, package manager, and runtime
- Folder structure and module boundaries
- Entry points and key configuration files
- Test structure and validation commands
- Recent work with `git log --oneline -5`
- Current branch and dirty state with `git status --short`

If paths are provided in the input, prioritize those areas.

---

## Output

Produce a concise summary:

- **Project Purpose**: one sentence
- **Tech Stack**: languages, frameworks, runtime, data stores
- **Architecture**: main folders and boundaries
- **Key Commands**: install, dev, test, build, lint
- **Current Context**: branch, recent commits, linked issue or PR
- **Patterns to Respect**: naming, errors, tests, UI/API conventions

Keep it scannable. Include file references for important rules or examples.
