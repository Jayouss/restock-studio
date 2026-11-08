#!/usr/bin/env python3
"""Automated consistent SQLite backup using the online sqlite3.backup API."""
from __future__ import annotations

import datetime
from pathlib import Path
import sqlite3
import sys

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
DB_FILE = DATA_DIR / "restock.sqlite3"


def run_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        print(f"Database {DB_FILE} does not exist yet. Skipping backup.")
        return 0

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"restock_backup_{now_str}.sqlite3"

    print(f"Backing up {DB_FILE} to {target}...")
    source = sqlite3.connect(str(DB_FILE))
    dest = sqlite3.connect(str(target))
    with dest:
        source.backup(dest, pages=50)
    source.close()
    dest.close()

    size = target.stat().st_size
    print(f"Backup successful: {target.name} ({size} bytes)")

    # Retain backups for 7 days
    now_ts = datetime.datetime.now().timestamp()
    for item in BACKUP_DIR.glob("restock_backup_*.sqlite3"):
        if now_ts - item.stat().st_mtime > 7 * 86400:
            item.unlink()
            print(f"Pruned backup older than 7 days: {item.name}")

    return 0


if __name__ == "__main__":
    sys.exit(run_backup())
