import sys
import sqlite3
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


DB_PATH = get_base_dir() / "data" / "tools.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn


def init_db():
    """테이블을 생성합니다. (이미 있으면 무시)"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            main_code   TEXT NOT NULL,
            main_name   TEXT NOT NULL,
            sub_code    TEXT NOT NULL,
            sub_name    TEXT,
            type_name   TEXT,
            UNIQUE(main_code, sub_code)
        )
    """)

    cur.execute("PRAGMA table_info(categories)")
    cat_cols = set()
    for row in cur.fetchall():
        try:
            cat_cols.add(row["name"])
        except Exception:
            cat_cols.add(row[1])
    if "type_name" not in cat_cols:
        cur.execute("ALTER TABLE categories ADD COLUMN type_name TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS makers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            is_active   INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id     INTEGER NOT NULL,
            maker_id        INTEGER,
            tool_code       TEXT,
            tool_name       TEXT NOT NULL,
            diameter        REAL,
            length          REAL,
            effective_len   REAL,
            corner_r        REAL,
            angle           REAL,
            flute_count     INTEGER,
            thread_spec     TEXT,
            shank_dia       REAL,
            total_length    REAL,
            tool_type       TEXT,
            remark          TEXT,
            created_at      TEXT DEFAULT (datetime('now', 'localtime')),

            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (maker_id) REFERENCES makers(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id         INTEGER NOT NULL,
            barcode         TEXT NOT NULL UNIQUE,
            sub_name        TEXT,
            quantity        INTEGER DEFAULT 1,
            status          TEXT DEFAULT '정상',
            is_grade_b      INTEGER DEFAULT 0,
            registered_at   TEXT DEFAULT (datetime('now', 'localtime')),
            registered_by   TEXT,

            FOREIGN KEY (tool_id) REFERENCES tools(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS thread_specs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            standard    TEXT NOT NULL,
            spec        TEXT NOT NULL,
            UNIQUE(standard, spec)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tap_labels (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_code    TEXT NOT NULL,
            pitch       TEXT NOT NULL,
            label       TEXT NOT NULL,
            UNIQUE(sub_code, pitch)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS catalog (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            maker_name      TEXT,
            tool_code       TEXT NOT NULL,
            tool_name       TEXT,
            main_code       TEXT,
            sub_code        TEXT,
            diameter        REAL,
            length          REAL,
            effective_len   REAL,
            corner_r        REAL,
            angle           REAL,
            flute_count     INTEGER,
            thread_spec     TEXT,
            shank_dia       REAL,
            total_length    REAL,
            source          TEXT,
            created_at      TEXT DEFAULT (datetime('now', 'localtime')),
            UNIQUE(maker_name, tool_code)
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_catalog_code ON catalog(tool_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_catalog_maker ON catalog(maker_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_barcode ON inventory(barcode)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tools_tool_code ON tools(tool_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_tool_id ON inventory(tool_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_sub_name ON inventory(sub_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_registered ON inventory(registered_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_categories_sub ON categories(sub_code)")

    conn.commit()
    conn.close()
    print(f"DB 초기화 완료 → {DB_PATH}")


if __name__ == "__main__":
    init_db()
