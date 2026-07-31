"""
기존 엑셀 공구관리대장 → SQLite 이관 스크립트
사용법: python -m database.migrate_excel
"""

import re
from pathlib import Path
import openpyxl
from database.db import get_connection, init_db

# 엑셀 파일 위치 (프로젝트 루트 기준)
EXCEL_PATH = Path(__file__).parent.parent / "공구관리대장_성진세미텍.xlsm"

# 이관할 시트 목록
SHEETS = ["EM(ALU)", "EM(SUS)", "EM(STEEL)", "DR", "SP", "B급 재등록"]


def parse_number(text):
    """문자열에서 숫자만 추출"""
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    # "생크직경:6" → 6
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def get_or_create_maker(cur, name):
    if not name or str(name).strip() in ("", "-"):
        name = "-"
    name = str(name).strip()
    cur.execute("SELECT id FROM makers WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("INSERT INTO makers (name) VALUES (?)", (name,))
    return cur.lastrowid


def get_category_id(cur, main_name, sub_code):
    """대분류명 + 소분류코드로 category_id 찾기"""
    cur.execute("""
        SELECT id FROM categories
        WHERE main_name = ? AND sub_code = ?
    """, (str(main_name).strip(), str(sub_code).strip()))
    row = cur.fetchone()
    if row:
        return row["id"]

    # 소분류만으로 재시도
    cur.execute("SELECT id FROM categories WHERE sub_code = ?", (str(sub_code).strip(),))
    row = cur.fetchone()
    if row:
        return row["id"]

    return None


def migrate():
    if not EXCEL_PATH.exists():
        print(f"❌ 엑셀 파일을 찾을 수 없습니다: {EXCEL_PATH}")
        print("   프로젝트 폴더에 엑셀 파일을 복사한 뒤 다시 실행하세요.")
        return

    init_db()
    conn = get_connection()
    cur = conn.cursor()

    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)

    total_tools = 0
    total_inventory = 0
    skipped = 0

    for sheet_name in SHEETS:
        if sheet_name not in wb.sheetnames:
            print(f"⚠️ 시트 없음: {sheet_name}")
            continue

        ws = wb[sheet_name]
        is_grade_b = (sheet_name == "B급 재등록")
        print(f"\n▶ 시트 처리 중: {sheet_name}")

        rows = list(ws.iter_rows(min_row=2, values_only=True))
        count = 0

        for row in rows:
            if not row or len(row) < 8:
                continue

            # 컬럼 매핑
            # 0:번호, 1:대분류, 2:소분류, 3:제조사, 4:상품명,
            # 5:상품명(부), 6:상품코드, 7:바코드, 8:수량,
            # 9:생크, 10:전체길이
            main_name = row[1]
            sub_code = row[2]
            maker_name = row[3]
            tool_name = row[4]
            sub_name = row[5]
            tool_code = row[6]
            barcode = row[7]
            qty = row[8] if len(row) > 8 else 1
            shank_raw = row[9] if len(row) > 9 else None
            total_len_raw = row[10] if len(row) > 10 else None

            # 필수값 체크
            if not barcode or not str(barcode).strip():
                skipped += 1
                continue

            barcode = str(barcode).strip()
            tool_code = str(tool_code).strip() if tool_code else None
            tool_name = str(tool_name).strip() if tool_name else "공구"
            sub_name = str(sub_name).strip() if sub_name else None

            # 이미 같은 바코드가 있으면 스킵
            cur.execute("SELECT id FROM inventory WHERE barcode = ?", (barcode,))
            if cur.fetchone():
                skipped += 1
                continue

            # 카테고리
            category_id = get_category_id(cur, main_name, sub_code)
            if not category_id:
                print(f"  ⚠ 카테고리 없음: {main_name} / {sub_code} → 스킵")
                skipped += 1
                continue

            # 제조사
            maker_id = get_or_create_maker(cur, maker_name)

            # tools 테이블에 등록 (같은 tool_code가 있으면 재사용)
            tool_id = None
            if tool_code:
                cur.execute("SELECT id FROM tools WHERE tool_code = ? LIMIT 1", (tool_code,))
                existing = cur.fetchone()
                if existing:
                    tool_id = existing["id"]

            if not tool_id:
                shank_dia = parse_number(shank_raw)
                total_length = parse_number(total_len_raw)

                cur.execute("""
                    INSERT INTO tools (
                        category_id, maker_id, tool_code, tool_name,
                        shank_dia, total_length
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (category_id, maker_id, tool_code, tool_name, shank_dia, total_length))
                tool_id = cur.lastrowid
                total_tools += 1

            # inventory 등록
            status = "B급" if is_grade_b else "정상"
            cur.execute("""
                INSERT INTO inventory (
                    tool_id, barcode, sub_name, quantity, status, is_grade_b
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tool_id,
                barcode,
                sub_name,
                int(qty) if qty and str(qty).isdigit() else 1,
                status,
                1 if is_grade_b else 0
            ))
            total_inventory += 1
            count += 1

        print(f"  → {count}건 이관 완료")

    conn.commit()
    conn.close()
    wb.close()

    print("\n" + "=" * 40)
    print(f"✅ 이관 완료")
    print(f"   tools 추가 : {total_tools}개")
    print(f"   inventory  : {total_inventory}개")
    print(f"   스킵       : {skipped}개")
    print("=" * 40)


if __name__ == "__main__":
    migrate()