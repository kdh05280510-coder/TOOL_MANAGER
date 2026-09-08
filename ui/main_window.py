import customtkinter as ctk
from datetime import datetime
import tkinter.messagebox as messagebox
from urllib.parse import quote_plus
from pathlib import Path
from database.db import get_connection, get_base_dir


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
        self.list_win = None
        self.search_driver = None

        self.create_widgets()
        self.load_initial_data()
        self.protocol("WM_DELETE_WINDOW", self.on_app_close)

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
            ("etc_note", "기타"),
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
            if key == "tool_code":
                ctk.CTkButton(
                    row, text="AI검색", width=60, height=28,
                    command=lambda: self.on_web_search_code("ai"),
                ).pack(side="left", padx=(8, 0))
                ctk.CTkButton(
                    row, text="제미나이", width=64, height=28,
                    fg_color="#8E44AD", hover_color="#6C3483",
                    command=lambda: self.on_web_search_code("gemini"),
                ).pack(side="left", padx=(4, 0))

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

    def is_sp_main(self):
        main = self.current_main or self.combo_main.get() or ""
        return main.startswith("SP") or "특수" in main

    def load_thread_specs(self, *keys):
        conn = get_connection()
        cur = conn.cursor()
        out = []
        seen = set()
        for key in keys:
            cur.execute(
                "SELECT spec FROM thread_specs WHERE standard = ? ORDER BY id",
                (key,),
            )
            for row in cur.fetchall():
                spec = row["spec"]
                if spec and spec not in seen:
                    seen.add(spec)
                    out.append(spec)
        conn.close()
        return out

    def current_tap_specs(self):
        sub = self.combo_sub.get().strip()
        fine = self.tap_mode == "fine"
        if sub == "TAP-NPT":
            return self.load_thread_specs("npt")
        if sub == "TAP-PT":
            return self.load_thread_specs("pt")
        if sub in ("THD(UNC)", "TAP(UNC)"):
            return self.load_thread_specs("inch_coarse")
        if sub in ("THD(UNF)", "TAP(UNF)"):
            return self.load_thread_specs("inch_fine")
        if sub == "TAP-H(UNF)":
            return self.load_thread_specs("heli_inch_fine")
        if sub == "TAP-H(UNC)":
            return self.load_thread_specs("heli_inch_coarse")
        if sub == "THD" and self.is_inch_tap():
            return self.load_thread_specs("inch_fine", "inch_coarse")
        if sub == "THD":
            return self.load_thread_specs("thd_fine" if fine else "thd_coarse")
        if sub == "TAP-H":
            return self.load_thread_specs(
                "heli_metric_fine" if fine else "heli_metric_coarse"
            )
        if self.is_inch_tap():
            return self.load_thread_specs("inch_coarse")
        return self.load_thread_specs("metric_fine" if fine else "metric_coarse")

    def tap_type_label(self):
        sub = self.combo_sub.get().strip()
        pitch = "fine" if self.tap_mode == "fine" else "coarse"
        conn = get_connection()
        cur = conn.cursor()
        row = None
        try:
            cur.execute(
                "SELECT label FROM tap_labels WHERE sub_code = ? AND pitch = ?",
                (sub, pitch),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT label FROM tap_labels WHERE sub_code = ? AND pitch = 'any'",
                    (sub,),
                )
                row = cur.fetchone()
        except Exception:
            row = None
        conn.close()
        if row and row["label"]:
            return row["label"]
        return self.get_tool_type(sub, self.current_main) or "탭"

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
        is_thd = str(choice).upper().startswith("THD")
        is_tap = str(choice).startswith("TAP") or is_thd
        is_rm = choice == "RM"
        is_cm = choice == "CM"
        is_tc = choice == "TC"
        is_dv = choice == "DV"

        def show(key):
            if key in self.entries:
                self.entries[key]["row"].pack(fill="x", pady=4, side="top", anchor="w")

        if self.is_sp_main():
            for key in self.entries:
                show(key)
            if is_tap:
                if self.combo_sub.get() in ("TAP", "TAP-H", "THD"):
                    self.tap_btn_row.pack(
                        fill="x", pady=(0, 4), side="top",
                        after=self.entries["thread_spec"]["row"]
                    )
                    self.tap_list_row.pack(
                        fill="x", pady=(0, 4), side="top", after=self.tap_btn_row
                    )
                    self.set_tap_mode("coarse")
                else:
                    self.tap_list_row.pack(
                        fill="x", pady=(0, 4), side="top",
                        after=self.entries["thread_spec"]["row"]
                    )
                    self.render_tap_specs()
            return

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
            if is_thd:
                show("diameter")
                show("length")
                show("effective_len")
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

    def ensure_search_driver(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        if self.search_driver is not None:
            try:
                _ = self.search_driver.current_url
                return
            except Exception:
                try:
                    self.search_driver.quit()
                except Exception:
                    pass
                self.search_driver = None

        options = Options()
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        profile_dir = get_base_dir() / "data" / "chrome_search_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_dir}")
        self.search_driver = webdriver.Chrome(options=options)

    def submit_gemini_query(self, query):
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        driver = self.search_driver
        current = ""
        try:
            current = driver.current_url or ""
        except Exception:
            current = ""
        if "gemini.google.com" not in current:
            driver.get("https://gemini.google.com/app")

        wait = WebDriverWait(driver, 20)
        selectors = [
            "div.ql-editor[contenteditable='true']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
            "rich-textarea textarea",
            "textarea",
        ]
        box = None
        last_err = None
        for sel in selectors:
            try:
                box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                if box:
                    break
            except Exception as e:
                last_err = e
                box = None
        if box is None:
            raise RuntimeError(
                "제미나이 입력칸을 찾지 못했습니다.\n"
                "검색 창에서 구글 로그인 후 다시 [제미나이]를 누르세요."
            )

        try:
            driver.execute_script("arguments[0].click();", box)
        except Exception:
            box.click()
        time.sleep(0.25)
        try:
            box.send_keys(Keys.CONTROL, "a")
            box.send_keys(Keys.BACKSPACE)
        except Exception:
            pass
        box.send_keys(query)
        time.sleep(0.2)
        box.send_keys(Keys.ENTER)
        time.sleep(0.3)
        for sel in (
            "button[aria-label='전송']",
            "button[aria-label='보내기']",
            "button[aria-label='Send']",
            "button.send-button",
        ):
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, sel)
                if btns and btns[0].is_enabled():
                    btns[0].click()
                    break
            except Exception:
                pass

    def on_web_search_code(self, target="ai"):
        code = self.entries["tool_code"]["entry"].get().strip()
        if not code:
            messagebox.showwarning("입력 오류", "상품코드를 입력하세요.")
            return
        q = f"{code} 공구 제원 날지름 날장 생크지름 전체길이"
        try:
            self.ensure_search_driver()
            if target == "gemini":
                self.submit_gemini_query(q)
                label = "제미나이"
            else:
                url = "https://www.google.com/search?udm=50&hl=ko&q=" + quote_plus(q)
                self.search_driver.get(url)
                label = "구글 AI모드"
            self.status_label.configure(
                text=f"{label}: {code}  →  같은 창에서 검색",
                text_color="green",
            )
        except Exception as e:
            messagebox.showerror("검색 실패", str(e))

    def on_app_close(self):
        if self.search_driver is not None:
            try:
                self.search_driver.quit()
            except Exception:
                pass
            self.search_driver = None
        self.destroy()

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
            etc_note = self.visible_value("etc_note")
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

            is_tap = sub_code.startswith("TAP") or sub_code.startswith("THD")
            is_sp = self.is_sp_main()
            if not is_sp:
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
                thread_spec, flute_count, thickness, neck_dia, etc_note
            )

            def to_f(v):
                if not v:
                    return None
                return float(v)

            cur.execute("""
                INSERT INTO tools (
                    category_id, maker_id, tool_code, tool_name,
                    diameter, length, effective_len, corner_r, angle,
                    flute_count, thread_spec, shank_dia, total_length,
                    tool_type, remark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                category_id, maker_id,
                tool_code if tool_code else None,
                tool_name,
                to_f(diameter), to_f(length), to_f(effective_len),
                to_f(corner_r), to_f(angle),
                int(float(flute_count)) if flute_count else None,
                thread_spec if thread_spec else None,
                to_f(shank_dia), to_f(total_length),
                self.get_tool_type(sub_code, main_name),
                etc_note if etc_note else None,
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
                    today, seq, is_grade_b, angle, thickness, neck_dia,
                    effective_len, corner_r, etc_note
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
                conn.close()
                return False

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
                return True

            qty_str = ctk.CTkInputDialog(
                text="등록할 수량을 입력하세요:", title="재등록"
            ).get_input()
            if not qty_str or not qty_str.isdigit() or int(qty_str) <= 0:
                messagebox.showwarning("입력 오류", "수량은 1 이상의 정수로 입력하세요.")
                conn.close()
                return True
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
            return True

        except Exception as e:
            messagebox.showerror("오류 발생", str(e))
            self.status_label.configure(text="재등록 실패", text_color="red")
            return True

    def on_search_register(self):
        code = self.entry_search_code.get().strip()
        if not code:
            messagebox.showwarning("입력 오류", "상품코드를 입력하세요.")
            return
        self.entries["tool_code"]["entry"].delete(0, "end")
        self.entries["tool_code"]["entry"].insert(0, code)

        if self.on_reregister():
            return

        messagebox.showinfo(
            "알림",
            "동일한 상품코드의 등록 공구가 없습니다.\n제원은 직접 입력하세요.",
        )

    def on_show_list(self, grade=None):
        from ui.list_window import ListWindow
        win = self.list_win
        if win is not None:
            try:
                if win.winfo_exists():
                    win.apply_grade(grade)
                    win.deiconify()
                    win.bring_to_front()
                    return
            except Exception:
                self.list_win = None
        win = ListWindow(self, grade=grade)
        self.list_win = win
        win.protocol("WM_DELETE_WINDOW", self.on_list_close)

    def on_list_close(self):
        if self.list_win is not None:
            try:
                self.list_win.destroy()
            except Exception:
                pass
        self.list_win = None

    def on_reset(self):
        for key in self.entries:
            self._clear_entry(key)
        self.status_label.configure(text="초기화 완료", text_color="green")

    def fmt_num(self, value):
        if value is None or value == "":
            return ""
        try:
            s = str(value).strip()

        # 소수점이 없는 숫자라면 .0 추가
            if "." not in s:
                return s + ".0"

        # 소수점이 있으면 입력값 그대로 반환
            return s

        except (ValueError, TypeError):
            return str(value)

    def collect_filled_name_parts(self, sub_code, diameter, length, effective_len,
                                  corner_r, angle, thread_spec,
                                  flute_count="", thickness="", neck_dia="",
                                  etc_note="", main_name=None):
        parts = []
        if thread_spec:
            parts.append(str(thread_spec).strip())
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
        if thickness:
            parts.append(f"T{self.fmt_num(thickness)}")
        if neck_dia:
            parts.append(f"d{self.fmt_num(neck_dia)}")
        if flute_count:
            parts.append(f"{flute_count}날")
        if etc_note:
            parts.append(str(etc_note).strip())
        tool_type = self.get_tool_type(sub_code, main_name or self.current_main)
        if tool_type and tool_type not in parts:
            parts.append(tool_type)
        return parts

    def make_tool_name(self, sub_code, diameter, length, effective_len,
                       corner_r, angle, thread_spec,
                       flute_count="", thickness="", neck_dia="", etc_note=""):
        if self.is_sp_main():
            parts = self.collect_filled_name_parts(
                sub_code, diameter, length, effective_len, corner_r, angle,
                thread_spec, flute_count, thickness, neck_dia, etc_note
            )
            return " ".join(parts) if parts else "특수공구"

        if str(sub_code).startswith("TAP") or str(sub_code).startswith("THD"):
            parts = []
            if thread_spec:
                parts.append(thread_spec)
            if str(sub_code).startswith("THD"):
                if diameter:
                    parts.append(f"D{self.fmt_num(diameter)}")
                if length:
                    parts.append(f"L{self.fmt_num(length)}")
                if effective_len:
                    parts.append(f"H{self.fmt_num(effective_len)}")
            return " ".join(parts) if parts else "나사"

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
                      today, seq, is_grade_b, angle="", thickness="", neck_dia="",
                      effective_len="", corner_r="", etc_note=""):
        if self.is_sp_main():
            parts = self.collect_filled_name_parts(
                sub_code, diameter, length, effective_len, corner_r, angle,
                thread_spec, flute_count, thickness, neck_dia, etc_note
            )
            name = " ".join(parts) if parts else "특수공구"
            return f"{name} {today}-{seq}".strip()

        tool_type = self.get_tool_type(sub_code)

        if str(sub_code).startswith("TAP") or str(sub_code).startswith("THD"):
            parts = [str(thread_spec or "").strip(), self.tap_type_label()]
            if str(sub_code).startswith("THD"):
                if diameter is not None and str(diameter).strip() != "":
                    parts.append(f"D{self.fmt_num(diameter)}")
                if length is not None and str(length).strip() != "":
                    parts.append(f"L{self.fmt_num(length)}")
            name = " ".join(p for p in parts if p).strip()
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

    def get_tool_type(self, sub_code, main_name=None):
        sub_code = (sub_code or "").strip()
        if not sub_code:
            return ""
        conn = get_connection()
        cur = conn.cursor()
        row = None
        if main_name:
            cur.execute(
                """
                SELECT type_name, sub_name FROM categories
                WHERE main_name = ? AND sub_code = ?
                """,
                (main_name, sub_code),
            )
            row = cur.fetchone()
        if row is None:
            cur.execute(
                """
                SELECT type_name, sub_name FROM categories
                WHERE sub_code = ?
                ORDER BY id LIMIT 1
                """,
                (sub_code,),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return ""
        return (row["type_name"] or row["sub_name"] or "").strip()


def run_app():
    app = MainWindow()
    app.mainloop()
