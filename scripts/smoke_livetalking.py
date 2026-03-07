"""LiveTalking Engine Smoke Test.

Verifies that LiveTalking is ready to run:
- app.py exists
- model path exists
- avatar path exists
- port is available
- prints exact launch command

Usage:
    uv run python scripts/smoke_livetalking.py
"""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Defaults
DEFAULT_PORT = int(os.getenv("LIVETALKING_PORT", "8010"))
DEFAULT_MODEL = os.getenv("LIVETALKING_MODEL", "wav2lip")
DEFAULT_AVATAR_ID = os.getenv("LIVETALKING_AVATAR_ID", "wav2lip256_avatar1")
DEFAULT_TRANSPORT = os.getenv("LIVETALKING_TRANSPORT", "webrtc")

LIVETALKING_DIR = project_root / "external" / "livetalking"
APP_PY = LIVETALKING_DIR / "app.py"
MODELS_DIR = LIVETALKING_DIR / "models"
AVATARS_DIR = LIVETALKING_DIR / "data" / "avatars"


def check_port_free(port: int) -> bool:
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(("127.0.0.1", port))
            return result != 0  # 0 means port is in use
    except Exception:
        return True


def run_smoke_test() -> bool:
    """Run all smoke test checks. Returns True if all pass."""
    checks: list[tuple[str, bool, str]] = []

    # 1. Check app.py exists
    exists = APP_PY.exists()
    checks.append((
        "app.py exists",
        exists,
        str(APP_PY) if exists else f"NOT FOUND: {APP_PY}",
    ))

    # 2. Check models directory
    models_exist = MODELS_DIR.exists()
    model_detail = ""
    if models_exist:
        model_files = list(MODELS_DIR.rglob("*.pth"))
        model_detail = f"{len(model_files)} .pth files found"
    else:
        model_detail = f"NOT FOUND: {MODELS_DIR}"
    checks.append(("models directory", models_exist, model_detail))

    # 3. Check specific model
    if DEFAULT_MODEL == "wav2lip":
        model_file = MODELS_DIR / "wav2lip.pth"
    elif DEFAULT_MODEL == "musetalk":
        model_file = MODELS_DIR / "musetalk"
    else:
        model_file = MODELS_DIR
    model_ready = model_file.exists()
    checks.append((
        f"model '{DEFAULT_MODEL}'",
        model_ready,
        str(model_file) if model_ready else f"NOT FOUND: {model_file}",
    ))

    # 4. Check avatar directory
    avatar_dir = AVATARS_DIR / DEFAULT_AVATAR_ID
    avatar_ready = avatar_dir.exists()
    checks.append((
        f"avatar '{DEFAULT_AVATAR_ID}'",
        avatar_ready,
        str(avatar_dir) if avatar_ready else f"NOT FOUND: {avatar_dir}",
    ))

    # 5. Check port availability
    port_free = check_port_free(DEFAULT_PORT)
    checks.append((
        f"port {DEFAULT_PORT} available",
        port_free,
        "free" if port_free else f"IN USE (port {DEFAULT_PORT})",
    ))

    # Print results
    print("=" * 60)
    print("  LiveTalking Smoke Test")
    print("=" * 60)
    print()

    all_pass = True
    for name, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        icon = "[OK]" if passed else "[!!]"
        print(f"  {icon} {name}: {status}")
        print(f"      {detail}")
        if not passed:
            all_pass = False

    print()
    print("-" * 60)

    # Print launch command
    cmd_parts = [
        "python", "app.py",
        "--transport", DEFAULT_TRANSPORT,
        "--model", DEFAULT_MODEL,
        "--avatar_id", DEFAULT_AVATAR_ID,
        "--listenport", str(DEFAULT_PORT),
    ]
    launch_cmd = " ".join(cmd_parts)

    print()
    print("  Launch command (run from external/livetalking/):")
    print(f"    {launch_cmd}")
    print()
    print("  UV-compatible command (run from project root):")
    print(f"    cd external/livetalking && python {' '.join(cmd_parts[1:])}")
    print()

    if all_pass:
        print("  Result: ALL CHECKS PASSED")
    else:
        print("  Result: SOME CHECKS FAILED (see above)")
        print("  Tip: Run setup scripts to download missing models/avatars")

    print("=" * 60)
    return all_pass


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
