
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# === Cấu hình Selenium ===
options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # Nếu muốn chạy ẩn

driver = webdriver.Chrome(options=options)

# === Hàm cuộn trang từng đoạn và thu thập link ngay khi xuất hiện ===
def crawl_all_links(max_pages=413):
    base_url = "https://diamondsdirect.com/natural-diamonds/?_fs=cust_shape_esai%3B%3BRound&from={}"
    all_links = []

    for page_num in range(1, max_pages + 1):
        url = base_url.format(page_num)
        driver.get(url)
        time.sleep(2)  # đợi trang load

        anchors = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/round-"]')
        page_links = []

        for a in anchors:
            href = a.get_attribute("href")
            if href and href not in all_links:
                all_links.append(href)
                page_links.append(href)

        print(f"[+] Page {page_num} - Found {len(page_links)} links")

    return all_links

# === Crawl toàn bộ khoảng giá ===
links = crawl_all_links()
driver.quit()

# Lưu kết quả
df = pd.DataFrame(links, columns=["link"])
df.to_csv("diamond_links.csv", index=False)
print(f"Tổng cộng: {len(links)} links được lưu.")