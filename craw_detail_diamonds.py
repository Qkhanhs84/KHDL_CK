from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
import pandas as pd
from multiprocessing import Pool, cpu_count

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

def crawl_links(link_list, process_id):
    driver = setup_driver()
    results = []

    def get_field_by_class(field):
        try:
            el = driver.find_element(By.CSS_SELECTOR, f'li.{field} span span')
            return el.text.strip()
        except:
            return None

    def get_price():
        try:
            el = driver.find_element(By.CSS_SELECTOR, 'div.product-detail-top-section span.price.price--withoutTax')
            return el.text.strip()
        except:
            return None

    for idx, link in enumerate(link_list):
        try:
            driver.get(link)
            sleep(2)

            data = {}
            for field in ["carat", "color", "clarity", "cut", "table", "depth", "measurements"]:
                data[field] = get_field_by_class(field)
            data["price"] = get_price()

            results.append(data)
            print(f"[Process {process_id}] {idx+1}/{len(link_list)}: Done")
        except Exception as e:
            print(f"[Process {process_id}] Error at {link}: {e}")
            results.append({"link": link, "carat": None, "color": None, "clarity": None, "cut": None,
                            "table": None, "depth": None, "measurements": None, "price": None})

    driver.quit()
    return results

df_links = pd.read_csv("diamond_links.csv")
all_links = df_links['link'].tolist()

# Chia nhỏ dữ liệu (4 process)
def split_list(lst, n):
    k, m = divmod(len(lst), n)
    return [lst[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]

chunks = split_list(all_links, 4)  # chia 4 phần

# Dùng multiprocessing Pool để chạy song song
if __name__ == "__main__":
    with Pool(processes=4) as pool:
        results = pool.starmap(crawl_links, [(chunk, i) for i, chunk in enumerate(chunks)])

    # Gộp kết quả từ các process
    flat_results = [item for sublist in results for item in sublist]
    df = pd.DataFrame(flat_results)
    df.to_csv("diamond_full_data3.csv", index=False)
    print(f"✅ Đã lưu {len(flat_results)} records vào diamond_full_data3.csv")
