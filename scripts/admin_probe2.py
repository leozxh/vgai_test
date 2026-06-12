"""第二轮中台探查：登录后依次点击 8 个一级菜单，dump 每个的二级菜单和页面内容。"""
import os
import sys
import time
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 移除旧 chromedriver
def _strip():
    path_var = os.environ.get("PATH", "")
    sep = os.pathsep
    os.environ["PATH"] = sep.join(p for p in path_var.split(sep) if "webdriver\\bin" not in p.replace("/", "\\").lower())
_strip()
os.environ["NO_PROXY"] = os.environ.get("NO_PROXY", "") + ",localhost,127.0.0.1"

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

URL = sys.argv[1]
EMAIL = sys.argv[2]
PASSWORD = sys.argv[3]
TOP_MENUS = ['数据概览', '用户', '商业', '增长', '通信平台', 'AI', '客服', '产品']

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


JS_DUMP = r"""
function visible(el) {
    var r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return false;
    var s = window.getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden';
}
var out = { url: location.href, all_text: [], buttons: [], headings: [], tables: 0, forms: 0 };
var seen = new Set();
// 收集所有可见短文本
document.querySelectorAll('a, button, [role="menuitem"], [role="tab"], li, .ant-menu-item, .ant-menu-submenu, .ant-tabs-tab, [class*="menu-item"], [class*="tab"], [class*="nav-item"]').forEach(el => {
    if (!visible(el)) return;
    var t = (el.innerText || el.textContent || '').trim().split('\n')[0].trim();
    if (!t || t.length > 40 || seen.has(t)) return;
    seen.add(t);
    out.all_text.push(t);
});
out.tables = document.querySelectorAll('table, [role="table"], [class*="table"]').length;
out.forms = document.querySelectorAll('form, [class*="form"]').length;
document.querySelectorAll('h1,h2,h3,h4').forEach(h => {
    if (visible(h)) {
        var t = (h.textContent || '').trim();
        if (t && t.length < 60) out.headings.push(t);
    }
});
return JSON.stringify(out);
"""


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
        driver.get(URL)
        time.sleep(3)
        # 登录
        inputs = driver.find_elements(By.CSS_SELECTOR, 'input')
        email_input = pwd_input = None
        for inp in inputs:
            t = (inp.get_attribute('type') or '').lower()
            if t == 'password':
                pwd_input = inp
            elif t in ('email', 'text') and email_input is None:
                email_input = inp
        if email_input and pwd_input:
            email_input.send_keys(EMAIL)
            pwd_input.send_keys(PASSWORD)
            for b in driver.find_elements(By.CSS_SELECTOR, 'button'):
                if any(k in (b.text or '').strip().lower() for k in ['log in', 'login', 'sign in', '登录']):
                    b.click(); break
            time.sleep(6)
        logging.info(f'登录后 URL: {driver.current_url}')

        # 切换到 Visiva 产品（左上角"全部产品"下拉）
        try:
            switcher = driver.find_elements(By.XPATH, "//*[contains(normalize-space(text()), '全部产品')]")
            for sw in switcher:
                if sw.is_displayed():
                    try:
                        sw.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", sw)
                    break
            time.sleep(1.5)
            driver.save_screenshot(os.path.join(OUT_DIR, '03_product_dropdown.png'))
            # 选 visiva（大小写不敏感）
            picked = False
            for cand in driver.find_elements(By.XPATH, "//*[translate(normalize-space(text()), 'VISIA', 'visia')='visiva']"):
                if cand.is_displayed():
                    try:
                        cand.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", cand)
                    picked = True
                    logging.info('已选 Visiva')
                    break
            if not picked:
                # 退路：找包含 visiva 文本的可见元素
                for cand in driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'VISIA', 'visia'), 'visiva')]"):
                    if cand.is_displayed() and len(cand.text.strip()) < 30:
                        try:
                            cand.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", cand)
                        picked = True
                        logging.info(f'已选: {cand.text.strip()}')
                        break
            time.sleep(2.5)
            driver.save_screenshot(os.path.join(OUT_DIR, '04_after_visiva.png'))
        except Exception as e:
            logging.warning(f'切换到 Visiva 失败: {e}')

        results = {}
        for menu in TOP_MENUS:
            logging.info(f'\n=== 点击一级菜单: {menu} ===')
            # 用 XPath 找菜单文本元素并向上找可点击祖先后点击
            try:
                els = driver.find_elements(By.XPATH, f"//*[normalize-space(text())='{menu}']")
            except Exception:
                els = []
            clicked = False
            for el in els:
                try:
                    if not el.is_displayed():
                        continue
                    rect = el.rect
                    if rect['y'] > 200:  # 只看顶栏
                        continue
                    # 找最近的 button/a/li 祖先
                    target = driver.execute_script(
                        "var n = arguments[0]; while (n && !['BUTTON','A','LI'].includes(n.tagName) && !((n.className||'').match(/menu-item|tab/i))) { n = n.parentElement; if (!n || n === document.body) break; } return n || arguments[0];",
                        el
                    )
                    try:
                        target.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", target)
                    clicked = True
                    break
                except Exception:
                    continue
            if not clicked:
                logging.warning(f'未点到 {menu}')
                continue
            time.sleep(3)
            try:
                snap = json.loads(driver.execute_script(JS_DUMP))
            except Exception as e:
                snap = {'error': str(e)}
            results[menu] = snap
            safe = menu.replace('/', '_')
            driver.save_screenshot(os.path.join(OUT_DIR, f'menu_{safe}.png'))

            # 尝试探查二级菜单：在当前页找侧边栏/标签，依次点击前 5 个新出现的标签
            try:
                tabs_js = r"""
                function visible(el) {
                    var r = el.getBoundingClientRect();
                    return r.width > 0 && r.height > 0;
                }
                var seen = new Set();
                var out = [];
                document.querySelectorAll('[role="tab"], .ant-tabs-tab, [class*="tab-item"], [class*="sider"] [class*="menu-item"], aside [class*="item"]').forEach(el => {
                    if (!visible(el)) return;
                    var t = (el.innerText || '').trim().split('\n')[0].trim();
                    if (!t || t.length > 30 || seen.has(t)) return;
                    seen.add(t);
                    out.push(t);
                });
                return JSON.stringify(out);
                """
                tabs = json.loads(driver.execute_script(tabs_js))
                results[menu]['tabs_or_subnav'] = tabs
                logging.info(f'{menu} 子项: {tabs}')
            except Exception as e:
                logging.warning(f'子项探查失败: {e}')

        with open(os.path.join(OUT_DIR, 'menus.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logging.info(f'已保存 menus.json，覆盖 {len(results)} 个一级菜单')

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
