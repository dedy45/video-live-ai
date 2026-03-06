#!/usr/bin/env python3
"""Setup script for LiveTalking integration.

This script will:
1. Clone LiveTalking as a git submodule
2. Install required dependencies
3. Download model weights (MuseTalk, ER-NeRF, GFPGAN)
4. Verify GPU availability
5. Create necessary directories

Usage:
    python scripts/setup_livetalking.py
    python scripts/setup_livetalking.py --skip-models  # Skip model download
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> bool:
    """Run a shell command and return success status."""
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        return False


def check_git() -> bool:
    """Check if git is installed."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: git is not installed", file=sys.stderr)
        return False


def setup_submodule(project_root: Path) -> bool:
    """Setup LiveTalking as a git submodule."""
    print("\n=== Setting up LiveTalking submodule ===")
    
    external_dir = project_root / "external"
    external_dir.mkdir(exist_ok=True)
    
    livetalking_dir = external_dir / "livetalking"
    
    if livetalking_dir.exists():
        print(f"LiveTalking already exists at {livetalking_dir}")
        return True
    
    # Add as submodule
    if not run_command(
        ["git", "submodule", "add", "https://github.com/lipku/LiveTalking.git", "external/livetalking"],
        cwd=project_root,
    ):
        print("Failed to add LiveTalking submodule", file=sys.stderr)
        return False
    
    # Initialize and update submodule
    if not run_command(["git", "submodule", "update", "--init", "--recursive"], cwd=project_root):
        print("Failed to initialize submodule", file=sys.stderr)
        return False
    
    print("✓ LiveTalking submodule setup complete")
    return True


def install_dependencies(project_root: Path) -> bool:
    """Install LiveTalking dependencies."""
    print("\n=== Installing dependencies ===")
    
    livetalking_dir = project_root / "external" / "livetalking"
    requirements_file = livetalking_dir / "requirements.txt"
    
    # Check if LiveTalking submodule exists
    if not livetalking_dir.exists():
        print("⚠ LiveTalking submodule not cloned yet")
        print("  This is okay - dependencies will be installed when you run setup again")
        print("  after cloning the submodule")
        return True
    
    if not requirements_file.exists():
        print(f"⚠ Warning: {requirements_file} not found")
        print("  Installing basic dependencies from pyproject.toml instead")
        # Install from pyproject.toml [livetalking] section
        if not run_command(["uv", "pip", "install", "-e", ".[livetalking]"], cwd=project_root):
            print("Failed to install dependencies from pyproject.toml", file=sys.stderr)
            return False
        print("✓ Basic dependencies installed")
        return True
    
    # Install using uv (faster than pip)
    print(f"Installing from: {requirements_file}")
    if not run_command(["uv", "pip", "install", "-r", str(requirements_file)], cwd=project_root):
        print("Failed to install dependencies", file=sys.stderr)
        return False
    
    print("✓ Dependencies installed")
    return True


def create_directories(project_root: Path) -> bool:
    """Create necessary directories for models and assets."""
    print("\n=== Creating directories ===")
    
    dirs = [
        project_root / "models" / "musetalk",
        project_root / "models" / "er-nerf",
        project_root / "models" / "gfpgan",
        project_root / "assets" / "avatar",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path}")
    
    print("✓ Directories created")
    return True


def download_models(project_root: Path) -> bool:
    """Download model weights."""
    print("\n=== Downloading models ===")
    print("Note: This will download ~5GB of model weights")
    print("Models needed:")
    print("  - MuseTalk 1.5 (~1.5GB)")
    print("  - ER-NeRF (~2GB)")
    print("  - GFPGAN (~1.5GB)")
    
    response = input("\nProceed with download? (y/n): ")
    if response.lower() != "y":
        print("Skipping model download")
        return True
    
    # TODO: Implement actual model download
    # This would typically use huggingface_hub or direct wget/curl
    
    print("\n⚠ Model download not yet implemented")
    print("Please download models manually:")
    print("  1. MuseTalk: https://github.com/TMElyralab/MuseTalk")
    print("  2. ER-NeRF: https://github.com/Fictionarry/ER-NeRF")
    print("  3. GFPGAN: https://github.com/TencentARC/GFPGAN")
    
    return True


def check_gpu() -> bool:
    """Check if GPU is available."""
    print("\n=== Checking GPU ===")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"✓ GPU detected: {gpu_name}")
            print(f"  VRAM: {vram:.1f} GB")
            
            if vram < 8:
                print("⚠ Warning: LiveTalking requires at least 8GB VRAM")
                print("  Consider using MOCK_MODE for testing")
            
            return True
        else:
            print("⚠ No GPU detected")
            print("  LiveTalking requires NVIDIA GPU with CUDA")
            print("  Use MOCK_MODE=true for testing without GPU")
            return False
            
    except ImportError:
        print("⚠ PyTorch not installed")
        print("  Install with: uv pip install torch")
        return False


def update_env_file(project_root: Path) -> bool:
    """Update .env file with LiveTalking configuration."""
    print("\n=== Updating .env file ===")
    
    env_file = project_root / ".env"
    
    livetalking_config = """
# === LiveTalking Configuration ===
LIVETALKING_ENABLED=true
LIVETALKING_REFERENCE_VIDEO=assets/avatar/reference.mp4
LIVETALKING_REFERENCE_AUDIO=assets/avatar/reference.wav
LIVETALKING_USE_WEBRTC=false
LIVETALKING_USE_RTMP=true
LIVETALKING_FPS=30
LIVETALKING_RESOLUTION=512,512
"""
    
    if env_file.exists():
        with open(env_file, "r") as f:
            content = f.read()
        
        if "LIVETALKING_ENABLED" in content:
            print("LiveTalking config already exists in .env")
            return True
        
        with open(env_file, "a") as f:
            f.write(livetalking_config)
        
        print("✓ Added LiveTalking config to .env")
    else:
        print("⚠ .env file not found")
        print("  Please copy .env.example to .env first")
        return False
    
    return True


def main() -> int:
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup LiveTalking integration")
    parser.add_argument("--skip-models", action="store_true", help="Skip model download")
    args = parser.parse_args()
    
    print("=== LiveTalking Setup ===")
    print("This will integrate LiveTalking into videoliveai")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    print(f"\nProject root: {project_root}")
    
    # Check prerequisites
    if not check_git():
        return 1
    
    # Setup steps
    steps = [
        ("Setup submodule", lambda: setup_submodule(project_root)),
        ("Install dependencies", lambda: install_dependencies(project_root)),
        ("Create directories", lambda: create_directories(project_root)),
        ("Check GPU", check_gpu),
        ("Update .env", lambda: update_env_file(project_root)),
    ]
    
    if not args.skip_models:
        steps.insert(3, ("Download models", lambda: download_models(project_root)))
    
    # Run all steps
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}", file=sys.stderr)
            return 1
    
    print("\n" + "=" * 50)
    print("✓ LiveTalking setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Prepare reference materials:")
    print("   - Record 5-minute video of avatar (assets/avatar/reference.mp4)")
    print("   - Record 3-10 second audio sample (assets/avatar/reference.wav)")
    print("\n2. Download models (if skipped):")
    print("   - Run: python scripts/setup_livetalking.py")
    print("\n3. Test the integration:")
    print("   - Run: set MOCK_MODE=true && uv run python -m src.main")
    print("\n4. Train ER-NeRF avatar:")
    print("   - Run: python external/livetalking/train_avatar.py")
    print("\n5. Start production:")
    print("   - Run: uv run python -m src.main")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
