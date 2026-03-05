---
description: Mandatory rule — Agent MUST update docs after every implementation task
---

// turbo-all

# Documentation Update Protocol (MANDATORY)

This workflow is **MANDATORY** after every implementation task. The agent MUST follow these steps before reporting completion to the user.

## When to Trigger

This workflow MUST execute:

- After completing ANY phase or sub-phase
- After adding new files or modules
- After modifying architecture (new layers, new endpoints, new dependencies)
- After fixing bugs or hardening code
- After adding new API endpoints
- Before calling `notify_user` to report task completion

## Documentation Files to Update

### 1. `videoliveai/docs/task_status.md`

**Update when**: Any task completes or status changes.

- Update `Last Updated` timestamp
- Update Overall Status header
- Mark completed phases with ✅
- Add new phases to the table if created
- Update file count

### 2. `videoliveai/docs/changelogs.md`

**Update when**: Any code change is made.

- Add new version entry (bump minor for features, patch for fixes)
- List all files added/modified under `### Added` or `### Fixed`
- Include SDR notes if design decisions were made
- Format: `[version] — YYYY-MM-DD`

### 3. `videoliveai/docs/architecture.md`

**Update when**: New modules, layers, or architectural patterns are added.

- Update version number
- Update layer diagram if layers change
- Update directory structure if new folders added
- Update Key Design Decisions table
- Update Startup Sequence if new components registered
- Add new sections for major components (e.g., Dashboard API, Analytics, Health System)

### 4. `videoliveai/docs/workflow.md`

**Update when**: New commands, scripts, or development procedures added.

- Update version number
- Add new CLI commands (e.g., `verify_pipeline.py`)
- Add new URLs (dashboard, API docs)
- Update environment setup if new env vars added
- Update testing commands if new test files added

### 5. `videoliveai/docs/security.md`

**Update when**: New API keys, auth mechanisms, or security features added.

- Update API Keys table with new services
- Update auth mechanisms (dashboard HTTP Basic, etc.)
- Document new security features (rate limiting, CORS, etc.)

### 6. `videoliveai/docs/contributing.md`

**Update when**: New coding standards, rules, or conventions established.

- Update Agent-Specific Rules
- Add new commit types if needed
- Update testing requirements

## Verification Checklist

Before calling `notify_user`, verify:

- [ ] `task_status.md` — reflects current completion state
- [ ] `changelogs.md` — has entry for the changes just made
- [ ] `architecture.md` — matches current codebase structure
- [ ] `workflow.md` — includes all runnable commands
- [ ] `security.md` — lists all API keys and auth methods
- [ ] `contributing.md` — rules match current workflow

## Example Update Flow

```
1. Complete implementation task (e.g., add Dashboard API)
2. Update task_status.md → Mark Phase 14 as ✅ Done
3. Update changelogs.md → Add v0.3.0 entry with Dashboard details
4. Update architecture.md → Add Dashboard API section, update diagram
5. Update workflow.md → Add `http://localhost:8000/dashboard` URL
6. Update security.md → Add DASHBOARD_USERNAME/PASSWORD to keys table
7. Update contributing.md → (only if new conventions established)
8. THEN notify_user
```

## Failure Consequence

If the agent skips this workflow, the documentation drifts from reality, making the project unmaintainable. The user has explicitly requested this protocol be enforced.
