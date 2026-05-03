---
name: rules-interactive
description: Use when a greenfield project needs Codex to interview the user and generate a project AGENTS.md before implementation.
---

# Rules Interactive: Greenfield AGENTS.md Generator

Use this workflow when a product idea has just been formulated, usually in the first PRD, and the project structure is still unknown.

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

---

## Objective

Interview the user, recommend a practical project shape, and generate `AGENTS.md` before implementation begins.

This workflow should define everything Codex needs to work effectively:

- Project type
- Tech stack
- Architecture
- Tooling
- Testing strategy
- Folder structure
- Key files
- Coding conventions
- GitHub Issues and PR workflow
- Validation commands
- Security and operational expectations

---

## Phase 1: Load Product Context

If a PRD path is provided, read it. If no path is provided, look for:

1. `.agents/PRDs/*.prd.md`
2. `PRD.md` at the project root
3. Conversation context

If multiple PRDs exist, ask which one should drive the rules.

Summarize:

- Product goal
- Primary users
- MVP scope
- Functional requirements
- Non-functional requirements
- Constraints and open questions

---

## Phase 2: Interview

Ask questions in small batches. After each batch, briefly summarize what you learned and where you are leaning.

### Batch 1: Product and Delivery Context

Ask:

1. Who will use this first: you, an internal team, beta users, or public users?
2. What is the target platform: web, mobile, desktop, CLI, API, automation, library, or something else?
3. What matters most for the first version: speed, polish, reliability, scalability, compliance, cost, or learning?
4. Is this a throwaway prototype, a production MVP, or a long-lived product?

### Batch 2: Tech Preferences and Constraints

Ask:

1. Preferred language or framework, if any?
2. Preferred package manager and runtime?
3. Any must-use services, databases, APIs, or hosting platforms?
4. Any technologies to avoid?
5. Any licensing, privacy, compliance, or data residency constraints?

### Batch 3: Architecture and Data

Ask:

1. What are the core entities or resources?
2. Does the app need authentication or roles?
3. Does it need offline support, realtime behavior, background jobs, files, payments, email, or notifications?
4. What data must be persisted, and how sensitive is it?
5. Are there external systems that must be integrated?

### Batch 4: Quality and Workflow

Ask:

1. What testing depth is expected for MVP?
2. What validation should block a PR?
3. How should GitHub Issues be labeled and sized?
4. What environments are needed: local only, preview, staging, production?
5. What documentation should be maintained from day one?

---

## Phase 3: Recommend

Before writing `AGENTS.md`, provide a recommendation with tradeoffs.

Include:

- **Project Type**: recommended category
- **Tech Stack**: language, framework, package manager, database, styling/UI, testing
- **Architecture**: monolith, modular monolith, services, packages, vertical slices, layered architecture, or other
- **Folder Structure**: proposed tree with responsibilities
- **Key Files**: files to create first and why
- **Commands**: install, dev, test, lint, build, typecheck, format
- **Testing Strategy**: unit, integration, end-to-end, smoke, security
- **GitHub Workflow**: issue labels, branch naming, PR expectations
- **Risks**: main risks and mitigations

Ask the user to confirm or adjust the recommendation before generating `AGENTS.md` when choices are consequential.

---

## Phase 4: Generate AGENTS.md

Use `.agents/AGENTS-template.md` as the base and fill it with the confirmed recommendations.

**Output path**: `AGENTS.md` at the project root.

The generated file must include:

1. Project overview
2. Product context from the PRD
3. Recommended tech stack
4. Architecture and folder structure
5. Key files to create first
6. Development commands
7. Testing and validation strategy
8. Coding conventions
9. Security and configuration rules
10. GitHub Issues and PR workflow
11. AI-layer artifact paths:
    - PRDs: `.agents/PRDs/`
    - Stories: `.agents/stories/`
    - Plans: `.agents/plans/`
    - Reports: `.agents/reports/`
    - Reviews: `.agents/reviews/`
12. Open questions and decision log

If commands cannot be known until the project is scaffolded, write clear placeholders such as:

```markdown
- **Install**: TBD after scaffold
- **Test**: TBD after test framework selection
```

Do not create a demo app or product scaffold during this workflow. Generate rules only.

---

## Phase 5: Output

```markdown
## AGENTS.md Created

**File**: `AGENTS.md`
**Source PRD**: `.agents/PRDs/{name}.prd.md` or N/A

### Recommended Project Shape

{short summary}

### Key Decisions

- {decision 1}
- {decision 2}
- {decision 3}

### Open Questions

- {question or "None"}

### Next Step

Run `create-stories {prd-path}` to convert the PRD into GitHub issue-ready stories.
```

---

## Guidance

- Recommend defaults, but make the tradeoffs visible.
- Keep questions practical and answerable.
- Avoid premature architecture complexity.
- Prefer a small production-quality foundation over a sprawling scaffold.
- Do not invent user preferences; mark unknowns as TBD.
