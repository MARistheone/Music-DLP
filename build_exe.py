"""
Build script for Music DLP - PyInstaller packaging.

Usage:
    python build_exe.py          # Build the exe
    python build_exe.py --debug  # Build with console window for debugging
    python build_exe.py --clean  # Clean build artifacts before building
"""

import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"
SPEC_FILE = PROJECT_DIR / "MusicDLP.spec"
OUTPUT_NAME = "MusicDLP"


def check_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("ERROR: PyInstaller not installed. Run: pip install pyinstaller")
        sys.exit(1)


def clean_build():
    """Remove previous build artifacts."""
    for d in [BUILD_DIR, DIST_DIR]:
        if d.exists():
            print(f"Removing {d}...")
            shutil.rmtree(d)
    print("Clean complete.")


def build(debug=False):
    """Run PyInstaller build."""
    check_pyinstaller()

    if not SPEC_FILE.exists():
        print(f"ERROR: Spec file not found: {SPEC_FILE}")
        sys.exit(1)

    cmd = [sys.executable, "-m", "PyInstaller", str(SPEC_FILE), "--noconfirm"]

    mode = "DEBUG" if debug else "RELEASE"
    print(f"Building in {mode} mode...")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))

    if result.returncode != 0:
        print("\nBUILD FAILED")
        sys.exit(1)

    dist_app_dir = DIST_DIR / OUTPUT_NAME
    print(f"\nBuild successful! Output: {dist_app_dir}")
    return dist_app_dir


def create_distribution(dist_app_dir: Path):
    """Create the final distribution package with helper files."""
    if not dist_app_dir.exists():
        print(f"ERROR: Build output not found at {dist_app_dir}")
        sys.exit(1)

    # Create cookies.txt.example
    cookies_example = dist_app_dir / "cookies.txt.example"
    cookies_example.write_text(
        "# Export cookies from your browser using a browser extension\n"
        "# such as 'Get cookies.txt LOCALLY' for Chrome/Firefox.\n"
        "#\n"
        "# Steps:\n"
        "# 1. Install the extension in your browser\n"
        "# 2. Log into YouTube\n"
        "# 3. Export cookies to a file\n"
        "# 4. Rename this file to cookies.txt\n"
        "# 5. Configure the path in Music DLP Settings\n",
        encoding="utf-8"
    )
    print(f"  Created: {cookies_example.name}")

    # Create ffmpeg placeholder directory
    ffmpeg_dir = dist_app_dir / "ffmpeg"
    ffmpeg_dir.mkdir(exist_ok=True)
    (ffmpeg_dir / "PUT_FFMPEG_HERE.txt").write_text(
        "Download FFmpeg from https://ffmpeg.org/download.html\n"
        "\n"
        "Place ffmpeg.exe and ffprobe.exe in this directory.\n"
        "Music DLP will automatically find them here.\n"
        "\n"
        "Alternatively, install FFmpeg system-wide and add it to your PATH.\n",
        encoding="utf-8"
    )
    print(f"  Created: ffmpeg/PUT_FFMPEG_HERE.txt")

    # Copy README if it exists
    readme_src = PROJECT_DIR / "README.md"
    if readme_src.exists():
        shutil.copy2(readme_src, dist_app_dir / "README.txt")
        print(f"  Copied: README.txt")

    print(f"\nDistribution ready at: {dist_app_dir}")
    print(f"\nNext steps:")
    print(f"  1. Copy ffmpeg.exe + ffprobe.exe into {ffmpeg_dir}")
    print(f"  2. Test: {dist_app_dir / 'MusicDLP.exe'}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build Music DLP executable")
    parser.add_argument("--debug", action="store_true", help="Build with console window")
    parser.add_argument("--clean", action="store_true", help="Clean before building")
    args = parser.parse_args()

    if args.clean:
        clean_build()

    dist_app_dir = build(debug=args.debug)
    create_distribution(dist_app_dir)
