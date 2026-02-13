"""
Git Reset Utility
Reset repository to a specific commit or state.

Usage:
    python git_reset.py --soft             # Undo last commit, keep changes staged
    python git_reset.py --mixed            # Undo last commit, unstage changes
    python git_reset.py --hard             # Undo last commit, discard changes
    python git_reset.py --hard HEAD~3      # Go back 3 commits
    python git_reset.py --hard abc123      # Reset to specific commit
    python git_reset.py --clean            # Remove untracked files
    python git_reset.py --nuke             # DELETE everything local, pull fresh from remote
"""

import subprocess
import sys
import argparse


def run_command(command, description, capture=True, check=True):
    """Execute a git command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            text=True,
            capture_output=capture
        )

        if capture:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

        print(f"✓ {description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Error during {description}:")
        if capture:
            print(e.stderr if e.stderr else str(e))
        return False


def get_commit_log(n=5):
    """Get recent commit history."""
    try:
        result = subprocess.run(
            f"git log --oneline -n {n}",
            shell=True,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def show_status():
    """Show current git status."""
    try:
        result = subprocess.run(
            "git status --short",
            shell=True,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def get_remote_branch():
    """Get the current tracking remote branch."""
    try:
        result = subprocess.run(
            "git rev-parse --abbrev-ref --symbolic-full-name @{u}",
            shell=True,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_current_branch():
    """Get the current branch name."""
    try:
        result = subprocess.run(
            "git rev-parse --abbrev-ref HEAD",
            shell=True,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def nuke_local_and_pull_fresh(force=False):
    """
    Delete ALL local changes and pull fresh from remote.
    This will:
    1. Fetch latest from remote
    2. Reset hard to remote branch
    3. Clean all untracked files and directories (except venv)
    4. Pull latest changes
    """
    print("\n" + "="*60)
    print("GIT NUKE - DELETE EVERYTHING LOCAL & PULL FRESH")
    print("="*60)

    # Get current branch info
    current_branch = get_current_branch()
    remote_branch = get_remote_branch()

    if not current_branch:
        print("\n✗ Error: Could not determine current branch")
        sys.exit(1)

    print(f"\nCurrent branch: {current_branch}")

    if remote_branch:
        print(f"Tracking remote: {remote_branch}")
    else:
        print(f"No upstream branch configured. Will use origin/{current_branch}")
        remote_branch = f"origin/{current_branch}"

    # Show current status
    print("\nCurrent local status:")
    status = show_status()
    if status:
        print(status if status.strip() else "  (working directory clean)")
    else:
        print("  (could not get status)")

    # Show recent commits
    print("\nLocal commits:")
    log = get_commit_log(3)
    if log:
        print(log)

    # Warning message
    print("\n" + "="*60)
    print("⚠⚠⚠ DANGER ZONE ⚠⚠⚠")
    print("="*60)
    print("\nThis operation will PERMANENTLY:")
    print("  1. DELETE all uncommitted changes")
    print("  2. DELETE all untracked files and directories")
    print("  3. Reset to match the remote repository EXACTLY")
    print("  4. Pull the latest changes from remote")
    print("\n  (Note: venv/ directory is preserved)")
    print("\n⚠ THIS CANNOT BE UNDONE! All local work will be LOST!")

    if not force:
        print("\n" + "-"*60)
        response = input("Type 'NUKE' to confirm destruction: ").strip()
        if response != 'NUKE':
            print("\nOperation cancelled. Your local changes are safe.")
            sys.exit(0)

    print("\n" + "="*60)
    print("EXECUTING NUKE SEQUENCE...")
    print("="*60)

    # Step 1: Fetch latest from remote
    if not run_command("git fetch --all", "Fetching latest from remote"):
        print("\n✗ Failed to fetch from remote. Check your network connection.")
        sys.exit(1)

    # Step 2: Reset hard to remote branch
    reset_target = remote_branch
    if not run_command(f"git reset --hard {reset_target}", f"Resetting to {reset_target}"):
        print(f"\n✗ Failed to reset to {reset_target}")
        sys.exit(1)

    # Step 3: Clean all untracked files and directories (excluding venv)
    # Exclude venv directories since Python may be running from there
    # Use check=False to not fail on locked files (common on Windows)
    clean_cmd = "git clean -f -d -x -e venv/ -e .venv/ -e env/ -e .env/"
    run_command(clean_cmd, "Removing untracked files (excluding venv)", check=False)
    print("\nNote: Some files may not be removed if locked (e.g., running processes)")

    # Step 4: Pull latest (in case there are any additional changes)
    run_command("git pull", "Pulling latest changes", check=False)

    # Show final status
    print("\n" + "="*60)
    print("NUKE COMPLETE - Repository Status")
    print("="*60)

    run_command("git status", "Current repository status", check=False)

    print("\nLatest commits after nuke:")
    log = get_commit_log(3)
    if log:
        print(log)

    print("\n" + "="*60)
    print("✓ NUKE COMPLETED - Repository is now in sync with remote")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Reset git repository to a specific state"
    )

    reset_group = parser.add_mutually_exclusive_group()
    reset_group.add_argument(
        "--soft",
        action="store_true",
        help="Reset to HEAD~1, keep changes staged (undo commit)"
    )
    reset_group.add_argument(
        "--mixed",
        action="store_true",
        help="Reset to HEAD~1, unstage changes (undo commit + unstage)"
    )
    reset_group.add_argument(
        "--hard",
        action="store_true",
        help="Reset to HEAD~1, discard all changes (WARNING: destructive)"
    )

    parser.add_argument(
        "commit",
        nargs="?",
        default="HEAD~1",
        help="Commit to reset to (default: HEAD~1). Use HEAD~N for N commits back"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove all untracked files and directories (WARNING: destructive)"
    )
    parser.add_argument(
        "--nuke",
        action="store_true",
        help="DELETE all local changes and pull fresh from remote (WARNING: VERY destructive)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    # Handle NUKE operation (delete everything local, pull fresh)
    if args.nuke:
        nuke_local_and_pull_fresh(args.force)
        return

    print("\n" + "="*60)
    print("GIT RESET UTILITY - XIII Trading LLC")
    print("="*60)

    # Show current status
    print("\nCurrent status:")
    status = show_status()
    if status:
        print(status if status.strip() else "  (working directory clean)")

    # Show recent commits
    print("\nRecent commits:")
    log = get_commit_log(5)
    if log:
        print(log)

    # Determine reset type
    if args.soft:
        reset_type = "soft"
        warning = "This will undo the last commit but keep your changes staged."
    elif args.mixed:
        reset_type = "mixed"
        warning = "This will undo the last commit and unstage your changes."
    elif args.hard:
        reset_type = "hard"
        warning = "⚠ WARNING: This will PERMANENTLY DELETE all uncommitted changes!"
    else:
        reset_type = "mixed"  # default
        warning = "This will undo the last commit and unstage your changes."

    # Handle clean operation
    if args.clean:
        print("\n" + "="*60)
        print("CLEAN UNTRACKED FILES")
        print("="*60)
        print("\n⚠ WARNING: This will permanently delete all untracked files!")

        if not args.force:
            # Show what would be deleted
            run_command("git clean -n -d", "Files that would be deleted")

            response = input("\nProceed with deletion? (yes/N): ").strip().lower()
            if response != 'yes':
                print("Clean cancelled.")
                sys.exit(0)

        if not run_command("git clean -f -d", "Removing untracked files"):
            sys.exit(1)

    # Perform reset
    print("\n" + "="*60)
    print(f"GIT RESET --{reset_type.upper()} {args.commit}")
    print("="*60)
    print(f"\n{warning}")

    if not args.force and reset_type == "hard":
        print("\n⚠ THIS OPERATION CANNOT BE UNDONE!")
        response = input("\nAre you absolutely sure? Type 'yes' to confirm: ").strip().lower()
        if response != 'yes':
            print("Reset cancelled.")
            sys.exit(0)
    elif not args.force:
        response = input("\nProceed? (y/N): ").strip().lower()
        if response != 'y':
            print("Reset cancelled.")
            sys.exit(0)

    # Execute reset
    reset_command = f"git reset --{reset_type} {args.commit}"

    if not run_command(reset_command, f"Resetting to {args.commit}"):
        print("\n⚠ Reset failed. Check that the commit exists.")
        print("Use 'git log' to see available commits")
        sys.exit(1)

    # Show new status
    print("\n" + "="*60)
    print("New status after reset:")
    print("="*60)
    run_command("git status", "Current repository status")

    # Show what to do next
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)

    if reset_type == "soft":
        print("\n✓ Changes are still staged. You can:")
        print("  - Modify files and recommit")
        print("  - Run: python git_commit.py \"new message\"")
    elif reset_type == "mixed":
        print("\n✓ Changes are unstaged. You can:")
        print("  - Modify files as needed")
        print("  - Stage and commit: python git_commit.py \"message\"")
    else:  # hard
        print("\n✓ Repository reset complete.")
        if args.commit != "HEAD~1":
            print(f"  - You may need to force push: git push --force")
            print("  ⚠ Be careful with force push on shared branches!")

    print("\n" + "="*60)
    print("✓ GIT RESET COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("\nGit Reset Utility")
        print("\nUsage examples:")
        print("  python git_reset.py --soft              # Undo commit, keep changes staged")
        print("  python git_reset.py --mixed             # Undo commit, unstage changes")
        print("  python git_reset.py --hard              # Undo commit, discard changes")
        print("  python git_reset.py --hard HEAD~3       # Go back 3 commits")
        print("  python git_reset.py --hard abc123       # Reset to commit abc123")
        print("  python git_reset.py --clean             # Remove untracked files")
        print("  python git_reset.py --nuke              # DELETE everything local, pull fresh")
        print("  python git_reset.py --nuke --force      # Same as above, skip confirmation")
        print("\nFor more help: python git_reset.py --help")
        sys.exit(0)

    main()
