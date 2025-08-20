from multiprocessing import Pool
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import mwclient
import schedule
from wikis_config import WIKIS
import sys

sys.stdout.reconfigure(encoding='utf-8')

# === Nạp biến môi trường ===
load_dotenv()
USERNAME = os.getenv("WIKI_USER")
PASSWORD = os.getenv("WIKI_PASS")

if not USERNAME or not PASSWORD:
    raise RuntimeError("Thiếu WIKI_USER hoặc WIKI_PASS.")

# === Ghi dấu lần chạy mới vào log.txt ===
with open("log.txt", "a", encoding="utf-8") as f:
    f.write("\n=== Chạy mới: {} ===\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

# === Hàm log chuẩn ===
def log(msg, wiki_desc=None): 
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    prefix = f"[{wiki_desc}]" if wiki_desc else ""
    full_msg = f"{timestamp} {prefix} {msg}"

    print(full_msg)
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

# === Hàm cập nhật trang ===
def update_page(site, page_name, wiki_desc):
    try:
        page = site.pages[page_name]
        if not page.exists:
            log(f"[⚠] Trang không tồn tại: {page_name}", wiki_desc)
            return

        log(f"[🟢] Tìm thấy trang: {page_name}", wiki_desc)
        current_text = page.text()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_ping = f"<!-- ping update {timestamp} -->"

        if "<!-- ping update" in current_text:
            start = current_text.find("<!-- ping update")
            end = current_text.find("-->", start)
            if end != -1:
                old_ping = current_text[start:end+3]
                new_text = current_text.replace(old_ping, new_ping, 1)
            else:
                new_text = current_text + "\n" + new_ping
        else:
            new_text = current_text + "\n" + new_ping

        page.save(new_text, summary="Tự động cập nhật để giữ wiki hoạt động")
        log(f"[✓] Cập nhật thành công: {page_name}", wiki_desc)

    except mwclient.errors.ProtectedPageError:
        log(f"[🔒] Trang bị khóa: {page_name}", wiki_desc)
    except Exception as e:
        log(f"[X] Lỗi không xác định: {e}", wiki_desc)

# === Hàm xử lý từng wiki ===
def process_wiki(wiki):
    desc = wiki["desc"]
    log(f"🌐 Bắt đầu xử lý wiki: {desc}", desc)
    try:
        site = mwclient.Site(
            host=wiki['hostcheck'],
            path=wiki['path'],
            scheme="https"
        )
        site.login(USERNAME, PASSWORD)
    except Exception as e:
        log(f"[X] Không thể kết nối hoặc đăng nhập: {e}", desc)
        return

    for i, page in enumerate(wiki["pages"]):
        update_page(site, page, desc)
        if i < len(wiki["pages"]) - 1:
            time.sleep(20)
            log("⏳ Tạm dừng 20s...", desc)

    log(f"✅ Hoàn tất: {desc}", desc)

# === Hàm chạy toàn bộ wiki ===
def update_all_pages():
    log("🔄 Bắt đầu cập nhật toàn bộ wiki...")
    with Pool(processes=4) as pool:
        pool.map(process_wiki, WIKIS)

# === Chạy thử 1 wiki đầu tiên ===
def test_first_wiki():
    test_wiki = WIKIS[0]
    desc = test_wiki['desc']
    try:
        site = mwclient.Site(
            host=test_wiki['hostcheck'],
            path=test_wiki['path'],
            scheme="https"
        )
        site.login(USERNAME, PASSWORD)
        log(f"[✔] Đăng nhập thành công vào wiki thử: {desc}")
    except Exception as e:
        log(f"[X] Thử kết nối thất bại: {e}")
        exit(1)

# === Chạy chính ===
if __name__ == "__main__":
    start_time = time.time()

    test_first_wiki()  # kiểm tra wiki đầu tiên

    # Gọi lần đầu tiên ngay khi khởi chạy
    update_all_pages()

    # Lên lịch chạy mỗi 10 phút
    schedule.every(10).minutes.do(update_all_pages)
    print("🤖 Bot đang chạy thử nghiệm, sẽ cập nhật mỗi 10 phút...")

    try:
        # Vòng lặp chờ
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Bot đã dừng bởi người dùng.")

    end_time = time.time()
    total_minutes = round((end_time - start_time) / 60, 2)
    log(f"🏁 Tất cả đã xử lý xong. Thời gian: {total_minutes} phút.")

# === Kết thúc chương trình ===
# Chương trình đã hoàn thành cập nhật các wiki và ghi log đầy đủ.