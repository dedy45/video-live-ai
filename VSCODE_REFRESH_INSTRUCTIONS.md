# VS Code Git Cache Refresh Instructions

## Problem
VS Code masih menunjukkan badge "10K+" meskipun Git status hanya 15 files.
Ini karena VS Code cache belum refresh setelah menghapus 65,489 files.

## Solution

### Option 1: Reload VS Code Window (RECOMMENDED)
1. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
2. Type: `Developer: Reload Window`
3. Press Enter
4. Badge 10K+ akan hilang setelah reload

### Option 2: Restart VS Code
1. Close VS Code completely
2. Reopen VS Code
3. Badge akan update otomatis

### Option 3: Refresh Git Status Manually
1. Click pada Source Control icon (Git icon di sidebar)
2. Click tombol refresh (circular arrow icon) di bagian atas
3. Tunggu beberapa detik untuk VS Code re-scan

### Option 4: Clear VS Code Cache (Nuclear Option)
```bash
# Close VS Code first, then:
# Windows:
Remove-Item -Path "$env:APPDATA\Code\Cache" -Recurse -Force
Remove-Item -Path "$env:APPDATA\Code\CachedData" -Recurse -Force

# Linux/Mac:
rm -rf ~/.config/Code/Cache
rm -rf ~/.config/Code/CachedData
```

## Verification

After refresh, Git status should show:
- **15 files** (legitimate changes)
- **405 tracked files** (source code only)
- **NO badge 10K+**

## What Was Cleaned

Total files removed: **65,489 files**
1. `.venv-livetalking/`: 49,044 files (5.382 GB)
2. Worktree `.venv/`: 11,845 files (396.5 MB)
3. Worktree `node_modules/`: 4,600 files (84.1 MB)

## Current Git Status (Actual)

```
 m .claude/worktrees/agent-ab5a5fb8
 m .claude/worktrees/brain-director-runtime
 M README.md
 M data/validation_history.json
 M docs/operations/livetiktokubuntu.md
 M docs/task_status.md
 m external/livetalking
 M src/control_plane/store.py
 M src/dashboard/api.py
 M src/dashboard/frontend/src/components/panels/PerformerWorkspace.svelte
 M src/dashboard/frontend/src/lib/api.ts
 M src/dashboard/frontend/src/lib/types.ts
 M src/dashboard/frontend/src/tests/voice-panel.test.ts
 M tests/test_dashboard.py
?? src/dashboard/frontend/src/components/panels/voice/
```

Total: 15 files only!

## Repository is Clean ✓

- ✅ .gitignore working correctly
- ✅ Model files (30GB) not tracked
- ✅ Virtual environments not tracked
- ✅ Only source code tracked
- ✅ Ready for commit and push
