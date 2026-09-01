import sys
from pathlib import Path
ROOT = Path.cwd()
if not (ROOT / "database" / "db.py").exists():
    ROOT = Path(r"D:\tool_manager")
sys.path.insert(0, str(ROOT))
from database.db import get_connection, init_db

# 지울 것
DELETE_LIST = [
    ("SP(특수)", "THD(UNC)"),
    ("SP(특수)", "THD"),
    ("SP(특수)", "TAP-H(UNF)"),
    ("TAP-I", "TAP"),
    ("TAP-I", "THD"),
    ("TAP-I", "TAP-H"),
]

# 공구는 여기로 이동
MOVE_TO = {
    ("SP(특수)", "THD(UNC)"): ("TAP-I", "TAP(UNC)"),
    ("SP(특수)", "THD"): ("TAP-M", "THD"),
    ("SP(특수)", "TAP-H(UNF)"): ("TAP-I", "TAP-H(UNF)"),
    ("TAP-I", "TAP"): ("TAP-I", "TAP(UNC)"),
    ("TAP-I", "THD"): ("TAP-M", "THD"),
    ("TAP-I", "TAP-H"): ("TAP-I", "TAP-H(UNC)"),
}


def cat_id(cur, main, sub):
    cur.execute(
        "SELECT id FROM categories WHERE main_name=? AND sub_code=?",
        (main, sub),
    )
    row = cur.fetchone()
    return row["id"] if row else None


def main():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    for main, sub in DELETE_LIST:
        old_id = cat_id(cur, main, sub)
        if not old_id:
            print("없음:", main, sub)
            continue
        dest = MOVE_TO.get((main, sub))
        if dest:
            new_id = cat_id(cur, dest[0], dest[1])
            if new_id:
                cur.execute(
                    "UPDATE tools SET category_id=? WHERE category_id=?",
                    (new_id, old_id),
                )
                print("공구이동:", main, sub, "->", dest[0], dest[1], cur.rowcount, "건")
        try:
            cur.execute("DELETE FROM categories WHERE id=?", (old_id,))
            print("삭제:", main, sub)
        except Exception as e:
            print("삭제실패:", main, sub, e)

    conn.commit()
    cur.execute("""
        SELECT main_name, sub_code FROM categories
        WHERE main_name IN ('SP(특수)','TAP-I','TAP-M')
        ORDER BY main_name, id
    """)
    print("--- 남은 분류 ---")
    for r in cur.fetchall():
        print(r["main_name"], "/", r["sub_code"])
    conn.close()


if __name__ == "__main__":
    main()
