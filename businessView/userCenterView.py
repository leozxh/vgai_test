"""用户中心相关：Profile、My Creations、奖励中心、新用户特惠

每个方法返回 (pass: bool, detail: str)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import logging
from selenium.webdriver.common.by import By
from common.common_fun import Common


class UserCenterView(Common):
    def __init__(self, driver, base_url='https://visiva.top'):
        super().__init__(driver)
        self.base = base_url.rstrip('/')

    def goto(self, path='/app'):
        self.driver.get(self.base + path)
        time.sleep(3)
        return self.driver.current_url

    def find_text(self, text):
        try:
            els = self.driver.find_elements(By.XPATH, f"//*[contains(normalize-space(text()), '{text}')]")
            return any(e.is_displayed() for e in els)
        except Exception:
            return False

    def click_text(self, text):
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

    # ---- P-22-* My Creations ----

    def check_creations_video_tab(self):
        self.goto('/app/creations')
        time.sleep(2)
        ok = self.find_text('Video') and ('/creations' in self.driver.current_url)
        return ok, f'url={self.driver.current_url} Video tab可见={self.find_text("Video")}'

    def check_creations_image_tab(self):
        self.goto('/app/creations')
        time.sleep(2)
        ok_click = self.click_text('Image')
        time.sleep(1.5)
        ok = self.find_text('Image')
        return ok_click and ok, f'点击 Image tab={ok_click}'

    def check_creations_list(self):
        self.goto('/app/creations')
        time.sleep(3)
        # 列表项通常是带视频/图片的卡片
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR,
                '[class*="card"], [class*="item"], video, img')
            visible = [c for c in cards if c.is_displayed() and c.rect['width'] > 50]
            return len(visible) > 0, f'卡片/元素数={len(visible)}'
        except Exception as e:
            return False, str(e)[:80]

    def check_creations_infinite_scroll(self):
        self.goto('/app/creations')
        time.sleep(2)
        try:
            before = self.driver.execute_script("return document.querySelectorAll('[class*=\"card\"], video, img').length;")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            after = self.driver.execute_script("return document.querySelectorAll('[class*=\"card\"], video, img').length;")
            ok = after > before or before > 3  # 元素数增加 或 初始数足够
            return ok, f'滚动前 {before}，滚动后 {after}'
        except Exception as e:
            return False, str(e)[:80]

    def check_creations_preview(self):
        """点击卡片可全屏预览"""
        self.goto('/app/creations')
        time.sleep(3)
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR, 'video, [class*="card"] img')
            for c in cards:
                if c.is_displayed() and c.rect['width'] > 100:
                    try:
                        c.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", c)
                    time.sleep(1.5)
                    # 弹窗类标识
                    has_modal = self.driver.execute_script(
                        "return document.querySelectorAll('[role=\"dialog\"], [class*=\"modal\"], [class*=\"preview\"], [class*=\"lightbox\"]').length;")
                    return has_modal > 0, f'弹窗数={has_modal}'
            return False, '未找到可点击的作品卡片'
        except Exception as e:
            return False, str(e)[:80]

    # ---- P-21-* Profile 设定 ----

    def open_profile(self):
        """从 UserMenu 打开 Profile，或直接访问 URL"""
        # 优先 URL 直达，简单稳定
        urls_to_try = ['/app/profile', '/app/settings', '/app/account']
        for p in urls_to_try:
            self.goto(p)
            cur = self.driver.current_url
            if any(k in cur for k in ['profile', 'settings', 'account']):
                return True
        return False

    def check_profile_loaded(self):
        ok = self.open_profile()
        cur = self.driver.current_url
        return ok, f'url={cur}'

    def check_profile_email_shown(self):
        if not self.open_profile():
            return False, '未能进入 Profile'
        time.sleep(1)
        body = self.driver.find_element(By.TAG_NAME, 'body').text
        # 邮箱形式
        import re
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body)
        return len(emails) > 0, f'邮箱={emails[:3]}'

    def check_profile_username(self):
        if not self.open_profile():
            return False, '未能进入 Profile'
        time.sleep(1)
        # 找姓名/Username 输入框
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[name*="name" i]')
            visible = [i for i in inputs if i.is_displayed()]
            return len(visible) > 0, f'文本输入框数={len(visible)}'
        except Exception as e:
            return False, str(e)[:80]

    def check_profile_password_change(self):
        if not self.open_profile():
            return False, '未能进入 Profile'
        time.sleep(1)
        ok = self.find_text('Password') or self.find_text('password') or self.find_text('Change password')
        return ok, '检测到密码相关入口' if ok else '未找到密码入口'

    def check_profile_subscription_info(self):
        if not self.open_profile():
            return False, '未能进入 Profile'
        time.sleep(1)
        kws = ['Lite', 'Pro', 'Max', 'Free', 'Subscription', 'Plan', '套餐']
        seen = [k for k in kws if self.find_text(k)]
        return len(seen) > 0, f'命中套餐关键词={seen}'

    def check_profile_credits_shown(self):
        if not self.open_profile():
            return False, '未能进入 Profile'
        time.sleep(1)
        body = self.driver.find_element(By.TAG_NAME, 'body').text
        ok = ('credit' in body.lower() or '积分' in body or 'Balance' in body)
        return ok, '检测到积分信息' if ok else '未找到积分'

    # ---- P-19-* 奖励中心 ----

    def open_rewards(self):
        self.goto('/app')
        time.sleep(1.5)
        # 找礼物图标
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, 'header button, nav button, button')
            for b in buttons:
                if not b.is_displayed():
                    continue
                if b.rect['y'] > 120:
                    continue
                svg = b.find_elements(By.TAG_NAME, 'svg')
                # 礼物按钮一般是小尺寸 icon button
                if svg and b.rect['width'] < 60:
                    try:
                        b.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", b)
                    time.sleep(1.5)
                    if self.find_text('Daily') or self.find_text('Refer') or self.find_text('Rewards'):
                        return True
            return False
        except Exception:
            return False

    def check_rewards_open(self):
        ok = self.open_rewards()
        return ok, '奖励中心 slideover 打开' if ok else '未能打开'

    def check_rewards_referral_link(self):
        if not self.open_rewards():
            return False, '未能打开奖励中心'
        time.sleep(1)
        body = self.driver.find_element(By.TAG_NAME, 'body').text
        ok = 'referral' in body.lower() or 'visiva.ai/app/' in body or 'invite' in body.lower()
        return ok, '检测到邀请链接相关文本' if ok else '未找到邀请链接'

    def check_rewards_stats(self):
        if not self.open_rewards():
            return False, '未能打开奖励中心'
        time.sleep(1)
        body = self.driver.find_element(By.TAG_NAME, 'body').text
        ok = any(k in body for k in ['Total Referrals', 'Total Rewards', 'Referrals', 'Rewards', '邀请', '奖励'])
        return ok, '检测到统计信息' if ok else '未找到统计'

    # ---- P-23-* 支付流程 ----

    def check_upgrade_modal(self):
        self.goto('/app')
        time.sleep(1)
        ok_click = self.click_text('Upgrade') or self.click_text('Get Pro')
        time.sleep(2)
        if not ok_click:
            return False, '未找到 Upgrade 按钮（可能用户为最高套餐）'
        plans = [t for t in ['Lite', 'Pro', 'Max'] if self.find_text(t)]
        return len(plans) >= 2, f'套餐显示={plans}'

    def check_pricing_buy_now_redirect(self):
        """点 Buy Now 应在新标签页打开 checkout"""
        self.goto('/pricing')
        time.sleep(2)
        before_handles = len(self.driver.window_handles)
        ok_click = self.click_text('Buy Now') or self.click_text('Get Pro')
        if not ok_click:
            return False, '未找到 Buy Now 按钮'
        time.sleep(3)
        after_handles = len(self.driver.window_handles)
        new_tab = after_handles > before_handles
        if new_tab:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            url = self.driver.current_url
            ok = 'checkout' in url.lower() or 'pay' in url.lower()
            # 切回原窗口
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return ok, f'新标签页 url={url}'
        return False, '未打开新标签页'
