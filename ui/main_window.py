import customtkinter as ctk
from datetime import datetime
import tkinter.messagebox as messagebox
from database.db import get_connection


# 보통나사 / 가는나사 (소분류 UNC·UNF가 아니라 버튼으로 구분)
TAP_LISTS = {
    "metric_coarse": ["M2 x 0.4", "M2.5 x 0.45", "M3 x 0.5",
        "M3.5 x 0.6", "M4 x 0.7", "M4.5 x 0.75", "M5 x 0.8",
        "M6 x 1.0", "M7 x 1.0", "M8 x 1.25", "M9 x 1.25", 
        "M10 x 1.5", "M11 x 1.5", "M12 x 1.75", "M14 x 2.0", 
        "M16 x 2.0", "M18 x 2.5", "M20 x 2.5", "M22 x 2.5", 
        "M24 x 3.0", "M27 x 3.0", "M30 x 3.5", "M33 x 3.5", 
        "M36 x 4.0", "M42 x 4.5", "M48 x 5.0",
    ],
    "metric_fine": ["M2 x 0.25", "M2.5 x 0.35", "M3 x 0.35", 
        "M3.5 x 0.35", "M4 x 0.5", "M4.5 x 0.5", "M5 x 0.5", 
        "M6 x 0.75", "M7 x 0.75", "M8 x 0.75", "M8 x 1.0", 
        "M9 x 0.75", "M9 x 1.0", "M10 x 0.75", "M10 x 1.0", 
        "M10 x 1.25", "M11 x 0.75", "M11 x 1.0", "M12 x 1.0", 
        "M12 x 1.25", "M12 x 1.5", "M14 x 1.0", "M14 x 1.25", 
        "M14 x 1.5", "M16 x 1.0", "M16 x 1.5", "M18 x 1.0", 
        "M18 x 1.5", "M18 x 2.0", "M20 x 1.0", "M20 x 1.5", 
        "M20 x 2.0", "M22 x 1.5", "M22 x 2.0", "M24 x 1.5", 
        "M24 x 2.0", "M27 x 1.5", "M27 x 2.0", "M30 x 1.5", 
        "M30 x 2.0", "M33 x 2.0", "M36 x 2.0", "M36 x 3.0", 
        "M42 x 2.0", "M42 x 3.0", "M48 x 2.0", "M48 x 3.0",
    ],
    "inch_coarse": ["#4-40 UNC", "#5-40 UNC", "#6-32 UNC", "#8-32 UNC", 
        "#10-24 UNC", "#12-24 UNC", "1/4-20 UNC", "5/16-18 UNC", 
        "3/8-16 UNC", "7/16-14 UNC", "1/2-13 UNC", "9/16-12 UNC", 
        "5/8-11 UNC", "3/4-10 UNC", "7/8-9 UNC", "1-8 UNC", 
        "1 1/8-7 UNC", "1 1/4-7 UNC", "1 3/8-6 UNC", "1 1/2-6 UNC", "1 3/4-5 UNC", "2-4 1/2 UNC"
    ],
    "inch_fine": ["#4-48 UNF", "#5-44 UNF", "#6-40 UNF", "#8-36 UNF", 
        "#10-32 UNF", "#12-28 UNF", "1/4-28 UNF", "5/16-24 UNF", 
        "3/8-24 UNF", "7/16-20 UNF", "1/2-20 UNF", "9/16-18 UNF", 
        "5/8-18 UNF", "3/4-16 UNF", "7/8-14 UNF", "1-12 UNF", 
        "1 1/8-12 UNF", "1 1/4-12 UNF", "1 3/8-12 UNF", "1 1/2-12 UNF"
    ],
    "heli_metric_coarse": ["M2 x 0.4 STI", "M2.2 x 0.45 STI", "M2.5 x 0.45 STI", "M3 x 0.5 STI", 
        "M3.5 x 0.6 STI", "M4 x 0.7 STI", "M5 x 0.8 STI", "M6 x 1.0 STI", 
        "M7 x 1.0 STI", "M8 x 1.25 STI", "M9 x 1.25 STI", "M10 x 1.5 STI", 
        "M11 x 1.5 STI", "M12 x 1.75 STI", "M14 x 2.0 STI", "M16 x 2.0 STI", 
        "M18 x 2.5 STI", "M20 x 2.5 STI", "M22 x 2.5 STI", "M24 x 3.0 STI", 
        "M27 x 3.0 STI", "M30 x 3.5 STI", "M33 x 3.5 STI", "M36 x 4.0 STI", "M39 x 4.0 STI"],
    "heli_metric_fine": ["M8 x 1.0 STI", "M10 x 1.0 STI", "M10 x 1.25 STI", "M11 x 1.0 STI", 
        "M11 x 1.25 STI", "M12 x 1.25 STI", "M12 x 1.5 STI", "M14 x 1.5 STI", 
        "M16 x 1.5 STI", "M18 x 1.5 STI", "M18 x 2.0 STI", "M20 x 1.5 STI", 
        "M20 x 2.0 STI", "M22 x 1.5 STI", "M22 x 2.0 STI", "M24 x 2.0 STI", 
        "M27 x 2.0 STI", "M30 x 2.0 STI", "M33 x 2.0 STI", "M36 x 2.0 STI", 
        "M36 x 3.0 STI", "M39 x 2.0 STI"],
    "heli_inch_coarse": ["#1-64 UNC STI", "#2-56 UNC STI", "#3-48 UNC STI", "#4-40 UNC STI", 
        "#5-40 UNC STI", "#6-32 UNC STI", "#8-32 UNC STI", "#10-24 UNC STI", 
        "#12-24 UNC STI", "1/4-20 UNC STI", "5/16-18 UNC STI", "3/8-16 UNC STI", 
        "7/16-14 UNC STI", "1/2-13 UNC STI", "9/16-12 UNC STI", "5/8-11 UNC STI", 
        "3/4-10 UNC STI", "7/8-9 UNC STI", "1-8 UNC STI", "1 1/8-7 UNC STI", 
        "1 1/4-7 UNC STI", "1 3/8-6 UNC STI", "1 1/2-6 UNC STI"],
    "heli_inch_fine": ["#2-64 UNF STI", "#3-56 UNF STI", "#4-48 UNF STI", "#5-44 UNF STI", 
        "#6-40 UNF STI", "#8-36 UNF STI", "#10-32 UNF STI", "#12-28 UNF STI", 
        "1/4-28 UNF STI", "5/16-24 UNF STI", "3/8-24 UNF STI", "7/16-20 UNF STI", 
        "1/2-20 UNF STI", "9/16-18 UNF STI", "5/8-18 UNF STI", "3/4-16 UNF STI", 
        "7/8-14 UNF STI", "1-12 UNF STI", "1 1/8-12 UNF STI", "1 1/4-12 UNF STI", 
        "1 3/8-12 UNF STI", "1 1/2-12 UNF STI"],
    "pt": ["PT 1/8-28", "PT 1/4-19", "PT 3/8-19", "PT 1/2-14", "PT 3/4-14", "PT 1-11", "PT 1 1/4-11", "PT 1 1/2-11", "PT 2-11", "PT 2 1/2-11", "PT 3-11", "PT 4-11"],
    "npt": ["NPT 1/16-27", "NPT 1/8-27", "NPT 1/4-18", "NPT 3/8-18", 
            "NPT 1/2-14", "NPT 3/4-14", "NPT 1-11.5", "NPT 1 1/4-11.5", 
            "NPT 1 1/2-11.5", "NPT 2-11.5", "NPT 2 1/2-8", "NPT 3-8", "NPT 3 1/2-8", "NPT 4-8"],
    "thd_coarse": ["M2 x 0.4", "M2.5 x 0.45", "M3 x 0.5", "M3.5 x 0.6", 
                   "M4 x 0.7", "M4.5 x 0.75", "M5 x 0.8", "M6 x 1.0", 
                   "M7 x 1.0", "M8 x 1.25", "M9 x 1.25", "M10 x 1.5", 
                   "M11 x 1.5", "M12 x 1.75", "M14 x 2.0", "M16 x 2.0", 
                   "M18 x 2.5", "M20 x 2.5", "M22 x 2.5", "M24 x 3.0", 
                   "M27 x 3.0", "M30 x 3.5", "M33 x 3.5", "M36 x 4.0", 
                   "M42 x 4.5", "M48 x 5.0"],
    "thd_fine": ["M2 x 0.25", "M2.5 x 0.35", "M3 x 0.35", "M3.5 x 0.35", 
                 "M4 x 0.5", "M4.5 x 0.5", "M5 x 0.5", "M6 x 0.75", 
                 "M7 x 0.75", "M8 x 0.75", "M8 x 1.0", "M9 x 0.75", 
                 "M9 x 1.0", "M10 x 0.75", "M10 x 1.0", "M10 x 1.25", 
                 "M11 x 0.75", "M11 x 1.0", "M12 x 1.0", "M12 x 1.25", 
                 "M12 x 1.5", "M14 x 1.0", "M14 x 1.25", "M14 x 1.5", 
                 "M16 x 1.0", "M16 x 1.5", "M18 x 1.0", "M18 x 1.5", 
                 "M18 x 2.0", "M20 x 1.0", "M20 x 1.5", "M20 x 2.0", 
                 "M22 x 1.5", "M22 x 2.0", "M24 x 1.5", "M24 x 2.0", 
                 "M27 x 1.5", "M27 x 2.0", "M30 x 1.5", "M30 x 2.0", 
                 "M33 x 2.0", "M36 x 2.0", "M36 x 3.0", "M42 x 2.0", 
                 "M42 x 3.0", "M48 x 2.0", "M48 x 3.0"],
}


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("공구 등록 프로그램")
        self.geometry("980x760")
        self.minsize(880, 640)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.all_makers = []
        self.all_subs = []
        self.all_mains = []
        self.current_main = ""
        self.tap_mode = "coarse"

        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        title = ctk.CTkLabel(
            self, text="공구 등록 프로그램",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(pady=(15, 10))

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        left_frame = ctk.CTkFrame(main_frame, width=260)
        left_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)
        left_frame.pack_propagate(False)

        ctk.CTkLabel(
            left_frame, text="분류 선택",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 12))

        ctk.CTkLabel(left_frame, text="대분류").pack(anchor="w", padx=15)
        self.combo_main = ctk.CTkComboBox(
            left_frame, width=220,
            command=self.on_main_category_change
        )
        self.combo_main.pack(padx=15, pady=(0, 10))
        self.combo_main.bind("<KeyRelease>", self.on_main_keyrelease)

        ctk.CTkLabel(left_frame, text="소분류").pack(anchor="w", padx=15)
        self.combo_sub = ctk.CTkComboBox(
            left_frame, width=220,
            command=self.on_sub_category_change
        )
        self.combo_sub.pack(padx=15, pady=(0, 10))
        self.combo_sub.bind("<KeyRelease>", self.on_sub_keyrelease)

        ctk.CTkLabel(left_frame, text="제조사").pack(anchor="w", padx=15)
        self.entry_maker = ctk.CTkEntry(left_frame, width=220, placeholder_text="제조사 검색")
        self.entry_maker.pack(padx=15, pady=(0, 4))
        self.entry_maker.bind("<KeyRelease>", self.on_maker_keyrelease)

        self.maker_list = ctk.CTkScrollableFrame(left_frame, width=220, height=180)
        self.maker_list.pack(padx=15, pady=(0, 8), fill="x")

        self.check_grade_b = ctk.CTkCheckBox(left_frame, text="B급 등록")
        self.check_grade_b.pack(anchor="w", padx=15, pady=8)

        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        ctk.CTkLabel(
            right_frame, text="공구 정보 입력",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="top", pady=(10, 8))

        self.form_box = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.form_box.pack(side="top", fill="x", padx=15, pady=(0, 10))

        self.entries = {}
        fields = [
            ("tool_code", "상품코드"),
            ("diameter", "날지름 (D)"),
            ("length", "날장 (L)"),
            ("effective_len", "유효장 (H)"),
            ("corner_r", "코너R"),
            ("angle", "날 끝각도 (°)"),
            ("flute_count", "날 수"),
            ("thickness", "날두께 (T)"),
            ("neck_dia", "목직경 (d)"),
            ("thread_spec", "나사규격"),
            ("shank_dia", "생크지름"),
            ("total_length", "전체길이"),
            ("quantity", "수량"),
        ]

        for key, label in fields:
            row = ctk.CTkFrame(self.form_box, fg_color="transparent")
            ctk.CTkLabel(row, text=label, width=110, anchor="w").pack(side="left")
            widget = ctk.CTkEntry(row, width=220)
            widget.pack(side="left")
            self.entries[key] = {"row": row, "entry": widget}

        # 나사 보통/가는 버튼 + 스크롤 목록
        self.tap_btn_row = ctk.CTkFrame(self.form_box, fg_color="transparent")
        self.btn_coarse = ctk.CTkButton(
            self.tap_btn_row, text="보통나사", width=100, height=28,
            command=lambda: self.set_tap_mode("coarse")
        )
        self.btn_coarse.pack(side="left", padx=(110, 6))
        self.btn_fine = ctk.CTkButton(
            self.tap_btn_row, text="가는나사", width=100, height=28,
            fg_color="#7F8C8D",
            command=lambda: self.set_tap_mode("fine")
        )
        self.btn_fine.pack(side="left", padx=6)

        self.tap_list_row = ctk.CTkFrame(self.form_box, fg_color="transparent")
        ctk.CTkLabel(self.tap_list_row, text="", width=110).pack(side="left")
        self.tap_list = ctk.CTkScrollableFrame(self.tap_list_row, width=220, height=150)
        self.tap_list.pack(side="left")

        entry_keys = [k for k in self.entries.keys() if k != "thread_spec"]

        def focus_next(idx):
            nxt = idx + 1
            while nxt < len(entry_keys):
                key = entry_keys[nxt]
                if self.entries[key]["row"].winfo_ismapped():
                    self.entries[key]["entry"].focus()
                    break
                nxt += 1

        for i, key in enumerate(entry_keys):
            self.entries[key]["entry"].bind("<Return>", lambda e, n=i: focus_next(n))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(
            btn_frame, text="등록", width=100, height=36,
            command=self.on_register
        ).pack(side="left", padx=6)

        self.entry_search_code = ctk.CTkEntry(
            btn_frame, width=160, height=36,
            placeholder_text="상품코드를 입력하세요"
        )
        self.entry_search_code.pack(side="left", padx=6)

        ctk.CTkButton(
            btn_frame, text="검색 등록", width=100, height=36,
            fg_color="#2E8B57", hover_color="#256F46",
            command=self.on_search_register
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_frame, text="A급 공구 목록", width=120, height=36,
            fg_color="#3B8ED0",
            command=lambda: self.on_show_list(grade="A")
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_frame, text="B급 공구 목록", width=120, height=36,
            fg_color="#3B8ED0",
            command=lambda: self.on_show_list(grade="B")
        ).pack(side="left", padx=6)

        self.status_label = ctk.CTkLabel(self, text="준비됨", text_color="gray")
        self.status_label.pack(pady=(0, 10))

    def render_makers(self, keyword=""):
        for w in self.maker_list.winfo_children():
            w.destroy()
        typed = keyword.strip().lower()
        items = self.all_makers
        if typed:
            items = [x for x in self.all_makers if typed in x.lower()]
        for name in items:
            ctk.CTkButton(
                self.maker_list, text=name, width=200, height=26,
                anchor="w", fg_color="transparent",
                text_color=("black", "white"),
                command=lambda n=name: self.select_maker(n)
            ).pack(fill="x", pady=1)

    def select_maker(self, name):
        self.entry_maker.delete(0, "end")
        self.entry_maker.insert(0, name)

    def get_maker(self):
        return self.entry_maker.get().strip()

    def set_tap_mode(self, mode):
        self.tap_mode = mode
        if mode == "coarse":
            self.btn_coarse.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.btn_fine.configure(fg_color="#7F8C8D")
        else:
            self.btn_fine.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.btn_coarse.configure(fg_color="#7F8C8D")
        self.render_tap_specs()

    def is_inch_tap(self):
        main = self.current_main or self.combo_main.get() or ""
        return main.startswith("TAP-I") or "인치" in main

    def is_metric_tap(self):
        main = self.current_main or self.combo_main.get() or ""
        return main.startswith("TAP-M") or "미터" in main

    def current_tap_specs(self):
        sub = self.combo_sub.get().strip()
        fine = self.tap_mode == "fine"
        if sub == "TAP-NPT":
            return TAP_LISTS["npt"]
        if sub == "TAP-PT":
            return TAP_LISTS["pt"]
        if sub == "THD(UNC)":
            return TAP_LISTS["inch_coarse"]
        if sub == "THD(UNF)":
            return TAP_LISTS["inch_fine"]
        if sub == "TAP(UNF)":
            return TAP_LISTS["inch_fine"]
        if sub == "TAP(UNC)":
            return TAP_LISTS["inch_coarse"]
        if sub == "TAP-H(UNF)":
            return TAP_LISTS["heli_inch_fine"]
        if sub == "TAP-H(UNC)":
            return TAP_LISTS["heli_inch_coarse"]
        if sub == "THD" and self.is_inch_tap():
            return TAP_LISTS["inch_fine"] + TAP_LISTS["inch_coarse"]
        if sub == "THD":
            return TAP_LISTS["thd_fine" if fine else "thd_coarse"]
        if sub == "TAP-H":
            return TAP_LISTS["heli_metric_fine" if fine else "heli_metric_coarse"]
        if self.is_inch_tap():
            return TAP_LISTS["inch_coarse"]
        return TAP_LISTS["metric_fine" if fine else "metric_coarse"]

    def tap_type_label(self):
        sub = self.combo_sub.get().strip()
        fine = self.tap_mode == "fine"
        pitch = "가는나사" if fine else "보통나사"
        if self.is_inch_tap():
            if sub == "TAP-NPT":
                return "NPT탭"
            if sub == "TAP-PT":
                return "PT탭"
            if sub == "THD":
                return "쓰레드"
            if "TAP-H" in sub:
                return "헬리탭"
            return "인치탭"
        if sub == "THD":
            return f"{pitch} 쓰레드"
        if sub == "TAP-H":
            return f"{pitch} 헬리탭"
        return f"{pitch} 탭"

    def render_tap_specs(self):
        for w in self.tap_list.winfo_children():
            w.destroy()
        specs = self.current_tap_specs()
        for spec in specs:
            ctk.CTkButton(
                self.tap_list, text=spec, width=200, height=26,
                anchor="w", fg_color="transparent",
                text_color=("black", "white"),
                command=lambda s=spec: self.select_thread(s)
            ).pack(fill="x", pady=1)

    def select_thread(self, spec):
        e = self.entries["thread_spec"]["entry"]
        e.delete(0, "end")
        e.insert(0, spec)

    def load_initial_data(self):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT main_name FROM categories ORDER BY id")
        mains = [row["main_name"] for row in cur.fetchall()]
        self.all_mains = mains
        self.combo_main.configure(values=mains)
        if mains:
            self.combo_main.set(mains[0])
            self.on_main_category_change(mains[0])

        cur.execute("SELECT name FROM makers WHERE is_active = 1 ORDER BY name")
        makers = [row["name"] for row in cur.fetchall()]
        conn.close()
        self.all_makers = makers
        self.render_makers()
        if makers:
            self.select_maker(makers[0])

    def on_main_category_change(self, choice):
        self.current_main = choice
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT sub_code FROM categories WHERE main_name = ? ORDER BY id",
            (choice,)
        )
        subs = [row["sub_code"] for row in cur.fetchall()]
        conn.close()
        self.all_subs = subs
        self.combo_sub.configure(values=subs)
        if subs:
            self.combo_sub.set(subs[0])
            self.on_sub_category_change(subs[0])

    def _clear_entry(self, key):
        self.entries[key]["entry"].delete(0, "end")

    def on_sub_category_change(self, choice):
        keep = {"tool_code", "quantity"}
        for key in self.entries:
            if key not in keep:
                self._clear_entry(key)
            self.entries[key]["row"].pack_forget()
        self.tap_btn_row.pack_forget()
        self.tap_list_row.pack_forget()

        endmill_prefixes = ["EM", "BM", "BN", "RF", "LN"]
        is_endmill = any(choice.startswith(p) for p in endmill_prefixes)
        is_drill = choice in ["DR", "DR-SGESS", "DR-SGES", "CD", "NC", "FD", "MD"]
        is_tap = str(choice).startswith("TAP") or str(choice).startswith("THD")
        is_rm = choice == "RM"
        is_cm = choice == "CM"
        is_tc = choice == "TC"
        is_dv = choice == "DV"

        def show(key):
            if key in self.entries:
                self.entries[key]["row"].pack(fill="x", pady=4, side="top", anchor="w")

        show("tool_code")

        if is_endmill:
            show("diameter")
            show("length")
            if choice.startswith("BN"):
                show("corner_r")
            if "-R" in choice:
                show("effective_len")
            show("flute_count")
        elif is_drill:
            show("diameter")
            show("length")
            show("angle")
        elif is_rm:
            show("diameter")
            show("length")
        elif is_cm:
            show("diameter")
        elif is_tc:
            show("diameter")
            show("thickness")
            show("neck_dia")
            show("flute_count")
        elif is_dv:
            show("diameter")
            show("angle")
        elif is_tap:
            show("thread_spec")
            if self.is_metric_tap() and self.combo_sub.get() in ("TAP", "TAP-H", "THD"):
                self.tap_btn_row.pack(
                    fill="x", pady=(0, 4), side="top",
                    after=self.entries["thread_spec"]["row"]
                )
                self.tap_list_row.pack(fill="x", pady=(0, 4), side="top", after=self.tap_btn_row)
                self.set_tap_mode("coarse")
            else:
                self.tap_list_row.pack(
                    fill="x", pady=(0, 4), side="top",
                    after=self.entries["thread_spec"]["row"]
                )
                self.render_tap_specs()
        else:
            show("diameter")
            show("length")

        show("shank_dia")
        show("total_length")
        show("quantity")

    def _filter_list(self, source_list, typed):
        typed = typed.strip().lower()
        if not typed:
            return list(source_list)
        starts = [x for x in source_list if x.lower().startswith(typed)]
        contains = [x for x in source_list if typed in x.lower() and x not in starts]
        return starts + contains

    def on_maker_keyrelease(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Left", "Right", "Tab"):
            return
        self.render_makers(self.entry_maker.get())

    def on_main_keyrelease(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Left", "Right", "Tab"):
            return
        typed = self.combo_main.get()
        filtered = self._filter_list(self.all_mains, typed)
        self.combo_main.configure(values=filtered if filtered else self.all_mains)

    def on_sub_keyrelease(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Left", "Right", "Tab"):
            return
        typed = self.combo_sub.get()
        filtered = self._filter_list(self.all_subs, typed)
        self.combo_sub.configure(values=filtered if filtered else self.all_subs)

    def visible_value(self, key):
        if key not in self.entries:
            return ""
        if not self.entries[key]["row"].winfo_ismapped():
            return ""
        return self.entries[key]["entry"].get().strip()

    def on_register(self):
        try:
            main_name = self.combo_main.get()
            sub_code = self.combo_sub.get()
            maker_name = self.get_maker()
            is_grade_b = self.check_grade_b.get()

            diameter = self.visible_value("diameter")
            length = self.visible_value("length")
            effective_len = self.visible_value("effective_len")
            corner_r = self.visible_value("corner_r")
            angle = self.visible_value("angle")
            flute_count = self.visible_value("flute_count")
            thickness = self.visible_value("thickness")
            neck_dia = self.visible_value("neck_dia")
            thread_spec = self.visible_value("thread_spec")
            shank_dia = self.visible_value("shank_dia")
            total_length = self.visible_value("total_length")
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
                "thickness": "날두께", "neck_dia": "목직경",
                "shank_dia": "생크지름", "total_length": "전체길이",
            }
            for key, name in number_fields.items():
                value = self.visible_value(key)
                if value:
                    try:
                        float(value)
                    except ValueError:
                        messagebox.showwarning("입력 오류", f"{name}은(는) 숫자로 입력하세요.")
                        return

            is_tap = sub_code.startswith("TAP") or sub_code == "THD"
            if not is_tap and not diameter:
                messagebox.showwarning("입력 오류", "날지름을 입력하세요.")
                return
            if is_tap and not thread_spec:
                messagebox.showwarning("입력 오류", "나사규격을 선택하세요.")
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
                sub_code, diameter, length, effective_len, corner_r, angle,
                thread_spec, flute_count, thickness, neck_dia
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
                    today, seq, is_grade_b, angle, thickness, neck_dia
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

    def on_reregister(self):
        try:
            tool_code = self.entries["tool_code"]["entry"].get().strip()
            if not tool_code:
                tool_code = self.entry_search_code.get().strip()
            if not tool_code:
                messagebox.showwarning("입력 오류", "재등록할 상품코드를 입력하세요.")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT t.id, t.tool_name, t.tool_code, t.diameter, t.length,
                       t.flute_count, t.thread_spec, t.shank_dia, t.total_length,
                       t.angle, c.sub_code, m.name as maker_name
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
                    today, seq, is_grade_b,
                    "" if tool["angle"] is None else str(tool["angle"]),
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

    def on_search_register(self):
        code = self.entry_search_code.get().strip()
        if not code:
            messagebox.showwarning("입력 오류", "상품코드를 입력하세요.")
            return
        self.entries["tool_code"]["entry"].delete(0, "end")
        self.entries["tool_code"]["entry"].insert(0, code)
        self.on_reregister()

    def on_show_list(self, grade=None):
        from ui.list_window import ListWindow
        ListWindow(self, grade=grade)

    def on_reset(self):
        for key in self.entries:
            self._clear_entry(key)
        self.status_label.configure(text="초기화 완료", text_color="green")

    def fmt_num(self, value):
        if value is None or value == "":
            return ""
        try:
            return f"{float(value):.1f}"
        except (ValueError, TypeError):
            return str(value)

    def make_tool_name(self, sub_code, diameter, length, effective_len,
                       corner_r, angle, thread_spec,
                       flute_count="", thickness="", neck_dia=""):
        if str(sub_code).startswith("TAP") or sub_code == "THD":
            return thread_spec if thread_spec else "나사"

        if sub_code == "RM":
            parts = []
            if diameter:
                parts.append(f"D{self.fmt_num(diameter)}")
            if length:
                parts.append(f"L{self.fmt_num(length)}")
            parts.append("리머")
            return " ".join(parts)

        if sub_code == "CM":
            return f"D{self.fmt_num(diameter)} CM" if diameter else "CM"

        if sub_code == "TC":
            parts = []
            if diameter:
                parts.append(f"D{self.fmt_num(diameter)}")
            if thickness:
                parts.append(f"T{self.fmt_num(thickness)}")
            if neck_dia:
                parts.append(f"d{self.fmt_num(neck_dia)}")
            if flute_count:
                parts.append(f"{flute_count}날")
            parts.append("T커터")
            return " ".join(parts)

        if sub_code == "DV":
            parts = []
            if diameter:
                parts.append(f"D{self.fmt_num(diameter)}")
            if angle:
                parts.append(f"{self.fmt_num(angle)}°")
            parts.append("더브테일")
            return " ".join(parts)

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

    def make_sub_name(self, sub_code, diameter, length, flute_count, thread_spec,
                      today, seq, is_grade_b, angle="", thickness="", neck_dia=""):
        tool_type = self.get_tool_type(sub_code)

        if str(sub_code).startswith("TAP") or sub_code == "THD":
            name = f"{thread_spec} {self.tap_type_label()}".strip()
        elif sub_code in ("RM", "CM", "TC", "DV"):
            name = self.make_tool_name(
                sub_code, diameter, length, "", "", angle, "",
                flute_count, thickness, neck_dia
            )
        else:
            parts = []
            if diameter is not None and str(diameter).strip() != "":
                parts.append(f"D{self.fmt_num(diameter)}")
            if length is not None and str(length).strip() != "":
                parts.append(f"L{self.fmt_num(length)}")
            if flute_count is not None and str(flute_count).strip() != "":
                parts.append(f"{flute_count}날")
            if tool_type:
                parts.append(tool_type)
            name = " ".join(parts)

        name = f"{name} {today}-{seq}".strip()
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
            "CM": "CM", "RM": "리머", "TC": "T커터", "DV": "더브테일", "SP": "특수제작공구",
            "THD": "쓰레드",
            "TAP": "탭", "TAP-H": "헬리탭",
            "TAP(UNF)": "UNF탭", "TAP(UNC)": "UNC탭",
            "TAP-H(UNF)": "헬리탭", "TAP-H(UNC)": "헬리탭",
            "TAP-NPT": "NPT탭", "TAP-PT": "PT탭",
            "TAP-M": "탭", "TAP-MF": "가는나사 탭",
        }
        return mapping.get(sub_code, "")


def run_app():
    app = MainWindow()
    app.mainloop()
