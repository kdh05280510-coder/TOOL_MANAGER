# D:\tool_manager\ensure_tap_labels.py
from database.db import get_connection, init_db

ROWS = [
    ("TAP", "coarse", "보통나사 탭"),
    ("TAP", "fine", "가는나사 탭"),
    ("TAP-H", "coarse", "보통나사 헬리탭"),
    ("TAP-H", "fine", "가는나사 헬리탭"),
    ("THD", "coarse", "보통나사 쓰레드"),
    ("THD", "fine", "가는나사 쓰레드"),
    ("THD", "any", "쓰레드"),
    ("THD(UNC)", "any", "UNC 쓰레드"),
    ("THD(UNC)", "coarse", "UNC 쓰레드"),
    ("THD(UNC)", "fine", "UNC 쓰레드"),
    ("THD(UNF)", "any", "UNF 쓰레드"),
    ("THD(UNF)", "coarse", "UNF 쓰레드"),
    ("THD(UNF)", "fine", "UNF 쓰레드"),
    ("TAP(UNC)", "any", "UNC탭"),
    ("TAP(UNC)", "coarse", "UNC탭"),
    ("TAP(UNC)", "fine", "UNC탭"),
    ("TAP(UNF)", "any", "UNF탭"),
    ("TAP(UNF)", "coarse", "UNF탭"),
    ("TAP(UNF)", "fine", "UNF탭"),
    ("TAP-H(UNC)", "any", "헬리탭"),
    ("TAP-H(UNC)", "coarse", "헬리탭"),
    ("TAP-H(UNC)", "fine", "헬리탭"),
    ("TAP-H(UNF)", "any", "헬리탭"),
    ("TAP-H(UNF)", "coarse", "헬리탭"),
    ("TAP-H(UNF)", "fine", "헬리탭"),
    ("TAP-PT", "any", "PT탭"),
    ("TAP-PT", "coarse", "PT탭"),
    ("TAP-PT", "fine", "PT탭"),
    ("TAP-NPT", "any", "NPT탭"),
    ("TAP-NPT", "coarse", "NPT탭"),
    ("TAP-NPT", "fine", "NPT탭"),
]


def main():
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR IGNORE INTO tap_labels (sub_code, pitch, label) VALUES (?, ?, ?)",
        ROWS,
    )
    conn.commit()
    print("tap_labels 준비 완료")
    cur.execute("SELECT sub_code, pitch, label FROM tap_labels ORDER BY sub_code, pitch")
    for r in cur.fetchall():
        print(f"  {r['sub_code']} / {r['pitch']} → {r['label']}")
    conn.close()


if __name__ == "__main__":
    main()
