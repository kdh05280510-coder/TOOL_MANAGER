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
        self.geometry("1700x800")
        self.minsize(900, 500)
        self.transient(parent)
        self.grab_set()

        self.page_size = 50
        self.current_page = 1
        self.total_count = 0
        self.select_mode = False
        self.checked_ids = set()
        self.row_vars = {}

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

        # 열 너비 (헤더/데이터 공통)
        self.col_widths = [40, 90, 90, 150, 140, 200, 250, 180, 60, 70, 110]
        self.col_titles = ["", "대분류", "소분류", "제조사", "상품명", "상품명(부)",
                           "바코드", "상품코드", "생크", "전체길이", "등록일"]

        # 헤더
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=15, pady=(10, 0))

        for i, (text, w) in enumerate(zip(self.col_titles, self.col_widths)):
            header.grid_columnconfigure(i, minsize=w)
            ctk.CTkLabel(
                header, text=text, width=w, anchor="w",
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=i, padx=2, sticky="w")
        

        # 목록 (스크롤)
        self.scroll = ctk.CTkScrollableFrame(self, height=400)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=8)

        # 하단
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

        ctk.CTkButton(bottom, text="닫기", width=90, command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(bottom, text="전체 삭제", width=90, fg_color="#7B241C",
                      command=self.delete_all).pack(side="right", padx=5)
        self.btn_export_selected = ctk.CTkButton(
            bottom, text="선택 항목 엑셀 저장", width=140, fg_color="#27AE60",
            command=lambda: self.export_to_excel(True)
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

    def fmt_num(self, v):
        if v is None or v == "":
            return ""
        try:
            return f"{float(v):.1f}"
        except Exception:
            return str(v)

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
                   OR t.tool_name LIKE ? OR IFNULL(c.main_name,'') LIKE ? OR IFNULL(c.sub_code,'') LIKE ?
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
                   OR t.tool_name LIKE ? OR IFNULL(c.main_name,'') LIKE ? OR IFNULL(c.sub_code,'') LIKE ?
                ORDER BY i.id DESC LIMIT ? OFFSET ?
            """, (like, like, like, like, like, like, self.page_size, offset))
        else:
            cur.execute(sql + " ORDER BY i.id DESC LIMIT ? OFFSET ?", (self.page_size, offset))

        rows = cur.fetchall()
        conn.close()

        max_page = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        self.page_label.configure(text=f"{self.current_page} / {max_page}")
        self.count_label.configure(text=f"총 {self.total_count}건")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < max_page else "disabled")

        if self.select_mode:
            self.btn_export_selected.pack(side="right", padx=5)
        else:
            self.btn_export_selected.pack_forget()

        if not rows:
            ctk.CTkLabel(self.scroll, text="데이터 없음").pack(pady=20)
            return

        for row in rows:
            inv_id = str(row["id"])
            fr = ctk.CTkFrame(self.scroll, fg_color="transparent")
            fr.pack(fill="x", pady=1)

            for i, w in enumerate(self.col_widths):
                fr.grid_columnconfigure(i, minsize=w)

            # 0열: 체크 or 빈칸
            if self.select_mode:
                var = ctk.BooleanVar(value=(inv_id in self.checked_ids))
                self.row_vars[inv_id] = var

                def make_cmd(i=inv_id, v=var):
                    def cmd():
                        if v.get():
                            self.checked_ids.add(i)
                        else:
                            self.checked_ids.discard(i)
                    return cmd

                ctk.CTkCheckBox(
                    fr, text="", width=self.col_widths[0], variable=var, command=make_cmd()
                ).grid(row=0, column=0, padx=2, sticky="w")
            else:
                ctk.CTkLabel(fr, text="", width=self.col_widths[0]).grid(
                    row=0, column=0, padx=2, sticky="w"
                )

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

    def on_export_excel(self):
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
            messagebox.showinfo("선택 모드", "체크 후 [선택 항목 엑셀 저장]을 누르세요.")

        ctk.CTkButton(dialog, text="전체 다운로드", width=200, command=do_all).pack(pady=5)
        ctk.CTkButton(dialog, text="선택한 것만", width=200, fg_color="#2980B9", command=do_sel).pack(pady=5)

    def export_to_excel(self, selected_only=False):
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
            cur.execute(sql + f" WHERE i.id IN ({ph}) ORDER BY i.id DESC", tuple(self.checked_ids))
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