from database.db import init_db
from ui.main_window import run_app

if __name__ == "__main__":
    init_db()          # 테이블 없으면 생성
    run_app()          # UI 실행
      