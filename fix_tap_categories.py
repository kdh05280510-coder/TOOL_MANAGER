"""공구가 가리키는 분류를 TAP-M / TAP-I 로 옮긴 뒤 옛 분류 삭제.
D:\\tool_manager 에서 실행:
  python fix_tap_categories.py
"""
import sys
from pathlib import Path

ROOT = Path.cwd()
if not (ROOT / "database" / "db.py").exists():
    ROOT = Path(r"D:\tool_manager")
sys.path.insert(0, str(ROOT))

from database.db import get_connection, init_db

KEEP = [
    ("TAP-M", "TAP-M", "TAP"),
    ("TAP-M", "TAP-M", "TAP-H"),
    ("TAP-M", "TAP-M", "THD"),
    ("TAP-I", "TAP-I", "TAP"),
    ("TAP-I", "TAP-I", "TAP-H"),
    ("TAP-I", "TAP-I", "TAP-NPT"),
    ("TAP-I", "TAP-I", "TAP-PT"),
    ("TAP-I", "TAP-I", "THD"),
]


def get_id(cur, main_name, sub_code):
    cur.execute(
        "SELECT id FROM categories WHERE main_name=? AND sub_code=?",
        (main_name, sub_code),
    )
    row = cur.fetchone()
    return row["id"] if row else None


def ensure(cur, main_code, main_name, sub_code):
    cur.execute(
        "SELECT id, main_name FROM categories WHERE main_code=? AND sub_code=?",
        (main_code, sub_code),
    )
    row = cur.fetchone()
    if row:
        if row["main_name"] != main_name:
            cur.execute(
                "UPDATE categories SET main_name=? WHERE id=?",
                (main_name, row["id"]),
            )
            print("이름변경:", row["main_name"], "->", main_name, "/", sub_code)
        else:
            print("유지:", main_name, "/", sub_code)
        return
    cur.execute(
        "INSERT INTO categories (main_code, main_name, sub_code) VALUES (?, ?, ?)",
        (main_code, main_name, sub_code),
    )
    print("추가:", main_name, "/", sub_code)


def map_old_to_new(main_name, sub_code):
    main = main_name or ""
    sub = sub_code or "TAP"
    if "인치" in main or main.startswith("TAP-I"):
        new_main = "TAP-I"
    else:
        new_main = "TAP-M"
    if sub in ("TAP-NPT", "NPT"):
        return "TAP-I", "TAP-NPT"
    if sub in ("TAP-PT", "PT"):
        return "TAP-I", "TAP-PT"
    if sub == "THD":
        return new_main, "THD"
    if "TAP-H" in sub or str(sub).endswith("-H"):
        return new_main, "TAP-H"
    return new_main, "TAP"


def main():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    for item in KEEP:
        ensure(cur, *item)
    conn.commit()

    cur.execute("SELECT id, main_name, sub_code FROM categories")
    all_cats = list(cur.fetchall())

    old_ids = []
    for cat in all_cats:
        name = cat["main_name"] or ""
        if name in ("TAP-M", "TAP-I"):
            continue
        if name.startswith("TAP") or "탭" in name:
            old_ids.append(cat)

    for cat in old_ids:
        new_main, new_sub = map_old_to_new(cat["main_name"], cat["sub_code"])
        new_id = get_id(cur, new_main, new_sub)
        if not new_id:
            print("매핑 실패:", cat["main_name"], cat["sub_code"])
            continue
        cur.execute(
            "UPDATE tools SET category_id=? WHERE category_id=?",
            (new_id, cat["id"]),
        )
        print("공구이동:", cat["main_name"], cat["sub_code"], "->", new_main, new_sub, "(", cur.rowcount, "건)")

    conn.commit()

    for cat in old_ids:
        try:
            cur.execute("DELETE FROM categories WHERE id=?", (cat["id"],))
            print("분류삭제:", cat["main_name"], cat["sub_code"])
        except Exception as e:
            print("삭제못함:", cat["main_name"], cat["sub_code"], e)

    conn.commit()
    cur.execute("""
        SELECT main_name, sub_code FROM categories
        WHERE main_name IN ('TAP-M', 'TAP-I')
        ORDER BY main_name, id
    """)
    print("--- 현재 TAP 분류 ---")
    for r in cur.fetchall():
        print(r["main_name"], "/", r["sub_code"])
    conn.close()


if __name__ == "__main__":
    main()
