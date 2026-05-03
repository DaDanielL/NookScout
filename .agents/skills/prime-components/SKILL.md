---
name: prime-components
description: Use before UI component work when Codex needs to learn local component conventions and examples to mirror.
---

# Prime Components: Learn Component Patterns

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

## Objective

Understand the local component system well enough to add or change UI without breaking visual, accessibility, or architectural conventions.

---

## Step 0: Load GitHub Context

If the input includes a GitHub issue or PR, inspect it:

```bash
gh issue view {NUMBER} --json number,title,body,labels,state,url
gh pr view {NUMBER} --json number,title,body,files,state,url
```

Use the command that matches the input.

---

## Step 1: Read Rules and Discover UI Primitives

Read `AGENTS.md` first. Then inspect:

- Component directories
- Shared UI primitives
- Theme and styling configuration
- Utility functions for class names or variants
- Existing form, modal, table, navigation, and layout components
- Tests or stories for components, if present

Use provided paths first. Otherwise search common locations such as `components/`, `src/components/`, `app/`, `pages/`, `features/`, `ui/`, and `packages/*`.

---

## Step 2: Extract Patterns

Capture examples for:

- Component file naming
- Props types and exported interfaces
- Composition style
- Styling conventions
- Accessibility patterns
- Loading, disabled, empty, and error states
- Test style or visual verification approach

---

## Output

Summarize:

- **UI System**: primitives, component library, styling tools
- **Component Patterns**: file structure, props, composition, variants
- **State and Forms**: how user interactions are handled
- **Accessibility**: labels, keyboard behavior, focus, semantics
- **Examples to Mirror**: file:line references
- **Validation**: commands or browser checks to run
