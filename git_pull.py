"""
Git Pull Utility
Fetches and merges latest changes from remote repository.

Usage:
    python git_pull.py
    python git_pull.py --rebase
    python git_pull.py --force
"""

import subprocess
import sys
import argparse


def run_command(command, description):
    """Execute a git command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    
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
        
        print(f"✓ {description} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error during {description}:")
        print(e.stderr if e.stderr else str(e))
        return False


def check_uncommitted_changes():
    """Check if there are uncommitted changes."""
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


def get_current_branch():
    """Get the name of the current branch."""
    try:
        result = subprocess.run(
            "git branch --show-current",
            shell=True,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Pull latest changes from remote repository"
    )
    parser.add_argument(
        "--rebase",
        action="store_true",
        help="Use rebase instead of merge"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force pull (WARNING: will overwrite local changes)"
    )
    parser.add_argument(
        "--stash",
        action="store_true",
        help="Stash changes before pulling, then pop after"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("GIT PULL UTILITY - XIII Trading LLC")
    print("="*60)
    
    # Get current branch
    current_branch = get_current_branch()
    print(f"\nCurrent branch: {current_branch}")
    
    # Check for uncommitted changes
    has_changes = check_uncommitted_changes()
    
    if has_changes and not args.stash and not args.force:
        print("\n⚠ WARNING: You have uncommitted changes.")
        print("Options:")
        print("  1. Commit your changes first: python git_commit.py \"message\"")
        print("  2. Stash your changes: python git_pull.py --stash")
        print("  3. Force pull (discard changes): python git_pull.py --force")
        
        response = input("\nProceed anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("Pull cancelled.")
            sys.exit(0)
    
    # Stash changes if requested
    stashed = False
    if args.stash and has_changes:
        if run_command("git stash", "Stashing local changes"):
            stashed = True
        else:
            print("Failed to stash changes. Exiting.")
            sys.exit(1)
    
    # Force pull (reset to remote)
    if args.force:
        print("\n⚠ FORCE PULL: This will overwrite local changes!")
        response = input("Are you sure? (yes/N): ").strip().lower()
        if response != 'yes':
            print("Force pull cancelled.")
            sys.exit(0)
        
        if not run_command("git fetch origin", "Fetching from remote"):
            sys.exit(1)
        
        if not run_command(f"git reset --hard origin/{current_branch}", 
                          "Resetting to remote"):
            sys.exit(1)
    
    # Regular pull (with or without rebase)
    else:
        pull_command = "git pull --rebase" if args.rebase else "git pull"
        
        if not run_command(pull_command, "Pulling from remote"):
            print("\n⚠ Pull failed. Possible conflicts or diverged branches.")
            print("You may need to:")
            print("  - Resolve conflicts manually")
            print("  - Use: python git_pull.py --rebase")
            print("  - Use: python git_pull.py --force (WARNING: overwrites local)")
            sys.exit(1)
    
    # Pop stashed changes if we stashed them
    if stashed:
        print("\n" + "="*60)
        print("Restoring stashed changes")
        print("="*60)
        
        if not run_command("git stash pop", "Applying stashed changes"):
            print("\n⚠ Could not apply stashed changes automatically.")
            print("Your changes are still in the stash.")
            print("Run 'git stash list' to see stashed changes")
            print("Run 'git stash pop' to manually apply them")
    
    # Show current status
    run_command("git status", "Current repository status")
    
    print("\n" + "="*60)
    print("✓ GIT PULL COMPLETED SUCCESSFULLY")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()