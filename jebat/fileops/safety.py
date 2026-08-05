"""Safe file backup manager — creates .bak copies before destructive operations."""

import shutil
import time
from pathlib import Path
from typing import Optional


BACKUP_DIR = Path.home() / ".jebat" / "backups"


class BackupManager:
    """Creates timestamped backups before write/patch operations."""

    def __init__(self, backup_dir: str | Path | None = None) -> None:
        self.backup_dir = Path(backup_dir) if backup_dir else BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, file_path: str | Path) -> str:
        """Create a timestamped backup and return the backup path."""
        src = Path(file_path).resolve()
        if not src.is_file():
            return ""
        ts = str(int(time.time() * 1000))
        backup_name = f"{src.name}.{ts}.bak"
        dest = self.backup_dir / backup_name
        shutil.copy2(str(src), str(dest))
        return str(dest)

    def list_backups(self, file_path: str | Path) -> list[dict]:
        """List backups for a given file, sorted by time descending."""
        src = Path(file_path).resolve()
        pattern = f"{src.name}.*.bak"
        backups = []
        for bak in self.backup_dir.glob(pattern):
            backups.append(
                {
                    "path": str(bak),
                    "timestamp": bak.stat().st_mtime,
                    "size": bak.stat().st_size,
                }
            )
        backups.sort(key=lambda b: b["timestamp"], reverse=True)
        return backups

    def restore(self, backup_path: str, target_path: Optional[str] = None) -> str:
        """Restore a backup to its original location (or a target path)."""
        bak = Path(backup_path)
        if not bak.is_file():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        target = Path(target_path) if target_path else bak.parent / bak.name.split(".")[0]
        shutil.copy2(str(bak), str(target))
        return str(target)