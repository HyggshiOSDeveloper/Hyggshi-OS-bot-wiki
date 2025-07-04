import mwclient
from datetime import datetime
import os

# Thông tin đăng nhập bot
SITE_NAME = 'hyggshi-os.fandom.com'

USERNAME = os.environ['FANDOM_USER']
PASSWORD = os.environ['FANDOM_PASS']
# Tên trang bạn muốn ping

PAGE_NAME = 'Hyggshi OS 2.0'  # Trang bạn muốn sửa để giữ wiki sống

def update_page():
    site = mwclient.Site(SITE_NAME, path='/')
    site.login(USERNAME, PASSWORD)
    page = site.pages[PAGE_NAME]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    current = page.text()
    if "<!-- ping update" in current:
        updated = current.replace("<!-- ping update -->", f"<!-- ping update {now} -->")
    else:
        updated = current + f"\n<!-- ping update {now} -->"
    
    page.save(updated, summary='Tự động ping để giữ wiki sống')
    print(f"[✓] Pinged at {now}")

update_page()
