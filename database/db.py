import sys
import sqlite3
from pathlib import Path

# DB 파일 위치
DB_PATH = Path(__file__).parent.parent / "data" / "tools.db"

def get_base_dir():
    if getattr(sys, "frozen", False):
        # exe로 실행할 때: exe가 있는 폴더
        return Path(sys.executable).parent
    else:
        # python main.py 로 실행할 때
        return Path(__file__).resolve().parent.parent

DB_PATH = get_base_dir() / "data" / "tools.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")      # 읽기/쓰기 동시 성능 향상
    conn.execute("PRAGMA synchronous = NORMAL")    # 안전성과 속도 균형
    conn.execute("PRAGMA temp_store = MEMORY")     # 임시 테이블을 메모리에
    return conn


def init_db():
    """테이블을 생성합니다. (이미 있으면 무시)"""
    conn = get_connection()
    cur = conn.cursor()

    # 1. 카테고리
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            main_code   TEXT NOT NULL,
            main_name   TEXT NOT NULL,
            sub_code    TEXT NOT NULL,
            sub_name    TEXT,
            UNIQUE(main_code, sub_code)
        )
    """)

    # 2. 제조사
    cur.execute("""
        CREATE TABLE IF NOT EXISTS makers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            is_active   INTEGER DEFAULT 1
        )
    """)

    # 3. 공구 마스터
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

    # 4. 재고/등록 이력
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

    # 5. 나사 규격 (선택)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS thread_specs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            standard    TEXT NOT NULL,
            spec        TEXT NOT NULL,
            UNIQUE(standard, spec)
        )
    """)

    # 6. 카탈로그 (제원 전용)
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

    # 인덱스
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_barcode ON inventory(barcode)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tools_tool_code ON tools(tool_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status)")

    # 추가 추천 인덱스
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