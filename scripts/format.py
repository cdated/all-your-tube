#!/usr/bin/env python3
"""
Format script that runs mdformat, isort, and black on the codebase.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"Running {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(e.stderr)
        return False


def main():
    """Run all formatters"""
    project_root = Path(__file__).parent.parent

    success = True

    # Find Markdown files
    md_files = list(project_root.glob("*.md"))
    docs_md_files = list(project_root.glob("docs/**/*.md"))
    all_md_files = md_files + docs_md_files

    if all_md_files:
        md_file_paths = [str(f) for f in all_md_files]
        success &= run_command(
            ["mdformat"] + md_file_paths, "mdformat (Markdown formatting)"
        )
    else:
        print("No Markdown files found to format")

    # Sort imports
    success &= run_command(["isort", "src/", "scripts/"], "isort (import sorting)")

    # Format Python code
    success &= run_command(["black", "src/", "scripts/"], "black (Python formatting)")

    if success:
        print("\n🎉 All formatting completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some formatting commands failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
