"""카탈로그 엑셀 가져오기.

등록 화면에서는 상품코드로 공구제원만 채운다.
대분류/소분류/상품명은 회사마다 다르므로 가져와도 화면에 넣지 않는다.

실행:
  python import_catalog.py
  python import_catalog.py D:\\파일.xlsx
"""
import sys
from pathlib import Path

ROOT = Path.cwd()
if not (ROOT / "database" / "db.py").exists():
    ROOT = Path(r"D:\tool_manager")
sys.path.insert(0, str(ROOT))

import pandas as pd
from database.catalog import init_catalog
from database.db import get_connection


# 엑셀 헤더 -> catalog 컬럼 (대소문자/공백 무시)
HEADER_MAP = {
    "상품코드": "tool_code", "공구코드": "tool_code", "코드": "tool_code",
    "tool_code": "tool_code", "품번": "tool_code",
    "제조사": "maker_name", "maker": "maker_name",
    "상품명": "tool_name", "공구명": "tool_name",
    "대분류": "main_name", "소분류": "sub_code",
    "날지름": "diameter", "날지름(d)": "diameter", "d": "diameter", "diameter": "diameter",
    "날장": "length", "날장(l)": "length", "l": "length", "length": "length",
    "유효장": "effective_len", "유효장(h)": "effective_len",
    "코너r": "corner_r", "코너r": "corner_r",
    "각도": "angle", "날끝각도": "angle",
    "날수": "flute_count", "날 수": "flute_count",
    "나사규격": "thread_spec",
    "생크": "shank_dia", "생크지름": "shank_dia",
    "전체길이": "total_length", "온길이": "total_length",
    "날두께": "thickness", "t": "thickness",
    "목직경": "neck_dia",
}


def norm(name):
    return str(name).strip().lower().replace(" ", "")


def to_float(v):
    if v is None or str(v).strip() in ("", "nan", "None"):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def to_int(v):
    f = to_float(v)
    return int(f) if f is not None else None


def pick_sheet(path):
    """상품코드 열이 있는 시트를 고른다. 요약 시트를 건너뛴다."""
    xl = pd.ExcelFile(path)
    preferred = []
    for name in xl.sheet_names:
        df = xl.parse(name, nrows=0)
        cols = [str(c).strip() for c in df.columns]
        mapped = [HEADER_MAP.get(norm(c)) for c in cols]
        if "tool_code" in mapped:
            preferred.append(name)
    if not preferred:
        raise ValueError(
            "엑셀에 '상품코드' 열이 없습니다. "
            f"시트: {', '.join(xl.sheet_names)}"
        )
    for name in preferred:
        if "catalog" in name.lower() or "카탈로그" in name:
            return name
    return preferred[0]


def import_excel(path):
    init_catalog()
    path = Path(path)
    sheet = pick_sheet(path)
    print("시트:", sheet)
    df = pd.read_excel(path, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    colmap = {}
    for c in df.columns:
        key = HEADER_MAP.get(norm(c))
        if key:
            colmap[c] = key

    if "tool_code" not in colmap.values():
        raise ValueError("엑셀에 '상품코드' 열이 없습니다. 첫 행이 제목인지 확인하세요.")

    conn = get_connection()
    cur = conn.cursor()
    ok = skip = fail = 0
    errors = []

    def cell_text(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        s = str(v).strip()
        return None if s.lower() in ("", "nan", "none") else s

    for _, row in df.iterrows():
        data = {}
        for excel_col, db_col in colmap.items():
            data[db_col] = row[excel_col]

        code = cell_text(data.get("tool_code"))
        if not code:
            skip += 1
            continue

        maker = cell_text(data.get("maker_name")) or ""
        vals = {
            "maker_name": maker,
            "tool_code": code,
            "tool_name": cell_text(data.get("tool_name")),
            "main_name": cell_text(data.get("main_name")),
            "sub_code": cell_text(data.get("sub_code")),
            "diameter": to_float(data.get("diameter")),
            "length": to_float(data.get("length")),
            "effective_len": to_float(data.get("effective_len")),
            "corner_r": to_float(data.get("corner_r")),
            "angle": to_float(data.get("angle")),
            "flute_count": to_int(data.get("flute_count")),
            "thread_spec": cell_text(data.get("thread_spec")),
            "shank_dia": to_float(data.get("shank_dia")),
            "total_length": to_float(data.get("total_length")),
            "thickness": to_float(data.get("thickness")),
            "neck_dia": to_float(data.get("neck_dia")),
            "source": path.name,
        }

        try:
            cur.execute(
                """
                UPDATE catalog SET
                    tool_name=?, main_name=?, sub_code=?,
                    diameter=?, length=?, effective_len=?, corner_r=?, angle=?,
                    flute_count=?, thread_spec=?, shank_dia=?, total_length=?,
                    thickness=?, neck_dia=?, source=?
                WHERE tool_code=? AND IFNULL(maker_name,'')=?
                """,
                (
                    vals["tool_name"], vals["main_name"], vals["sub_code"],
                    vals["diameter"], vals["length"], vals["effective_len"],
                    vals["corner_r"], vals["angle"], vals["flute_count"],
                    vals["thread_spec"], vals["shank_dia"], vals["total_length"],
                    vals["thickness"], vals["neck_dia"], vals["source"],
                    code, maker,
                ),
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO catalog (
                        maker_name, tool_code, tool_name, main_name, sub_code,
                        diameter, length, effective_len, corner_r, angle,
                        flute_count, thread_spec, shank_dia, total_length,
                        thickness, neck_dia, source
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        maker, code, vals["tool_name"], vals["main_name"], vals["sub_code"],
                        vals["diameter"], vals["length"], vals["effective_len"],
                        vals["corner_r"], vals["angle"], vals["flute_count"],
                        vals["thread_spec"], vals["shank_dia"], vals["total_length"],
                        vals["thickness"], vals["neck_dia"], vals["source"],
                    ),
                )
            ok += 1
        except Exception as e:
            fail += 1
            if len(errors) < 8:
                errors.append(f"{code}: {e}")

    conn.commit()
    conn.close()
    for msg in errors:
        print("실패:", msg)
    if fail and not errors:
        print("실패 건만 있고 메시지가 없습니다.")
    return ok, skip, fail


def main():
    if len(sys.argv) >= 2:
        path = sys.argv[1]
    else:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                title="카탈로그 엑셀 선택",
                filetypes=[("Excel", "*.xlsx *.xls")],
            )
            root.destroy()
        except Exception:
            path = ""
    if not path:
        print("파일 없음")
        return
    print("파일:", path)
    ok, skip, fail = import_excel(path)
    print(f"저장 {ok} / 스킵 {skip} / 실패 {fail}")


if __name__ == "__main__":
    main()