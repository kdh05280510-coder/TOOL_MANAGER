"""카탈로그 DB. database/catalog.py 로 저장 후
  from database.catalog import init_catalog, find_catalog
"""
from database.db import get_connection


def init_catalog():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maker_name TEXT,
            tool_code TEXT NOT NULL,
            tool_name TEXT,
            main_name TEXT,
            sub_code TEXT,
            diameter REAL,
            length REAL,
            effective_len REAL,
            corner_r REAL,
            angle REAL,
            flute_count INTEGER,
            thread_spec TEXT,
            shank_dia REAL,
            total_length REAL,
            thickness REAL,
            neck_dia REAL,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(tool_code, maker_name)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_catalog_code ON catalog(tool_code)")
    conn.commit()
    conn.close()


def find_catalog(tool_code):
    if not tool_code:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM catalog
        WHERE tool_code = ?
        ORDER BY id DESC LIMIT 1
    """, (tool_code.strip(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_catalog(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO catalog (
            maker_name, tool_code, tool_name, main_name, sub_code,
            diameter, length, effective_len, corner_r, angle,
            flute_count, thread_spec, shank_dia, total_length,
            thickness, neck_dia, source
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get("maker_name"), data.get("tool_code"), data.get("tool_name"),
        data.get("main_name"), data.get("sub_code"),
        data.get("diameter"), data.get("length"), data.get("effective_len"),
        data.get("corner_r"), data.get("angle"),
        data.get("flute_count"), data.get("thread_spec"),
        data.get("shank_dia"), data.get("total_length"),
        data.get("thickness"), data.get("neck_dia"),
        data.get("source") or "manual",
    ))
    conn.commit()
    conn.close()
