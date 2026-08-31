"""
한 번만 실행:
  cd D:\\tool_manager
  python optimize_db.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# 프로젝트 루트에서 실행한다고 가정
if (Path.cwd() / "database" / "db.py").exists():
    sys.path.insert(0, str(Path.cwd()))
else:
    sys.path.insert(0, str(ROOT))

from database.db import get_connection


def optimize():
    conn = get_connection()
    cur = conn.cursor()
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_inv_barcode ON inventory(barcode)",
        "CREATE INDEX IF NOT EXISTS idx_inv_tool_id ON inventory(tool_id)",
        "CREATE INDEX IF NOT EXISTS idx_inv_grade ON inventory(is_grade_b)",
        "CREATE INDEX IF NOT EXISTS idx_inv_registered ON inventory(registered_at)",
        "CREATE INDEX IF NOT EXISTS idx_tools_code ON tools(tool_code)",
        "CREATE INDEX IF NOT EXISTS idx_tools_cat ON tools(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_tools_maker ON tools(maker_id)",
        "CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(tool_name)",
        "CREATE INDEX IF NOT EXISTS idx_cat_main_sub ON categories(main_name, sub_code)",
        "CREATE INDEX IF NOT EXISTS idx_makers_name ON makers(name)",
        "ANALYZE",
    ]
    for sql in statements:
        cur.execute(sql)
        print("OK:", sql)
    conn.commit()
    conn.close()
    print("인덱스 생성 완료")


if __name__ == "__main__":
    optimize()
