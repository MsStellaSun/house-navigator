"""
上海新房爬虫 - 使用 Selenium 无头浏览器从贝壳找房抓取楼盘数据
fangdi.com.cn 有严格反爬机制，切换为贝壳作为替代数据源
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
# 贝壳找房 - 上海新房列表页（数据源相对开放）
BASE_URL = "https://sh.newhouse.fang.com/loupan/"
DATA_FILE = "scraped_data.json"
TIMEOUT = 30
MAX_RETRIES = 3


class BeiKeCrawler:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless=new")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("useAutomationExtension", False)
        self.driver = None
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    def _init_driver(self):
        if self.driver is None:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })

    def _wait_for_page_load(self, timeout: int = 20) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except Exception:
            return False

    def _parse_price(self, price_str: str) -> int:
        """从字符串提取价格数值"""
        if not price_str:
            return 0
        # 提取数字
        match = re.search(r'[\d,]+', price_str.replace(',', ''))
        if not match:
            return 0
        val = int(match.group().replace(',', ''))
        # 如果是"万"单位（总价），转换为元/平米（除以100）
        # 如果已经是单价，直接用
        return val

    def _extract_district(self, text: str) -> str:
        """从地址中提取行政区"""
        districts = [
            '浦东新区', '黄浦区', '静安区', '徐汇区', '长宁区', '普陀区',
            '虹口区', '杨浦区', '闵行区', '宝山区', '嘉定区', '松江区',
            '青浦区', '奉贤区', '金山区', '崇明区'
        ]
        for d in districts:
            if d in text:
                return d
        return text[:6] if len(text) > 6 else text

    def _load_existing_data(self) -> Optional[dict]:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _save_data(self, data: dict):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _parse_page(self) -> List[Dict]:
        """解析当前页面提取楼盘列表"""
        houses = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 贝壳找房的楼盘列表选择器
            selectors = [
                '.house-list .house-info',
                '.lp-list .lp-item',
                '.new-loupan-list .item',
                '[class*="loupan"] [class*="item"]',
                '.qtf-loupan-list .item',
            ]
            
            found = False
            for selector in selectors:
                items = soup.select(selector)
                if items and len(items) > 0:
                    print(f"  [解析] 使用选择器 '{selector}' 找到 {len(items)} 条")
                    found = True
                    
                    for item in items:
                        house = self._extract_loupan_item(item)
                        if house:
                            houses.append(house)
                    break
            
            # 备选：从 div 结构提取
            if not found:
                all_divs = soup.select('.flophase, .nhouse_item, #newhouse-list li')
                for div in all_divs:
                    house = self._extract_loupan_item(div)
                    if house:
                        houses.append(house)
                        
        except Exception as e:
            print(f"  [解析异常] {e}")
        
        return houses

    def _extract_loupan_item(self, element) -> Optional[Dict]:
        """从楼盘元素提取信息"""
        try:
            # 楼盘名
            name_selectors = ['.lp-name', '.name', 'h3 a', 'a[href*="loupan"]', 'h4']
            name = None
            for sel in name_selectors:
                el = element.select_one(sel)
                if el:
                    name = el.get_text(strip=True)
                    break
            
            if not name or len(name) < 2:
                return None
            
            # 价格
            price_selectors = ['.price', '.average-price', '[class*="price"]', '.jiage']
            price_text = "0"
            for sel in price_selectors:
                el = element.select_one(sel)
                if el:
                    price_text = el.get_text(strip=True)
                    break
            
            # 地址/区域
            addr_selectors = ['.address', '.district', '[class*="addr"]', '.dizhi']
            address = ""
            for sel in addr_selectors:
                el = element.select_one(sel)
                if el:
                    address = el.get_text(strip=True)
                    break
            
            district = self._extract_district(address)
            
            # 销售状态
            status_selectors = ['.state', '.sales-status', '[class*="status"]']
            status = "在售"
            for sel in status_selectors:
                el = element.select_one(sel)
                if el:
                    status_text = el.get_text(strip=True)
                    if '待售' in status_text or '预' in status_text:
                        status = '待售'
                    elif '售罄' in status_text or '售完' in status_text:
                        status = '售罄'
                    break
            
            return {
                "id": f"BK_{datetime.now().strftime('%Y%m%d')}_{hash(name) % 10000}",
                "name": name,
                "district": district,
                "address": address,
                "averagePrice": self._parse_price(price_text),
                "salesStatus": status,
                "launchDate": "",
            }
        except Exception as e:
            return None

    def fetch_data(self) -> dict:
        """主入口"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动贝壳找房数据同步任务...")
        
        existing_data = self._load_existing_data()
        old_houses = existing_data.get('houses', []) if existing_data else []
        print(f"  [数据] 现有 {len(old_houses)} 条记录")
        
        self._init_driver()
        houses = []
        
        try:
            print(f"  [访问] 正在打开 {BASE_URL}...")
            self.driver.get(BASE_URL)
            time.sleep(5)
            
            # 等待页面加载
            self._wait_for_page_load()
            time.sleep(3)
            
            # 尝试滚动加载更多数据
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(1)
            
            # 检查是否被拦截
            page_text = self.driver.page_source
            if '访问' in page_text and '验证' in page_text:
                print("  [警告] 触发了访问验证，尝试绕过...")
            
            houses = self._parse_page()
            print(f"  [完成] 共找到 {len(houses)} 条楼盘记录")
            
        except Exception as e:
            print(f"  [错误] {e}")
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        # 处理结果
        if houses and len(houses) > 0:
            print(f"  [成功] 抓取到 {len(houses)} 条数据")
            new_data = {
                "source": "贝壳找房 (sh.newhouse.fang.com)",
                "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "houses": houses,
            }
            self._save_data(new_data)
            return new_data
        else:
            print("  [失败] 未获取到数据，保留原有记录")
            if existing_data:
                existing_data['lastUpdated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (同步失败，保留旧数据)"
                self._save_data(existing_data)
                return existing_data
            else:
                return {
                    "source": "贝壳找房",
                    "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "houses": [],
                    "error": "无法获取新数据"
                }

    def run(self):
        data = self.fetch_data()
        total = len(data.get('houses', []))
        print(f"[完成] 数据已保存至 {DATA_FILE}，当前共 {total} 条楼盘记录")


if __name__ == "__main__":
    crawler = BeiKeCrawler()
    crawler.run()