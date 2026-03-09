#!/usr/bin/env python3
import argparse
import contextlib
import io
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path so src can be imported if script is run directly
base_dir = Path(__file__).parent.parent.resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

# Try imports
try:
    from src.dashboard.readiness import run_readiness_checks
    from src.dashboard.truth import get_runtime_truth_snapshot
    from src.config import is_mock_mode
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)

def main():
    parser = argparse.ArgumentParser(description="Check if the system is ready for real-mode operation.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    args = parser.parse_args()

    if args.json:
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setStream(sys.stderr)

    if not IMPORTS_OK:
        error_msg = f"Failed to import backend modules: {IMPORT_ERROR}"
        if args.json:
            print(json.dumps({
                "overall": "FAILED — Import Error",
                "is_ready": False,
                "failed_count": 1,
                "checks": [{"check": "Import backend modules", "passed": False, "message": IMPORT_ERROR}],
                "truth": None
            }, indent=2))
        else:
            print(f"[FAIL] Import backend modules: {IMPORT_ERROR}")
            print("\n" + "="*40)
            print("BLOCKED — Backend modules missing")
            print("="*40)
        sys.exit(1)

    if args.json:
        captured_stdout = io.StringIO()
        with contextlib.redirect_stdout(captured_stdout):
            readiness_result = run_readiness_checks()
            truth_snapshot = get_runtime_truth_snapshot()
        noisy_output = captured_stdout.getvalue()
        if noisy_output.strip():
            print(noisy_output, file=sys.stderr, end="")
    else:
        # 1. Run internal readiness checks from backend
        readiness_result = run_readiness_checks()
        # 3. Get truth snapshot
        truth_snapshot = get_runtime_truth_snapshot()

    # 2. Add extra checks specific to "Real Mode" script
    extra_checks = []

    # Check MOCK_MODE is NOT true
    mock = is_mock_mode()
    extra_checks.append({
        "check": "MOCK_MODE is NOT true",
        "passed": not mock,
        "message": f"MOCK_MODE is {'true' if mock else 'false'}"
    })

    # Check assets/avatar/reference.mp4 exists
    ref_mp4 = base_dir / "assets" / "avatar" / "reference.mp4"
    extra_checks.append({
        "check": "Reference MP4 exists",
        "passed": ref_mp4.exists(),
        "message": f"Path: {ref_mp4}"
    })

    # Check Product data source exists
    p_json = base_dir / "data" / "products.json"
    p_db = base_dir / "data" / "products.db"
    found_products = [p.name for p in (p_json, p_db) if p.exists()]
    extra_checks.append({
        "check": "Product data source exists",
        "passed": len(found_products) > 0,
        "message": f"Found: {', '.join(found_products)}" if found_products else "Neither products.json nor products.db found"
    })

    # Combine checks
    all_checks = []
    # Map readiness checks to our output format
    for c in readiness_result.checks:
        all_checks.append({
            "check": f"Readiness: {c.name}",
            "passed": c.passed,
            "message": c.message
        })
    all_checks.extend(extra_checks)

    failed_count = sum(1 for c in all_checks if not c["passed"])
    is_ready = (failed_count == 0)

    if args.json:
        output = {
            "overall": "READY FOR REAL MODE" if is_ready else f"BLOCKED — {failed_count} issues must be resolved",
            "is_ready": is_ready,
            "failed_count": failed_count,
            "checks": all_checks,
            "truth": truth_snapshot
        }
        print(json.dumps(output, indent=2))
    else:
        for c in all_checks:
            status = "PASS" if c["passed"] else "FAIL"
            print(f"[{status}] {c['check']}: {c['message']}")

        print("\n" + "="*40)
        if is_ready:
            print("READY FOR REAL MODE")
        else:
            print(f"BLOCKED — {failed_count} issues must be resolved")
        print("="*40)

        print("\nTruth Snapshot Summary:")
        print(f"  Mock Mode: {truth_snapshot.get('mock_mode')}")
        print(f"  Face:      {truth_snapshot.get('face_runtime_mode')}")
        face_engine = truth_snapshot.get("face_engine", {})
        if face_engine:
            print(f"    Requested model:  {face_engine.get('requested_model')}")
            print(f"    Resolved model:   {face_engine.get('resolved_model')}")
            print(f"    Requested avatar: {face_engine.get('requested_avatar_id')}")
            print(f"    Resolved avatar:  {face_engine.get('resolved_avatar_id')}")
            print(f"    Engine state:     {face_engine.get('engine_state')}")
            print(f"    Fallback active:  {face_engine.get('fallback_active')}")
        print(f"  Voice:     {truth_snapshot.get('voice_runtime_mode')}")
        print(f"  Stream:    {truth_snapshot.get('stream_runtime_mode')}")
        print(f"  Timestamp: {truth_snapshot.get('timestamp')}")

    sys.exit(0 if is_ready else 1)

if __name__ == "__main__":
    main()
