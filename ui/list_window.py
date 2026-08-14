from utils.toolyne_upload import upload_tools
import customtkinter as ctk
from tkinter import filedialog
import tkinter.messagebox as messagebox
from datetime import datetime
import pandas as pd
from database.db import get_connection


class ListWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("공구 목록")
        self.geometry("1800x650")
        self.minsize(900, 500)
        self.transient(parent)
        self.grab_set()

        self.page_size = 50
        self.current_page = 1
        self.total_count = 0
        self.select_mode = False
        self.checked_ids = set()
        self.row_vars = {}

        self.col_widths = [40, 90, 90, 200, 200, 220, 200, 200, 60, 70, 110]
        self.col_titles = ["", "대분류", "소분류", "제조사", "상품명", "상품명(부)",
                           "바코드", "상품코드", "생크", "전체길이", "등록일"]

        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(top, text="등록된 공구 목록",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="엑셀 다운로드", width=120, fg_color="#27AE60",
                      command=self.on_export_excel).pack(side="right", padx=5)
        ctk.CTkButton(top, text="새로고침", width=100,
                      command=self.load_data).pack(side="right", padx=5)

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

        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=15, pady=(10, 0))
        for i, (text, w) in enumerate(zip(self.col_titles, self.col_widths)):
            header.grid_columnconfigure(i, minsize=w)
            ctk.CTkLabel(header, text=text, width=w, anchor="w",
                         font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, padx=2, sticky="w")

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

        ctk.CTkButton(bottom, text="Toolyne 등록", width=110, fg_color="#8E44AD", hover_color="#6C3483", command=self.on_toolyne_upload).pack(side="right", padx=5)
        ctk.CTkButton(bottom, text="닫기", width=90, command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(bottom, text="전체 삭제", width=90, fg_color="#7B241C",
                      command=self.delete_all).pack(side="right", padx=5)
        self.btn_export_selected = ctk.CTkButton(
            bottom, text="선택 항목 엑셀 저장", width=140, fg_color="#27AE60",
            command=lambda: self.export_to_excel(True)
        )
        self.btn_cancel_select = ctk.CTkButton(
            bottom, text="Toolyne 등록 취소", width=120,
            fg_color="#7F8C8D", hover_color="#566573",
            command=self.cancel_select_mode
        )
        # 처음에는 숨김 (선택 모드일 때만 표시)

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
        for w in self.scroll.winfo_children():
            w.destroy()
        self.row_vars.clear()

        keyword = self.search_entry.get().strip()
        offset = (self.current_page - 1) * self.page_size

        conn = get_connection()
        cur = conn.cursor()

        if keyword:
            like = f"%{keyword}%"
            cur.execute("""
                SELECT COUNT(*) as cnt FROM inventory i
                JOIN tools t ON i.tool_id = t.id
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE i.barcode LIKE ? OR i.sub_name LIKE ? OR t.tool_code LIKE ?
                   OR t.tool_name LIKE ? OR IFNULL(c.main_name,'') LIKE ?
                   OR IFNULL(c.sub_code,'') LIKE ?
            """, (like, like, like, like, like, like))
        else:
            cur.execute("SELECT COUNT(*) as cnt FROM inventory")

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
            cur.execute(sql + """
                WHERE i.barcode LIKE ? OR i.sub_name LIKE ? OR t.tool_code LIKE ?
                   OR t.tool_name LIKE ? OR IFNULL(c.main_name,'') LIKE ?
                   OR IFNULL(c.sub_code,'') LIKE ?
                ORDER BY i.id DESC LIMIT ? OFFSET ?
            """, (like, like, like, like, like, like, self.page_size, offset))
        else:
            cur.execute(
                sql + " ORDER BY i.id DESC LIMIT ? OFFSET ?",
                (self.page_size, offset)
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

            # 반드시 이 줄이 먼저
            fr = ctk.CTkFrame(self.scroll, fg_color="transparent")
            fr.pack(fill="x", pady=1)

            for i, w in enumerate(self.col_widths):
                fr.grid_columnconfigure(i, minsize=w)

            if self.select_mode:
                var = ctk.BooleanVar(value=False)
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
                command=lambda i=inv_id, b=row["barcode"]: self.delete_one(i, b),
                ).grid(row=0, column=len(self.col_widths) + 1, padx=2)

    def fmt_num(self, v):

        if v is None or v == "":
            return ""
        try:
            return f"{float(v):.1f}"
        except Exception:
            return str(v)

    
        for w in self.scroll.winfo_children():
            w.destroy()
        self.row_vars.clear()

        keyword = self.search_entry.get().strip()
        offset = (self.current_page - 1) * self.page_size
        conn = get_connection()
        cur = conn.cursor()

        if keyword:
            like = f"%{keyword}%"
            cur.execute("""
                SELECT COUNT(*) as cnt FROM inventory i
                JOIN tools t ON i.tool_id = t.id
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE i.barcode LIKE ? OR i.sub_name LIKE ? OR t.tool_code LIKE ?
                   OR t.tool_name LIKE ? OR IFNULL(c.main_name,'') LIKE ?
                   OR IFNULL(c.sub_code,'') LIKE ?
            """, (like, like, like, like, like, like))
        else:
            cur.execute("SELECT COUNT(*) as cnt FROM inventory")
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
            cur.execute(sql + """
                WHERE i.barcode LIKE ? OR i.sub_name LIKE ? OR t.tool_code LIKE ?
                   OR t.tool_name LIKE ? OR IFNULL(c.main_name,'') LIKE ?
                   OR IFNULL(c.sub_code,'') LIKE ?
                ORDER BY i.id DESC LIMIT ? OFFSET ?
            """, (like, like, like, like, like, like, self.page_size, offset))
        else:
            cur.execute(sql + " ORDER BY i.id DESC LIMIT ? OFFSET ?",
                        (self.page_size, offset))

        rows = cur.fetchall()
        conn.close()

        max_page = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        self.page_label.configure(text=f"{self.current_page} / {max_page}")
        self.count_label.configure(text=f"총 {self.total_count}건")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < max_page else "disabled")

        if self.select_mode:
                var = ctk.BooleanVar(value=False)
                self.row_vars[inv_id] = var
                ctk.CTkCheckBox(
                    fr, text="", width=self.col_widths[0], variable=var
                ).grid(row=0, column=0, padx=2, sticky="w")
        else:
                ctk.CTkLabel(fr, text="", width=self.col_widths[0]).grid(
                    row=0, column=0, padx=2, sticky="w"
                )

        if not rows:
            ctk.CTkLabel(self.scroll, text="데이터 없음").pack(pady=20)
            return

        for row in rows:
            inv_id = str(row["id"])

            fr = ctk.CTkFrame(self.scroll, fg_color="transparent")
            fr.pack(fill="x", pady=1)

            for i, w in enumerate(self.col_widths):
                fr.grid_columnconfigure(i, minsize=w)

            # 0열: 체크박스 또는 빈칸
            if self.select_mode:
                var = ctk.BooleanVar(value=False)
                self.row_vars[inv_id] = var
                ctk.CTkCheckBox(
                    fr, text="", width=self.col_widths[0], variable=var
                ).grid(row=0, column=0, padx=2, sticky="w")
            else:
                ctk.CTkLabel(
                    fr, text="", width=self.col_widths[0]
                ).grid(row=0, column=0, padx=2, sticky="w")

            # 1열~ : 데이터
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

            # 삭제 버튼
            ctk.CTkButton(
                fr, text="삭제", width=50, height=24, fg_color="#C0392B",
                command=lambda i=inv_id, b=row["barcode"]: self.delete_one(i, b)
            ).grid(row=0, column=len(self.col_widths), padx=4)

    def delete_one(self, inv_id, barcode):
        if not messagebox.askyesno("삭제", f"바코드 [{barcode}] 삭제할까요?"):
            return
        conn = get_connection()
        conn.execute("DELETE FROM inventory WHERE id=?", (inv_id,))
        conn.commit()
        conn.close()
        self.load_data()

    
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id as inv_id, i.barcode, i.sub_name,
                   t.id as tool_id, t.tool_name, t.tool_code,
                   t.shank_dia, t.total_length
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            WHERE i.id = ?
        """, (inv_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("공구 수정")
        dialog.geometry("420x400")
        dialog.transient(self)
        dialog.grab_set()

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
            if not barcode:
                messagebox.showwarning("오류", "바코드는 필수입니다.")
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
                conn = get_connection()
                cur = conn.cursor()

                cur.execute(
                    "SELECT id FROM inventory WHERE barcode=? AND id!=?",
                    (barcode, row["inv_id"])
                )
                if cur.fetchone():
                    messagebox.showwarning("오류", "이미 존재하는 바코드입니다.")
                    conn.close()
                    return

                shank = fields["shank_dia"].get().strip()
                total = fields["total_length"].get().strip()

                cur.execute("""
                    UPDATE tools
                    SET tool_name=?, tool_code=?, shank_dia=?, total_length=?
                    WHERE id=?
                """, (
                    fields["tool_name"].get().strip(),
                    fields["tool_code"].get().strip() or None,
                    float(shank) if shank else None,
                    float(total) if total else None,
                    row["tool_id"],
                ))

                cur.execute("""
                    UPDATE inventory SET barcode=?, sub_name=? WHERE id=?
                """, (barcode, fields["sub_name"].get().strip(), row["inv_id"]))

                conn.commit()
                conn.close()

                messagebox.showinfo("완료", "수정되었습니다.")
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("오류", str(e))

        bf = ctk.CTkFrame(dialog, fg_color="transparent")
        bf.pack(pady=15)
        ctk.CTkButton(bf, text="저장", width=100, command=save).pack(side="left", padx=8)
        ctk.CTkButton(bf, text="취소", width=100, fg_color="#7F8C8D",
                      command=dialog.destroy).pack(side="left", padx=8)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id as inv_id, i.barcode, i.sub_name,
                   t.id as tool_id, t.tool_name, t.tool_code,
                   t.shank_dia, t.total_length
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            WHERE i.id = ?
        """, (inv_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("공구 수정")
        dialog.geometry("420x400")
        dialog.transient(self)
        dialog.grab_set()

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
            if not barcode:
                messagebox.showwarning("오류", "바코드는 필수입니다.")
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
                conn = get_connection()
                cur = conn.cursor()

                cur.execute(
                    "SELECT id FROM inventory WHERE barcode=? AND id!=?",
                    (barcode, row["inv_id"])
                )
                if cur.fetchone():
                    messagebox.showwarning("오류", "이미 존재하는 바코드입니다.")
                    conn.close()
                    return

                shank = fields["shank_dia"].get().strip()
                total = fields["total_length"].get().strip()

                cur.execute("""
                    UPDATE tools
                    SET tool_name=?, tool_code=?, shank_dia=?, total_length=?
                    WHERE id=?
                """, (
                    fields["tool_name"].get().strip(),
                    fields["tool_code"].get().strip() or None,
                    float(shank) if shank else None,
                    float(total) if total else None,
                    row["tool_id"],
                ))

                cur.execute("""
                    UPDATE inventory SET barcode=?, sub_name=? WHERE id=?
                """, (barcode, fields["sub_name"].get().strip(), row["inv_id"]))

                conn.commit()
                conn.close()

                messagebox.showinfo("완료", "수정되었습니다.")
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("오류", str(e))

        bf = ctk.CTkFrame(dialog, fg_color="transparent")
        bf.pack(pady=15)
        ctk.CTkButton(bf, text="저장", width=100, command=save).pack(side="left", padx=8)
        ctk.CTkButton(bf, text="취소", width=100, fg_color="#7F8C8D",
                      command=dialog.destroy).pack(side="left", padx=8)

    def edit_item(self, inv_id):
        conn = get_connection()
        cur = conn.cursor()

        # 현재 데이터
        cur.execute("""
            SELECT i.id as inv_id, i.barcode, i.sub_name,
                   t.id as tool_id, t.tool_name, t.tool_code,
                   t.shank_dia, t.total_length, t.category_id,
                   c.main_name, c.sub_code
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE i.id = ?
        """, (inv_id,))
        row = cur.fetchone()

        # 대분류 목록
        cur.execute("SELECT DISTINCT main_name FROM categories ORDER BY id")
        main_list = [r["main_name"] for r in cur.fetchall()]

        # 현재 대분류의 소분류 목록
        current_main = row["main_name"] or (main_list[0] if main_list else "")
        cur.execute(
            "SELECT sub_code FROM categories WHERE main_name = ? ORDER BY id",
            (current_main,)
        )
        sub_list = [r["sub_code"] for r in cur.fetchall()]
        conn.close()

        if not row:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("공구 수정")
        dialog.geometry("420x520")
        dialog.transient(self)
        dialog.grab_set()

        # ----- 대분류 -----
        fr_main = ctk.CTkFrame(dialog, fg_color="transparent")
        fr_main.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(fr_main, text="대분류", width=100, anchor="w").pack(side="left")
        combo_main = ctk.CTkComboBox(fr_main, width=240, values=main_list)
        combo_main.pack(side="left")
        if row["main_name"]:
            combo_main.set(row["main_name"])
        elif main_list:
            combo_main.set(main_list[0])

        # ----- 소분류 -----
        fr_sub = ctk.CTkFrame(dialog, fg_color="transparent")
        fr_sub.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(fr_sub, text="소분류", width=100, anchor="w").pack(side="left")
        combo_sub = ctk.CTkComboBox(fr_sub, width=240, values=sub_list)
        combo_sub.pack(side="left")
        if row["sub_code"]:
            combo_sub.set(row["sub_code"])
        elif sub_list:
            combo_sub.set(sub_list[0])

        def on_main_change(choice):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT sub_code FROM categories WHERE main_name = ? ORDER BY id",
                (choice,)
            )
            subs = [r["sub_code"] for r in cur.fetchall()]
            conn.close()
            combo_sub.configure(values=subs)
            if subs:
                combo_sub.set(subs[0])

        combo_main.configure(command=on_main_change)

        # ----- 나머지 필드 -----
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
                conn = get_connection()
                cur = conn.cursor()

                # 바코드 중복
                cur.execute(
                    "SELECT id FROM inventory WHERE barcode=? AND id!=?",
                    (barcode, row["inv_id"])
                )
                if cur.fetchone():
                    messagebox.showwarning("오류", "이미 존재하는 바코드입니다.")
                    conn.close()
                    return

                # 카테고리 id
                cur.execute(
                    "SELECT id FROM categories WHERE main_name=? AND sub_code=?",
                    (main_name, sub_code)
                )
                cat = cur.fetchone()
                if not cat:
                    messagebox.showerror("오류", "카테고리 정보를 찾을 수 없습니다.")
                    conn.close()
                    return
                category_id = cat["id"]

                shank = fields["shank_dia"].get().strip()
                total = fields["total_length"].get().strip()

                cur.execute("""
                    UPDATE tools
                    SET category_id=?, tool_name=?, tool_code=?,
                        shank_dia=?, total_length=?
                    WHERE id=?
                """, (
                    category_id,
                    fields["tool_name"].get().strip(),
                    fields["tool_code"].get().strip() or None,
                    float(shank) if shank else None,
                    float(total) if total else None,
                    row["tool_id"],
                ))

                cur.execute("""
                    UPDATE inventory SET barcode=?, sub_name=? WHERE id=?
                """, (barcode, fields["sub_name"].get().strip(), row["inv_id"]))

                conn.commit()
                conn.close()

                messagebox.showinfo("완료", "수정되었습니다.")
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("오류", str(e))

        bf = ctk.CTkFrame(dialog, fg_color="transparent")
        bf.pack(pady=15)
        ctk.CTkButton(bf, text="저장", width=100, command=save).pack(side="left", padx=8)
        ctk.CTkButton(bf, text="취소", width=100, fg_color="#7F8C8D",
                      command=dialog.destroy).pack(side="left", padx=8)

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

    
        # 1단계: 선택 모드 켜기
        if not self.select_mode:
            self.select_mode = True
            self.checked_ids.clear()
            self.load_data()
            messagebox.showinfo(
                "Toolyne 등록",
                "등록할 항목을 체크한 뒤\n다시 [Toolyne 등록]을 누르세요."
            )
            return

        # 체크박스 상태를 다시 수집
        self.checked_ids.clear()
        for inv_id, var in self.row_vars.items():
                if var.get():
                    self.checked_ids.add(inv_id)

        if not self.checked_ids:
            messagebox.showwarning("알림", "선택된 항목이 없습니다.\n체크박스를 선택한 뒤 다시 눌러주세요.")
            return

        if not messagebox.askyesno(
            "확인",
            f"{len(self.checked_ids)}개를 Toolyne에 등록할까요?\nChrome이 실행됩니다."
        ):
            return

        try:
            from utils.toolyne_upload import upload_tools
            ok = upload_tools(rows)
            if ok:
                messagebox.showinfo("완료", "Toolyne 등록이 완료되었습니다.")
            else:
                messagebox.showerror("실패", "등록에 실패했습니다.\nChrome/로그인을 확인하세요.")
        except Exception as e:
            messagebox.showerror("오류", f"실행 중 오류:\n{e}")
            return

        conn = get_connection()
        cur = conn.cursor()
        ph = ",".join("?" * len(self.checked_ids))
        cur.execute(f"""
            SELECT
                c.main_name, c.sub_code, m.name as maker_name,
                t.tool_name, i.sub_name, t.tool_code, i.barcode,
                t.shank_dia, t.total_length
            FROM inventory i
            JOIN tools t ON i.tool_id = t.id
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN makers m ON t.maker_id = m.id
            WHERE i.id IN ({ph})
            ORDER BY i.id
        """, tuple(self.checked_ids))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        if not rows:
            messagebox.showwarning("알림", "DB에서 선택 항목을 찾지 못했습니다.")
            return

        ok = upload_tools(rows)

        if ok:
            messagebox.showinfo("완료", "Toolyne 등록이 완료되었습니다.")
        else:
            messagebox.showerror("실패", "오류가 발생했습니다.\n터미널 로그를 확인하세요.")

        self.select_mode = False
        self.checked_ids.clear()
        self.load_data()

    def on_toolyne_upload(self):
        # 1) 선택 모드 켜기
        if not self.select_mode:
            self.select_mode = True
            self.checked_ids.clear()
            self.row_vars.clear()
            self.load_data()
            messagebox.showinfo(
                "Toolyne 등록",
                "1. 등록할 항목을 체크하세요.\n"
                "2. 다시 [Toolyne 등록] 버튼을 누르세요."
            )
            return

        # 2) 체크된 항목 수집
        selected = []
        for inv_id, var in self.row_vars.items():
            try:
                if var.get():
                    selected.append(inv_id)
            except Exception:
                pass

        if not selected:
            messagebox.showwarning("알림", "체크된 항목이 없습니다.")
            return

        if not messagebox.askyesno("확인", f"{len(selected)}개를 Toolyne에 등록할까요?"):
            return

        # 3) DB 조회
        try:
            conn = get_connection()
            cur = conn.cursor()
            ph = ",".join("?" * len(selected))
            cur.execute(f"""
                SELECT
                    c.main_name, c.sub_code, m.name as maker_name,
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

        # 4) 업로드
        try:
            from utils.toolyne_upload import upload_tools
            ok, msg = upload_tools(rows)
            if ok:
                messagebox.showinfo("완료", msg)
            else:
                messagebox.showerror("실패", msg)
        except Exception as e:
            messagebox.showerror("실행 오류", str(e))

        # 5) 선택 모드 종료
        self.select_mode = False
        self.checked_ids.clear()
        self.row_vars.clear()
        self.load_data()

    def cancel_select_mode(self):
        self.select_mode = False
        self.checked_ids.clear()
        self.row_vars.clear()
        self.load_data()
        messagebox.showinfo("취소", "Toolyne 등록을 취소했습니다.")

    def on_export_excel(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("엑셀 다운로드")
        dialog.geometry("300x160")
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="다운로드 범위",
                     font=ctk.CTkFont(weight="bold")).pack(pady=15)

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
            messagebox.showinfo("선택 모드", "체크 후 [선택 항목 엑셀 저장]을 누르세요.")

        ctk.CTkButton(dialog, text="전체 다운로드", width=200, command=do_all).pack(pady=5)
        ctk.CTkButton(dialog, text="선택한 것만", width=200, fg_color="#2980B9",
                      command=do_sel).pack(pady=5)

    def export_to_excel(self, selected_only=False):
        # 체크박스 상태 다시 읽기 (Toolyne과 동일)
        if selected_only:
            self.checked_ids.clear()
            for inv_id, var in self.row_vars.items():
                try:
                    if var.get():
                        self.checked_ids.add(inv_id)
                except Exception:
                    pass

            if not self.checked_ids:
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
            if not self.checked_ids:
                messagebox.showwarning("알림", "선택된 항목이 없습니다.")
                conn.close()
                return
            ph = ",".join("?" * len(self.checked_ids))
            cur.execute(sql + f" WHERE i.id IN ({ph}) ORDER BY i.id DESC",
                        tuple(self.checked_ids))
        else:
            cur.execute(sql + " ORDER BY i.id DESC")
        rows = cur.fetchall()
        conn.close()
        if not rows:
            messagebox.showinfo("알림", "데이터 없음")
            return
        df = pd.DataFrame([dict(r) for r in rows])
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile=f"공구목록_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if not path:
            return
        df.to_excel(path, index=False)
        messagebox.showinfo("완료", f"저장됨\n{path}")
        self.select_mode = False
        self.checked_ids.clear()
        self.load_data()