"""
上海新房爬虫 - 使用 Selenium 无头浏览器从网上房地产 (fangdi.com.cn) 抓取楼盘数据
支持动态页面渲染和验证码自动识别
"""
import json
import base64
import time
import os
import re
from datetime import datetime
from typing import Optional, List, Dict

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    import ddddocr
except ImportError as e:
    print(f"缺少依赖库: {e}")
    print("请运行: pip install selenium ddddocr pillow")
    raise SystemExit(1)

# ============ 配置 ============
BASE_URL = "https://www.fangdi.com.cn"
SEARCH_URL = f"{BASE_URL}/new_house/new_house.html"
DATA_FILE = "scraped_data.json"
TIMEOUT = 30
MAX_RETRIES = 3


class SeleniumCrawler:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        # 反检测设置
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = None
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    def _init_driver(self):
        """初始化 Chrome 驱动"""
        if self.driver is None:
            self.driver = webdriver.Chrome(options=self.options)
            # 去除 webdriver 标识
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })

    def _extract_captcha_from_canvas(self) -> Optional[bytes]:
        """从页面 canvas 提取验证码图片"""
        try:
            # 尝试找到验证码 canvas 元素
            canvases = self.driver.find_elements(By.CSS_SELECTOR, "canvas")
            for canvas in canvases:
                try:
                    # 尝试获取 canvas 的 data URL
                    data_url = self.driver.execute_script(
                        "return arguments[0].toDataURL('image/jpeg');", canvas
                    )
                    if data_url and data_url.startswith("data:image"):
                        # 提取 base64 部分
                        img_data = data_url.split(",")[1]
                        return base64.b64decode(img_data)
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def _solve_captcha(self, image_bytes: bytes) -> Optional[str]:
        """OCR识别验证码"""
        try:
            result = self.ocr.classification(image_bytes)
            result = re.sub(r'[^a-zA-Z0-9]', '', result)
            if 4 <= len(result) <= 6:
                return result
        except Exception as e:
            print(f"  [验证码识别失败] {e}")
        return None

    def _wait_for_page_load(self, timeout: int = 20) -> bool:
        """等待页面加载完成"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except Exception:
            return False

    def _parse_house_list(self) -> List[Dict]:
        """解析楼盘列表"""
        houses = []
        
        try:
            from bs4 import BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 尝试多种选择器来定位楼盘列表
            selectors = [
                '.house-list .house-item',
                '.project-list .project-item',
                '.list-table tr',
                '.search-result .item',
                'table.list-table tbody tr',
                '#houseList .item',
                '.new-house-list .item',
            ]
            
            for selector in selectors:
                items = soup.select(selector)
                if items and len(items) > 1:
                    print(f"  [解析] 使用选择器 '{selector}' 找到 {len(items)} 条记录")
                    
                    for item in items:
                        house = self._extract_house(item)
                        if house:
                            houses.append(house)
                    
                    if houses:
                        break
            
            # 如果上述方法都没找到，尝试从表格中提取
            if not houses:
                tables = soup.select('table')
                for table in tables:
                    rows = table.select('tr')
                    for row in rows:
                        cells = row.select('td')
                        if len(cells) >= 4:
                            house = self._extract_house_from_cells(cells)
                            if house:
                                houses.append(house)
            
            # 如果仍然没找到，尝试从 script 标签提取 JSON
            if not houses:
                scripts = soup.select('script')
                for script in scripts:
                    text = script.string or ''
                    if 'houseList' in text or 'projectList' in text or 'houses' in text:
                        extracted = self._extract_from_script(text)
                        if extracted:
                            houses.extend(extracted)
                            break

        except Exception as e:
            print(f"  [解析失败] {e}")
        
        return houses

    def _extract_house(self, element) -> Optional[Dict]:
        """从元素提取楼盘信息"""
        try:
            # 尝试多种可能的选择器
            name_selectors = ['.name', '.title', 'h3', 'h4', '.project-name', 'a']
            price_selectors = ['.price', '.average-price', '.price-val', '[class*="price"]']
            district_selectors = ['.district', '.area', '[class*="area"]', '[class*="district"]']
            
            name_el = None
            for sel in name_selectors:
                name_el = element.select_one(sel)
                if name_el:
                    break
            
            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 2:
                return None
            
            price_el = None
            for sel in price_selectors:
                price_el = element.select_one(sel)
                if price_el:
                    break
            
            price_text = price_el.get_text(strip=True) if price_el else "0"
            price = self._parse_price(price_text)
            
            district_el = None
            for sel in district_selectors:
                district_el = element.select_one(sel)
                if district_el:
                    break
            
            district = district_el.get_text(strip=True) if district_el else ""
            
            return {
                "id": f"FD_{datetime.now().strftime('%Y%m%d')}_{hash(name) % 10000}",
                "name": name,
                "district": district,
                "averagePrice": price,
                "salesStatus": "在售",
                "launchDate": "",
            }
        except Exception:
            return None

    def _extract_house_from_cells(self, cells) -> Optional[Dict]:
        """从表格单元格提取"""
        try:
            name = cells[0].get_text(strip=True)
            if not name or len(name) < 2 or '楼盘' in name or '项目' in name:
                return None
            return {
                "id": f"FD_{datetime.now().strftime('%Y%m%d')}_{hash(name) % 10000}",
                "name": name,
                "district": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "averagePrice": self._parse_price(cells[2].get_text(strip=True) if len(cells) > 2 else "0"),
                "salesStatus": cells[3].get_text(strip=True) if len(cells) > 3 else "在售",
                "launchDate": cells[4].get_text(strip=True) if len(cells) > 4 else "",
            }
        except Exception:
            return None

    def _extract_from_script(self, script_text: str) -> List[Dict]:
        """从JS脚本提取JSON数据"""
        houses = []
        try:
            # 尝试多种正则模式
            patterns = [
                r'house[s]?\s*[=:]\s*\[([\s\S]+?)\];',
                r'project[s]?\s*[=:]\s*\[([\s\S]+?)\];',
                r'\"houses\"\s*:\s*\[([\s\S]+?)\]',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, script_text)
                for match in matches:
                    try:
                        # 尝试解析为 JSON 数组
                        json_str = '[' + match + ']'
                        data = json.loads(json_str)
                        for item in data:
                            if isinstance(item, dict) and 'name' in item:
                                houses.append({
                                    "id": item.get('id', f"FD_{datetime.now().strftime('%Y%m%d')}_{len(houses)}"),
                                    "name": item.get('name', ''),
                                    "district": item.get('district', item.get('area', '')),
                                    "averagePrice": self._parse_price(str(item.get('price', '0'))),
                                    "salesStatus": item.get('status', '在售'),
                                })
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        return houses

    def _parse_price(self, price_str: str) -> int:
        """从字符串提取价格"""
        match = re.search(r'[\d,]+', price_str.replace(',', ''))
        return int(match.group().replace(',', '')) if match else 0

    def _load_existing_data(self) -> Optional[dict]:
        """加载已有数据"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _save_data(self, data: dict):
        """保存数据"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def fetch_data(self) -> dict:
        """主入口：抓取数据，失败时保留原数据"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动网上房地产数据同步任务 (Selenium模式)...")
        
        existing_data = self._load_existing_data()
        old_houses = existing_data.get('houses', []) if existing_data else []
        print(f"  [数据] 现有 {len(old_houses)} 条记录，将尝试更新...")
        
        self._init_driver()
        houses = []
        
        try:
            print(f"  [访问] 正在打开 {SEARCH_URL}...")
            self.driver.get(SEARCH_URL)
            self._wait_for_page_load()
            time.sleep(3)  # 等待动态内容加载
            
            # 检查是否有验证码弹窗
            for attempt in range(MAX_RETRIES):
                try:
                    # 尝试查找并关闭验证码弹窗
                    captcha_close_selectors = [
                        ".captcha-close", ".close-btn", ".modal-close",
                        "//button[contains(text(),'关闭')]",
                    ]
                    for selector in captcha_close_selectors:
                        try:
                            if selector.startswith("//"):
                                self.driver.find_element(By.XPATH, selector).click()
                            else:
                                self.driver.find_element(By.CSS_SELECTOR, selector).click()
                            time.sleep(1)
                            print(f"  [验证码] 已关闭弹窗")
                            break
                        except:
                            pass
                    
                    # 提取验证码图片
                    captcha_img = self._extract_captcha_from_canvas()
                    if captcha_img:
                        captcha_code = self._solve_captcha(captcha_img)
                        if captcha_code:
                            print(f"  [验证码] 识别码: {captcha_code}")
                            # 查找验证码输入框并填写
                            try:
                                captcha_input = self.driver.find_element(By.CSS_SELECTOR, 
                                    "input[name*='captcha'], input[id*='captcha'], input[placeholder*='验证码']")
                                captcha_input.clear()
                                captcha_input.send_keys(captcha_code)
                                time.sleep(1)
                                # 点击查询/搜索按钮
                                submit_btn = self.driver.find_element(By.CSS_SELECTOR,
                                    "button[type='submit'], .search-btn, .query-btn")
                                submit_btn.click()
                                time.sleep(3)
                            except Exception as e:
                                print(f"  [验证码填写失败] {e}")
                    else:
                        print(f"  [验证码] 无需验证码或已自动通过")
                    
                    # 检查页面是否正常加载了数据
                    page_source = self.driver.page_source
                    if '楼盘' in page_source or '项目' in page_source or 'house' in page_source.lower():
                        print(f"  [成功] 页面已加载")
                        break
                    else:
                        print(f"  [尝试 {attempt+1}] 页面未正常加载，重试...")
                        self.driver.refresh()
                        time.sleep(3)
                        
                except Exception as e:
                    print(f"  [尝试 {attempt+1}] 错误: {e}")
                    time.sleep(2)
            
            # 解析楼盘数据
            houses = self._parse_house_list()
            print(f"  [解析] 共找到 {len(houses)} 条楼盘记录")
            
        except Exception as e:
            print(f"  [错误] {e}")
        finally:
            self.driver.quit()
            self.driver = None
        
        # 根据结果处理
        if houses and len(houses) > 0:
            print(f"  [成功] 抓取到 {len(houses)} 条新数据")
            new_data = {
                "source": "上海市网上房地产 (www.fangdi.com.cn)",
                "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "houses": houses,
            }
            self._save_data(new_data)
            return new_data
        else:
            print("  [失败] 未能抓取到数据，保留原有记录")
            if existing_data:
                existing_data['lastUpdated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (同步失败，保留旧数据)"
                self._save_data(existing_data)
                return existing_data
            else:
                return {
                    "source": "上海市网上房地产 (www.fangdi.com.cn)",
                    "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (同步失败)",
                    "houses": [],
                    "error": "无法获取新数据，请检查网络或验证码识别服务"
                }

    def run(self):
        """运行爬虫"""
        data = self.fetch_data()
        total = len(data.get('houses', []))
        print(f"[完成] 数据已保存至 {DATA_FILE}，当前共 {total} 条楼盘记录")


if __name__ == "__main__":
    # 检查必要依赖
    try:
        from selenium import webdriver
        import ddddocr
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请运行: pip install selenium ddddocr pillow")
        exit(1)
    
    crawler = SeleniumCrawler()
    crawler.run()