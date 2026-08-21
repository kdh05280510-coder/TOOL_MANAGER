import customtkinter as ctk
from datetime import datetime
import tkinter.messagebox as messagebox
from database.db import get_connection


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("공구 등록 프로그램")
        self.geometry("700x800")
        self.minsize(800, 600)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.all_makers = []
        self.all_subs = []

        self.create_widgets()
        self.load_initial_data()

    # --------------------------------------------------
    # 화면 만들기
    # --------------------------------------------------
    def create_widgets(self):
        title = ctk.CTkLabel(
            self, text="공구 등록 프로그램",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(pady=(15, 10))

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ----- 왼쪽: 분류 -----
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)

        ctk.CTkLabel(
            left_frame, text="분류 선택",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))

        ctk.CTkLabel(left_frame, text="대분류").pack(anchor="w", padx=15)
        self.combo_main = ctk.CTkComboBox(
            left_frame, width=220,
            command=self.on_main_category_change
        )
        self.combo_main.pack(padx=15, pady=(0, 12))
        self.combo_main.bind("<KeyRelease>", self.on_main_keyrelease)

        ctk.CTkLabel(left_frame, text="소분류").pack(anchor="w", padx=15)
        self.combo_sub = ctk.CTkComboBox(
            left_frame, width=220,
            command=self.on_sub_category_change
        )
        self.combo_sub.pack(padx=15, pady=(0, 12))
        self.combo_sub.bind("<KeyRelease>", self.on_sub_keyrelease)

        ctk.CTkLabel(left_frame, text="제조사").pack(anchor="w", padx=15)
        # 입력 가능 + 필터
        self.combo_maker = ctk.CTkComboBox(
            left_frame, width=220,
            command=self.on_maker_selected
        )
        self.combo_maker.pack(padx=15, pady=(0, 12))
        self.combo_maker.bind("<KeyRelease>", self.on_maker_keyrelease)

        self.check_grade_b = ctk.CTkCheckBox(left_frame, text="B급 등록")
        self.check_grade_b.pack(anchor="w", padx=15, pady=10)

        # ----- 오른쪽: 입력 -----
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        ctk.CTkLabel(
            right_frame, text="공구 정보 입력",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))

        self.fields_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.fields_frame.pack(fill="both", expand=True, padx=15)

        self.entries = {}
        fields = [
            ("tool_code", "상품코드"),
            ("diameter", "날지름 (D)"),
            ("length", "날장 (L)"),
            ("effective_len", "유효장 (H)"),
            ("corner_r", "코너R"),
            ("angle", "날 끝각도 (°)"),
            ("flute_count", "날 수"),
            ("thread_spec", "나사규격"),
            ("shank_dia", "생크지름"),
            ("total_length", "전체길이"),
            ("quantity", "수량"),
        ]

        for key, label in fields:
            row = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)

            lbl = ctk.CTkLabel(row, text=label, width=110, anchor="w")
            lbl.pack(side="left")

            entry = ctk.CTkEntry(row, width=200)
            entry.pack(side="left", padx=10)

            self.entries[key] = {"label": lbl, "entry": entry, "row": row}

        # 나머지 칸: 엔터 → 다음 칸
        entry_keys = list(self.entries.keys())
        for i, key in enumerate(entry_keys):
            entry = self.entries[key]["entry"]

            def make_handler(idx):
                def handler(event):
                    next_key = entry_keys[(idx + 1) % len(entry_keys)]
                    self.entries[next_key]["entry"].focus_set()
                    return "break"
                return handler

            entry.bind("<Return>", make_handler(i))

                # ----- 하단 버튼 (레이아웃 이미지 기준) -----
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        # 등록 = 신규 등록
        ctk.CTkButton(
            btn_frame, text="등록", width=100, height=36,
            command=self.on_register
        ).pack(side="left", padx=6)

        # 상품코드 빠른 입력 (검색 등록용)
        self.entry_search_code = ctk.CTkEntry(
            btn_frame, width=160, height=36,
            placeholder_text="상품코드를 입력하세요"
        )
        self.entry_search_code.pack(side="left", padx=6)

        # 검색 등록 = 상품코드로 재등록
        ctk.CTkButton(
            btn_frame, text="검색 등록", width=100, height=36,
            fg_color="#2E8B57", hover_color="#256F46",
            command=self.on_search_register
        ).pack(side="left", padx=6)

        # A급 목록
        ctk.CTkButton(
            btn_frame, text="A급 공구 목록", width=120, height=36,
            fg_color="#3B8ED0",
            command=lambda: self.on_show_list(grade="A")
        ).pack(side="left", padx=6)

        # B급 목록
        ctk.CTkButton(
            btn_frame, text="B급 공구 목록", width=120, height=36,
            fg_color="#3B8ED0",
            command=lambda: self.on_show_list(grade="B")
        ).pack(side="left", padx=6)

        self.status_label = ctk.CTkLabel(self, text="준비됨", text_color="gray")
        self.status_label.pack(pady=(0, 10))

    # --------------------------------------------------
    # 초기 데이터
    # --------------------------------------------------
    def load_initial_data(self):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT main_name FROM categories ORDER BY id")
        mains = [row["main_name"] for row in cur.fetchall()]
        self.all_mains = mains
        self.combo_main.configure(values = mains)
        self.combo_main.configure(values=mains)
        if mains:
            self.combo_main.set(mains[0])
            self.on_main_category_change(mains[0])

        cur.execute("SELECT name FROM makers WHERE is_active = 1 ORDER BY name")
        makers = [row["name"] for row in cur.fetchall()]
        self.all_makers = makers
        self.combo_maker.configure(values=makers)
        if makers:
            self.combo_maker.set(makers[0])

        conn.close()

    # --------------------------------------------------
    # 분류 / 제조사
    # --------------------------------------------------
    def on_main_category_change(self, choice):
        self.current_main = choice
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT sub_code FROM categories WHERE main_name = ? ORDER BY id",
            (choice,)
        )
        subs = [row["sub_code"] for row in cur.fetchall()]
        self.all_subs = subs
        self.combo_sub.configure(values=subs)
        if subs:
            self.combo_sub.set(subs[0])
            self.on_sub_category_change(subs[0])
        conn.close()

    def on_sub_category_change(self, choice):
        # SP 일때는 전부 보여주기
        if  hasattr(self, "current_main") and self.current_main == "SP(특수)":
            for key in self.entries:
                self.entries[key]["row"].pack(fill="x", pady=4)
            return
        for key in self.entries:
            self.entries[key]["row"].pack_forget()

        endmill_prefixes = ["EM", "BM", "BN", "RF", "LN"]
        is_endmill = any(choice.startswith(p) for p in endmill_prefixes)
        is_drill = choice in ["DR", "DR-SGESS", "DR-SGES", "CD", "NC", "FD", "MD"]
        is_tap = "TAP" in choice or choice == "THD"
        is_cm = choice == "CM"

        # 표시 순서
        self.entries["tool_code"]["row"].pack(fill="x", pady=4)

        if is_endmill or is_drill or is_cm or choice in ["RM", "TC", "SP", "DV", "SR"]:
            self.entries["diameter"]["row"].pack(fill="x", pady=4)

        if choice.startswith("BN"):
            self.entries["corner_r"]["row"].pack(fill="x", pady=4)

        if is_endmill or is_drill or is_cm:
            self.entries["length"]["row"].pack(fill="x", pady=4)

        if "-R" in choice:
            self.entries["effective_len"]["row"].pack(fill="x", pady=4)

        if is_drill or is_cm:
            self.entries["angle"]["row"].pack(fill="x", pady=4)

        if is_endmill:
            self.entries["flute_count"]["row"].pack(fill="x", pady=4)

        if is_tap:
            self.entries["thread_spec"]["row"].pack(fill="x", pady=4)

        self.entries["shank_dia"]["row"].pack(fill="x", pady=4)
        self.entries["total_length"]["row"].pack(fill="x", pady=4)
        self.entries["quantity"]["row"].pack(fill="x", pady=4)

    def _filter_list(self, source_list, typed):
        """입력어로 필터: 시작 일치 우선, 그다음 포함"""
        typed = typed.strip().lower()
        if not typed:
            return list(source_list)

        starts = [x for x in source_list if x.lower().startswith(typed)]
        contains = [x for x in source_list if typed in x.lower() and x not in starts]
        return starts + contains

    def on_maker_keyrelease(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Left", "Right", "Tab"):
            return
        typed = self.combo_maker.get()
        filtered = self._filter_list(self.all_makers, typed)
        self.combo_maker.configure(values=filtered if filtered else self.all_makers)

    def on_main_keyrelease(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Left", "Right", "Tab"):
            return
        if not hasattr(self, "all_mains"):
            return
        typed = self.combo_main.get()
        filtered = self._filter_list(self.all_mains, typed)
        self.combo_main.configure(values=filtered if filtered else self.all_mains)

    def on_sub_keyrelease(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Left", "Right", "Tab"):
            return
        if not hasattr(self, "all_subs"):
            return
        typed = self.combo_sub.get()
        filtered = self._filter_list(self.all_subs, typed)
        self.combo_sub.configure(values=filtered if filtered else self.all_subs)

    def on_maker_selected(self, choice):
        self.combo_maker.set(choice)

    # --------------------------------------------------
    # 상품코드 자동 조회
    # --------------------------------------------------
    def on_tool_code_lookup(self, event=None):
        tool_code = self.entries["tool_code"]["entry"].get().strip()
        if not tool_code:
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                t.tool_name, t.diameter, t.length, t.effective_len,
                t.corner_r, t.angle, t.flute_count, t.thread_spec,
                t.shank_dia, t.total_length,
                c.main_name, c.sub_code, m.name as maker_name
            FROM tools t
            JOIN categories c ON t.category_id = c.id
            LEFT JOIN makers m ON t.maker_id = m.id
            WHERE t.tool_code = ?
            ORDER BY t.id DESC
            LIMIT 1
        """, (tool_code,))
        row = cur.fetchone()
        conn.close()

        if not row:
            self.status_label.configure(
                text="해당 상품코드 없음 (신규 입력 가능)", text_color="orange"
            )
            return

        if row["main_name"]:
            self.combo_main.set(row["main_name"])
            self.on_main_category_change(row["main_name"])
        if row["sub_code"]:
            self.combo_sub.set(row["sub_code"])
            self.on_sub_category_change(row["sub_code"])
        if row["maker_name"]:
            self.combo_maker.set(row["maker_name"])

        mapping = {
            "diameter": row["diameter"],
            "length": row["length"],
            "effective_len": row["effective_len"],
            "corner_r": row["corner_r"],
            "angle": row["angle"],
            "flute_count": row["flute_count"],
            "thread_spec": row["thread_spec"],
            "shank_dia": row["shank_dia"],
            "total_length": row["total_length"],
        }
        for key, value in mapping.items():
            entry = self.entries[key]["entry"]
            entry.delete(0, "end")
            if value is not None and str(value) != "":
                if key == "flute_count":
                    entry.insert(0, str(int(float(value))))
                elif key == "thread_spec":
                    entry.insert(0, str(value))
                else:
                    entry.insert(0, self.fmt_num(value))

        self.status_label.configure(
            text=f"불러옴: {row['tool_name'] or tool_code}", text_color="green"
        )
        self.entries["quantity"]["entry"].focus_set()

    # --------------------------------------------------
    # 신규 등록
    # --------------------------------------------------
    def on_register(self):
        try:
            main_name = self.combo_main.get()
            sub_code = self.combo_sub.get()
            maker_name = self.combo_maker.get()
            is_grade_b = self.check_grade_b.get()

            diameter = self.entries["diameter"]["entry"].get().strip()
            length = self.entries["length"]["entry"].get().strip()
            effective_len = self.entries["effective_len"]["entry"].get().strip()
            corner_r = self.entries["corner_r"]["entry"].get().strip()
            angle = self.entries["angle"]["entry"].get().strip()
            flute_count = self.entries["flute_count"]["entry"].get().strip()
            thread_spec = self.entries["thread_spec"]["entry"].get().strip()
            shank_dia = self.entries["shank_dia"]["entry"].get().strip()
            total_length = self.entries["total_length"]["entry"].get().strip()
            tool_code = self.entries["tool_code"]["entry"].get().strip()
            quantity_str = self.entries["quantity"]["entry"].get().strip()

            if not main_name or not sub_code:
                messagebox.showwarning("입력 오류", "대분류와 소분류를 선택하세요.")
                return
            if not maker_name:
                messagebox.showwarning("입력 오류", "제조사를 선택하세요.")
                return
            if not quantity_str or not quantity_str.isdigit() or int(quantity_str) <= 0:
                messagebox.showwarning("입력 오류", "수량은 1 이상의 정수로 입력하세요.")
                return

            quantity = int(quantity_str)

            number_fields = {
                "diameter": "날지름", "length": "날장", "effective_len": "유효장",
                "corner_r": "코너R", "angle": "각도", "flute_count": "날 수",
                "shank_dia": "생크지름", "total_length": "전체길이",
            }
            for key, name in number_fields.items():
                value = self.entries[key]["entry"].get().strip()
                if self.entries[key]["row"].winfo_ismapped() and value:
                    try:
                        float(value)
                    except ValueError:
                        messagebox.showwarning("입력 오류", f"{name}은(는) 숫자로 입력하세요.")
                        return

            if not diameter and sub_code not in ["TAP", "TAP-H", "THD"]:
                messagebox.showwarning("입력 오류", "날지름을 입력하세요.")
                return

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT id FROM categories WHERE main_name=? AND sub_code=?",
                (main_name, sub_code)
            )
            cat_row = cur.fetchone()
            if not cat_row:
                messagebox.showerror("오류", "카테고리 정보를 찾을 수 없습니다.")
                conn.close()
                return
            category_id = cat_row["id"]

            cur.execute("SELECT id FROM makers WHERE name=?", (maker_name,))
            maker_row = cur.fetchone()
            maker_id = maker_row["id"] if maker_row else None

            tool_name = self.make_tool_name(
                sub_code, diameter, length, effective_len, corner_r, angle, thread_spec
            )

            def to_f(v):
                return float(f"{float(v):.1f}") if v else None

            cur.execute("""
                INSERT INTO tools (
                    category_id, maker_id, tool_code, tool_name,
                    diameter, length, effective_len, corner_r, angle,
                    flute_count, thread_spec, shank_dia, total_length, tool_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                category_id, maker_id,
                tool_code if tool_code else None,
                tool_name,
                to_f(diameter), to_f(length), to_f(effective_len),
                to_f(corner_r), to_f(angle),
                int(float(flute_count)) if flute_count else None,
                thread_spec if thread_spec else None,
                to_f(shank_dia), to_f(total_length),
                self.get_tool_type(sub_code),
            ))
            tool_id = cur.lastrowid

            today = datetime.now().strftime("%y%m%d")
            base_code = tool_code if tool_code else "UNKNOWN"

            cur.execute("""
                SELECT barcode FROM inventory
                WHERE barcode LIKE ?
                ORDER BY barcode DESC LIMIT 1
            """, (f"{base_code}-{today}-%",))
            last_row = cur.fetchone()
            start_seq = 1
            if last_row:
                try:
                    start_seq = int(last_row["barcode"].split("-")[-1]) + 1
                except Exception:
                    start_seq = 1

            for i in range(quantity):
                seq = f"{start_seq + i:02d}"
                barcode = f"{base_code}-{today}-{seq}"
                sub_name = self.make_sub_name(
                    sub_code, diameter, length, flute_count, thread_spec,
                    today, seq, is_grade_b
                )
                cur.execute("""
                    INSERT INTO inventory (
                        tool_id, barcode, sub_name, quantity, status, is_grade_b
                    ) VALUES (?, ?, ?, 1, ?, ?)
                """, (
                    tool_id, barcode, sub_name,
                    "B급" if is_grade_b else "정상",
                    1 if is_grade_b else 0,
                ))

            conn.commit()
            conn.close()

            messagebox.showinfo("등록 완료", f"{quantity}개 등록이 완료되었습니다.")
            self.status_label.configure(text=f"{quantity}개 등록 완료", text_color="green")
            self.on_reset()

        except Exception as e:
            messagebox.showerror("오류 발생", str(e))
            self.status_label.configure(text="등록 실패", text_color="red")

    # --------------------------------------------------
    # 재등록
    # --------------------------------------------------
    def on_reregister(self):
        try:
            tool_code = self.entries["tool_code"]["entry"].get().strip()
            if not tool_code:
                messagebox.showwarning("입력 오류", "재등록할 상품코드를 입력하세요.")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT t.id, t.tool_name, t.tool_code, t.diameter, t.length,
                       t.flute_count, t.thread_spec, t.shank_dia, t.total_length,
                       c.sub_code, m.name as maker_name
                FROM tools t
                JOIN categories c ON t.category_id = c.id
                LEFT JOIN makers m ON t.maker_id = m.id
                WHERE t.tool_code = ?
                ORDER BY t.id DESC LIMIT 1
            """, (tool_code,))
            tool = cur.fetchone()

            if not tool:
                messagebox.showinfo("알림", "동일한 상품코드의 공구가 없습니다.")
                conn.close()
                return

            answer = messagebox.askyesno(
                "재등록 확인",
                f"공구를 찾았습니다.\n\n"
                f"상품명: {tool['tool_name']}\n"
                f"제조사: {tool['maker_name'] or '-'}\n"
                f"생크지름: {tool['shank_dia'] or '-'}\n"
                f"전체길이: {tool['total_length'] or '-'}\n\n"
                f"재등록 하시겠습니까?"
            )
            if not answer:
                conn.close()
                return

            qty_str = ctk.CTkInputDialog(
                text="등록할 수량을 입력하세요:", title="재등록"
            ).get_input()
            if not qty_str or not qty_str.isdigit() or int(qty_str) <= 0:
                messagebox.showwarning("입력 오류", "수량은 1 이상의 정수로 입력하세요.")
                conn.close()
                return
            quantity = int(qty_str)

            is_grade_b = self.check_grade_b.get()
            today = datetime.now().strftime("%y%m%d")
            sub_code = tool["sub_code"]

            cur.execute("""
                SELECT barcode FROM inventory
                WHERE barcode LIKE ?
                ORDER BY barcode DESC LIMIT 1
            """, (f"{tool_code}-{today}-%",))
            last_row = cur.fetchone()
            start_seq = 1
            if last_row:
                try:
                    start_seq = int(last_row["barcode"].split("-")[-1]) + 1
                except Exception:
                    start_seq = 1

            for i in range(quantity):
                seq = f"{start_seq + i:02d}"
                barcode = f"{tool_code}-{today}-{seq}"
                dia = tool["diameter"]
                if dia is None or str(dia).strip() == "":
                    import re
                    m = re.search(r"[Dd]\s*([0-9.]+)", str(tool["tool_name"] or ""))
                    if m:
                        dia = m.group(1)

                leng = tool["length"]
                if leng is None or str(leng).strip() == "":
                    import re
                    m = re.search(r"[Ll]\s*([0-9.]+)", str(tool["tool_name"] or ""))
                    if m:
                        leng = m.group(1)

                sub_name = self.make_sub_name(
                    sub_code,
                    "" if dia is None else str(dia),
                    "" if leng is None else str(leng),
                    "" if tool["flute_count"] is None else str(tool["flute_count"]),
                    tool["thread_spec"] or "",
                    today, seq, is_grade_b
                )
                cur.execute("""
                    INSERT INTO inventory (
                        tool_id, barcode, sub_name, quantity, status, is_grade_b
                    ) VALUES (?, ?, ?, 1, ?, ?)
                """, (
                    tool["id"], barcode, sub_name,
                    "B급" if is_grade_b else "정상",
                    1 if is_grade_b else 0,
                ))

            conn.commit()
            conn.close()

            messagebox.showinfo("재등록 완료", f"{quantity}개 재등록이 완료되었습니다.")
            self.status_label.configure(text=f"{quantity}개 재등록 완료", text_color="green")
            self.on_reset()

        except Exception as e:
            messagebox.showerror("오류 발생", str(e))
            self.status_label.configure(text="재등록 실패", text_color="red")

    # --------------------------------------------------
    # 검색등록
    # --------------------------------------------------

    def on_search_register(self):
        code = self.entry_search_code.get().strip()
        if not code:
            messagebox.showwarning("입력 오류", "상품코드를 입력하세요.")
            return
        # 위쪽 상품코드 칸에도 넣고 기존 재등록 로직 사용
        self.entries["tool_code"]["entry"].delete(0, "end")
        self.entries["tool_code"]["entry"].insert(0, code)
        self.on_reregister()

    def on_show_list(self, grade=None):
        from ui.list_window import ListWindow
        ListWindow(self, grade=grade)  # grade: "A" / "B" / None

    def on_reset(self):
        for key in self.entries:
            self.entries[key]["entry"].delete(0, "end")
        self.check_grade_b.deselect()
        self.status_label.configure(text="초기화 완료", text_color="green")

    def fmt_num(self, value):
        if value is None or value == "":
            return ""
        try:
            return f"{float(value):.1f}"
        except (ValueError, TypeError):
            return str(value)

    def make_tool_name(self, sub_code, diameter, length, effective_len, corner_r, angle, thread_spec):
        if sub_code in ["TAP", "TAP-H", "THD", "TAP(UNC)", "TAP(UNF)", "TAP-PT", "TAP-NPT"]:
            return thread_spec if thread_spec else "나사"
        parts = []
        if diameter:
            parts.append(f"D{self.fmt_num(diameter)}")
        if length:
            parts.append(f"L{self.fmt_num(length)}")
        if effective_len:
            parts.append(f"H{self.fmt_num(effective_len)}")
        if corner_r:
            parts.append(f"R{self.fmt_num(corner_r)}")
        if angle:
            parts.append(f"{self.fmt_num(angle)}°")
        return " ".join(parts) if parts else "공구"

    def make_sub_name(self, sub_code, diameter, length, flute_count, thread_spec, today, seq, is_grade_b):
        tool_type = self.get_tool_type(sub_code)
        if sub_code in ["TAP", "TAP-H", "THD"]:
            name = f"{thread_spec} {tool_type}"
        else:
            name = f"D{self.fmt_num(diameter)}" if diameter else ""
            if flute_count:
                name += f" {flute_count}날"
            name += f" {tool_type}"
        if not is_grade_b:
            name += f" {today}-{seq}"
        return name.strip()

    def get_tool_type(self, sub_code):
        mapping = {
            "EM(SUS)": "스퀘어", "EM(ALU)": "스퀘어", "EM(STEEL)": "스퀘어",
            "EM-R(SUS)": "리브 스퀘어", "EM-R(ALU)": "리브 스퀘어", "EM-R(STEEL)": "리브 스퀘어",
            "BM(SUS)": "볼", "BM(ALU)": "볼", "BM(STEEL)": "볼",
            "BM-R(SUS)": "리브 볼", "BM-R(ALU)": "리브 볼", "BM-R(STEEL)": "리브 볼",
            "BN(SUS)": "코너R", "BN(ALU)": "코너R", "BN(STEEL)": "코너R",
            "BN-R(SUS)": "리브 코너R", "BN-R(ALU)": "리브 코너R", "BN-R(STEEL)": "리브 코너R",
            "RF(SUS)": "라핑", "RF(ALU)": "라핑", "RF(STEEL)": "라핑",
            "RF-R(SUS)": "리브 라핑", "RF-R(ALU)": "리브 라핑", "RF-R(STEEL)": "리브 라핑",
            "LN(SUS)": "롱넥", "LN(ALU)": "롱넥", "LN(STEEL)": "롱넥",
            "DR": "드릴", "DR-SGESS": "드릴", "DR-SGES": "드릴",
            "CD": "초경 드릴", "MD": "마이크로 드릴", "FD": "플랫 드릴", "NC": "NC 드릴",
            "CM": "챔퍼", "THD": "쓰레드", "TAP": "탭", "TAP-H": "헬리코일",
            "RM": "리머", "TC": "T-CUTTER", "SP": "특수제작공구",
        }
        return mapping.get(sub_code, "")


def run_app():
    app = MainWindow()
    app.mainloop()