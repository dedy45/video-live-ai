#!/usr/bin/env python3
"""
Fish-Speech S2-Pro Indonesian Language Test Script
Tests S2-Pro's Indonesian language support with various emotion tags
"""

import sys
import os
from pathlib import Path

# Color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{NC}\n")

def print_section(text):
    print(f"\n{YELLOW}{text}{NC}")
    print("-" * 60)

def check_environment():
    """Check if Fish-Speech S2-Pro is properly installed"""
    print_section("Environment Check")
    
    # Check if we're in the right directory
    fish_speech_dir = Path("external/fish-speech")
    if not fish_speech_dir.exists():
        print(f"{RED}✗{NC} Fish-Speech directory not found at {fish_speech_dir}")
        print(f"  Run this script from the videoliveai project root")
        return False
    
    # Check if S2-Pro model exists
    s2_model_dir = fish_speech_dir / "checkpoints" / "s2-pro"
    if not s2_model_dir.exists():
        print(f"{RED}✗{NC} S2-Pro model not found at {s2_model_dir}")
        print(f"  Run upgrade-to-s2.sh first to download the model")
        return False
    
    print(f"{GREEN}✓{NC} Fish-Speech directory found")
    print(f"{GREEN}✓{NC} S2-Pro model found")
    
    # Check UV virtual environment
    venv_dir = fish_speech_dir / ".venv"
    if not venv_dir.exists():
        print(f"{YELLOW}!{NC} UV virtual environment not found")
        print(f"  Create it with: cd {fish_speech_dir} && uv venv")
        return False
    
    print(f"{GREEN}✓{NC} UV virtual environment found")
    
    return True

def print_test_cases():
    """Print Indonesian test cases for WebUI testing"""
    print_header("Fish-Speech S2-Pro Indonesian Test Cases")
    
    test_cases = [
        {
            "name": "1. Sapaan Dasar (Basic Greeting)",
            "type": "Basic",
            "tags": "—",
            "text": "Halo, selamat datang di toko kami. Hari ini kami punya banyak produk menarik untuk Anda."
        },
        {
            "name": "2. Excited Emotion",
            "type": "Emotion",
            "tags": "[excited]",
            "text": "[excited] Wah, ada promo spesial hari ini! Diskon hingga lima puluh persen untuk semua produk pilihan!"
        },
        {
            "name": "3. Whisper Emotion",
            "type": "Emotion",
            "tags": "[whisper]",
            "text": "[whisper] Psst, ini rahasia ya. Stok produk ini tinggal sedikit, jadi buruan pesan sebelum kehabisan."
        },
        {
            "name": "4. Professional Broadcast Tone",
            "type": "Tone",
            "tags": "[professional broadcast tone]",
            "text": "[professional broadcast tone] Selamat malam pemirsa. Berikut adalah informasi produk unggulan kami malam ini dengan harga terbaik."
        },
        {
            "name": "5. Multi-Emotion (Campuran)",
            "type": "Mixed",
            "tags": "[excited] + [whisper] + [normal]",
            "text": "[excited] Halo semuanya! [whisper] Hari ini ada kejutan spesial loh. [normal] Yuk langsung kita lihat produk-produknya."
        },
        {
            "name": "6. Long-Form Description",
            "type": "Long-form",
            "tags": "—",
            "text": "Produk yang satu ini sangat istimewa. Terbuat dari bahan berkualitas tinggi, dengan desain yang modern dan elegan. Cocok untuk digunakan sehari-hari maupun acara spesial. Harganya juga sangat terjangkau, dan kami memberikan garansi resmi satu tahun. Jadi tunggu apa lagi? Pesan sekarang juga selagi stok masih tersedia!"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{GREEN}{test['name']}{NC}")
        print(f"Type: {test['type']}")
        print(f"Tags: {test['tags']}")
        print(f"\nText to copy:")
        print(f"{BLUE}{test['text']}{NC}")
        print()
    
    print_section("How to Use")
    print("1. Start Fish-Speech WebUI with UV:")
    print(f"   cd external/fish-speech")
    print(f"   uv run python tools/run_webui.py")
    print()
    print("2. Open browser: http://localhost:7860")
    print()
    print("3. Copy-paste each test text above into the WebUI")
    print()
    print("4. Click 'Generate' and listen to the output")
    print()
    print(f"{YELLOW}Note:{NC} S2-Pro automatically detects Indonesian language")
    print("      No manual language selection needed!")
    print()

def print_emotion_tags_reference():
    """Print reference for available emotion tags"""
    print_section("Available Emotion Tags Reference")
    
    tags = [
        ("[excited]", "Excited, enthusiastic tone"),
        ("[whisper]", "Soft, quiet whisper"),
        ("[laugh]", "Laughing tone"),
        ("[sad]", "Sad, melancholic tone"),
        ("[angry]", "Angry, frustrated tone"),
        ("[professional broadcast tone]", "Professional news anchor style"),
        ("[casual friendly tone]", "Casual, friendly conversation"),
        ("[storytelling tone]", "Narrative storytelling style"),
    ]
    
    print("\nBuilt-in emotion tags:")
    for tag, description in tags:
        print(f"  {GREEN}{tag:30}{NC} - {description}")
    
    print(f"\n{YELLOW}Pro Tip:{NC} You can also use free-form descriptions like:")
    print(f"  [speaking like a game show host]")
    print(f"  [warm and welcoming tone]")
    print(f"  [energetic sales pitch]")
    print()

def main():
    print_header("Fish-Speech S2-Pro Indonesian Test Suite")
    
    # Check environment
    if not check_environment():
        print(f"\n{RED}Environment check failed. Please fix the issues above.{NC}\n")
        sys.exit(1)
    
    print(f"\n{GREEN}✓ Environment check passed!{NC}\n")
    
    # Print test cases
    print_test_cases()
    
    # Print emotion tags reference
    print_emotion_tags_reference()
    
    # Print WebUI instructions
    print_section("Quick Start Commands")
    print(f"cd external/fish-speech")
    print(f"uv run python tools/run_webui.py")
    print()
    print(f"Then open: {BLUE}http://localhost:7860{NC}")
    print()

if __name__ == "__main__":
    main()
