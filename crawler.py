"""
上海新房爬虫 - 从网上房地产 (fangdi.com.cn) 抓取楼盘数据
支持验证码识别（ddddocr），失败时保留原数据
"""
import json
import requests
import time
import os
import re
from datetime import datetime
from typing import Optional

try:
    import ddddocr
except ImportError:
    ddddocr = None

# ============ 配置 ============
BASE_URL = "https://www.fangdi.com.cn"
DATA_FILE = "scraped_data.json"
TIMEOUT = 30
MAX_RETRIES = 3


class ShanghaiHouseCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        })
        self.ocr = ddddocr.DdddOcr(show_ad=False) if ddddocr else None
        self.cookies = {}

    def _get_captcha_image(self) -> Optional[bytes]:
        """获取验证码图片"""
        # 尝试多个可能的验证码地址
        captcha_paths = [
            "/auth/captcha.jpg",
            "/new_house/captcha.jpg",
            "/captcha.jpg",
            "/ImageServlet",
        ]
        for path in captcha_paths:
            try:
                resp = self.session.get(BASE_URL + path, timeout=10)
                if resp.status_code == 200 and len(resp.content) > 100:
                    return resp.content
            except Exception:
                continue
        return None

    def _solve_captcha(self, image_bytes: bytes) -> Optional[str]:
        """OCR识别验证码"""
        if not self.ocr:
            return None
        try:
            result = self.ocr.classification(image_bytes)
            # 清理结果：只保留字母数字，长度4-6位
            result = re.sub(r'[^a-zA-Z0-9]', '', result)
            if 4 <= len(result) <= 6:
                return result
        except Exception as e:
            print(f"  [验证码识别失败] {e}")
        return None

    def _fetch_page_with_captcha(self, page: int = 1) -> Optional[dict]:
        """带验证码的页面抓取（带重试）"""
        for attempt in range(MAX_RETRIES):
            try:
                # Step 1: 先访问主页，获取初始cookies
                main_resp = self.session.get(
                    f"{BASE_URL}/new_house/new_house.html",
                    timeout=TIMEOUT
                )
                if main_resp.status_code != 200:
                    print(f"  [尝试 {attempt+1}] 主页访问失败: {main_resp.status_code}")
                    time.sleep(2)
                    continue

                self.cookies.update(self.session.cookies.get_dict())

                # Step 2: 获取验证码
                captcha_img = self._get_captcha_image()
                if not captcha_img:
                    print(f"  [尝试 {attempt+1}] 无法获取验证码图片")
                    time.sleep(3)
                    continue

                captcha_code = self._solve_captcha(captcha_img)
                if not captcha_code:
                    print(f"  [尝试 {attempt+1}] 验证码识别失败，保留旧数据")
                    time.sleep(2)
                    continue

                print(f"  [尝试 {attempt+1}] 识别验证码: {captcha_code}")

                # Step 3: 发送查询请求（POST表单或AJAX）
                # fangdi.com.cn 使用的是静态HTML+AJAX模式，搜索参数在URL或POST数据里
                search_url = f"{BASE_URL}/new_house/new_house.html"
                post_data = {
                    "captcha": captcha_code,
                    "pageNo": page,
                    "pageSize": 50,
                    # 根据实际表单参数调整
                }

                # 尝试不同的请求方式
                resp = self.session.post(
                    search_url,
                    data=post_data,
                    timeout=TIMEOUT,
                    allow_redirects=True
                )

                # 检查是否成功（通过返回的数据量判断）
                if resp.status_code == 200:
                    text = resp.text
                    # 如果返回页面中包含楼盘数量信息，说明成功
                    if '项目' in text or '楼盘' in text or len(text) > 5000:
                        return self._parse_html(text)
                    elif '验证码' in text or 'captcha' in text.lower():
                        print(f"  [尝试 {attempt+1}] 验证码仍错误，需要重新识别")
                        time.sleep(2)
                        continue
                    else:
                        print(f"  [尝试 {attempt+1}] 返回数据异常: {len(text)} 字节")
                        time.sleep(2)
                        continue

            except requests.RequestException as e:
                print(f"  [尝试 {attempt+1}] 网络错误: {e}")
                time.sleep(2)
                continue
            except Exception as e:
                print(f"  [尝试 {attempt+1}] 未知错误: {e}")
                time.sleep(2)
                continue

        return None

    def _parse_html(self, html: str) -> Optional[dict]:
        """解析HTML页面，提取楼盘数据"""
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html, 'html.parser')
            houses = []

            # 尝试多种选择器模式（网站结构可能有变化）
            # 模式1: table 列表
            rows = soup.select('table.list-table tr, table tr, .house-list tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) >= 5:
                    house = self._extract_house_from_row(cells)
                    if house:
                        houses.append(house)

            # 模式2: div 卡片列表
            if not houses:
                cards = soup.select('.house-item, .project-item, .list-item')
                for card in cards:
                    house = self._extract_house_from_card(card)
                    if house:
                        houses.append(house)

            # 模式3: AJAX JSON 数据
            if not houses:
                scripts = soup.select('script')
                for script in scripts:
                    text = script.string or ''
                    if 'houseList' in text or 'projectList' in text:
                        houses = self._extract_from_script(text)
                        if houses:
                            break

            print(f"  [解析] 共找到 {len(houses)} 条楼盘记录")
            return houses if houses else None

        except Exception as e:
            print(f"  [解析HTML失败] {e}")
            return None

    def _extract_house_from_row(self, cells) -> Optional[dict]:
        """从表格行提取数据"""
        try:
            name = cells[0].get_text(strip=True)
            if not name or len(name) < 2:
                return None
            return {
                "id": f"FD_{datetime.now().strftime('%Y%m%d')}_{len(cells)}",
                "name": name,
                "district": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "averagePrice": self._parse_price(cells[2].get_text(strip=True) if len(cells) > 2 else "0"),
                "salesStatus": cells[3].get_text(strip=True) if len(cells) > 3 else "在售",
                "launchDate": cells[4].get_text(strip=True) if len(cells) > 4 else "",
            }
        except Exception:
            return None

    def _extract_house_from_card(self, card) -> Optional[dict]:
        """从卡片提取数据"""
        try:
            name_el = card.select_one('.name, .title, h3, h4')
            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 2:
                return None

            price_el = card.select_one('.price, .average-price')
            price_text = price_el.get_text(strip=True) if price_el else "0"

            district_el = card.select_one('.district, .area')
            district = district_el.get_text(strip=True) if district_el else ""

            return {
                "id": f"FD_{datetime.now().strftime('%Y%m%d')}_{hash(name) % 10000}",
                "name": name,
                "district": district,
                "averagePrice": self._parse_price(price_text),
                "salesStatus": "在售",
                "launchDate": "",
            }
        except Exception:
            return None

    def _extract_from_script(self, script_text: str) -> list:
        """从JS脚本中提取JSON数据"""
        houses = []
        try:
            # 尝试用正则提取 JSON 对象
            patterns = [
                r'\{[^{}]*"houses"[^{}]*\[[^\]]+\][^{}]*\}',
                r'projectList\s*=\s*(\[[\s\S]*?\]);',
                r'houseList\s*=\s*(\[[\s\S]*?\]);',
            ]
            for pattern in patterns:
                match = re.search(pattern, script_text)
                if match:
                    try:
                        data = json.loads(match.group(0))
                        if isinstance(data, list):
                            houses = data
                        elif isinstance(data, dict) and 'houses' in data:
                            houses = data['houses']
                        break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        return houses

    def _parse_price(self, price_str: str) -> int:
        """从字符串提取价格数值"""
        match = re.search(r'[\d,]+', price_str.replace(',', ''))
        if match:
            return int(match.group().replace(',', ''))
        return 0

    def _load_existing_data(self) -> Optional[dict]:
        """加载已有的scraped_data.json"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _save_data(self, data: dict):
        """保存数据到文件"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def fetch_data(self) -> dict:
        """
        主入口：尝试抓取新数据，失败时保留原数据
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动网上房地产数据同步任务...")

        existing_data = self._load_existing_data()
        old_houses = existing_data.get('houses', []) if existing_data else []
        print(f"  [数据] 现有 {len(old_houses)} 条记录，将尝试更新...")

        # 尝试抓取第1页数据
        result = self._fetch_page_with_captcha(page=1)

        if result and isinstance(result, list) and len(result) > 0:
            print(f"  [成功] 抓取到 {len(result)} 条新数据")
            new_data = {
                "source": "上海市网上房地产 (www.fangdi.com.cn)",
                "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "houses": result,
            }
            self._save_data(new_data)
            return new_data
        elif result and isinstance(result, list) and len(result) == 0:
            print("  [警告] 服务器返回空数据，保留原有记录")

        # 抓取失败，保留原数据
        print("  [失败] 抓取未成功，保留原有数据")
        if existing_data:
            # 更新时间戳但不改变数据
            existing_data['lastUpdated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (同步失败，保留旧数据)"
            self._save_data(existing_data)
            return existing_data
        else:
            # 没有原数据，返回一个提示性数据
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
    crawler = ShanghaiHouseCrawler()
    crawler.run()