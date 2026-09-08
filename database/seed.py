from database.db import get_connection, init_db


def seed_categories(cur):
    """대분류 + 소분류 초기 데이터"""
    categories = [
        # M(엔드밀)
        ("M", "M(엔드밀)", "EM(SUS)", "스퀘어(SUS)"),
        ("M", "M(엔드밀)", "EM-R(SUS)", "리브 스퀘어(SUS)"),
        ("M", "M(엔드밀)", "BM(SUS)", "볼(SUS)"),
        ("M", "M(엔드밀)", "BM-R(SUS)", "리브 볼(SUS)"),
        ("M", "M(엔드밀)", "BN(SUS)", "코너R(SUS)"),
        ("M", "M(엔드밀)", "BN-R(SUS)", "리브 코너R(SUS)"),
        ("M", "M(엔드밀)", "RF(SUS)", "라핑(SUS)"),
        ("M", "M(엔드밀)", "RF-R(SUS)", "리브 라핑(SUS)"),
        ("M", "M(엔드밀)", "LN(SUS)", "롱넥(SUS)"),

        # N(엔드밀)
        ("N", "N(엔드밀)", "EM(ALU)", "스퀘어(ALU)"),
        ("N", "N(엔드밀)", "EM-R(ALU)", "리브 스퀘어(ALU)"),
        ("N", "N(엔드밀)", "BM(ALU)", "볼(ALU)"),
        ("N", "N(엔드밀)", "BM-R(ALU)", "리브 볼(ALU)"),
        ("N", "N(엔드밀)", "BN(ALU)", "코너R(ALU)"),
        ("N", "N(엔드밀)", "BN-R(ALU)", "리브 코너R(ALU)"),
        ("N", "N(엔드밀)", "RF(ALU)", "라핑(ALU)"),
        ("N", "N(엔드밀)", "RF-R(ALU)", "리브 라핑(ALU)"),
        ("N", "N(엔드밀)", "LN(ALU)", "롱넥(ALU)"),

        # H(엔드밀)
        ("H", "H(엔드밀)", "EM(STEEL)", "스퀘어(STEEL)"),
        ("H", "H(엔드밀)", "EM-R(STEEL)", "리브 스퀘어(STEEL)"),
        ("H", "H(엔드밀)", "BM(STEEL)", "볼(STEEL)"),
        ("H", "H(엔드밀)", "BM-R(STEEL)", "리브 볼(STEEL)"),
        ("H", "H(엔드밀)", "BN(STEEL)", "코너R(STEEL)"),
        ("H", "H(엔드밀)", "BN-R(STEEL)", "리브 코너R(STEEL)"),
        ("H", "H(엔드밀)", "RF(STEEL)", "라핑(STEEL)"),
        ("H", "H(엔드밀)", "RF-R(STEEL)", "리브 라핑(STEEL)"),
        ("H", "H(엔드밀)", "LN(STEEL)", "롱넥(STEEL)"),

        # DR(드릴)
        ("DR", "DR(드릴)", "DR", "드릴"),
        ("DR", "DR(드릴)", "DR-SGESS", "드릴-SGESS"),
        ("DR", "DR(드릴)", "DR-SGES", "드릴-SGES"),
        ("DR", "DR(드릴)", "CD", "초경 드릴"),
        ("DR", "DR(드릴)", "NC", "NC 드릴"),
        ("DR", "DR(드릴)", "FD", "플랫 드릴"),
        ("DR", "DR(드릴)", "MD", "마이크로 드릴"),

        # TAP 미터
        ("TAP_M", "TAP(미터 탭)", "TAP", "탭"),
        ("TAP_M", "TAP(미터 탭)", "TAP-H", "헬리코일"),
        ("TAP_M", "TAP(미터 탭)", "THD", "쓰레드"),

        # TAP 인치
        ("TAP_I", "TAP(인치 탭)", "TAP(UNC)", "UNC"),
        ("TAP_I", "TAP(인치 탭)", "TAP(UNF)", "UNF"),
        ("TAP_I", "TAP(인치 탭)", "TAP-PT", "PT"),
        ("TAP_I", "TAP(인치 탭)", "TAP-NPT", "NPT"),
        ("TAP_I", "TAP(인치 탭)", "TAP-H(UNC)", "헬리코일 UNC"),
        ("TAP_I", "TAP(인치 탭)", "TAP-H(UNF)", "헬리코일 UNF"),

        # SP(특수)
        ("SP", "SP(특수)", "RM", "리머"),
        ("SP", "SP(특수)", "THD", "쓰레드"),
        ("SP", "SP(특수)", "CM", "챔퍼"),
        ("SP", "SP(특수)", "SP", "특수제작공구"),
        ("SP", "SP(특수)", "TC", "T-CUTTER"),
        ("SP", "SP(특수)", "DV", "DV"),
        ("SP", "SP(특수)", "SR", "SR"),
    ]

    cur.executemany("""
        INSERT OR IGNORE INTO categories (main_code, main_name, sub_code, sub_name)
        VALUES (?, ?, ?, ?)
    """, categories)
    print(f"카테고리 {len(categories)}개 등록 완료")


def seed_makers(cur):
    """제조사 초기 데이터"""
    makers = [
        "-",
        "ATOM-ADLL", "ATOM-ADPN", "ATOM-ADR", "ATOM-ADR-SUS", "ATOM-ADR-SV",
        "ATOM-ADRL", "ATOM-ADRL-SUS", "ATOM-ADRS", "ATOM-ADRS-SV", "ATOM-ADRSL", "ATOM-ASWR",
        "FPTOOLS", "GUHRING-5768", "HITACHI","Hofmann & Vratny", "IWATA",
        "JJTOOLS", "JJTOOLS (for ABS)", "JJTOOLS (for ALU)", "JJTOOLS (for SUS)",
        "JJTOOLS (for G-TAC)", "JJTOOLS (for G-TAG)", "JJTOOLS (HARD)", "JJTOOLS (JJ)",
        "JJTOOLS (R-TAG)",
        "KENNAMETAL", "MITSUBISHI",
        "NACHI-AG", "NACHI-AQUA", "NACHI-REVO", "NACHI-SGESR", "NACHI-SGESS", "NACHI-SGES",
        "NSTOOL", "OSG",
        "SANDVIK-CORODRILL", "SANDVIK-DURA", "SANDVIK-PLURA",
        "SUMITOMO", "UNIONTOOL", "VARGUS",
        "WALTER-A6181", "WALTER-DB131", "WALTER-DB133", "WALTER-DC150", "WALTER-DC160", "WALTER-DC180",
        "WIDIA", "WIDIN", "YAMAWA",
        "YG-1(4G mills)", "YG-1(ALU-CUT HPC)", "YG-1(ALU-CUT)", "YG-1(DREAM)",
        "YG-1(NO.1)", "YG-1(PANG)", "YG-1(SUS-CUT)", "YG-1(X-POWER)",
    ]

    cur.executemany("""
        INSERT OR IGNORE INTO makers (name) VALUES (?)
    """, [(m,) for m in makers])
    print(f"제조사 {len(makers)}개 등록 완료")


def seed_thread_specs(cur):
    specs = []

    def add(key, items):
        for s in items:
            specs.append((key, s))

    add("metric_coarse", [
        "M2 x 0.4", "M2.5 x 0.45", "M3 x 0.5", "M4 x 0.7",
        "M5 x 0.8", "M6 x 1.0", "M8 x 1.25", "M10 x 1.5",
        "M12 x 1.75", "M14 x 2.0", "M16 x 2.0", "M18 x 2.5",
        "M20 x 2.5", "M24 x 3.0",
    ])
    add("metric_fine", [
        "M8 x 1.0", "M10 x 1.0", "M10 x 1.25", "M12 x 1.25",
        "M12 x 1.5", "M14 x 1.5", "M16 x 1.5", "M18 x 1.5",
        "M20 x 1.5", "M20 x 2.0", "M24 x 2.0",
    ])
    add("inch_coarse", [
        "4-40 UNC", "6-32 UNC", "8-32 UNC", "10-24 UNC",
        "1/4-20 UNC", "5/16-18 UNC", "3/8-16 UNC", "7/16-14 UNC", "1/2-13 UNC",
    ])
    add("inch_fine", [
        "4-48 UNF", "6-40 UNF", "8-36 UNF", "10-32 UNF",
        "1/4-28 UNF", "5/16-24 UNF", "3/8-24 UNF", "7/16-20 UNF", "1/2-20 UNF",
    ])
    add("heli_metric_coarse", [
        "M3 STI", "M4 STI", "M5 STI", "M6 STI", "M8 STI", "M10 STI", "M12 STI",
    ])
    add("heli_metric_fine", [
        "M8 x 1.0 STI", "M10 x 1.0 STI", "M10 x 1.25 STI",
        "M12 x 1.25 STI", "M12 x 1.5 STI",
    ])
    add("heli_inch_coarse", [
        "4-40 UNC STI", "6-32 UNC STI", "8-32 UNC STI",
        "10-24 UNC STI", "1/4-20 UNC STI",
    ])
    add("heli_inch_fine", [
        "4-48 UNF STI", "6-40 UNF STI", "8-36 UNF STI",
        "10-32 UNF STI", "1/4-28 UNF STI",
    ])
    add("pt", [
        "1/16-28 PT", "1/8-28 PT", "1/4-19 PT",
        "3/8-19 PT", "1/2-14 PT", "3/4-14 PT",
    ])
    add("npt", [
        "1/16-27 NPT", "1/8-27 NPT", "1/4-18 NPT",
        "3/8-18 NPT", "1/2-14 NPT", "3/4-14 NPT",
    ])
    add("thd_coarse", [
        "M3 x 0.5", "M4 x 0.7", "M5 x 0.8", "M6 x 1.0",
        "M8 x 1.25", "M10 x 1.5", "M12 x 1.75",
    ])
    add("thd_fine", [
        "M8 x 1.0", "M10 x 1.0", "M10 x 1.25",
        "M12 x 1.25", "M12 x 1.5", "M16 x 1.5",
    ])

    cur.executemany(
        "INSERT OR IGNORE INTO thread_specs (standard, spec) VALUES (?, ?)",
        specs,
    )
    print(f"나사규격 {len(specs)}개 등록 완료")


def run_seed():
    init_db()  # 테이블이 없으면 생성
    conn = get_connection()
    cur = conn.cursor()

    seed_categories(cur)
    seed_makers(cur)
    seed_thread_specs(cur)

    conn.commit()
    conn.close()
    print("초기 데이터 입력 완료!")


if __name__ == "__main__":
    run_seed()