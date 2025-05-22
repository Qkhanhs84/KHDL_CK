
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
def get_detail_urls_in_price_range(driver, min_price, max_price):
    # Truy cập trang với filter giá và list view
    url = (
        f"https://www.bluenile.com/diamond-search?"
        f"CaratFrom=0.05&Color=K,J,I,H,G,F,E,D"
        f"&PriceFrom={min_price}&PriceTo={max_price}"
        f"&Clarity=SI2,SI1,VS2,VS1,VVS2,VVS1,IF,FL"
        f"&Cut=Good,Very+Good,Ideal,AstorIdeal"
        f"&Sort=Latest&resultsView=List"
    )
    driver.get(url)

    # Đợi ít nhất một link chi tiết xuất hiện
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/diamond-details/')]") )
    )

    detail_urls = set()
    prev_count = 0
    no_change = 0
    max_no_change = 10

    # Cuộn bằng window, không dùng container
    while True:
        # Cuộn window xuống một đoạn
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(0.01)

        # Thu thập tất cả <a> còn trong DOM
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '/diamond-details/')]")
        for link in links:
            href = link.get_attribute("href")
            if href:
                detail_urls.add(href)

        curr_count = len(detail_urls)

        # Kiểm tra nếu không có link mới
        if curr_count == prev_count:
            no_change += 1
        else:
            prev_count = curr_count
            no_change = 0

        # Dừng khi không có link mới sau max_no_change lần và đã cuộn tới đáy
        scroll_pos = driver.execute_script("return window.pageYOffset + window.innerHeight;")
        scroll_height = driver.execute_script("return document.body.scrollHeight;")
        reached_bottom = scroll_pos >= scroll_height

        if reached_bottom and no_change >= max_no_change:
            break

    print(f"🔍 Thu được {len(set(detail_urls))} URL từ ${min_price} đến ${max_price}")
    return list(set(detail_urls))

# === Crawl toàn bộ khoảng giá ===
all_urls = []
for price_min in range(4000, 10001, 50):  # 4000-10000 step 50
    price_max = price_min + 49
    try:
        urls = get_detail_urls_in_price_range(driver, price_min, price_max)
        all_urls.extend(urls)
        time.sleep(1)
    except Exception as e:
        print(f"❌ Lỗi ở khoảng giá {price_min}-{price_max}: {e}")

# === Lưu kết quả ===
df = pd.DataFrame({'url': sorted(set(all_urls))})
df.to_csv("diamond_urls.csv", index=False)
print(f"\n✅ Đã lưu tổng {len(df)} URL vào diamond_urls.csv")

# === Đóng trình duyệt ===
driver.quit()

