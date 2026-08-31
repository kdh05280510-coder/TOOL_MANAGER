import sys
from pathlib import Path
ROOT = Path.cwd()
if not (ROOT / "database" / "db.py").exists():
    ROOT = Path(r"D:\tool_manager")
sys.path.insert(0, str(ROOT))
from database.db import get_connection, init_db

ROWS = [
    ("TAP-I", "TAP-I", "TAP(UNC)"),
    ("TAP-I", "TAP-I", "TAP(UNF)"),
    ("TAP-I", "TAP-I", "TAP-H(UNC)"),
    ("TAP-I", "TAP-I", "TAP-H(UNF)"),
    ("TAP-I", "TAP-I", "TAP-NPT"),
    ("TAP-I", "TAP-I", "TAP-PT"),
    ("TAP-I", "TAP-I", "THD"),
]

def main():
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    for code, name, sub in ROWS:
        cur.execute("SELECT id FROM categories WHERE main_code=? AND sub_code=?", (code, sub))
        if cur.fetchone():
            print("있음", name, sub)
            continue
        cur.execute(
            "INSERT INTO categories (main_code, main_name, sub_code) VALUES (?,?,?)",
            (code, name, sub),
        )
        print("추가", name, sub)
    conn.commit()
    cur.execute("SELECT sub_code FROM categories WHERE main_name='TAP-I' ORDER BY id")
    print("TAP-I 소분류:", [r["sub_code"] for r in cur.fetchall()])
    conn.close()

if __name__ == "__main__":
    main()
