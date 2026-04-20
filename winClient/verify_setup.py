#!/usr/bin/env python3
"""
Verify Stadium V3 setup - Check all dependencies and imports
"""
import sys
import os
from pathlib import Path

print("\n" + "="*60)
print("Stadium V3 Windows Client - Setup Verification")
print("="*60)

# 1. Check Python version
print(f"\n[1] Python Version: {sys.version}")
if sys.version_info < (3, 10):
    print("    ⚠️  WARNING: Python 3.10+ recommended")
else:
    print("    ✓ OK")

# 2. Check working directory
cwd = Path.cwd()
print(f"\n[2] Working Directory: {cwd}")
if cwd.name == "winClient":
    print("    ✓ OK - In correct directory")
else:
    print(f"    ❌ ERROR - Should be in 'winClient' folder, currently in '{cwd.name}'")
    print(f"    FIX: cd {cwd.parent / 'winClient'}")

# 3. Check key files exist
print("\n[3] Key Files:")
files_to_check = [
    "main.py",
    "config.py",
    "theme.py",
    "screens/__init__.py",
    "screens/welcome.py",
    "screens/final_screen.py",
    "engine/video_overlay.py",
]
all_exist = True
for f in files_to_check:
    path = Path(f)
    if path.exists():
        print(f"    ✓ {f}")
    else:
        print(f"    ❌ {f} - MISSING")
        all_exist = False

if not all_exist:
    print("\n    ERROR: Some files are missing!")
    sys.exit(1)

# 4. Check Python dependencies
print("\n[4] Python Packages:")
packages = ["PyQt5", "cv2", "mediapipe", "requests", "numpy", "PIL"]
missing = []

for pkg in packages:
    try:
        if pkg == "cv2":
            import cv2
        elif pkg == "PIL":
            from PIL import Image
        else:
            __import__(pkg)
        print(f"    ✓ {pkg}")
    except ImportError:
        print(f"    ❌ {pkg} - NOT INSTALLED")
        missing.append(pkg)

if missing:
    print(f"\n    INSTALL MISSING: pip install {' '.join(missing)}")
    sys.exit(1)

# 5. Test imports
print("\n[5] Import Test:")
try:
    from screens.welcome import WelcomeScreen
    print("    ✓ screens.welcome")
except ImportError as e:
    print(f"    ❌ screens.welcome - {e}")

try:
    from screens.final_screen import FinalScreen
    print("    ✓ screens.final_screen")
except ImportError as e:
    print(f"    ❌ screens.final_screen - {e}")

try:
    from engine.video_overlay import VideoOverlayEngine
    print("    ✓ engine.video_overlay")
except ImportError as e:
    print(f"    ❌ engine.video_overlay - {e}")

print("\n" + "="*60)
print("✓ Setup Verification Complete!")
print("="*60)
print("\nYou can now run: python main.py\n")
