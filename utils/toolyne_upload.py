import time
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_ID = "rlaehgud"
LOGIN_PW = "0528"


def upload_tools(rows):
    """
    rows: list[dict]
    성공 시 (True, 메시지), 실패 시 (False, 에러메시지)
    """
    if not rows:
        return False, "업로드할 항목이 없습니다."

    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)

        # 로그인
        driver.get("https://www.toolyne.com/u/login/login.php")
        wait.until(EC.presence_of_element_located((By.ID, "login_id"))).send_keys(LOGIN_ID)
        driver.find_element(By.ID, "login_pw").send_keys(LOGIN_PW)
        driver.find_element(By.ID, "btn_login").click()
        time.sleep(3)

        for i, row in enumerate(rows, 1):
            driver.get("https://www.toolyne.com/u/mytool/mytool_reg.php")
            time.sleep(2)

            def safe(v):
                if v is None:
                    return ""
                return str(v)

            wait.until(EC.presence_of_element_located((By.ID, "ct1_name"))).clear()
            driver.find_element(By.ID, "ct1_name").send_keys(safe(row.get("main_name")))
            driver.find_element(By.ID, "ct2_name").send_keys(safe(row.get("sub_code")))
            driver.find_element(By.ID, "mytool_brand_name").send_keys(safe(row.get("maker_name")))
            driver.find_element(By.ID, "mytool_model").send_keys(safe(row.get("tool_name")))
            driver.find_element(By.ID, "mytool_subtitle").send_keys(safe(row.get("sub_name")))
            driver.find_element(By.ID, "mytool_ordercode").send_keys(safe(row.get("tool_code")))
            driver.find_element(By.ID, "mytool_barcode_mng").send_keys(safe(row.get("barcode")))

            Select(driver.find_element(By.ID, "use_yn")).select_by_value("Y")

            buttons = driver.find_elements(By.CLASS_NAME, "btn_add_opt")
            option_num = 1

            shank = row.get("shank_dia")
            if shank is not None and str(shank).strip() != "":
                if buttons:
                    buttons[0].click()
                    time.sleep(0.5)
                    driver.find_element(By.NAME, f"opt_name[{option_num}]").send_keys("생크직경")
                    driver.find_element(By.NAME, f"opt_val[{option_num}]").send_keys(str(shank))
                    option_num += 1

            length = row.get("total_length")
            if length is not None and str(length).strip() != "":
                buttons = driver.find_elements(By.CLASS_NAME, "btn_add_opt")
                if buttons:
                    buttons[0].click()
                    time.sleep(0.5)
                    driver.find_element(By.NAME, f"opt_name[{option_num}]").send_keys("전체길이")
                    driver.find_element(By.NAME, f"opt_val[{option_num}]").send_keys(str(length))
                    option_num += 1

            save_btn = driver.find_element(By.ID, "btn_reg_mytool")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save_btn)
            time.sleep(0.8)
            driver.execute_script("arguments[0].click();", save_btn)

            alert = wait.until(EC.alert_is_present())
            alert.accept()
            time.sleep(0.5)

        # 2차 등록
        driver.get("https://www.toolyne.com/u/zonemytool/zonemytool_list.php")
        time.sleep(2)

        try:
            Select(driver.find_element(By.NAME, "table_mytool_length")).select_by_value("100")
            time.sleep(2)
        except Exception:
            pass

        try:
            all_chk = driver.find_element(By.ID, "all")
            if not all_chk.is_selected():
                driver.execute_script("arguments[0].click();", all_chk)
            time.sleep(1)
        except Exception:
            pass

        try:
            save_buttons = driver.find_elements(By.XPATH, "//button[contains(@class,'btn-info')]")
            if save_buttons:
                save_buttons[0].click()
                try:
                    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
                    alert.accept()
                except Exception:
                    pass
        except Exception:
            pass

        return True, f"{len(rows)}개 등록 완료"

    except Exception as e:
        return False, f"{e}\n\n{traceback.format_exc()}"
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass