---
name: create-rules
description: Use when an existing codebase needs Codex to analyze local patterns and generate or update the project AGENTS.md.
---

# Create Project Rules

Generate an `AGENTS.md` file by analyzing an existing codebase and extracting the patterns Codex should follow.

Use `rules-interactive` instead when this is a greenfield project and the structure, stack, and architecture have not been chosen yet.

---

## Objective

Create project-specific rules that give Codex context about:

- What this project is
- Technologies used
- How the code is organized
- Architecture and module boundaries
- Patterns and conventions to follow
- How to build, test, validate, and review
- Known risks, constraints, and key files

---

## Phase 1: Discover

### Identify Project Type

Determine what kind of project this is:

| Type | Indicators |
|------|------------|
| Web App (Full-stack) | Frontend and backend in one repo, routes/API/server code |
| Web App (Frontend) | React/Vue/Svelte/etc. with no first-party backend |
| API/Backend | Server routes, workers, jobs, no primary UI |
| Library/Package | Publishable package metadata, exports, public API |
| CLI Tool | Command-line entry points or executable scripts |
| Mobile/Desktop App | Native or cross-platform app framework |
| Monorepo | Workspaces, multiple packages/apps |
| Script/Automation | Standalone scripts or internal automation |

### Analyze Configuration

Look for root configuration and manifest files:

```text
package.json
pnpm-workspace.yaml
pyproject.toml
Cargo.toml
go.mod
pom.xml
Makefile
Taskfile.yml
Dockerfile
docker-compose.yml
*.config.*
```

### Map Directory Structure

Explore the codebase to understand:

- Source directories
- Tests
- Shared libraries
- Config and infrastructure
- Scripts and generated artifacts
- Documentation
- AI-layer artifacts in `.agents/`

---

## Phase 2: Analyze

### Extract Tech Stack

Identify:

- Runtime and language versions
- Frameworks
- Database and storage
- API or integration protocols
- Testing tools
- Build tools
- Linting and formatting
- Package manager
- Deployment or infrastructure tools

### Identify Patterns

Study existing code for:

- **Naming**: files, functions, classes, branches, tests
- **Structure**: modules, layers, vertical slices, shared utilities
- **Errors**: error creation, propagation, user-facing messages
- **Types/Schemas**: interfaces, validation, generated types
- **State/Data Flow**: UI state, services, repositories, jobs, queues
- **Tests**: unit, integration, end-to-end, fixtures
- **Security**: auth, secrets, input validation, dependency hygiene

### Find Key Files

Identify files that are important for future agents:

- Entry points
- Configuration
- Core business logic
- Shared utilities
- Type definitions
- Public contracts
- Test setup
- Deployment and environment docs

---

## Phase 3: Generate

Use `.agents/AGENTS-template.md` as a starting point.

**Output path**: `AGENTS.md` at the project root.

Adapt to the project:

- Remove sections that do not apply.
- Add sections specific to this project type.
- Keep it concise and operational.
- Prefer exact commands over vague descriptions.
- Include file references for key patterns.

Required sections:

1. **Project Overview**
2. **Tech Stack**
3. **Commands**
4. **Architecture**
5. **Folder Structure**
6. **Code Patterns**
7. **Testing and Validation**
8. **GitHub Workflow**
9. **Key Files**
10. **Agent Notes**

Optional sections:

- API contracts
- Database patterns
- UI/design system
- Security requirements
- Deployment
- On-demand context references

---

## Phase 4: Output

```markdown
## AGENTS.md Created

**File**: `AGENTS.md`

### Project Type

{Detected project type}

### Tech Stack Summary

{Key technologies detected}

### Structure

{Brief structure overview}

### Next Steps

1. Review `AGENTS.md`.
2. Add missing project-specific constraints.
3. Run `prd-interactive` or `create-prd` if product requirements are not documented.
4. Continue with `create-stories`, `prime`, `plan`, `implement`, `validate`, and `review`.
```

---

## Tips

- Keep `AGENTS.md` focused and scannable.
- Do not duplicate long documentation; link to it.
- Include concrete examples and commands.
- Update `AGENTS.md` when architecture, commands, or conventions change.
