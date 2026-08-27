from utils.toolyne_upload import upload_tools
import customtkinter as ctk
from tkinter import filedialog
import tkinter.messagebox as messagebox
from datetime import datetime
from pathlib import Path
import pandas as pd
from database.db import get_connection


class ListWindow(ctk.CTkToplevel):
    def __init__(self, parent, grade=None):
        super().__init__(parent)
        self.grade = grade  # "A", "B", None

        if grade == "A":
            self.title("A급 공구 목록")
        elif grade == "B":
            self.title("B급 공구 목록")
        else:
            self.title("공구 목록")

        self.geometry("1800x650")
        self.minsize(900, 500)
        self.transient(parent)
        self.grab_set()

        self.page_size = 10
        self.current_page = 1
        self.total_count = 0
        self.select_mode = False
        self.checked_ids = set()
        self.row_vars = {}
        self.filter_options = {}

        self.col_widths = [40, 90, 90, 200, 200, 220, 200, 200, 60, 70, 110]
        self.col_titles = [
            "", "대분류", "소분류", "제조사", "상품명", "상품명(부)",
            "바코드", "상품코드", "생크", "전체길이", "등록일",
        ]

        self.create_widgets()
        self.load_data()

    def fmt_num(self, v):
        if v is None or v == "":
            return ""
        try:
            return f"{float(v):.1f}"
        except (TypeError, ValueError):
            return str(v)

    def _filter_text(self, combo, placeholder):
        v = combo.get().strip()
        if not v or v == placeholder:
            return ""
        return v

    def refresh_filter_options(self):
        f_main = self._filter_text(self.combo_f_main, "대분류")
        f_sub = self._filter_text(self.combo_f_sub, "소분류")
        f_maker = self._filter_text(self.combo_f_maker, "제조사")
        f_name = self._filter_text(self.combo_f_name, "상품명")
        f_barcode = self._filter_text(self.combo_f_barcode, "바코드")
        f_code = self._filter_text(self.combo_f_code, "상품코드")

        grade_sql = ""
        if getattr(self, "grade", None) == "A":
            grade_sql = " AND IFNULL(i.is_grade_b, 0) = 0"
        elif getattr(self, "grade", None) == "B":
            grade_sql = " AND IFNULL(i.is_grade_b, 0) = 1"

        def conds(exclude):
            extra = ""
            params = []
            if f_main and exclude != "main":
                extra += " AND IFNULL(c.main_name,'') LIKE ?"
                params.append(f"%{f_main}%")
            if f_sub and exclude != "sub":
                extra += " AND IFNULL(c.sub_code,'') LIKE ?"
                params.append(f"%{f_sub}%")
            if f_maker and exclude != "maker":
                extra += " AND IFNULL(m.name,'') LIKE ?"
                params.append(f"%{f_maker}%")
            if f_name and exclude != "name":
                extra += " AND IFNULL(t.tool_name,'') LIKE ?"
                params.append(f"%{f_name}%")
            if f_barcode and exclude != "barcode":
                extra += " AND IFNULL(i.barcode,'') LIKE ?"
                params.append(f"%{f_barcode}%")
            if f_code and exclude != "code":
                extra += " AND IFNULL(t.tool_code,'') LIKE ?"
                params.append(f"%{f_code}%")
            return extra, params

        base = """
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN makers m ON t.maker_id = m.id
            WHERE 1=1
        """
        conn = get_connection()
        cur = conn.cursor()

        def uniq(col, exclude):
            extra, params = conds(exclude)
            cur.execute(
                f"SELECT DISTINCT {col} {base} {grade_sql} {extra} AND {col} IS NOT NULL ORDER BY {col}",
                tuple(params),
            )
            return [str(r[0]) for r in cur.fetchall() if r[0]]

        self.filter_options = {
            "main": uniq("c.main_name", "main"),
            "sub": uniq("c.sub_code", "sub"),
            "maker": uniq("m.name", "maker"),
            "name": uniq("t.tool_name", "name"),
            "barcode": uniq("i.barcode", "barcode"),
            "code": uniq("t.tool_code", "code"),
        }
        conn.close()

        self.combo_f_main.configure(values=["대분류"] + self.filter_options["main"])
        self.combo_f_sub.configure(values=["소분류"] + self.filter_options["sub"])
        self.combo_f_maker.configure(values=["제조사"] + self.filter_options["maker"])
        self.combo_f_name.configure(values=["상품명"] + self.filter_options["name"])
        self.combo_f_barcode.configure(values=["바코드"] + self.filter_options["barcode"])
        self.combo_f_code.configure(values=["상품코드"] + self.filter_options["code"])
        conn = get_connection()
        cur = conn.cursor()

        grade_sql = ""
        if getattr(self, "grade", None) == "A":
            grade_sql = " AND IFNULL(i.is_grade_b, 0) = 0"
        elif getattr(self, "grade", None) == "B":
            grade_sql = " AND IFNULL(i.is_grade_b, 0) = 1"

        def uniq(sql):
            cur.execute(sql)
            return [str(r[0]) for r in cur.fetchall() if r[0]]

        mains = uniq(f"""
            SELECT DISTINCT c.main_name FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE c.main_name IS NOT NULL {grade_sql}
            ORDER BY c.main_name
        """)
        subs = uniq(f"""
            SELECT DISTINCT c.sub_code FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE c.sub_code IS NOT NULL {grade_sql}
            ORDER BY c.sub_code
        """)
        makers = uniq(f"""
            SELECT DISTINCT m.name FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN makers m ON t.maker_id = m.id
            WHERE m.name IS NOT NULL {grade_sql}
            ORDER BY m.name
        """)
        names = uniq(f"""
            SELECT DISTINCT t.tool_name FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            WHERE t.tool_name IS NOT NULL {grade_sql}
            ORDER BY t.tool_name
        """)
        barcodes = uniq(f"""
            SELECT DISTINCT i.barcode FROM inventory i
            WHERE i.barcode IS NOT NULL {grade_sql}
            ORDER BY i.barcode
        """)
        codes = uniq(f"""
            SELECT DISTINCT t.tool_code FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            WHERE t.tool_code IS NOT NULL {grade_sql}
            ORDER BY t.tool_code
        """)
        conn.close()

        self.combo_f_main.configure(values=["대분류"] + mains)
        self.combo_f_sub.configure(values=["소분류"] + subs)
        self.combo_f_maker.configure(values=["제조사"] + makers)
        self.combo_f_name.configure(values=["상품명"] + names)
        self.combo_f_barcode.configure(values=["바코드"] + barcodes)
        self.combo_f_code.configure(values=["상품코드"] + codes)

    def on_filter_change(self, event=None):
        self.current_page = 1
        self.load_data()

    def reset_filters(self):
        self.combo_f_main.set("대분류")
        self.combo_f_sub.set("소분류")
        self.combo_f_maker.set("제조사")
        self.combo_f_name.set("상품명")
        self.combo_f_barcode.set("바코드")
        self.combo_f_code.set("상품코드")
        if hasattr(self, "search_entry"):
            self.search_entry.delete(0, "end")
        self.refresh_filter_options()
        self.current_page = 1
        self.load_data()

    def create_widgets(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(
            top, text="등록된 공구 목록",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")
        ctk.CTkButton(
            top, text="엑셀 다운로드", width=120, fg_color="#27AE60",
            command=self.on_export_excel
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            top, text="새로고침", width=100, command=self.load_data
        ).pack(side="right", padx=5)

        search = ctk.CTkFrame(self, fg_color="transparent")
        search.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(search, text="검색:").pack(side="left")
        self.search_entry = ctk.CTkEntry(search, width=220)
        self.search_entry.pack(side="left", padx=8)
        self.search_entry.bind("<Return>", lambda e: self.on_search())
        ctk.CTkButton(search, text="검색", width=70, command=self.on_search).pack(side="left")
        ctk.CTkLabel(search, text="  보기:").pack(side="left", padx=(15, 5))
        ctk.CTkButton(search, text="10개", width=55, height=28,
                      command=lambda: self.set_page_size(10)).pack(side="left", padx=2)
        ctk.CTkButton(search, text="50개", width=55, height=28,
                      command=lambda: self.set_page_size(50)).pack(side="left", padx=2)
        ctk.CTkButton(search, text="100개", width=55, height=28,
                      command=lambda: self.set_page_size(100)).pack(side="left", padx=2)

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=15, pady=6)

        self.combo_f_main = ctk.CTkComboBox(filter_frame, width=140, values=["대분류"], state="readonly")
        self.combo_f_sub = ctk.CTkComboBox(filter_frame, width=140, values=["소분류"], state="readonly")
        self.combo_f_maker = ctk.CTkComboBox(filter_frame, width=160, values=["제조사"], state="readonly")
        self.combo_f_name = ctk.CTkComboBox(filter_frame, width=160, values=["상품명"], state="readonly")
        self.combo_f_barcode = ctk.CTkComboBox(filter_frame, width=180, values=["바코드"], state="readonly")
        self.combo_f_code = ctk.CTkComboBox(filter_frame, width=150, values=["상품코드"], state="readonly")

        self.combo_f_main.set("대분류")
        self.combo_f_sub.set("소분류")
        self.combo_f_maker.set("제조사")
        self.combo_f_name.set("상품명")
        self.combo_f_barcode.set("바코드")
        self.combo_f_code.set("상품코드")

        self.combo_f_main.pack(side="left", padx=4)
        self.combo_f_sub.pack(side="left", padx=4)
        self.combo_f_maker.pack(side="left", padx=4)
        self.combo_f_name.pack(side="left", padx=4)
        self.combo_f_barcode.pack(side="left", padx=4)
        self.combo_f_code.pack(side="left", padx=4)

        self.combo_f_main.bind("<Button-1>", lambda e: self.open_filter_list(
            self.combo_f_main, "대분류", self.filter_options.get("main", [])))
        self.combo_f_sub.bind("<Button-1>", lambda e: self.open_filter_list(
            self.combo_f_sub, "소분류", self.filter_options.get("sub", [])))
        self.combo_f_maker.bind("<Button-1>", lambda e: self.open_filter_list(
            self.combo_f_maker, "제조사", self.filter_options.get("maker", [])))
        self.combo_f_name.bind("<Button-1>", lambda e: self.open_filter_list(
            self.combo_f_name, "상품명", self.filter_options.get("name", [])))
        self.combo_f_barcode.bind("<Button-1>", lambda e: self.open_filter_list(
            self.combo_f_barcode, "바코드", self.filter_options.get("barcode", [])))
        self.combo_f_code.bind("<Button-1>", lambda e: self.open_filter_list(
            self.combo_f_code, "상품코드", self.filter_options.get("code", [])))

        ctk.CTkButton(
            filter_frame, text="필터 초기화", width=90, height=28,
            fg_color="#7F8C8D", command=self.reset_filters
        ).pack(side="left", padx=8)

        self.refresh_filter_options()

        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=15, pady=(10, 0))
        for i, (text, w) in enumerate(zip(self.col_titles, self.col_widths)):
            header.grid_columnconfigure(i, minsize=w)
            ctk.CTkLabel(
                header, text=text, width=w, anchor="w",
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=i, padx=2, sticky="w")

        self.scroll = ctk.CTkScrollableFrame(self, height=400)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=8)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=15, pady=10)
        self.btn_prev = ctk.CTkButton(bottom, text="◀ 이전", width=90, command=self.prev_page)
        self.btn_prev.pack(side="left", padx=5)
        self.page_label = ctk.CTkLabel(bottom, text="1 / 1", width=100)
        self.page_label.pack(side="left")
        self.btn_next = ctk.CTkButton(bottom, text="다음 ▶", width=90, command=self.next_page)
        self.btn_next.pack(side="left", padx=5)
        self.count_label = ctk.CTkLabel(bottom, text="총 0건", text_color="gray")
        self.count_label.pack(side="left", padx=15)

        ctk.CTkButton(
            bottom, text="라벨 다운로드", width=120,
            fg_color="#D35400", hover_color="#A04000",
            command=self.on_export_label
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            bottom, text="Toolyne 등록", width=110,
            fg_color="#8E44AD", hover_color="#6C3483",
            command=self.on_toolyne_upload
        ).pack(side="right", padx=5)
        ctk.CTkButton(bottom, text="닫기", width=90, command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(
            bottom, text="전체 삭제", width=90, fg_color="#7B241C",
            command=self.delete_all
        ).pack(side="right", padx=5)

        self.btn_export_selected = ctk.CTkButton(
            bottom, text="선택 항목 엑셀 저장", width=140, fg_color="#27AE60",
            command=lambda: self.export_to_excel(True)
        )
        self.btn_cancel_select = ctk.CTkButton(
            bottom, text="선택 취소", width=90,
            fg_color="#7F8C8D", hover_color="#566573",
            command=self.cancel_select_mode
        )

    def set_page_size(self, size):
        self.page_size = size
        self.current_page = 1
        self.load_data()

    def on_search(self):
        self.current_page = 1
        self.load_data()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        max_page = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        if self.current_page < max_page:
            self.current_page += 1
            self.load_data()

    def load_data(self):
        for inv_id, var in list(self.row_vars.items()):
            try:
                if var.get():
                    self.checked_ids.add(str(inv_id))
                else:
                    self.checked_ids.discard(str(inv_id))
            except Exception:
                pass

        for w in self.scroll.winfo_children():
            w.destroy()
        self.row_vars.clear()

        keyword = self.search_entry.get().strip()
        offset = (self.current_page - 1) * self.page_size

        grade_sql = ""
        if getattr(self, "grade", None) == "A":
            grade_sql = " AND IFNULL(i.is_grade_b, 0) = 0"
        elif getattr(self, "grade", None) == "B":
            grade_sql = " AND IFNULL(i.is_grade_b, 0) = 1"

        f_main = self._filter_text(self.combo_f_main, "대분류")
        f_sub = self._filter_text(self.combo_f_sub, "소분류")
        f_maker = self._filter_text(self.combo_f_maker, "제조사")
        f_name = self._filter_text(self.combo_f_name, "상품명")
        f_barcode = self._filter_text(self.combo_f_barcode, "바코드")
        f_code = self._filter_text(self.combo_f_code, "상품코드")

        extra = ""
        extra_params = []
        if f_main:
            extra += " AND IFNULL(c.main_name,'') LIKE ?"
            extra_params.append(f"%{f_main}%")
        if f_sub:
            extra += " AND IFNULL(c.sub_code,'') LIKE ?"
            extra_params.append(f"%{f_sub}%")
        if f_maker:
            extra += " AND IFNULL(m.name,'') LIKE ?"
            extra_params.append(f"%{f_maker}%")
        if f_name:
            extra += " AND IFNULL(t.tool_name,'') LIKE ?"
            extra_params.append(f"%{f_name}%")
        if f_barcode:
            extra += " AND IFNULL(i.barcode,'') LIKE ?"
            extra_params.append(f"%{f_barcode}%")
        if f_code:
            extra += " AND IFNULL(t.tool_code,'') LIKE ?"
            extra_params.append(f"%{f_code}%")

        conn = get_connection()
        cur = conn.cursor()

        if keyword:
            like = f"%{keyword}%"
            cur.execute(f"""
                SELECT COUNT(*) as cnt
                FROM inventory i
                JOIN tools t ON i.tool_id = t.id
                LEFT JOIN categories c ON t.category_id = c.id
                LEFT JOIN makers m ON t.maker_id = m.id
                WHERE (
                    i.barcode LIKE ? OR i.sub_name LIKE ? OR t.tool_code LIKE ?
                    OR t.tool_name LIKE ? OR IFNULL(c.main_name,'') LIKE ?
                    OR IFNULL(c.sub_code,'') LIKE ?
                )
                {grade_sql} {extra}
            """, (like, like, like, like, like, like) + tuple(extra_params))
        else:
            cur.execute(f"""
                SELECT COUNT(*) as cnt
                FROM inventory i
                JOIN tools t ON i.tool_id = t.id
                LEFT JOIN categories c ON t.category_id = c.id
                LEFT JOIN makers m ON t.maker_id = m.id
                WHERE 1=1 {grade_sql} {extra}
            """, tuple(extra_params))

        self.total_count = cur.fetchone()["cnt"]

        sql = """
            SELECT i.id, c.main_name, c.sub_code, m.name as maker_name,
                   t.tool_name, i.sub_name, i.barcode, t.tool_code,
                   t.shank_dia, t.total_length, i.registered_at
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN makers m ON t.maker_id = m.id
        """

        if keyword:
            like = f"%{keyword}%"
            cur.execute(sql + f"""
                WHERE (
                    i.barcode LIKE ? OR i.sub_name LIKE ? OR t.tool_code LIKE ?
                    OR t.tool_name LIKE ? OR IFNULL(c.main_name,'') LIKE ?
                    OR IFNULL(c.sub_code,'') LIKE ?
                )
                {grade_sql} {extra}
                ORDER BY i.id DESC LIMIT ? OFFSET ?
            """, (like, like, like, like, like, like) + tuple(extra_params) + (self.page_size, offset))
        else:
            cur.execute(
                sql + f" WHERE 1=1 {grade_sql} {extra} ORDER BY i.id DESC LIMIT ? OFFSET ?",
                tuple(extra_params) + (self.page_size, offset)
            )

        rows = cur.fetchall()
        conn.close()

        max_page = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        self.page_label.configure(text=f"{self.current_page} / {max_page}")
        self.count_label.configure(text=f"총 {self.total_count}건")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < max_page else "disabled")

        if self.select_mode:
            self.btn_export_selected.pack(side="right", padx=5)
            self.btn_cancel_select.pack(side="right", padx=5)
        else:
            self.btn_export_selected.pack_forget()
            self.btn_cancel_select.pack_forget()

        if not rows:
            ctk.CTkLabel(self.scroll, text="데이터 없음").pack(pady=20)
            return

        for row in rows:
            inv_id = str(row["id"])
            fr = ctk.CTkFrame(self.scroll, fg_color="transparent")
            fr.pack(fill="x", pady=1)

            for i, w in enumerate(self.col_widths):
                fr.grid_columnconfigure(i, minsize=w)

            if self.select_mode:
                var = ctk.BooleanVar(value=(inv_id in self.checked_ids))
                self.row_vars[inv_id] = var
                ctk.CTkCheckBox(
                    fr, text="", width=self.col_widths[0], variable=var
                ).grid(row=0, column=0, padx=2, sticky="w")
            else:
                ctk.CTkLabel(
                    fr, text="", width=self.col_widths[0]
                ).grid(row=0, column=0, padx=2, sticky="w")

            values = [
                row["main_name"] or "",
                row["sub_code"] or "",
                row["maker_name"] or "",
                row["tool_name"] or "",
                row["sub_name"] or "",
                row["barcode"] or "",
                row["tool_code"] or "",
                self.fmt_num(row["shank_dia"]),
                self.fmt_num(row["total_length"]),
                (row["registered_at"] or "")[:16],
            ]
            for col, text in enumerate(values, start=1):
                ctk.CTkLabel(
                    fr, text=text, width=self.col_widths[col], anchor="w"
                ).grid(row=0, column=col, padx=2, sticky="w")

            ctk.CTkButton(
                fr, text="수정", width=50, height=24, fg_color="#2E86C1",
                command=lambda i=inv_id: self.edit_item(i)
            ).grid(row=0, column=len(self.col_widths), padx=2)
            ctk.CTkButton(
                fr, text="삭제", width=50, height=24, fg_color="#C0392B",
                command=lambda i=inv_id, b=row["barcode"]: self.delete_one(i, b)
            ).grid(row=0, column=len(self.col_widths) + 1, padx=2)

    def collect_checked_ids(self):
        for inv_id, var in list(self.row_vars.items()):
            try:
                if var.get():
                    self.checked_ids.add(str(inv_id))
                else:
                    self.checked_ids.discard(str(inv_id))
            except Exception:
                pass
        return set(self.checked_ids)

    def delete_one(self, inv_id, barcode):
        if not messagebox.askyesno("삭제", f"바코드 [{barcode}] 을(를) 삭제할까요?"):
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM inventory WHERE id = ?", (inv_id,))
            conn.commit()
            conn.close()
            self.load_data()
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def delete_all(self):
        if self.total_count == 0:
            return
        if not messagebox.askyesno("전체 삭제", f"{self.total_count}건 삭제할까요?"):
            return
        if not messagebox.askyesno("최종 확인", "되돌릴 수 없습니다. 계속?"):
            return
        conn = get_connection()
        conn.execute("DELETE FROM inventory")
        conn.commit()
        conn.close()
        self.current_page = 1
        self.load_data()

    def edit_item(self, inv_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id as inv_id, i.barcode, i.sub_name,
                   t.id as tool_id, t.tool_name, t.tool_code,
                   t.shank_dia, t.total_length, t.category_id, t.maker_id,
                   c.main_name, c.sub_code, m.name as maker_name
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN makers m ON t.maker_id = m.id
            WHERE i.id = ?
        """, (inv_id,))
        row = cur.fetchone()

        cur.execute("SELECT DISTINCT main_name FROM categories ORDER BY id")
        main_list = [r["main_name"] for r in cur.fetchall()]

        current_main = (row["main_name"] if row else None) or (main_list[0] if main_list else "")
        cur.execute(
            "SELECT sub_code FROM categories WHERE main_name = ? ORDER BY id",
            (current_main,)
        )
        sub_list = [r["sub_code"] for r in cur.fetchall()]

        cur.execute("SELECT name FROM makers WHERE is_active = 1 ORDER BY name")
        maker_list = [r["name"] for r in cur.fetchall()]
        conn.close()

        if not row:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("공구 수정")
        dialog.geometry("420x560")
        dialog.transient(self)
        dialog.grab_set()

        fr_main = ctk.CTkFrame(dialog, fg_color="transparent")
        fr_main.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(fr_main, text="대분류", width=100, anchor="w").pack(side="left")
        combo_main = ctk.CTkComboBox(fr_main, width=240, values=main_list)
        combo_main.pack(side="left")
        combo_main.set(row["main_name"] or (main_list[0] if main_list else ""))

        fr_sub = ctk.CTkFrame(dialog, fg_color="transparent")
        fr_sub.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(fr_sub, text="소분류", width=100, anchor="w").pack(side="left")
        combo_sub = ctk.CTkComboBox(fr_sub, width=240, values=sub_list)
        combo_sub.pack(side="left")
        combo_sub.set(row["sub_code"] or (sub_list[0] if sub_list else ""))

        fr_maker = ctk.CTkFrame(dialog, fg_color="transparent")
        fr_maker.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(fr_maker, text="제조사", width=100, anchor="w").pack(side="left")
        combo_maker = ctk.CTkComboBox(fr_maker, width=240, values=maker_list)
        combo_maker.pack(side="left")
        combo_maker.set(row["maker_name"] or (maker_list[0] if maker_list else ""))

        def on_main_change(choice):
            conn2 = get_connection()
            cur2 = conn2.cursor()
            cur2.execute(
                "SELECT sub_code FROM categories WHERE main_name = ? ORDER BY id",
                (choice,)
            )
            subs = [r["sub_code"] for r in cur2.fetchall()]
            conn2.close()
            combo_sub.configure(values=subs)
            if subs:
                combo_sub.set(subs[0])

        combo_main.configure(command=on_main_change)

        fields = {}
        items = [
            ("tool_name", "상품명", row["tool_name"] or ""),
            ("sub_name", "상품명(부)", row["sub_name"] or ""),
            ("barcode", "바코드", row["barcode"] or ""),
            ("tool_code", "상품코드", row["tool_code"] or ""),
            ("shank_dia", "생크지름", "" if row["shank_dia"] is None else str(row["shank_dia"])),
            ("total_length", "전체길이", "" if row["total_length"] is None else str(row["total_length"])),
        ]
        for key, label, val in items:
            line = ctk.CTkFrame(dialog, fg_color="transparent")
            line.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(line, text=label, width=100, anchor="w").pack(side="left")
            e = ctk.CTkEntry(line, width=240)
            e.insert(0, val)
            e.pack(side="left")
            fields[key] = e

        def save():
            barcode = fields["barcode"].get().strip()
            main_name = combo_main.get().strip()
            sub_code = combo_sub.get().strip()
            maker_name = combo_maker.get().strip()

            if not barcode:
                messagebox.showwarning("오류", "바코드는 필수입니다.")
                return
            if not main_name or not sub_code:
                messagebox.showwarning("오류", "대분류와 소분류를 선택하세요.")
                return

            for name, key in [("생크지름", "shank_dia"), ("전체길이", "total_length")]:
                v = fields[key].get().strip()
                if v:
                    try:
                        float(v)
                    except ValueError:
                        messagebox.showwarning("오류", f"{name}은 숫자로 입력하세요.")
                        return

            try:
                conn2 = get_connection()
                cur2 = conn2.cursor()
                cur2.execute(
                    "SELECT id FROM inventory WHERE barcode=? AND id!=?",
                    (barcode, row["inv_id"])
                )
                if cur2.fetchone():
                    messagebox.showwarning("오류", "이미 존재하는 바코드입니다.")
                    conn2.close()
                    return

                cur2.execute(
                    "SELECT id FROM categories WHERE main_name=? AND sub_code=?",
                    (main_name, sub_code)
                )
                cat = cur2.fetchone()
                if not cat:
                    messagebox.showerror("오류", "카테고리 정보를 찾을 수 없습니다.")
                    conn2.close()
                    return

                maker_id = None
                if maker_name:
                    cur2.execute("SELECT id FROM makers WHERE name = ?", (maker_name,))
                    mk = cur2.fetchone()
                    if mk:
                        maker_id = mk["id"]

                shank = fields["shank_dia"].get().strip()
                total = fields["total_length"].get().strip()
                cur2.execute("""
                    UPDATE tools
                    SET category_id=?, maker_id=?, tool_name=?, tool_code=?,
                        shank_dia=?, total_length=?
                    WHERE id=?
                """, (
                    cat["id"], maker_id,
                    fields["tool_name"].get().strip(),
                    fields["tool_code"].get().strip() or None,
                    float(shank) if shank else None,
                    float(total) if total else None,
                    row["tool_id"],
                ))
                cur2.execute(
                    "UPDATE inventory SET barcode=?, sub_name=? WHERE id=?",
                    (barcode, fields["sub_name"].get().strip(), row["inv_id"])
                )
                conn2.commit()
                conn2.close()
                messagebox.showinfo("완료", "수정되었습니다.")
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("오류", str(e))

        bf = ctk.CTkFrame(dialog, fg_color="transparent")
        bf.pack(pady=15)
        ctk.CTkButton(bf, text="저장", width=100, command=save).pack(side="left", padx=8)
        ctk.CTkButton(
            bf, text="취소", width=100, fg_color="#7F8C8D", command=dialog.destroy
        ).pack(side="left", padx=8)

    def on_toolyne_upload(self):
        if not self.select_mode:
            self.select_mode = True
            self.load_data()
            messagebox.showinfo(
                "선택 모드",
                "항목을 체크한 뒤\n[Toolyne 등록] 또는 [라벨/엑셀] 버튼을 다시 누르세요."
            )
            return

        selected = self.collect_checked_ids()
        if not selected:
            messagebox.showwarning("알림", "체크된 항목이 없습니다.")
            return
        if not messagebox.askyesno("확인", f"{len(selected)}개를 Toolyne에 등록할까요?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            ph = ",".join("?" * len(selected))
            cur.execute(f"""
                SELECT c.main_name, c.sub_code, m.name as maker_name,
                       t.tool_name, i.sub_name, t.tool_code, i.barcode,
                       t.shank_dia, t.total_length
                FROM inventory i
                JOIN tools t ON i.tool_id = t.id
                LEFT JOIN categories c ON t.category_id = c.id
                LEFT JOIN makers m ON t.maker_id = m.id
                WHERE i.id IN ({ph})
                ORDER BY i.id
            """, tuple(selected))
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            messagebox.showerror("DB 오류", str(e))
            return

        if not rows:
            messagebox.showwarning("알림", "DB에서 데이터를 찾지 못했습니다.")
            return

        try:
            result = upload_tools(rows)
            if isinstance(result, tuple):
                ok, msg = result
            else:
                ok, msg = bool(result), "완료" if result else "실패"
            if ok:
                messagebox.showinfo("완료", msg)
            else:
                messagebox.showerror("실패", msg)
        except Exception as e:
            messagebox.showerror("실행 오류", str(e))

        self.select_mode = False
        self.checked_ids.clear()
        self.row_vars.clear()
        self.load_data()

    def cancel_select_mode(self):
        self.select_mode = False
        self.checked_ids.clear()
        self.row_vars.clear()
        self.load_data()
        messagebox.showinfo("취소", "선택 모드를 취소했습니다.")

    def on_export_excel(self):
        if self.select_mode:
            self.export_to_excel(True)
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("엑셀 다운로드")
        dialog.geometry("300x160")
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="다운로드 범위", font=ctk.CTkFont(weight="bold")).pack(pady=15)

        def do_all():
            dialog.destroy()
            self.select_mode = False
            self.checked_ids.clear()
            self.load_data()
            self.export_to_excel(False)

        def do_sel():
            dialog.destroy()
            self.select_mode = True
            self.checked_ids.clear()
            self.load_data()
            messagebox.showinfo("선택 모드", "체크 후 [선택 항목 엑셀 저장] 또는 [엑셀 다운로드]를 누르세요.")

        ctk.CTkButton(dialog, text="전체 다운로드", width=200, command=do_all).pack(pady=5)
        ctk.CTkButton(dialog, text="선택한 것만", width=200, fg_color="#2980B9", command=do_sel).pack(pady=5)

    def export_to_excel(self, selected_only=False):
        selected = set()
        if selected_only:
            selected = self.collect_checked_ids()
            if not selected:
                messagebox.showwarning("알림", "선택된 항목이 없습니다.")
                return

        conn = get_connection()
        cur = conn.cursor()
        sql = """
            SELECT c.main_name as 대분류, c.sub_code as 소분류, m.name as 제조사,
                   t.tool_name as 상품명, i.sub_name as 상품명_부, i.barcode as 바코드,
                   t.tool_code as 상품코드, t.shank_dia as 생크지름,
                   t.total_length as 전체길이, i.registered_at as 등록일
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN makers m ON t.maker_id = m.id
        """
        if selected_only:
            ph = ",".join("?" * len(selected))
            cur.execute(sql + f" WHERE i.id IN ({ph}) ORDER BY i.id DESC", tuple(selected))
        else:
            grade_sql = ""
            if getattr(self, "grade", None) == "A":
                grade_sql = " WHERE IFNULL(i.is_grade_b, 0) = 0"
            elif getattr(self, "grade", None) == "B":
                grade_sql = " WHERE IFNULL(i.is_grade_b, 0) = 1"
            cur.execute(sql + grade_sql + " ORDER BY i.id DESC")

        rows = cur.fetchall()
        conn.close()
        if not rows:
            messagebox.showinfo("알림", "데이터 없음")
            return

        df = pd.DataFrame([dict(r) for r in rows])
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"공구목록_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if not path:
            return
        df.to_excel(path, index=False)
        messagebox.showinfo("완료", f"저장됨\n{path}")
        self.select_mode = False
        self.checked_ids.clear()
        self.load_data()

    def on_export_label(self):
        if self.select_mode:
            self.export_to_label(True)
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("라벨 다운로드")
        dialog.geometry("320x180")
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="라벨로 내보낼 범위", font=ctk.CTkFont(weight="bold")).pack(pady=15)

        def do_all():
            dialog.destroy()
            self.select_mode = False
            self.checked_ids.clear()
            self.load_data()
            self.export_to_label(False)

        def do_sel():
            dialog.destroy()
            self.select_mode = True
            self.checked_ids.clear()
            self.load_data()
            messagebox.showinfo("선택 모드", "라벨로 만들 항목을 체크한 뒤\n[라벨 다운로드]를 다시 누르세요.")

        ctk.CTkButton(dialog, text="전체 라벨", width=200, command=do_all).pack(pady=5)
        ctk.CTkButton(dialog, text="선택한 것만", width=200, fg_color="#2980B9", command=do_sel).pack(pady=5)

    def extract_flute(self, sub_name):
        import re
        text = str(sub_name or "")
        m = re.search(r"(\d+)\s*날", text)
        if m:
            return m.group(1) + "F"
        return ""

    def export_to_label(self, selected_only=False):
        selected = set()
        if selected_only:
            selected = self.collect_checked_ids()
            if not selected:
                messagebox.showwarning("알림", "선택된 항목이 없습니다.")
                return

        conn = get_connection()
        cur = conn.cursor()
        sql = """
            SELECT i.barcode, t.tool_name, i.sub_name, c.sub_code
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
        """
        if selected_only:
            ph = ",".join("?" * len(selected))
            cur.execute(sql + f" WHERE i.id IN ({ph}) ORDER BY i.id DESC", tuple(selected))
        else:
            grade_sql = ""
            if getattr(self, "grade", None) == "A":
                grade_sql = " WHERE IFNULL(i.is_grade_b, 0) = 0"
            elif getattr(self, "grade", None) == "B":
                grade_sql = " WHERE IFNULL(i.is_grade_b, 0) = 1"
            cur.execute(sql + grade_sql + " ORDER BY i.id DESC")

        rows = cur.fetchall()
        conn.close()
        if not rows:
            messagebox.showinfo("알림", "라벨로 만들 데이터가 없습니다.")
            return

        label_rows = []
        for row in rows:
            barcode = row["barcode"] or ""
            if "-" in barcode:
                no = barcode.split("-")[-1]
            else:
                no = barcode[-2:] if len(barcode) >= 2 else barcode
            flute = self.extract_flute(row["sub_name"])
            sub = row["sub_code"] or ""
            if flute:
                sub = f"{sub} {flute}".strip()
            label_rows.append({
                "No": no,
                "바코드": barcode,
                "상품명": row["tool_name"] or "",
                "소분류": sub,
            })

        df = pd.DataFrame(label_rows)
        path = Path(r"D:\900_공구관리대장\LABEL_PRINT.xlsx")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            df.to_excel(path, index=False)
            messagebox.showinfo("완료", f"{len(label_rows)}개 라벨 저장됨\n{path}")
        except PermissionError:
            messagebox.showerror(
                "저장 실패",
                "라벨 파일이 다른 프로그램에서 열려 있습니다.\n엑셀을 닫고 다시 시도하세요.\n"
                f"{path}"
            )
            return

        self.select_mode = False
        self.checked_ids.clear()
        self.load_data()

    def open_filter_list(self, combo, title, values):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("280x360")
        win.transient(self)
        win.grab_set()

        entry = ctk.CTkEntry(win, placeholder_text="검색")
        entry.pack(fill="x", padx=10, pady=8)

        box = ctk.CTkScrollableFrame(win, height=280)
        box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def render(keyword=""):
            for w in box.winfo_children():
                w.destroy()
            kw = keyword.strip().lower()
            items = [title] + [v for v in values if v and v != title]
            if kw:
                items = [title] + [v for v in items[1:] if kw in v.lower()]
            for v in items:
                ctk.CTkButton(
                    box, text=v, anchor="w",
                    fg_color="transparent", text_color=("black", "white"),
                    command=lambda x=v: pick(x)
                ).pack(fill="x", pady=1)

        def pick(v):
            combo.set(v)
            win.destroy()
            self.current_page = 1
            self.refresh_filter_options()
            self.load_data()

        def on_key(_e):
            render(entry.get())

        entry.bind("<KeyRelease>", on_key)
        render()
        entry.focus()