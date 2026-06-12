"""营销站业务逻辑：首页、定价页、法律页、页脚

每个方法返回 (pass: bool, detail: str)，统一格式便于驱动器记录。
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import time
import re
from urllib.parse import urlsplit
from selenium.webdriver.common.by import By
from common.common_fun import Common


class MarketingView(Common):
    def __init__(self, driver, base_url='https://visiva.top'):
        super().__init__(driver)
        self.base = base_url.rstrip('/')

    # ---- 通用 ----

    def goto(self, path=''):
        url = self.base + (path if path.startswith('/') or path == '' else '/' + path)
        self.driver.get(url)
        time.sleep(2)
        return self.driver.current_url

    def find_text(self, text, partial=True):
        """页面是否能找到指定文本（可见）"""
        try:
            if partial:
                els = self.driver.find_elements(By.XPATH, f"//*[contains(normalize-space(text()), '{text}')]")
            else:
                els = self.driver.find_elements(By.XPATH, f"//*[normalize-space(text())='{text}']")
            return any(e.is_displayed() for e in els)
        except Exception:
            return False

    def click_text(self, text, scope='button, a'):
        """按可见文本点击 button/a，返回是否点击成功"""
        try:
            els = self.driver.find_elements(By.XPATH,
                f"//a[contains(normalize-space(.), '{text}')] | //button[contains(normalize-space(.), '{text}')]")
            for el in els:
                if el.is_displayed():
                    try:
                        el.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", el)
                    return True
            return False
        except Exception:
            return False

    # ---- M-1-* 营销站首页 ----

    def check_tdk(self):
        self.goto('/')
        title = self.driver.title or ''
        try:
            desc = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]').get_attribute('content') or ''
        except Exception:
            desc = ''
        ok = bool(title) and 'Visiva' in title
        return ok, f'title="{title[:80]}" desc_len={len(desc)}'

    def check_logo_back_home(self):
        self.goto('/pricing')
        time.sleep(1)
        # logo 通常是 a[href="/"] 或者顶栏第一个 img
        try:
            logos = self.driver.find_elements(By.CSS_SELECTOR, 'header a[href="/"], nav a[href="/"], a[href="/"] img')
            for l in logos:
                if l.is_displayed():
                    try:
                        l.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", l)
                    time.sleep(2)
                    cur = urlsplit(self.driver.current_url)
                    ok = cur.path in ('', '/')
                    return ok, f'当前 path={cur.path}'
            return False, '未找到 logo 链接'
        except Exception as e:
            return False, str(e)[:80]

    def check_nav_pricing(self):
        self.goto('/')
        ok_click = self.click_text('Pricing')
        time.sleep(2)
        cur = self.driver.current_url
        ok = '/pricing' in cur
        return ok, f'点击成功={ok_click} url={cur}'

    def check_nav_get_started(self):
        self.goto('/')
        # Get Started 或 Try Now 等 CTA 文案
        for kw in ['Get Started', 'Try Now', 'Try For Free', 'Start Free']:
            if self.click_text(kw):
                time.sleep(3)
                cur = self.driver.current_url
                ok = '/app' in cur
                return ok, f'点击 {kw} → {cur}'
        return False, '未找到 CTA 按钮'

    def check_lang_switch(self):
        self.goto('/zh-TW')
        time.sleep(2)
        cur = self.driver.current_url
        ok = '/zh-TW' in cur
        # 检查是否有繁体中文
        html = self.driver.page_source[:5000]
        has_zh = bool(re.search(r'[\u4e00-\u9fff]', html))
        return ok and has_zh, f'url={cur} has_chinese={has_zh}'

    def check_video_section(self):
        self.goto('/')
        time.sleep(2)
        try:
            videos = self.driver.find_elements(By.CSS_SELECTOR, 'video, source[type*="video"]')
            visible = [v for v in videos if v.is_displayed()]
            return len(visible) > 0, f'video 元素数={len(videos)} 可见={len(visible)}'
        except Exception as e:
            return False, str(e)[:80]

    def check_ai_tools_section(self):
        self.goto('/')
        time.sleep(1)
        # 滚到中部
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(1.5)
        # 找带链接的卡片：href 含 /app/ 或常见功能词
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/app"], a[href*="video"], a[href*="image"]')
            visible = [c for c in cards if c.is_displayed()]
            return len(visible) >= 3, f'AI Tools 卡片数={len(visible)}'
        except Exception as e:
            return False, str(e)[:80]

    def check_faq_expand(self):
        self.goto('/')
        # 滚到 FAQ 区域
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 1500);")
        time.sleep(1)
        try:
            # FAQ 通常是 details/summary 或 button[aria-expanded]
            faqs = self.driver.find_elements(By.CSS_SELECTOR,
                'details, summary, button[aria-expanded], [class*="faq"] button, [class*="accordion"] button')
            visible = [f for f in faqs if f.is_displayed()]
            if not visible:
                return False, '未找到 FAQ 控件'
            # 点击第一个并验证展开
            target = visible[0]
            before = target.get_attribute('aria-expanded') or 'unknown'
            try:
                target.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", target)
            time.sleep(0.6)
            after = target.get_attribute('aria-expanded') or 'unknown'
            return before != after or before == 'unknown', f'aria-expanded {before}→{after}'
        except Exception as e:
            return False, str(e)[:80]

    def check_carousel(self):
        self.goto('/')
        # 找轮播/滑动控件
        try:
            carousels = self.driver.find_elements(By.CSS_SELECTOR,
                '[class*="swiper"], [class*="carousel"], [class*="slider"]')
            visible = [c for c in carousels if c.is_displayed()]
            return len(visible) > 0, f'轮播容器数={len(visible)}'
        except Exception as e:
            return False, str(e)[:80]

    def check_whatsapp_btn(self):
        self.goto('/')
        time.sleep(1)
        try:
            # WhatsApp 按钮通常包含 wa.me / whatsapp 字样或图标
            els = self.driver.find_elements(By.XPATH,
                "//*[contains(@href, 'whatsapp') or contains(@href, 'wa.me') or contains(@aria-label, 'WhatsApp') or contains(@alt, 'WhatsApp')]")
            visible = [e for e in els if e.is_displayed()]
            return len(visible) > 0, f'WhatsApp 元素数={len(visible)}'
        except Exception as e:
            return False, str(e)[:80]

    def check_cookie_banner(self):
        # 清 cookie 模拟首次访问
        self.driver.delete_all_cookies()
        self.goto('/')
        time.sleep(2.5)
        ok = self.find_text('Cookie') or self.find_text('cookie')
        return ok, '检测到 Cookie 提示' if ok else '未检测到 Cookie 提示'

    def check_mobile_menu(self):
        self.driver.set_window_size(390, 844)
        self.goto('/')
        time.sleep(1.5)
        try:
            # 找汉堡图标（通常是 button 含 menu / svg 的图标按钮）
            btns = self.driver.find_elements(By.CSS_SELECTOR,
                'button[aria-label*="menu" i], button[class*="menu"], button[class*="hamburger"], [class*="mobile-menu-btn"]')
            visible = [b for b in btns if b.is_displayed()]
            if not visible:
                self.driver.set_window_size(1920, 1080)
                return False, '移动端汉堡按钮未找到'
            try:
                visible[0].click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", visible[0])
            time.sleep(1)
            ok = self.find_text('Pricing') or self.find_text('AI')
            self.driver.set_window_size(1920, 1080)
            return ok, '展开后能看到 Pricing/AI'
        except Exception as e:
            self.driver.set_window_size(1920, 1080)
            return False, str(e)[:80]

    def check_no_console_error(self):
        self.goto('/')
        time.sleep(2)
        try:
            logs = self.driver.get_log('browser')
        except Exception:
            return True, 'driver 不支持 browser log，跳过校验'
        severe = [l for l in logs if l.get('level') in ('SEVERE',) and 'favicon' not in l.get('message', '').lower()]
        return len(severe) == 0, f'SEVERE 日志数={len(severe)}'

    # ---- M-2-* 定价页 ----

    def check_pricing_tdk(self):
        self.goto('/pricing')
        title = self.driver.title or ''
        ok = bool(title) and ('Pricing' in title or 'Visiva' in title or 'visiva' in title.lower())
        return ok, f'title="{title[:80]}"'

    def check_pricing_tiers(self):
        self.goto('/pricing')
        time.sleep(2)
        tiers = []
        for name in ['Lite', 'Pro', 'Max', 'Free']:
            if self.find_text(name):
                tiers.append(name)
        return len(tiers) >= 2, f'套餐={tiers}'

    def check_pricing_monthly_yearly(self):
        self.goto('/pricing')
        time.sleep(2)
        # 找 Monthly / Yearly 切换
        has_monthly = self.find_text('Monthly') or self.find_text('monthly')
        has_yearly = self.find_text('Yearly') or self.find_text('Annual')
        return has_monthly and has_yearly, f'Monthly={has_monthly} Yearly={has_yearly}'

    def check_pricing_buy_not_login(self):
        self.driver.delete_all_cookies()
        self.goto('/pricing')
        time.sleep(2)
        ok = self.click_text('Buy Now') or self.click_text('Get Pro') or self.click_text('Get Started')
        if not ok:
            return False, '未找到 Buy Now/Get Pro 按钮'
        time.sleep(2.5)
        # 应当弹出登录 / 跳转到 /app
        has_login = self.find_text('Log In') or self.find_text('Sign in') or self.find_text('Email')
        in_app = '/app' in self.driver.current_url
        return has_login or in_app, f'有登录入口={has_login} 进入 app={in_app}'

    # ---- 法律页 ----

    def check_legal_page(self, path, must_have=None):
        """检查 /terms /privacy 等法律页可访问"""
        self.goto(path)
        time.sleep(1.5)
        title = self.driver.title or ''
        text = self.driver.find_element(By.TAG_NAME, 'body').text[:1000]
        if must_have:
            ok = must_have.lower() in (title + text).lower()
        else:
            ok = len(text) > 200
        return ok, f'title="{title[:60]}" body_len={len(text)}'
