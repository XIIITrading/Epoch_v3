"""
Git Commit Utility
Stages all changes, commits with auto-generated timestamp, and pushes to remote.

Usage:
    python git_commit.py
    python git_commit.py --no-push
"""

import subprocess
import sys
import argparse
from datetime import datetime


def run_command(command, description, ignore_stderr_patterns=None):
    """Execute a git command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    ignore_stderr_patterns = ignore_stderr_patterns or []

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        print(f">> {description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        stderr_content = e.stderr if e.stderr else ""

        if stderr_content:
            stderr_lines = stderr_content.strip().split('\n')
            is_only_warnings = True

            for line in stderr_lines:
                line = line.strip()
                if not line:
                    continue
                if not any(pattern in line for pattern in ignore_stderr_patterns):
                    if not (line.startswith("hint:") or line.startswith("warning:")):
                        is_only_warnings = False
                        break

            if is_only_warnings:
                print(stderr_content)
                print(f">> {description} completed successfully")
                return True

        print(f"ERROR during {description}:")
        print(stderr_content if stderr_content else str(e))
        return False


def check_git_status():
    """Check if there are changes to commit."""
    try:
        result = subprocess.run(
            "git status --porcelain",
            shell=True,
            text=True,
            capture_output=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Stage, commit, and push changes to git"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Commit but don't push to remote"
    )

    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Update {timestamp}"

    print("\n" + "="*60)
    print("GIT COMMIT UTILITY - XIII Trading LLC")
    print(f"Commit message: {message}")
    print("="*60)

    # Check if there are changes
    if not check_git_status():
        print("\n>> No changes to commit. Working directory is clean.")
        return

    # Stage all changes
    if not run_command(
        'git add -A',
        "Staging all changes",
        ignore_stderr_patterns=["ignored by one of your .gitignore", "LF will be replaced by CRLF", "CRLF will be replaced by LF"]
    ):
        sys.exit(1)

    # Show what will be committed
    run_command("git status --short", "Changes to be committed")

    # Commit changes
    if not run_command(f'git commit -m "{message}"', "Creating commit"):
        sys.exit(1)

    # Push to remote (unless --no-push flag is set)
    if not args.no_push:
        if not run_command("git push", "Pushing to remote"):
            print("\n>> Push failed. You may need to pull first.")
            print("Try running: python git_pull.py")
            sys.exit(1)
    else:
        print("\n>> Changes committed locally (not pushed to remote)")

    print("\n" + "="*60)
    print(">> GIT COMMIT COMPLETED SUCCESSFULLY")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
