from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Pool, Manager, Lock
from ctypes import c_int
import pandas as pd
import time

def crawl_diamond_data(args):
    """Hàm chạy ở mỗi tiến trình riêng biệt"""
    urls_chunk, counter, lock = args

    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    results = []

    for url in urls_chunk:
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1)

            try:
                show_more_btn = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='show-more']"))
                )
                driver.execute_script("arguments[0].click();", show_more_btn)
                time.sleep(0.5)
            except:
                pass

            def get(prefix):
                try:
                    element = driver.find_element(By.XPATH, f"//div[starts-with(@data-qa, '{prefix}')]")
                    return element.text.strip()
                except:
                    return ""

            def get2(prefix):
                try:
                    element = driver.find_element(By.XPATH, f"//div[starts-with(@dataqa, '{prefix}')]")
                    return element.text.strip()
                except:
                    return ""

            data = {
                "carat": get("CaratWeight-"),
                "cut": get("Cut-"),
                "color": get("Color-"),
                "clarity": get("Clarity-"),
                "depth": get("depthPrecentage-"),
                "table": get("tablePrecentage-"),
                "price": get("price"),
                "measurements": get2("Measurements-"),
            }
            results.append(data)

            # Tăng biến đếm an toàn trong môi trường đa tiến trình
            with lock:
                counter.value += 1
                print(f"📦 Đã thu được {counter.value} mẫu")

            time.sleep(1)
        except Exception as e:
            print(f"❌ Lỗi {url}: {e}")

    driver.quit()
    return results

def split_list(lst, n):
    """Chia danh sách thành n phần đều nhau"""
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

if __name__ == "__main__":
    df = pd.read_csv("diamond_urls.csv")
    urls = df["url"].tolist()
    urls = urls[3000:]  # Có thể điều chỉnh số lượng tùy ý

    NUM_PROCESSES = 4
    url_chunks = split_list(urls, NUM_PROCESSES)

    manager = Manager()
    counter = manager.Value(c_int, 0)  # Biến đếm dùng chung
    lock = manager.Lock()              # Khóa để đảm bảo thread-safe khi in/log

    # Gắn counter và lock vào mỗi chunk khi truyền vào hàm crawl
    args_list = [(chunk, counter, lock) for chunk in url_chunks]

    with Pool(processes=NUM_PROCESSES) as pool:
        all_data_chunks = pool.map(crawl_diamond_data, args_list)

    # Gộp dữ liệu từ các tiến trình
    all_data = []
    for chunk in all_data_chunks:
        all_data.extend(chunk)

    # Lưu vào file CSV
    pd.DataFrame(all_data).to_csv("diamond_details3.csv", index=False)
    print("✅ Đã lưu kết quả vào diamond_details3.csv")
