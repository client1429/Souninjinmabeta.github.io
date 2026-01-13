import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import string
import time
import os
import json
import threading
import queue
import logging
import atexit
import shutil
import subprocess
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# ==================== LOCK FILE ====================
LOCK_FILE = "tool.lock"

def create_lock():
    try:
        open(LOCK_FILE, 'x').close()
        print("Lock created - Tool started")
    except FileExistsError:
        messagebox.showerror("Lỗi", "Tool đang chạy rồi! Không thể mở instance mới.")
        os._exit(1)

def remove_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            print("Lock removed - Tool closed")
    except:
        pass

create_lock()
atexit.register(remove_lock)

# Setup logging
logging.basicConfig(
    filename='log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

# CustomTkinter theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ==================== SETTINGS ====================
SETTINGS_FILE = "setting.txt"
PROFILE_DIR = os.path.join(os.path.dirname(__file__), "chrome_profile")
COMMON_SUCCESS_FILE = "tai_khoan_thanh_cong.txt"
FAILED_FILE = "heromc_ip_cuc.txt"

DEFAULT_GENERAL = {
    "file_path": "t.txt",
    "quantity": 10,
    "headless": False,
    "selected_site": "HEROMC",
    "typing_speed": "Trung bình (khuyến nghị)",
    "reset_warp": False,
    "warp_reset_wait": 8.0
}

DEFAULT_SITE_SETTINGS = {
    "3FMC": {
        "delay_min": 15.0,
        "delay_max": 35.0,
        "delay_after_load": 8.0,
        "delay_after_submit": 12.0,
        "recaptcha_timeout": 180.0,
        "delay_after_recaptcha": 3.0,
        "delay_before_fill": 2.0,
        "delay_per_char": 0.1,
        "delay_after_click_field": 0.4,
        "speed_multiplier": 1.0,
        "reload_before": False,
        "has_recaptcha": True,
        "mouse_simulation": True,
        "optimize_speed": False
    },
    "HEROMC": {
        "delay_min": 15.0,
        "delay_max": 35.0,
        "delay_after_load": 8.0,
        "delay_after_submit": 12.0,
        "recaptcha_timeout": 180.0,
        "delay_after_recaptcha": 3.0,
        "delay_before_fill": 2.0,
        "delay_per_char": 0.1,
        "delay_after_click_field": 0.4,
        "speed_multiplier": 1.0,
        "reload_before": True,
        "has_recaptcha": True,
        "mouse_simulation": True,
        "delay_click_register": 2.0,
        "delay_reload_form": 3.0,
        "optimize_speed": False
    },
    "LUCKYVN": {
        "delay_min": 15.0,
        "delay_max": 35.0,
        "delay_after_load": 8.0,
        "delay_after_submit": 12.0,
        "recaptcha_timeout": 180.0,
        "delay_after_recaptcha": 3.0,
        "delay_before_fill": 2.0,
        "delay_per_char": 0.1,
        "delay_after_click_field": 0.4,
        "speed_multiplier": 1.0,
        "reload_before": False,
        "has_recaptcha": False,
        "mouse_simulation": True,
        "delay_click_register": 2.0,
        "delay_reload_form": 3.0,
        "optimize_speed": False
    }
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                general = data.get("general", DEFAULT_GENERAL)
                sites = data.get("sites", DEFAULT_SITE_SETTINGS)
                for site in DEFAULT_SITE_SETTINGS:
                    if site not in sites:
                        sites[site] = DEFAULT_SITE_SETTINGS[site]
                return general, sites
        except Exception as e:
            logging.error(f"Lỗi load settings: {e}")
    return DEFAULT_GENERAL, DEFAULT_SITE_SETTINGS.copy()

def save_settings(general, sites, show_popup=False):
    try:
        data = {"general": general, "sites": sites}
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        if show_popup:
            messagebox.showinfo("Thành công", "Đã lưu settings vào setting.txt!")
    except Exception as e:
        if show_popup:
            messagebox.showerror("Lỗi", f"Lưu settings thất bại: {str(e)}")

general_settings, site_settings = load_settings()

# ==================== SITES ====================
SITES = {
    "3FMC": {
        "url": "https://3fmc.com/register",
        "username": "#username",
        "email": "#email",
        "password": "#password",
        "repeat_password": "#passwordRe",
        "submit": "button[name='insertAccounts']",
        "error_keywords": [
            "tồn tại", "không hợp lệ", "thất bại", "đã có", "alert-danger",
            "Bạn đã đạt giới hạn đăng ký tài khoản", "đăng ký thất bại",
            "giới hạn đăng ký", "đạt giới hạn", "hết lượt đăng ký", "quá giới hạn", "limit reached",
            "spam", "phát hiện spam", "Phát hiện Spam", "spam detected", "detected spam",
            "alert error", "danger alert"
        ],
        "success_keywords": ["thành công", "đăng ký thành công", "hoàn tất", "success"],
        "success_file": "3fmc đăng ký thành công.txt"
    },
    "HEROMC": {
        "home_url": "https://heromc.net/",
        "register_link_selector": "a[href='https://heromc.net/dang-ky/']",
        "url": "https://heromc.net/dang-ky/",
        "username": "input[name='User_name']",
        "email": "input[name='User_email']",
        "password": "input[name='User_password']",
        "repeat_password": "input[name='User_repeatPassword']",
        "submit": "input[value='Đăng ký']",
        "error_keywords": [
            "thất bại", "đã tồn tại", "địa chỉ ip của bạn bị cấm đăng ký tại heromc",
            "hãy liên hệ hỗ trợ", "ip của bạn bị cấm",
            "giới hạn đăng ký", "đạt giới hạn", "hết lượt đăng ký", "quá giới hạn",
            "spam", "phát hiện spam", "Phát hiện Spam"
        ],
        "success_keywords": [
            "đăng ký tài khoản thành công", "bạn đã đăng ký tài khoản tại heromc.net thành công",
            "chúc bạn chơi game vui vẻ", "bấm vào đây để đăng nhập", "id.heromc.net/member"
        ],
        "success_file": "heromc đăng ký thành công.txt"
    },
    "LUCKYVN": {
        "url": "https://luckyvn.com/dang-ky",
        "username": "#username-input",
        "email": "",
        "password": "#password-input",
        "repeat_password": "#retype-password",
        "submit": "button[type='submit'].register-btn",
        "error_keywords": [
            "đã tồn tại", "tên người dùng đã được sử dụng", "email đã đăng ký",
            "mật khẩu không khớp", "thất bại",
            "giới hạn đăng ký", "đạt giới hạn", "hết lượt đăng ký",
            "spam", "phát hiện spam", "Phát hiện Spam", "alert-danger"
        ],
        "success_keywords": [
            "đăng ký thành công", "tài khoản đã được tạo", "chào mừng", "success",
            "welcome", "verification", "xác nhận email"
        ],
        "success_file": "luckyvn đăng ký thành công.txt"
    }
}

# ==================== UTILS ====================
def human_type(element, text, driver, log_queue, stt):
    preset = typing_speed_preset.get()
    delay_per_char = 0.1
    if preset == "Chậm (an toàn nhất)":
        delay_per_char = 0.15
    elif preset == "Trung bình (khuyến nghị)":
        delay_per_char = 0.1
    elif preset == "Nhanh":
        delay_per_char = 0.07
    elif preset == "Rất nhanh (rủi ro cao)":
        delay_per_char = 0.04

    log_queue.put((f"[{stt}] Gõ theo mức '{preset}' (delay/char: {delay_per_char:.3f}s): {text}", "white"))

    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()
    time.sleep(random.uniform(0.2, 0.6))

    for char in text:
        element.send_keys(char)
        sleep_time = delay_per_char + random.uniform(-0.03, 0.03)
        time.sleep(max(0.0, sleep_time))

    time.sleep(random.uniform(0.4, 1.0))

def human_click(element, driver, log_queue, stt):
    log_queue.put((f"[{stt}] Click giống người thật", "white"))
    actions = ActionChains(driver)
    actions.move_to_element(element).pause(random.uniform(0.3, 0.7)).click().perform()

def tai_danh_sach_tai_khoan(tap_tin):
    if not os.path.exists(tap_tin):
        return None
    danh_sach = []
    with open(tap_tin, 'r', encoding='utf-8') as f:
        for dong in f:
            dong = dong.strip()
            if dong and '/' in dong:
                ten_dang_nhap, mat_khau = dong.split('/', 1)
                danh_sach.append((ten_dang_nhap.strip(), mat_khau.strip()))
    return danh_sach

def tao_ten_dang_nhap(ten_goc, current_num):
    ten_chinh = ten_goc.split('+')[0].strip()
    max_total_len = 16

    tail = ''
    if sequential_tail_var.get():
        seq_str = f"{current_num}"
        remaining = max_total_len - len(ten_chinh)
        if remaining <= 0:
            ten_chinh = ten_chinh[:15]
            tail = seq_str[-1:] if seq_str else '0'
        else:
            tail = seq_str[-remaining:] if len(seq_str) > remaining else seq_str.zfill(remaining)
    elif random_tail_var.get():
        remaining = max_total_len - len(ten_chinh)
        if remaining <= 0:
            ten_chinh = ten_chinh[:15]
            remaining = 1
        tail = ''.join(random.choices(string.ascii_lowercase + string.digits, k=remaining))

    username = f"{ten_chinh}{tail}"
    # Đảm bảo không vượt 16 (an toàn)
    username = username[:max_total_len]

    log_queue.put((f"Username tạo: {username} (gốc: '{ten_chinh}', đuôi: '{tail}', tổng dài: {len(username)})", "gray"))
    return username

def ghi_ket_qua_dang_ky(site_config, site_name, ten_dang_nhap, mat_khau, thanh_cong):
    thoi_gian = time.strftime("%Y-%m-%d %H:%M:%S")
    trang_thai = "THÀNH CÔNG" if thanh_cong else "THẤT BẠI"
    
    log = f"{thoi_gian} | [{site_config.get('url', site_config.get('home_url', ''))}] {trang_thai} | {ten_dang_nhap} | {mat_khau}\n"
    with open("log_dang_ky.txt", "a", encoding="utf-8") as f:
        f.write(log)

    if thanh_cong:
        file_name = site_config.get("success_file", "tai_khoan_thanh_cong_site.txt")
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(f"{ten_dang_nhap}/{mat_khau}\n")

        try:
            with open(COMMON_SUCCESS_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{site_name}] {ten_dang_nhap}/{mat_khau} | {thoi_gian}\n")
        except:
            pass
    else:
        if site_name == "HEROMC" and any(kw in log.lower() for kw in ["ip bị cấm", "địa chỉ ip của bạn bị cấm"]):
            with open(FAILED_FILE, "a", encoding="utf-8") as f:
                f.write(f"{thoi_gian} | IP BỊ CẤM | {ten_dang_nhap}/{mat_khau}\n")

# ==================== XÓA CACHE ====================
def clear_browser_data_keep_extensions():
    if not os.path.exists(PROFILE_DIR):
        return 0

    profile_path = os.path.join(PROFILE_DIR, "Default")
    if not os.path.exists(profile_path):
        return 0

    items_to_delete = [
        "Cache", "Code Cache", "GPUCache", "ShaderCache",
        "Cookies", "Cookies-journal",
        "History", "History-journal",
        "Web Data", "Web Data-journal",
        "Login Data", "Login Data-journal",
        "Network Action Predictor", "Network Action Predictor-journal",
        "Visited Links",
        "Sessions", "Session Storage",
        "Storage", "Service Worker", "IndexedDB",
        "Preferences",
        "Current Session", "Current Tabs", "Last Session", "Last Tabs",
        "Favicons", "Favicons-journal",
        "Jump List Icons", "Jump List IconsOld",
        "Network Persistent State",
    ]

    deleted_count = 0
    for item in items_to_delete:
        path = os.path.join(profile_path, item)
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
                deleted_count += 1
            except:
                pass
    return deleted_count

# ==================== RESET WARP ====================
def reset_warp(log_queue, wait_after_reset=8.0):
    try:
        log_queue.put(("Đang tắt WARP...", "yellow"))
        subprocess.run(["warp-cli", "disconnect"], capture_output=True, text=True, timeout=15)
        time.sleep(4)

        log_queue.put(("Đang bật lại WARP...", "yellow"))
        subprocess.run(["warp-cli", "connect"], capture_output=True, text=True, timeout=15)

        log_queue.put(("Bắt đầu chờ WARP kết nối... (chờ đến Connected, nhấn DỪNG nếu muốn dừng)", "yellow"))

        last_status = ""
        connected = False

        while not connected and not stop_event.is_set():
            try:
                status_proc = subprocess.run(["warp-cli", "status"], capture_output=True, text=True, timeout=8)
                current_status = status_proc.stdout.strip()
                output_lower = current_status.lower()

                if current_status != last_status:
                    log_queue.put((f"Status WARP: {current_status}", "white"))
                    last_status = current_status

                if "connected" in output_lower:
                    connected = True
                    log_queue.put(("✅ WARP đã kết nối thành công!", "green"))
                    break

                elif "connecting" in output_lower or "establishing" in output_lower:
                    log_queue.put(("Vẫn đang Connecting... chờ thêm...", "yellow"))

                elif "disconnected" in output_lower:
                    log_queue.put(("WARP Disconnected → bật lại...", "orange"))
                    subprocess.run(["warp-cli", "connect"], capture_output=True, text=True)

                else:
                    log_queue.put(("Status lạ: " + current_status, "orange"))

                time.sleep(2)

            except subprocess.TimeoutExpired:
                log_queue.put(("Timeout check status → thử lại...", "orange"))
                time.sleep(2)
                continue
            except Exception as e:
                log_queue.put((f"Lỗi check status: {str(e)}", "red"))
                time.sleep(3)
                continue

        if stop_event.is_set():
            log_queue.put(("Dừng thủ công trong lúc chờ WARP", "white"))
            return False

        if not connected:
            log_queue.put(("Không thể kết nối WARP (lỗi không xác định)", "red"))
            return False

        log_queue.put((f"⏳ Chờ thêm {wait_after_reset:.1f}s để IP ổn định...", "yellow"))
        time.sleep(wait_after_reset)

        log_queue.put(("✅ Reset WARP hoàn tất - IP đã thay đổi", "green"))
        return True

    except FileNotFoundError:
        log_queue.put(("❌ Không tìm thấy warp-cli!", "red"))
        return False
    except Exception as e:
        log_queue.put((f"❌ Lỗi reset WARP: {str(e)}", "red"))
        return False

# ==================== ĐĂNG KÝ ====================
def dang_ky_tai_khoan(site_config, ten_dang_nhap, mat_khau, stt, log_queue, stop_event):
    if stop_event.is_set():
        log_queue.put(("Đã dừng khẩn cấp", "white"))
        return False

    site_name = [k for k, v in SITES.items() if v == site_config][0]
    log_queue.put((f"[{stt}] [{site_name}] Đang đăng ký: {ten_dang_nhap}", "white"))

    driver = None
    try:
        log_queue.put((f"[{stt}] Đang khởi tạo Chrome...", "yellow"))

        # Không kill toàn bộ chrome → chỉ quit driver cũ nếu tồn tại
        if 'driver' in globals() and driver is not None:
            try:
                driver.quit()
                log_queue.put((f"[{stt}] Đã quit driver Chrome cũ để tránh conflict", "yellow"))
                time.sleep(2)
            except:
                pass

        # Retry khởi tạo driver 3 lần
        for attempt in range(3):
            try:
                driver = Driver(
                    browser="chrome",
                    uc=True,
                    headless=general_settings.get("headless", False),
                    user_data_dir=PROFILE_DIR,
                    incognito=False,
                    ad_block_on=True,
                    do_not_track=True,
                    chromium_arg="--disable-notifications,--disable-gpu,--no-sandbox,--ignore-certificate-errors,--disable-dev-shm-usage"
                )
                log_queue.put((f"[{stt}] ✅ Chrome OK (lần {attempt+1})", "green"))
                break
            except Exception as e:
                log_queue.put((f"[{stt}] Khởi tạo Chrome thất bại lần {attempt+1}: {str(e)}", "red"))
                time.sleep(5)
        else:
            log_queue.put((f"[{stt}] Không thể khởi tạo Chrome sau 3 lần thử → Bỏ qua acc này", "red"))
            return False

        if site_name == "HEROMC":
            log_queue.put((f"[{stt}] Bước 1: Truy cập home {site_config['home_url']}", "white"))
            driver.uc_open_with_reconnect(site_config["home_url"], reconnect_time=10)
            time.sleep(site_settings[site_name]["delay_after_load"])

            log_queue.put((f"[{stt}] Bước 2: Chờ {site_settings[site_name]['delay_click_register']}s rồi click link ĐĂNG KÝ", "white"))
            time.sleep(site_settings[site_name]["delay_click_register"])

            try:
                register_link = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'dang-ky/') and contains(text(), 'ĐĂNG KÝ')]"))
                )
            except:
                register_link = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, site_config["register_link_selector"]))
                )

            human_click(register_link, driver, log_queue, stt)
            time.sleep(site_settings[site_name]["delay_after_load"])

            log_queue.put((f"[{stt}] Chờ iframe đăng ký load...", "white"))
            iframe = WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='id.heromc.net/member/dangky.php']")))
            driver.switch_to.frame(iframe)
            log_queue.put((f"[{stt}] Đã switch vào iframe đăng ký", "green"))
        else:
            driver.uc_open_with_reconnect(site_config["url"], reconnect_time=10)
            time.sleep(site_settings[site_name]["delay_after_load"])

        page_source_lower = driver.page_source.lower()
        cloudflare_block_keywords = ["error 1015", "you are being rate limited", "ray id", "error 105", "rate limited", "access denied", "blocked"]
        if any(keyword in page_source_lower for keyword in cloudflare_block_keywords):
            log_queue.put((f"[{stt}] !!! CLOUDFLARE BLOCK - IP BỊ CHẶN !!!", "red"))
            stop_event.set()
            log_queue.put((f"[{stt}] → DỪNG KHẨN CẤP TOOL do Cloudflare chặn IP!", "red"))
            return False

        if site_settings[site_name]["reload_before"]:
            driver.refresh()
            time.sleep(site_settings[site_name]["delay_after_load"])

        log_queue.put((f"[{stt}] Chờ form đăng ký xuất hiện...", "white"))
        retry_count = 0
        while retry_count < 3:
            try:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, site_config["username"])))
                log_queue.put((f"[{stt}] Form đã xuất hiện sau {retry_count} lần retry", "green"))
                break
            except:
                retry_count += 1
                log_queue.put((f"[{stt}] Không thấy form - Retry reload lần {retry_count}/3", "yellow"))
                driver.refresh()
                time.sleep(site_settings[site_name]["delay_after_load"])

        if retry_count == 3:
            log_queue.put((f"[{stt}] Không load được form sau 3 lần thử - Thất bại", "red"))
            return False

        if site_settings[site_name]["has_recaptcha"]:
            log_queue.put((f"[{stt}] Chờ reCAPTCHA giải xong (timeout {site_settings[site_name]['recaptcha_timeout']}s)...", "yellow"))
            solved = False
            start_time = time.time()
            timeout_time = start_time + site_settings[site_name]["recaptcha_timeout"]

            while time.time() < timeout_time and not stop_event.is_set():
                try:
                    token = driver.execute_script("return document.querySelector('textarea#g-recaptcha-response')?.value || ''")
                    if token and len(token) > 100:
                        solved = True
                        break

                    checkbox_checked = driver.execute_script("return document.querySelector('.recaptcha-checkbox-checked') !== null")
                    if checkbox_checked:
                        solved = True
                        break
                except:
                    pass
                time.sleep(0.2 if site_settings[site_name].get("optimize_speed", False) else 0.5)

            if not solved:
                log_queue.put((f"[{stt}] reCAPTCHA timeout - Thất bại", "red"))
                return False

            time.sleep(site_settings[site_name]["delay_after_recaptcha"])
        else:
            log_queue.put((f"[{stt}] Không có reCAPTCHA", "green"))

        log_queue.put((f"[{stt}] Chờ {site_settings[site_name]['delay_before_fill']}s trước khi điền form", "white"))
        time.sleep(site_settings[site_name]["delay_before_fill"])

        log_queue.put((f"[{stt}] Điền thông tin form (gõ theo mức {typing_speed_preset.get()})", "white"))
        wait = WebDriverWait(driver, 45)

        if site_config["username"]:
            username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, site_config["username"])))
            human_click(username_field, driver, log_queue, stt)
            time.sleep(site_settings[site_name]["delay_after_click_field"])
            human_type(username_field, ten_dang_nhap, driver, log_queue, stt)

        if site_config["email"]:
            email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, site_config["email"])))
            human_click(email_field, driver, log_queue, stt)
            time.sleep(site_settings[site_name]["delay_after_click_field"])
            email_use = ten_dang_nhap if '@' in ten_dang_nhap else f"{ten_dang_nhap}@gmail.com"
            human_type(email_field, email_use, driver, log_queue, stt)

        password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, site_config["password"])))
        human_click(password_field, driver, log_queue, stt)
        time.sleep(site_settings[site_name]["delay_after_click_field"])
        human_type(password_field, mat_khau, driver, log_queue, stt)

        repeat_password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, site_config["repeat_password"])))
        human_click(repeat_password_field, driver, log_queue, stt)
        time.sleep(site_settings[site_name]["delay_after_click_field"])
        human_type(repeat_password_field, mat_khau, driver, log_queue, stt)

        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, site_config["submit"])))
        human_click(submit_btn, driver, log_queue, stt)
        log_queue.put((f"[{stt}] Submit OK", "white"))

        time.sleep(site_settings[site_name]["delay_after_submit"])

        # === KIỂM TRA KẾT QUẢ SAU SUBMIT ===
        page_source_lower = driver.page_source.lower()
        current_url = driver.current_url.lower()

        # ƯU TIÊN SUCCESS TRƯỚC
        success = False
        success_detected_by = ""

        for kw in site_config["success_keywords"]:
            if kw.lower() in page_source_lower:
                success = True
                success_detected_by = f"success keyword: {kw}"
                break

        if current_url != site_config.get("url", "").lower() and "register" not in current_url.lower() and "dang-ky" not in current_url.lower():
            success = True
            success_detected_by = f"redirect khỏi trang đăng ký ({current_url})"

        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//*[contains(text(), 'thành công') or contains(text(), 'đăng ký thành công') or contains(@class, 'success') or contains(@class, 'alert-success')]"
                ))
            )
            success = True
            success_detected_by = "tìm thấy element success"
        except:
            pass

        if success:
            log_queue.put((f"[{stt}] 🎉 THÀNH CÔNG ({success_detected_by}): {ten_dang_nhap}", "green"))
            ghi_ket_qua_dang_ky(site_config, site_name, ten_dang_nhap, mat_khau, True)
            return True

        # Chỉ khi KHÔNG success mới check lỗi
        error_detected = False
        error_keyword = ""

        for keyword in site_config["error_keywords"]:
            if keyword.lower() in page_source_lower:
                error_detected = True
                error_keyword = keyword
                break

        if 'alert-danger' in page_source_lower:
            error_detected = True
            error_keyword = "alert-danger"

        spam_keywords = ["phát hiện spam", "spam!", "phát hiện", "spam detected", "detected spam"]
        if any(kw in page_source_lower for kw in spam_keywords):
            error_detected = True
            error_keyword = "Phát hiện Spam"

        if error_detected:
            log_queue.put((f"[{stt}] Thất bại (lỗi: {error_keyword})", "red"))
            ghi_ket_qua_dang_ky(site_config, site_name, ten_dang_nhap, mat_khau, False)
            return False

        log_queue.put((f"[{stt}] Không xác định kết quả → coi là thất bại", "orange"))
        ghi_ket_qua_dang_ky(site_config, site_name, ten_dang_nhap, mat_khau, False)
        return False

    except KeyboardInterrupt:
        log_queue.put((f"[{stt}] Tool bị ngắt thủ công (Ctrl+C hoặc đóng cửa sổ)", "white"))
        return False
    except Exception as e:
        log_queue.put((f"[{stt}] LỖI CHI TIẾT: {str(e)}", "red"))
        return False
    finally:
        if driver is not None:
            try:
                driver.quit()
                log_queue.put((f"[{stt}] Đã đóng browser", "white"))
            except Exception as quit_err:
                log_queue.put((f"[{stt}] Đóng browser thất bại: {str(quit_err)} (bình thường nếu ngắt đột ngột)", "yellow"))

# ==================== GUI ====================
root = ctk.CTk()
root.title("Tool Đăng Ký Acc - SeleniumBase UC + Reset WARP")
root.geometry("950x1200")

log_queue = queue.Queue()
stop_event = threading.Event()

# Dropdown tốc độ gõ
typing_speed_preset = ctk.StringVar(value=general_settings.get("typing_speed", "Trung bình (khuyến nghị)"))

# Biến đuôi username
random_tail_var = ctk.BooleanVar(value=True)
sequential_tail_var = ctk.BooleanVar(value=False)

def process_log_queue():
    try:
        while True:
            msg, color = log_queue.get_nowait()
            if color == "green":
                log_text.insert("end", msg + "\n", "green")
            elif color == "red":
                log_text.insert("end", msg + "\n", "red")
            else:
                log_text.insert("end", msg + "\n", "white")
            log_text.see("end")
    except queue.Empty:
        pass
    root.after(100, process_log_queue)

log_text = scrolledtext.ScrolledText(root, height=14, bg="#111111", fg="#10b981", font=("Consolas", 10), insertbackground="#ffffff")
log_text.pack(padx=30, pady=10, fill="both", expand=False)

log_text.tag_config("green", foreground="#10b981")
log_text.tag_config("red", foreground="#ef4444")
log_text.tag_config("white", foreground="#d1d5db")

root.after(100, process_log_queue)

ctk.CTkLabel(root, text="TOOL ĐĂNG KÝ TÀI KHOẢN (SeleniumBase UC + Reset WARP)", font=("Segoe UI", 20, "bold")).pack(pady=15)

scroll_frame = ctk.CTkScrollableFrame(root)
scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)

frame = ctk.CTkFrame(scroll_frame)
frame.pack(padx=10, pady=10, fill="x")

ctk.CTkLabel(frame, text="Site:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", pady=8)
site_combo = ctk.CTkComboBox(frame, values=list(SITES.keys()), state="readonly", font=("Segoe UI", 11))
site_combo.set(general_settings.get("selected_site", "HEROMC"))
site_combo.grid(row=0, column=1, pady=8, sticky="ew")

ctk.CTkLabel(frame, text="File tài khoản gốc:", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w", pady=8)
file_entry = ctk.CTkEntry(frame, font=("Segoe UI", 11))
file_entry.insert(0, general_settings.get("file_path", "t.txt"))
file_entry.grid(row=1, column=1, pady=8, sticky="ew")

ctk.CTkLabel(frame, text="Số lượng acc:", font=("Segoe UI", 11)).grid(row=2, column=0, sticky="w", pady=8)
quantity_entry = ctk.CTkEntry(frame, font=("Segoe UI", 11))
quantity_entry.insert(0, str(general_settings.get("quantity", 10)))
quantity_entry.grid(row=2, column=1, pady=8, sticky="ew")

headless_var = ctk.BooleanVar(value=general_settings.get("headless", False))
ctk.CTkCheckBox(frame, text="Ẩn Chrome (headless)", variable=headless_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=10)

# Tab Nâng cao
tabview = ctk.CTkTabview(scroll_frame)
tabview.pack(padx=10, pady=10, fill="both", expand=True)

tab_advanced = tabview.add("Nâng cao")

ctk.CTkLabel(tab_advanced, text="Chọn site để tinh chỉnh:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
site_select_combo = ctk.CTkComboBox(tab_advanced, values=list(SITES.keys()), state="readonly")
site_select_combo.set(general_settings.get("selected_site", "HEROMC"))
site_select_combo.grid(row=0, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Delay giữa acc Min (giây):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
delay_min_entry = ctk.CTkEntry(tab_advanced)
delay_min_entry.insert(0, str(site_settings[site_select_combo.get()]["delay_min"]))
delay_min_entry.grid(row=1, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Max (giây):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
delay_max_entry = ctk.CTkEntry(tab_advanced)
delay_max_entry.insert(0, str(site_settings[site_select_combo.get()]["delay_max"]))
delay_max_entry.grid(row=2, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Delay sau load (giây):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
delay_after_load_entry = ctk.CTkEntry(tab_advanced)
delay_after_load_entry.insert(0, str(site_settings[site_select_combo.get()]["delay_after_load"]))
delay_after_load_entry.grid(row=3, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Delay sau submit (giây):").grid(row=4, column=0, padx=10, pady=5, sticky="w")
delay_after_submit_entry = ctk.CTkEntry(tab_advanced)
delay_after_submit_entry.insert(0, str(site_settings[site_select_combo.get()]["delay_after_submit"]))
delay_after_submit_entry.grid(row=4, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Check reCAPTCHA timeout (giây):").grid(row=5, column=0, padx=10, pady=5, sticky="w")
recaptcha_timeout_entry = ctk.CTkEntry(tab_advanced)
recaptcha_timeout_entry.insert(0, str(site_settings[site_select_combo.get()]["recaptcha_timeout"]))
recaptcha_timeout_entry.grid(row=5, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Delay sau reCAPTCHA (giây):").grid(row=6, column=0, padx=10, pady=5, sticky="w")
delay_after_recaptcha_entry = ctk.CTkEntry(tab_advanced)
delay_after_recaptcha_entry.insert(0, str(site_settings[site_select_combo.get()]["delay_after_recaptcha"]))
delay_after_recaptcha_entry.grid(row=6, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Delay trước điền form (giây):").grid(row=7, column=0, padx=10, pady=5, sticky="w")
delay_before_fill_entry = ctk.CTkEntry(tab_advanced)
delay_before_fill_entry.insert(0, str(site_settings[site_select_combo.get()].get("delay_before_fill", 2.0)))
delay_before_fill_entry.grid(row=7, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Tốc độ gõ human typing:").grid(row=8, column=0, padx=10, pady=5, sticky="w")
typing_combo = ctk.CTkComboBox(tab_advanced, values=[
    "Chậm (an toàn nhất)",
    "Trung bình (khuyến nghị)",
    "Nhanh",
    "Rất nhanh (rủi ro cao)"
], variable=typing_speed_preset, state="readonly")
typing_combo.grid(row=8, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Delay nhập mỗi ký tự (giây):").grid(row=9, column=0, padx=10, pady=5, sticky="w")
delay_per_char_entry = ctk.CTkEntry(tab_advanced, state="disabled")
delay_per_char_entry.insert(0, "0.100")
delay_per_char_entry.grid(row=9, column=1, pady=5, sticky="ew")

def update_delay_per_char(*args):
    preset = typing_speed_preset.get()
    delay = 0.1
    if preset == "Chậm (an toàn nhất)":
        delay = 0.15
    elif preset == "Trung bình (khuyến nghị)":
        delay = 0.1
    elif preset == "Nhanh":
        delay = 0.07
    elif preset == "Rất nhanh (rủi ro cao)":
        delay = 0.04
    delay_per_char_entry.configure(state="normal")
    delay_per_char_entry.delete(0, "end")
    delay_per_char_entry.insert(0, f"{delay:.3f}")
    delay_per_char_entry.configure(state="disabled")

typing_speed_preset.trace("w", update_delay_per_char)
update_delay_per_char()

ctk.CTkLabel(tab_advanced, text="Delay sau click field (giây):").grid(row=10, column=0, padx=10, pady=5, sticky="w")
delay_after_click_field_entry = ctk.CTkEntry(tab_advanced)
delay_after_click_field_entry.insert(0, str(site_settings[site_select_combo.get()].get("delay_after_click_field", 0.4)))
delay_after_click_field_entry.grid(row=10, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Delay click link ĐĂNG KÝ (giây):").grid(row=11, column=0, padx=10, pady=5, sticky="w")
delay_click_entry = ctk.CTkEntry(tab_advanced)
delay_click_entry.insert(0, str(site_settings[site_select_combo.get()].get("delay_click_register", 2.0)))
delay_click_entry.grid(row=11, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Delay reload trang (giây):").grid(row=12, column=0, padx=10, pady=5, sticky="w")
delay_reload_entry = ctk.CTkEntry(tab_advanced)
delay_reload_entry.insert(0, str(site_settings[site_select_combo.get()].get("delay_reload_form", 3.0)))
delay_reload_entry.grid(row=12, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Speed multiplier (0.5x - 2.0x):").grid(row=13, column=0, padx=10, pady=5, sticky="w")
speed_frame = ctk.CTkFrame(tab_advanced)
speed_frame.grid(row=13, column=1, pady=5, sticky="ew")

speed_slider = ctk.CTkSlider(speed_frame, from_=0.5, to=2.0, number_of_steps=15, command=lambda value: speed_value_label.configure(text=f"{value:.1f}x"))
speed_slider.set(site_settings[site_select_combo.get()]["speed_multiplier"])
speed_slider.pack(side="left", fill="x", expand=True, padx=(0, 5))

speed_value_label = ctk.CTkLabel(speed_frame, text=f"{site_settings[site_select_combo.get()]['speed_multiplier']:.1f}x", width=60)
speed_value_label.pack(side="left")

optimize_speed_var = ctk.BooleanVar(value=site_settings[site_select_combo.get()].get("optimize_speed", False))
ctk.CTkCheckBox(tab_advanced, text="Tối ưu tốc độ (giảm delay check reCAPTCHA)", variable=optimize_speed_var).grid(row=14, column=0, columnspan=2, pady=5, sticky="w")

reload_before_var = ctk.BooleanVar(value=site_settings[site_select_combo.get()]["reload_before"])
ctk.CTkCheckBox(tab_advanced, text="Reload trang trước khi load", variable=reload_before_var).grid(row=15, column=0, columnspan=2, pady=5, sticky="w")

has_recaptcha_var = ctk.BooleanVar(value=site_settings[site_select_combo.get()]["has_recaptcha"])
ctk.CTkCheckBox(tab_advanced, text="Bật reCAPTCHA", variable=has_recaptcha_var).grid(row=16, column=0, columnspan=2, pady=5, sticky="w")

mouse_sim_var = ctk.BooleanVar(value=site_settings[site_select_combo.get()]["mouse_simulation"])
ctk.CTkCheckBox(tab_advanced, text="Bật mouse simulation (click như người thật)", variable=mouse_sim_var).grid(row=17, column=0, columnspan=2, pady=5, sticky="w")

clear_cache_btn = ctk.CTkButton(tab_advanced, text="Xoá cache (giữ extensions & settings)", fg_color="#ff4444", command=clear_browser_data_keep_extensions)
clear_cache_btn.grid(row=18, column=0, columnspan=2, pady=10, sticky="ew")

auto_clear_var = ctk.BooleanVar(value=False)
ctk.CTkCheckBox(tab_advanced, text="Tự động xóa cache mỗi lần tạo 1 tài khoản", variable=auto_clear_var).grid(row=19, column=0, columnspan=2, pady=5, sticky="w")

# Reset WARP
ctk.CTkLabel(tab_advanced, text="Reset IP bằng 1.1.1.1 WARP", font=("Segoe UI", 14, "bold"), text_color="#00d4ff").grid(row=20, column=0, columnspan=2, pady=(20,5), sticky="w")

reset_warp_var = ctk.BooleanVar(value=general_settings.get("reset_warp", False))
ctk.CTkCheckBox(tab_advanced, text="Tự động reset WARP sau mỗi acc (chờ đến Connected)", variable=reset_warp_var).grid(row=21, column=0, columnspan=2, pady=5, sticky="w")

ctk.CTkLabel(tab_advanced, text="Thời gian chờ sau reset để IP ổn định (giây):").grid(row=22, column=0, padx=10, pady=5, sticky="w")
warp_wait_entry = ctk.CTkEntry(tab_advanced)
warp_wait_entry.insert(0, str(general_settings.get("warp_reset_wait", 8.0)))
warp_wait_entry.grid(row=22, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="(Tool sẽ chờ mãi đến khi WARP Connected, nhấn DỪNG nếu muốn dừng)", text_color="gray", font=("Segoe UI", 10)).grid(row=23, column=0, columnspan=2, pady=2, sticky="w")

# Đuôi username
ctk.CTkLabel(tab_advanced, text="Tùy chỉnh đuôi username", font=("Segoe UI", 12, "bold")).grid(row=25, column=0, columnspan=2, pady=10, sticky="w")

ctk.CTkCheckBox(tab_advanced, text="Random phần đuôi username (tổng 16 ký tự)", variable=random_tail_var).grid(row=26, column=0, columnspan=2, pady=5, sticky="w")

ctk.CTkCheckBox(tab_advanced, text="Số thứ tự tăng dần cho phần đuôi", variable=sequential_tail_var).grid(row=27, column=0, columnspan=2, pady=5, sticky="w")

ctk.CTkLabel(tab_advanced, text="Số bắt đầu:").grid(row=28, column=0, padx=10, pady=5, sticky="w")
start_num_entry = ctk.CTkEntry(tab_advanced)
start_num_entry.insert(0, "0")
start_num_entry.grid(row=28, column=1, pady=5, sticky="ew")

ctk.CTkLabel(tab_advanced, text="Số kết thúc:").grid(row=29, column=0, padx=10, pady=5, sticky="w")
end_num_entry = ctk.CTkEntry(tab_advanced)
end_num_entry.insert(0, "9999")
end_num_entry.grid(row=29, column=1, pady=5, sticky="ew")

# Nút điều khiển
btn_frame = ctk.CTkFrame(scroll_frame)
btn_frame.pack(pady=20)

start_btn = ctk.CTkButton(btn_frame, text="BẮT ĐẦU", fg_color="green", command=lambda: threading.Thread(target=start_tool, daemon=True).start())
start_btn.pack(side="left", padx=15)

stop_btn = ctk.CTkButton(btn_frame, text="DỪNG", fg_color="red", command=stop_event.set)
stop_btn.pack(side="left", padx=15)

def save_current_settings():
    general_settings["selected_site"] = site_combo.get()
    general_settings["file_path"] = file_entry.get().strip()
    general_settings["quantity"] = int(quantity_entry.get() or 10)
    general_settings["headless"] = headless_var.get()
    general_settings["typing_speed"] = typing_speed_preset.get()
    general_settings["reset_warp"] = reset_warp_var.get()
    try:
        general_settings["warp_reset_wait"] = float(warp_wait_entry.get() or 8.0)
    except ValueError:
        general_settings["warp_reset_wait"] = 8.0

    current_site = site_select_combo.get()
    try:
        site_settings[current_site] = {
            "delay_min": float(delay_min_entry.get() or 15.0),
            "delay_max": float(delay_max_entry.get() or 35.0),
            "delay_after_load": float(delay_after_load_entry.get() or 8.0),
            "delay_after_submit": float(delay_after_submit_entry.get() or 12.0),
            "recaptcha_timeout": float(recaptcha_timeout_entry.get() or 180.0),
            "delay_after_recaptcha": float(delay_after_recaptcha_entry.get() or 3.0),
            "delay_before_fill": float(delay_before_fill_entry.get() or 2.0),
            "delay_per_char": float(delay_per_char_entry.get() or 0.1),
            "delay_after_click_field": float(delay_after_click_field_entry.get() or 0.4),
            "speed_multiplier": speed_slider.get(),
            "reload_before": reload_before_var.get(),
            "has_recaptcha": has_recaptcha_var.get(),
            "mouse_simulation": mouse_sim_var.get(),
            "delay_click_register": float(delay_click_entry.get() or 2.0),
            "delay_reload_form": float(delay_reload_entry.get() or 3.0),
            "optimize_speed": optimize_speed_var.get()
        }
        save_settings(general_settings, site_settings, show_popup=True)
    except ValueError as ve:
        messagebox.showerror("Lỗi nhập liệu", f"Giá trị không hợp lệ (phải là số): {str(ve)}")

save_btn = ctk.CTkButton(btn_frame, text="LƯU SETTINGS", fg_color="#1f6feb", command=save_current_settings)
save_btn.pack(side="left", padx=15)

def start_tool():
    stop_event.clear()
    general_settings["selected_site"] = site_combo.get()
    general_settings["file_path"] = file_entry.get().strip()
    general_settings["quantity"] = int(quantity_entry.get() or 10)
    general_settings["headless"] = headless_var.get()
    general_settings["typing_speed"] = typing_speed_preset.get()
    general_settings["reset_warp"] = reset_warp_var.get()
    try:
        general_settings["warp_reset_wait"] = float(warp_wait_entry.get() or 8.0)
    except ValueError:
        general_settings["warp_reset_wait"] = 8.0

    current_site = general_settings["selected_site"]
    try:
        site_settings[current_site]["delay_min"] = float(delay_min_entry.get() or 15.0)
        site_settings[current_site]["delay_max"] = float(delay_max_entry.get() or 35.0)
        site_settings[current_site]["delay_after_load"] = float(delay_after_load_entry.get() or 8.0)
        site_settings[current_site]["delay_after_submit"] = float(delay_after_submit_entry.get() or 12.0)
        site_settings[current_site]["recaptcha_timeout"] = float(recaptcha_timeout_entry.get() or 180.0)
        site_settings[current_site]["delay_after_recaptcha"] = float(delay_after_recaptcha_entry.get() or 3.0)
        site_settings[current_site]["delay_before_fill"] = float(delay_before_fill_entry.get() or 2.0)
        site_settings[current_site]["delay_per_char"] = float(delay_per_char_entry.get() or 0.1)
        site_settings[current_site]["delay_after_click_field"] = float(delay_after_click_field_entry.get() or 0.4)
        site_settings[current_site]["speed_multiplier"] = speed_slider.get()
        site_settings[current_site]["reload_before"] = reload_before_var.get()
        site_settings[current_site]["has_recaptcha"] = has_recaptcha_var.get()
        site_settings[current_site]["mouse_simulation"] = mouse_sim_var.get()
        site_settings[current_site]["delay_click_register"] = float(delay_click_entry.get() or 2.0)
        site_settings[current_site]["delay_reload_form"] = float(delay_reload_entry.get() or 3.0)
        site_settings[current_site]["optimize_speed"] = optimize_speed_var.get()

        save_settings(general_settings, site_settings, show_popup=False)

        log_text.delete("1.0", "end")
        log_queue.put(("🚀 BẮT ĐẦU TOOL", "white"))
        if general_settings["reset_warp"]:
            log_queue.put(("Reset WARP sau mỗi acc: BẬT (chờ đến Connected)", "yellow"))
        else:
            log_queue.put(("Reset WARP: TẮT", "gray"))

        danh_sach = tai_danh_sach_tai_khoan(general_settings["file_path"])
        if not danh_sach:
            messagebox.showerror("Lỗi", "File không tồn tại hoặc rỗng!")
            return

        ten_goc, mat_khau = danh_sach[0]
        total = general_settings["quantity"]
        success_count = fail_count = 0

        start_num = int(start_num_entry.get() or 0)
        end_num = int(end_num_entry.get() or 9999)
        current_num = start_num

        for i in range(total):
            if stop_event.is_set():
                log_queue.put(("Tool dừng", "white"))
                break

            ten_moi = tao_ten_dang_nhap(ten_goc, current_num)
            log_queue.put((f"\n=== ACC {i+1}/{total} ===", "white"))

            ok = dang_ky_tai_khoan(SITES[current_site], ten_moi, mat_khau, i+1, log_queue, stop_event)

            if ok:
                success_count += 1
            else:
                fail_count += 1

            # Reset WARP nếu bật
            if general_settings["reset_warp"] and not stop_event.is_set():
                log_queue.put(("Bắt đầu reset 1.1.1.1 WARP... (chờ đến Connected)", "yellow"))
                reset_ok = reset_warp(log_queue, general_settings["warp_reset_wait"])
                if not reset_ok:
                    log_queue.put(("Reset WARP thất bại hoặc bị dừng thủ công → Tool dừng", "red"))
                    stop_event.set()
                    break

            if i < total - 1 and not stop_event.is_set():
                delay = random.uniform(site_settings[current_site]["delay_min"], site_settings[current_site]["delay_max"])
                log_queue.put((f"⏳ Chờ {delay:.1f}s...", "white"))
                time.sleep(delay)

            if sequential_tail_var.get():
                current_num += 1
                if current_num > end_num:
                    current_num = start_num

        log_queue.put((f"\n🎉 HOÀN THÀNH: {success_count} THÀNH CÔNG | {fail_count} THẤT BẠI", "white"))
        messagebox.showinfo("Hoàn thành", f"Thành công: {success_count}\nThất bại: {fail_count}")

    except ValueError as ve:
        messagebox.showerror("Lỗi nhập liệu", f"Giá trị delay không hợp lệ (phải là số): {str(ve)}")
    except KeyboardInterrupt:
        log_queue.put(("Tool bị ngắt thủ công (Ctrl+C hoặc đóng cửa sổ)", "white"))
        stop_event.set()

root.mainloop()