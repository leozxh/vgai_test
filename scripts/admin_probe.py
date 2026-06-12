"""临时探查脚本：登录 visiva 中台，dump 左侧菜单和当前页面 DOM 摘要。

用法: python scripts/admin_probe.py <url> <email> <password>
跑完即删除。
"""
import os
import sys
import time
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# 从 PATH 移除旧 chromedriver 目录，避免版本冲突
def _strip_stale_chromedriver_dirs_from_path():
    path_var = os.environ.get("PATH", "")
    if not path_var:
        return
    sep = os.pathsep
    parts = []
    for p in path_var.split(sep):
        if not p:
            continue
        norm = p.replace("/", "\\").lower()
        if "webdriver\\bin" in norm or norm.endswith("webdriver\\bin"):
            continue
        parts.append(p)
    os.environ["PATH"] = sep.join(parts)

_strip_stale_chromedriver_dirs_from_path()
os.environ["NO_PROXY"] = os.environ.get("NO_PROXY", "") + ",localhost,127.0.0.1"

URL = sys.argv[1]
EMAIL = sys.argv[2]
PASSWORD = sys.argv[3]

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots', 'admin')
os.makedirs(OUT_DIR, exist_ok=True)


def build_options():
    o = webdriver.ChromeOptions()
    o.add_argument('--no-sandbox')
    o.add_argument('--disable-dev-shm-usage')
    o.add_argument('--window-size=1920,1080')
    o.add_argument('--disable-blink-features=AutomationControlled')
    o.add_argument('--log-level=3')
    return o


def main():
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except Exception:
        service = Service()

    driver = webdriver.Chrome(service=service, options=build_options())
    driver.implicitly_wait(2)
    driver.set_page_load_timeout(45)

    try:
        logging.info(f'打开 {URL}')
        driver.get(URL)
        time.sleep(3)
        driver.save_screenshot(os.path.join(OUT_DIR, '01_landing.png'))

        # 尝试常见登录表单：email/password input
        try:
            inputs = driver.find_elements(By.CSS_SELECTOR, 'input')
            email_input = None
            pwd_input = None
            for inp in inputs:
                t = (inp.get_attribute('type') or '').lower()
                n = (inp.get_attribute('name') or '').lower()
                p = (inp.get_attribute('placeholder') or '').lower()
                if t == 'password' or 'password' in n or 'password' in p:
                    pwd_input = inp
                elif t in ('email', 'text') or 'email' in n or 'user' in n or 'email' in p or 'user' in p or 'account' in p:
                    if email_input is None:
                        email_input = inp
            if email_input and pwd_input:
                email_input.send_keys(EMAIL)
                pwd_input.send_keys(PASSWORD)
                # 找登录按钮
                buttons = driver.find_elements(By.CSS_SELECTOR, 'button, [type="submit"]')
                for b in buttons:
                    txt = (b.text or '').strip().lower()
                    if any(k in txt for k in ['log in', 'login', 'sign in', '登录', 'signin']):
                        b.click()
                        break
                else:
                    if buttons:
                        buttons[0].click()
                time.sleep(5)
                driver.save_screenshot(os.path.join(OUT_DIR, '02_after_login.png'))
                logging.info(f'登录后 URL: {driver.current_url}')
            else:
                logging.warning('未找到登录表单，可能已是免登或需要 SSO')
        except Exception as e:
            logging.error(f'登录步骤失败: {e}')

        # dump 全局菜单/侧边栏文本
        time.sleep(2)
        js = r"""
        function visible(el) {
            var r = el.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) return false;
            var s = window.getComputedStyle(el);
            return s.display !== 'none' && s.visibility !== 'hidden';
        }
        // 收集所有可见 a[href] 与含文本的菜单项
        var out = { current_url: location.href, title: document.title, links: [], menu_text: [], headings: [] };
        var anchors = document.querySelectorAll('a[href]');
        for (var a of anchors) {
            if (!visible(a)) continue;
            var t = (a.textContent || '').trim();
            if (!t || t.length > 80) continue;
            out.links.push({text: t, href: a.getAttribute('href')});
        }
        // 侧边栏 / 导航相关
        var navSel = '[class*="sider" i], [class*="sidebar" i], [class*="menu" i], [class*="nav" i], aside';
        var navs = document.querySelectorAll(navSel);
        var seen = new Set();
        for (var n of navs) {
            if (!visible(n)) continue;
            var lines = (n.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
            for (var ln of lines) {
                if (ln.length > 80) continue;
                if (seen.has(ln)) continue;
                seen.add(ln);
                out.menu_text.push(ln);
            }
        }
        // 标题
        document.querySelectorAll('h1,h2,h3').forEach(h => {
            if (visible(h)) {
                var t = (h.textContent || '').trim();
                if (t && t.length < 80) out.headings.push(t);
            }
        });
        return JSON.stringify(out);
        """
        snapshot = json.loads(driver.execute_script(js))
        with open(os.path.join(OUT_DIR, 'snapshot_root.json'), 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        logging.info(f"根页面链接数: {len(snapshot['links'])}, 菜单条目: {len(snapshot['menu_text'])}")

        # 遍历每个站内链接，访问后再 dump 一次（限制数量避免太慢）
        from urllib.parse import urlparse
        base = urlparse(driver.current_url)
        base_host = base.netloc
        visited = set()
        sub_pages = []
        candidates = []
        for lk in snapshot['links']:
            href = lk['href']
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            if href.startswith('http'):
                if urlparse(href).netloc != base_host:
                    continue
            candidates.append(lk)

        for lk in candidates[:25]:
            href = lk['href']
            try:
                if href.startswith('http'):
                    target = href
                else:
                    target = f"{base.scheme}://{base.netloc}{href if href.startswith('/') else '/' + href}"
                if target in visited:
                    continue
                visited.add(target)
                logging.info(f"探查: {lk['text']} -> {target}")
                driver.get(target)
                time.sleep(2.5)
                snap = json.loads(driver.execute_script(js))
                snap['source_link_text'] = lk['text']
                sub_pages.append(snap)
                safe = lk['text'].replace('/', '_').replace('\\', '_')[:30]
                driver.save_screenshot(os.path.join(OUT_DIR, f"page_{len(sub_pages):02d}_{safe}.png"))
            except Exception as e:
                logging.warning(f"探查 {href} 失败: {e}")

        with open(os.path.join(OUT_DIR, 'sub_pages.json'), 'w', encoding='utf-8') as f:
            json.dump(sub_pages, f, ensure_ascii=False, indent=2)
        logging.info(f"已探查子页面: {len(sub_pages)}")
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
