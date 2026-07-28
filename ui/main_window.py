import customtkinter as ctk
from datetime import datetime
import tkinter.messagebox as messagebox
from database.db import get_connection


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("공구 등록 프로그램")
        self.geometry("900x650")
        self.minsize(800, 600)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        title = ctk.CTkLabel(self, text="공구 등록 프로그램", font=ctk.CTkFont(size=22, weight="bold"))
        title.pack(pady=(15, 10))

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 왼쪽 프레임
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)

        ctk.CTkLabel(left_frame, text="분류 선택", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))

        ctk.CTkLabel(left_frame, text="대분류").pack(anchor="w", padx=15)
        self.combo_main = ctk.CTkComboBox(left_frame, width=220, state="readonly",
                                          command=self.on_main_category_change)
        self.combo_main.pack(padx=15, pady=(0, 12))

        ctk.CTkLabel(left_frame, text="소분류").pack(anchor="w", padx=15)
        self.combo_sub = ctk.CTkComboBox(left_frame, width=220, state="readonly",
                                         command=self.on_sub_category_change)
        self.combo_sub.pack(padx=15, pady=(0, 12))

        ctk.CTkLabel(left_frame, text="제조사").pack(anchor="w", padx=15)
        self.combo_maker = ctk.CTkComboBox(left_frame, width=220, state="readonly")
        self.combo_maker.pack(padx=15, pady=(0, 12))

        self.check_grade_b = ctk.CTkCheckBox(left_frame, text="B급 재등록")
        self.check_grade_b.pack(anchor="w", padx=15, pady=10)

        # 오른쪽 프레임
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        ctk.CTkLabel(right_frame, text="공구 정보 입력", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))

        self.fields_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.fields_frame.pack(fill="both", expand=True, padx=15)

        self.entries = {}

        fields = [
            ("shank_dia", "생크지름"),
            ("total_length", "전체길이"),
            ("tool_code", "상품코드"),
            ("quantity", "수량"),
            ("diameter", "날지름 (D)"),
            ("length", "날장 (L)"),
            ("effective_len", "유효장 (H)"),
            ("corner_r", "코너R"),
            ("angle", "각도 (°)"),
            ("flute_count", "날 수"),
            ("thread_spec", "나사규격"),
        ]

        for key, label in fields:
            row = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)

            lbl = ctk.CTkLabel(row, text=label, width=100, anchor="w")
            lbl.pack(side="left")

            entry = ctk.CTkEntry(row, width=200)
            entry.pack(side="left", padx=10)

            self.entries[key] = {"label": lbl, "entry": entry, "row": row}

        # 엔터 치면 다음 입력란으로 이동
        entry_list = [self.entries[k]["entry"] for k in self.entries]

        def focus_next(event, idx):
            next_idx = (idx + 1) % len(entry_list)
            entry_list[next_idx].focus_set()
            return "break"

        for i, entry in enumerate(entry_list):
            entry.bind("<Return>", lambda e, idx=i: focus_next(e, idx))

        # 하단 버튼
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        self.btn_register = ctk.CTkButton(btn_frame, text="신규 등록", width=120, height=40,
                                          command=self.on_register)
        self.btn_register.pack(side="left", padx=8)

        self.btn_reregister = ctk.CTkButton(btn_frame, text="재등록", width=120, height=40,
                                            fg_color="#2E8B57", command=self.on_reregister)
        self.btn_reregister.pack(side="left", padx=8)

        self.btn_list = ctk.CTkButton(btn_frame, text="목록 보기", width=120, height=40,
                                      fg_color="#4682B4", command=self.on_show_list)
        self.btn_list.pack(side="left", padx=8)

        self.btn_reset = ctk.CTkButton(btn_frame, text="초기화", width=120, height=40,
                                       fg_color="#A9A9A9", command=self.on_reset)
        self.btn_reset.pack(side="left", padx=8)

        self.status_label = ctk.CTkLabel(self, text="준비됨", text_color="gray")
        self.status_label.pack(pady=(0,10))

    def load_initial_data(self):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT main_name FROM categories ORDER BY id")
        mains = [row["main_name"] for row in cur.fetchall()]
        self.combo_main.configure(values=mains)
        if mains:
            self.combo_main.set(mains[0])
            self.on_main_category_change(mains[0])

        cur.execute("SELECT name FROM makers WHERE is_active = 1 ORDER BY name")
        makers = [row["name"] for row in cur.fetchall()]
        self.combo_maker.configure(values=makers)
        if makers:
            self.combo_maker.set(makers[0])

        conn.close()

    def on_main_category_change(self, choice):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT sub_code FROM categories WHERE main_name = ? ORDER BY id", (choice,))
        subs = [row["sub_code"] for row in cur.fetchall()]
        self.combo_sub.configure(values=subs)
        if subs:
            self.combo_sub.set(subs[0])
            self.on_sub_category_change(subs[0])
        conn.close()

    def on_sub_category_change(self, choice):
        # 일단 모두 숨김
        for key in self.entries:
            self.entries[key]["row"].pack_forget()

        # 엔드밀 계열
        endmill_prefixes = ["EM", "BM", "BN", "RF", "LN"]
        is_endmill = any(choice.startswith(p) for p in endmill_prefixes)

        # 드릴 계열
        is_drill = choice in ["DR", "DR-SGESS", "DR-SGES", "CD", "NC", "FD", "MD"]

        # 탭/쓰레드
        is_tap = "TAP" in choice or choice == "THD"

        # 챔퍼
        is_cm = choice == "CM"

        # 날지름
        if is_endmill or is_drill or is_cm or choice in ["RM", "TC", "SP", "DV", "SR"]:
            self.entries["diameter"]["row"].pack(fill="x", pady=4)

        # 코너R
        if choice.startswith("BN"):
            self.entries["corner_r"]["row"].pack(fill="x", pady=4)

        # 날장
        if is_endmill or is_drill or is_cm:
            self.entries["length"]["row"].pack(fill="x", pady=4)

        # 유효장 (리브 계열)
        if "-R" in choice:
            self.entries["effective_len"]["row"].pack(fill="x", pady=4)

        # 각도
        if is_drill or is_cm:
            self.entries["angle"]["row"].pack(fill="x", pady=4)

        # 날 수
        if is_endmill:
            self.entries["flute_count"]["row"].pack(fill="x", pady=4)

        # 나사규격
        if is_tap:
            self.entries["thread_spec"]["row"].pack(fill="x", pady=4)

        # 공통으로 항상 보이는 것
        always_show = ["shank_dia", "total_length", "tool_code", "quantity"]
        for key in always_show:
            self.entries[key]["row"].pack(fill="x", pady=4)

    def on_register(self):
        try:
            # 1. 입력값 가져오기
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

            # 2. 기본 유효성 검사
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

            # 숫자여야 하는 필드 검사
            number_fields = {
                "diameter": "날지름",
                "length": "날장",
                "effective_len": "유효장",
                "corner_r": "코너R",
                "angle": "각도",
                "flute_count": "날 수",
                "shank_dia": "생크지름",
                "total_length": "전체길이",
            }

            for key, name in number_fields.items():
                value = self.entries[key]["entry"].get().strip()
                # 입력란이 보이는 상태이고, 값이 있을 때만 검사
                if self.entries[key]["row"].winfo_ismapped() and value:
                    try:
                        float(value)
                    except ValueError:
                        messagebox.showwarning("입력 오류", f"{name}은(는) 숫자로 입력하세요.")
                        return

            if not diameter and sub_code not in ["TAP", "TAP-H", "THD"]:
                messagebox.showwarning("입력 오류", "날지름을 입력하세요.")
                return

            # 3. DB 연결
            conn = get_connection()
            cur = conn.cursor()

            # 카테고리 ID 조회
            cur.execute("""
                SELECT id FROM categories 
                WHERE main_name = ? AND sub_code = ?
            """, (main_name, sub_code))
            cat_row = cur.fetchone()
            if not cat_row:
                messagebox.showerror("오류", "카테고리 정보를 찾을 수 없습니다.")
                conn.close()
                return
            category_id = cat_row["id"]

            # 제조사 ID 조회
            cur.execute("SELECT id FROM makers WHERE name = ?", (maker_name,))
            maker_row = cur.fetchone()
            maker_id = maker_row["id"] if maker_row else None

            # 4. 공구명 생성
            tool_name = self.make_tool_name(sub_code, diameter, length, effective_len, corner_r, angle, thread_spec)

            # 5. tools 테이블에 등록
            cur.execute("""
                INSERT INTO tools (
                    category_id, maker_id, tool_code, tool_name,
                    diameter, length, effective_len, corner_r, angle,
                    flute_count, thread_spec, shank_dia, total_length, tool_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                category_id,
                maker_id,
                tool_code if tool_code else None,
                tool_name,
                float(diameter) if diameter else None,
                float(length) if length else None,
                float(effective_len) if effective_len else None,
                float(corner_r) if corner_r else None,
                float(angle) if angle else None,
                int(flute_count) if flute_count else None,
                thread_spec if thread_spec else None,
                float(shank_dia) if shank_dia else None,
                float(total_length) if total_length else None,
                self.get_tool_type(sub_code)
            ))

            tool_id = cur.lastrowid

            # 6. inventory 테이블에 수량만큼 등록
            today = datetime.now().strftime("%y%m%d")
            base_code = tool_code if tool_code else "UNKNOWN"

            for i in range(1, quantity + 1):
                seq = f"{i:02d}"
                barcode = f"{base_code}-{today}-{seq}"
                sub_name = self.make_sub_name(sub_code, diameter, length, flute_count, thread_spec, today, seq, is_grade_b)

            # 오늘 날짜로 이미 등록된 바코드 중 가장 큰 번호 찾기
            cur.execute("""
                SELECT barcode FROM inventory
                WHERE barcode LIKE ?
                ORDER BY barcode DESC
                LIMIT 1
            """, (f"{base_code}-{today}-%",))
            last_row = cur.fetchone()

            start_seq = 1
            if last_row:
                try:
                    last_seq = int(last_row["barcode"].split("-")[-1])
                    start_seq = last_seq + 1
                except:
                    start_seq = 1

            for i in range(quantity):
                seq = f"{start_seq + i:02d}"
                barcode = f"{base_code}-{today}-{seq}"
                sub_name = self.make_sub_name(
                    sub_code, diameter, length, flute_count, thread_spec, today, seq, is_grade_b
                )

                cur.execute("""
                    INSERT INTO inventory (
                        tool_id, barcode, sub_name, quantity, status, is_grade_b
                    ) VALUES (?, ?, ?, 1, ?, ?)
                """, (
                    tool_id,
                    barcode,
                    sub_name,
                    "B급" if is_grade_b else "정상",
                    1 if is_grade_b else 0
                ))

            conn.commit()
            conn.close()

            messagebox.showinfo("등록 완료", f"{quantity}개 등록이 완료되었습니다.")
            self.status_label.configure(text=f"{quantity}개 등록 완료", text_color="green")
            self.on_reset()

        except Exception as e:
            messagebox.showerror("오류 발생", str(e))
            self.status_label.configure(text="등록 실패", text_color="red")

    def on_reregister(self):
        try:
            tool_code = self.entries["tool_code"]["entry"].get().strip()

            if not tool_code:
                messagebox.showwarning("입력 오류", "재등록할 상품코드를 입력하세요.")
                return

            conn = get_connection()
            cur = conn.cursor()

            # 기존 공구 찾기
            cur.execute("""
                SELECT t.id, t.tool_name, t.tool_code, t.diameter, t.length,
                    t.flute_count, t.thread_spec, c.sub_code, m.name as maker_name
                FROM tools t
                JOIN categories c ON t.category_id = c.id
                LEFT JOIN makers m ON t.maker_id = m.id
                WHERE t.tool_code = ?
                ORDER BY t.id DESC
                LIMIT 1
            """, (tool_code,))
            tool = cur.fetchone()

            if not tool:
                messagebox.showinfo("알림", "동일한 상품코드의 공구가 없습니다.")
                conn.close()
                return

            # 확인 메시지
            answer = messagebox.askyesno(
                "재등록 확인",
                f"공구를 찾았습니다.\n\n"
                f"상품명: {tool['tool_name']}\n"
                f"제조사: {tool['maker_name'] or '-'}\n\n"
                f"재등록 하시겠습니까?"
            )
            if not answer:
                conn.close()
                return

            # 수량 입력
            qty_str = ctk.CTkInputDialog(text="등록할 수량을 입력하세요:", title="재등록").get_input()
            if not qty_str or not qty_str.isdigit() or int(qty_str) <= 0:
                messagebox.showwarning("입력 오류", "수량은 1 이상의 정수로 입력하세요.")
                conn.close()
                return
            quantity = int(qty_str)

            # 생크지름 입력
            shank_dia = ctk.CTkInputDialog(text="생크지름을 입력하세요:", title="재등록").get_input()
            if shank_dia is None:
                conn.close()
                return

            # 전체길이 입력
            total_length = ctk.CTkInputDialog(text="전체길이를 입력하세요:", title="재등록").get_input()
            if total_length is None:
                conn.close()
                return

            is_grade_b = self.check_grade_b.get()
            today = datetime.now().strftime("%y%m%d")
            sub_code = tool["sub_code"]

                        # 오늘 날짜로 이미 등록된 바코드 중 가장 큰 번호 찾기
            cur.execute("""
                SELECT barcode FROM inventory
                WHERE barcode LIKE ?
                ORDER BY barcode DESC
                LIMIT 1
            """, (f"{tool_code}-{today}-%",))
            last_row = cur.fetchone()

            start_seq = 1
            if last_row:
                try:
                    last_seq = int(last_row["barcode"].split("-")[-1])
                    start_seq = last_seq + 1
                except:
                    start_seq = 1

            for i in range(quantity):
                seq = f"{start_seq + i:02d}"
                barcode = f"{tool_code}-{today}-{seq}"
                sub_name = self.make_sub_name(
                    sub_code,
                    str(tool["diameter"]) if tool["diameter"] else "",
                    str(tool["length"]) if tool["length"] else "",
                    str(tool["flute_count"]) if tool["flute_count"] else "",
                    tool["thread_spec"] or "",
                    today, seq, is_grade_b
                )

                cur.execute("""
                    INSERT INTO inventory (
                        tool_id, barcode, sub_name, quantity, status, is_grade_b
                    ) VALUES (?, ?, ?, 1, ?, ?)
                """, (
                    tool["id"],
                    barcode,
                    sub_name,
                    "B급" if is_grade_b else "정상",
                    1 if is_grade_b else 0
                ))

            # 생크/전체길이 업데이트 (tools 테이블)
            cur.execute("""
                UPDATE tools 
                SET shank_dia = ?, total_length = ?
                WHERE id = ?
            """, (
                float(shank_dia) if shank_dia else None,
                float(total_length) if total_length else None,
                tool["id"]
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo("재등록 완료", f"{quantity}개 재등록이 완료되었습니다.")
            self.status_label.configure(text=f"{quantity}개 재등록 완료", text_color="green")
            self.on_reset()

        except Exception as e:
            messagebox.showerror("오류 발생", str(e))
            self.status_label.configure(text="재등록 실패", text_color="red")

    # 공구 목록 열기 함수
    def on_show_list(self):
        from ui.list_window import ListWindow
        ListWindow(self)

    def on_reset(self):
        for key in self.entries:
            self.entries[key]["entry"].delete(0, "end")
        self.check_grade_b.deselect()
        self.status_label.configure(text="초기화 완료", text_color="green")

    def make_tool_name(self, sub_code, diameter, length, effective_len, corner_r, angle, thread_spec):
        """상품명 생성"""
        if sub_code in ["TAP", "TAP-H", "THD", "TAP(UNC)", "TAP(UNF)", "TAP-PT", "TAP-NPT"]:
            return thread_spec if thread_spec else "나사"

        parts = []
        if diameter:
            parts.append(f"D{diameter}")
        if length:
            parts.append(f"L{length}")
        if effective_len:
            parts.append(f"H{effective_len}")
        if corner_r:
            parts.append(f"R{corner_r}")
        if angle:
            parts.append(f"{angle}°")

        return " ".join(parts) if parts else "공구"

    def make_sub_name(self, sub_code, diameter, length, flute_count, thread_spec, today, seq, is_grade_b):
        """상품명(부) 생성"""
        tool_type = self.get_tool_type(sub_code)

        if sub_code in ["TAP", "TAP-H", "THD"]:
            name = f"{thread_spec} {tool_type}"
        else:
            name = f"D{diameter}" if diameter else ""
            if flute_count:
                name += f" {flute_count}날"
            name += f" {tool_type}"

        if not is_grade_b:
            name += f" {today}-{seq}"

        return name.strip()

    def get_tool_type(self, sub_code):
        """공구 종류 반환"""
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