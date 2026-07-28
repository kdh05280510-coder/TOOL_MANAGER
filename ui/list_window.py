import customtkinter as ctk
from database.db import get_connection


class ListWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("공구 목록")
        self.geometry("1100x600")
        self.minsize(900, 500)

        # 창이 닫힐 때까지 부모 창 조작 막기
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # 상단 제목 + 새로고침
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(top_frame, text="등록된 공구 목록", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")

        ctk.CTkButton(top_frame, text="새로고침", width=100, command=self.load_data).pack(side="right", padx=5)

        # 검색창
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(search_frame, text="검색:").pack(side="left")
        self.search_entry = ctk.CTkEntry(search_frame, width=250, placeholder_text="상품코드 / 바코드 / 상품명")
        self.search_entry.pack(side="left", padx=8)
        self.search_entry.bind("<Return>", lambda e: self.load_data())

        ctk.CTkButton(search_frame, text="검색", width=80, command=self.load_data).pack(side="left")

        # 테이블 헤더
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=15, pady=(10, 0))

        headers = ["ID", "바코드", "상품명(부)", "상품코드", "상태", "등록일"]
        widths = [50, 180, 280, 140, 80, 120]

        for text, width in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=text, width=width, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)

        # 스크롤 가능한 목록
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=400)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # 하단 닫기 버튼
        ctk.CTkButton(self, text="닫기", width=120, command=self.destroy).pack(pady=10)

    def load_data(self):
        # 기존 목록 지우기
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        keyword = self.search_entry.get().strip()

        conn = get_connection()
        cur = conn.cursor()

        if keyword:
            cur.execute("""
                SELECT i.id, i.barcode, i.sub_name, t.tool_code, i.status, i.registered_at
                FROM inventory i
                JOIN tools t ON i.tool_id = t.id
                WHERE i.barcode LIKE ? OR i.sub_name LIKE ? OR t.tool_code LIKE ?
                ORDER BY i.id DESC
                LIMIT 300
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
        else:
            cur.execute("""
                SELECT i.id, i.barcode, i.sub_name, t.tool_code, i.status, i.registered_at
                FROM inventory i
                JOIN tools t ON i.tool_id = t.id
                ORDER BY i.id DESC
                LIMIT 300
            """)

        rows = cur.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(self.scroll_frame, text="등록된 데이터가 없습니다.").pack(pady=20)
            return

        for row in rows:
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            values = [
                str(row["id"]),
                row["barcode"] or "",
                row["sub_name"] or "",
                row["tool_code"] or "",
                row["status"] or "",
                (row["registered_at"] or "")[:16],
            ]
            widths = [50, 180, 280, 140, 80, 120]

            for val, width in zip(values, widths):
                ctk.CTkLabel(row_frame, text=val, width=width, anchor="w").pack(side="left", padx=2)
            # 삭제 버튼
            inv_id = row["id"]
            ctk.CTkButton(
                row_frame, text="삭제", width=60, height=24,
                fg_color="#C0392B", hover_color="#E74C3C",
                command=lambda i=inv_id: self.delete_item(i)
            ).pack(side="left", padx=5)

    def delete_item(self, inv_id):
        import tkinter.messagebox as messagebox

        if not messagebox.askyesno("삭제 확인", f"ID {inv_id} 항목을 삭제할까요?"):
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM inventory WHERE id = ?", (inv_id,))
        conn.commit()
        conn.close()

        self.load_data()