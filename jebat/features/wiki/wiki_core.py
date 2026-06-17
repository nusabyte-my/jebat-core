"""Wiki / Knowledge Base — SQLite FTS5-backed CRUD and search.

Stores markdown pages with full-text search, wikilinks, and backlinks.
Data lives in .jebat/wiki/ (pages as .md files, index as SQLite DB).

Features:
  - create / read / update / delete pages
  - FTS5 full-text search
  - [[wikilink]] parsing with automatic backlinks
  - list with optional prefix filter
  - stats (page count, total size)
"""

import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


WIKI_DIR = Path.home() / ".jebat" / "wiki"
PAGES_DIR = WIKI_DIR / "pages"
DB_PATH = WIKI_DIR / "index.db"

# Regex for [[wikilinks]]
WIKILINK_RE = re.compile(r"\[\[([^]]+)\]\]")


class WikiStore:
    """SQLite FTS5-backed wiki with markdown file storage."""

    def __init__(self, wiki_dir: Optional[Path] = None) -> None:
        base = Path(wiki_dir) if wiki_dir else WIKI_DIR
        self._pages_dir = base / "pages"
        self._db_path = base / "index.db"
        self._pages_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                title TEXT PRIMARY KEY,
                filename TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL DEFAULT '',
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                title, content, content='pages', content_rowid='rowid'
            )
        """)
        # Triggers to keep FTS in sync
        conn.executescript("""
            CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
                INSERT INTO pages_fts(rowid, title, content)
                VALUES (new.rowid, new.title, new.content);
            END;
            CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
                INSERT INTO pages_fts(pages_fts, rowid, title, content)
                VALUES ('delete', old.rowid, old.title, old.content);
            END;
            CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
                INSERT INTO pages_fts(pages_fts, rowid, title, content)
                VALUES ('delete', old.rowid, old.title, old.content);
                INSERT INTO pages_fts(rowid, title, content)
                VALUES (new.rowid, new.title, new.content);
            END;
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backlinks (
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                PRIMARY KEY (source, target)
            )
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _slug(self, title: str) -> str:
        """Convert a title to a safe filename."""
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", title.lower().strip())
        slug = re.sub(r"-{2,}", "-", slug).strip("-")
        return slug or "untitled"

    def _filename(self, title: str) -> str:
        return f"{self._slug(title)}.md"

    def _file_path(self, title: str) -> Path:
        return self._pages_dir / self._filename(title)

    def _extract_links(self, content: str) -> list[str]:
        """Extract [[wikilink]] targets from content."""
        return WIKILINK_RE.findall(content)

    def _update_backlinks(self, source: str, content: str) -> None:
        """Rebuild backlinks for a page."""
        conn = self._get_conn()
        # Remove old backlinks from this source
        conn.execute("DELETE FROM backlinks WHERE source = ?", (source,))
        # Insert new
        targets = self._extract_links(content)
        for target in targets:
            conn.execute(
                "INSERT OR IGNORE INTO backlinks (source, target) VALUES (?, ?)",
                (source, target),
            )
        conn.commit()
        conn.close()

    # --- CRUD ---

    def create_page(self, title: str, content: str) -> dict[str, Any]:
        """Create a new wiki page. Returns error if title exists."""
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT title FROM pages WHERE title = ?", (title,)
        ).fetchone()
        if existing:
            conn.close()
            return {"error": f"Page already exists: {title}"}

        filename = self._filename(title)
        file_path = self._pages_dir / filename
        now = time.time()

        try:
            file_path.write_text(content, encoding="utf-8")
        except Exception as e:
            conn.close()
            return {"error": f"Write failed: {e}"}

        size = len(content.encode("utf-8"))
        conn.execute(
            """INSERT INTO pages (title, filename, content, size_bytes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, filename, content, size, now, now),
        )
        conn.commit()
        conn.close()

        self._update_backlinks(title, content)

        return {
            "title": title,
            "filename": filename,
            "path": str(file_path),
            "size_bytes": size,
            "created": True,
        }

    def read_page(self, title: str) -> dict[str, Any]:
        """Read a wiki page by title."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT title, filename, size_bytes, created_at, updated_at FROM pages WHERE title = ?",
            (title,),
        ).fetchone()
        conn.close()

        if not row:
            return {"error": f"Page not found: {title}"}

        file_path = self._pages_dir / row[1]
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return {"error": f"File missing for page: {title}"}

        return {
            "title": row[0],
            "filename": row[1],
            "size_bytes": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "content": content,
        }

    def update_page(self, title: str, content: str) -> dict[str, Any]:
        """Update an existing page's content."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT title, filename FROM pages WHERE title = ?", (title,)
        ).fetchone()
        if not row:
            conn.close()
            return {"error": f"Page not found: {title}"}

        file_path = self._pages_dir / row[1]
        now = time.time()
        size = len(content.encode("utf-8"))

        try:
            file_path.write_text(content, encoding="utf-8")
        except Exception as e:
            conn.close()
            return {"error": f"Write failed: {e}"}

        conn.execute(
            "UPDATE pages SET size_bytes = ?, updated_at = ?, content = ? WHERE title = ?",
            (size, now, content, title),
        )
        conn.commit()
        conn.close()

        self._update_backlinks(title, content)

        return {
            "title": title,
            "filename": row[1],
            "path": str(file_path),
            "size_bytes": size,
            "updated": True,
        }

    def delete_page(self, title: str) -> dict[str, Any]:
        """Soft-delete a page (mark as deleted, keep file)."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT title, filename FROM pages WHERE title = ?", (title,)
        ).fetchone()
        if not row:
            conn.close()
            return {"error": f"Page not found: {title}"}

        conn.execute("DELETE FROM pages WHERE title = ?", (title,))
        conn.execute("DELETE FROM backlinks WHERE source = ?", (title,))
        conn.commit()
        conn.close()

        # Don't delete the .md file — soft delete
        return {"title": title, "deleted": True}

    def list_pages(self, prefix: str = "") -> dict[str, Any]:
        """List all page titles, optionally filtered by prefix."""
        conn = self._get_conn()
        if prefix:
            rows = conn.execute(
                "SELECT title, filename, size_bytes, updated_at FROM pages WHERE title LIKE ? ORDER BY title",
                (f"{prefix}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT title, filename, size_bytes, updated_at FROM pages ORDER BY title"
            ).fetchall()
        conn.close()

        return {
            "pages": [
                {
                    "title": r[0],
                    "filename": r[1],
                    "size_bytes": r[2],
                    "updated_at": r[3],
                }
                for r in rows
            ],
            "count": len(rows),
        }

    def get_backlinks(self, title: str) -> dict[str, Any]:
        """Get all pages that link to this title."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT source FROM backlinks WHERE target = ? ORDER BY source",
            (title,),
        ).fetchall()
        conn.close()
        return {"title": title, "backlinks": [r[0] for r in rows]}

    # --- Search ---

    def search(self, query: str, top_k: int = 10) -> dict[str, Any]:
        """FTS5 full-text search across all pages."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT p.title, p.filename, snippet(pages_fts, 1, '<b>', '</b>', '...', 32),
                          p.size_bytes, p.updated_at, rank
                   FROM pages_fts
                   JOIN pages p ON pages_fts.rowid = p.rowid
                   WHERE pages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, top_k),
            ).fetchall()
        except sqlite3.OperationalError:
            conn.close()
            return {"matches": [], "query": query, "error": "Invalid search query"}

        conn.close()
        return {
            "matches": [
                {
                    "title": r[0],
                    "filename": r[1],
                    "snippet": r[2],
                    "size_bytes": r[3],
                    "updated_at": r[4],
                }
                for r in rows
            ],
            "query": query,
            "count": len(rows),
        }

    def get_stats(self) -> dict[str, Any]:
        """Return wiki stats: page count, total size, last updated."""
        conn = self._get_conn()
        count_row = conn.execute("SELECT COUNT(*) FROM pages").fetchone()
        size_row = conn.execute("SELECT COALESCE(SUM(size_bytes), 0) FROM pages").fetchone()
        last_row = conn.execute(
            "SELECT title, updated_at FROM pages ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        backlink_count = conn.execute(
            "SELECT COUNT(*) FROM backlinks"
        ).fetchone()
        conn.close()

        return {
            "page_count": count_row[0],
            "total_size_bytes": size_row[0],
            "last_updated": {
                "title": last_row[0],
                "updated_at": last_row[1],
            } if last_row else None,
            "backlink_count": backlink_count[0],
        }