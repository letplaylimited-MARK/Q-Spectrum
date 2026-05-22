import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Dynamic path resolution: locate Archive/backups relative to script location
BACKUP_DIR = Path(__file__).parent.parent.parent / "Archive" / "backups"


def safe_file_operation(operation, *args, dry_run=False, **kwargs):
    """
    Wrapper for file operations that supports dry-run and automatic backup.

    Args:
        operation: Function to execute (e.g., shutil.copy, os.remove)
        *args: Arguments for the operation
        dry_run: If True, only print what would happen
        **kwargs: Keyword arguments for the operation
    """
    # 1. Identify target files for backup
    # Heuristic: The first argument is usually the source or target path
    target_path = args[0] if args else None

    if not target_path:
        print("❌ Error: No target path identified for backup.")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{os.path.basename(target_path)}_{timestamp}"

    # 2. Dry Run Mode
    if dry_run:
        print(f"👀 [DRY RUN] Would execute: {operation.__name__}")
        print(f"   - Target: {target_path}")
        print(f"   - Backup would be: {backup_path}")
        return True

    # 3. Create Backup (if file exists)
    if os.path.exists(target_path):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if os.path.isdir(target_path):
                shutil.copytree(target_path, str(backup_path))
            else:
                shutil.copy2(target_path, str(backup_path))
            print(f"💾 Backup created: {backup_path}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    # 4. Execute Operation
    try:
        operation(*args, **kwargs)
        print(f"✅ Operation successful: {operation.__name__}")
        return True
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        # 5. Rollback on failure
        if os.path.exists(backup_path):
            print("🔄 Attempting rollback...")
            try:
                if os.path.isdir(backup_path):
                    shutil.rmtree(target_path, ignore_errors=True)
                    shutil.copytree(backup_path, target_path)
                else:
                    shutil.copy2(backup_path, target_path)
                print("✅ Rollback successful.")
            except Exception as re:
                print(f"❌ Rollback failed: {re}")
        return False


# Example Usage
if __name__ == "__main__":
    # Example: Safe delete
    # safe_file_operation(os.remove, "test.txt", dry_run=True)
    print("🛡️ Safe File Operations Module Loaded.")
