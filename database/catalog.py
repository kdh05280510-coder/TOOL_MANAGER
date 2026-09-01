"""카탈로그 DB. database/catalog.py 로 저장 후
  from database.catalog import init_catalog, find_catalog, find_catalog_specs
"""
import re
from database.db import get_connection


SPEC_FIELDS = (
    "diameter",
    "length",
    "effective_len",
    "corner_r",
    "angle",
    "flute_count",
    "thread_spec",
    "shank_dia",
    "total_length",
    "thickness",
    "neck_dia",
)


def norm_code(code):
    if not code:
        return ""
    return re.sub(r"[\s\-_/]+", "", str(code)).upper()


def _row_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    try:
        return {k: row[k] for k in row.keys()}
    except Exception:
        return None


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
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    needed = {
        "maker_name": "TEXT",
        "tool_code": "TEXT",
        "tool_name": "TEXT",
        "main_name": "TEXT",
        "sub_code": "TEXT",
        "diameter": "REAL",
        "length": "REAL",
        "effective_len": "REAL",
        "corner_r": "REAL",
        "angle": "REAL",
        "flute_count": "INTEGER",
        "thread_spec": "TEXT",
        "shank_dia": "REAL",
        "total_length": "REAL",
        "thickness": "REAL",
        "neck_dia": "REAL",
        "source": "TEXT",
        "created_at": "TEXT",
    }
    cur.execute("PRAGMA table_info(catalog)")
    have = set()
    for row in cur.fetchall():
        try:
            name = row["name"]
        except Exception:
            name = row[1]
        have.add(name)
    for col, typ in needed.items():
        if col not in have:
            cur.execute(f"ALTER TABLE catalog ADD COLUMN {col} {typ}")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_catalog_code ON catalog(tool_code)")
    conn.commit()
    conn.close()


def catalog_count():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM catalog")
        row = cur.fetchone()
        conn.close()
        if row is None:
            return 0
        if isinstance(row, dict):
            return int(list(row.values())[0])
        return int(row[0])
    except Exception:
        return 0


def find_catalog(tool_code):
    """상품코드로 카탈로그 행 조회. 공백/하이픈 무시."""
    if not tool_code:
        return None
    raw = str(tool_code).strip()
    compact = norm_code(raw)
    if not compact:
        return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM catalog WHERE tool_code = ? ORDER BY id DESC LIMIT 1",
            (raw,),
        )
        row = _row_dict(cur.fetchone())
        if row is None:
            cur.execute(
                """
                SELECT * FROM catalog
                WHERE REPLACE(REPLACE(REPLACE(REPLACE(UPPER(IFNULL(tool_code,'')),' ',''),'-',''),'/',''),'_','') = ?
                ORDER BY id DESC LIMIT 1
                """,
                (compact,),
            )
            row = _row_dict(cur.fetchone())
    except Exception:
        conn.close()
        raise
    conn.close()
    return row


def find_catalog_specs(tool_code):
    """상품코드에 해당하는 공구제원만. 분류/상품명/제조사 없음."""
    row = find_catalog(tool_code)
    if not row:
        return None
    specs = {"tool_code": row.get("tool_code")}
    for key in SPEC_FIELDS:
        val = row.get(key)
        if val is None or val == "":
            continue
        specs[key] = val
    return specs


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
