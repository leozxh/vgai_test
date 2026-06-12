"""产品站导航与身份相关业务逻辑：登录/注册、产品首页、Header、侧边栏、UserMenu

每个方法返回 (pass: bool, detail: str)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import logging
from urllib.parse import urlsplit
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from common.common_fun import Common
from common.elementlibrary import Login


class ProductNavView(Common):
    def __init__(self, driver, base_url='https://visiva.top'):
        super().__init__(driver)
        self.base = base_url.rstrip('/')

    def goto(self, path='/app'):
        self.driver.get(self.base + path)
        time.sleep(2.5)
        return self.driver.current_url

    def logout(self):
        """退出登录（清 cookies + localStorage + sessionStorage + 刷新）"""
        try:
            # 先访问域名再清 storage（必须有域上下文）
            self.driver.get(self.base + '/')
            time.sleep(1)
            self.driver.delete_all_cookies()
            try:
                self.driver.execute_script(
                    "try{window.localStorage.clear();window.sessionStorage.clear();}catch(e){}")
            except Exception:
                pass
            self.goto('/app')
        except Exception:
            pass

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

    def find_text(self, text, partial=True):
        try:
            xp = (f"//*[contains(normalize-space(text()), '{text}')]"
                  if partial else f"//*[normalize-space(text())='{text}']")
            return any(e.is_displayed() for e in self.driver.find_elements(By.XPATH, xp))
        except Exception:
            return False

    def open_login_modal(self):
        self.logout()
        ok = self.click_text('Log In') or self.click_text('Login') or self.click_text('Sign In')
        time.sleep(1.5)
        return ok

    # ---- P-6-* 登录/注册 ----

    def check_unlogin_app(self):
        """P-6-1 未登录访问 /app 应展示未登录状态"""
        self.logout()
        # 应该看到 Log In 按钮，看不到 My Creations 这种登录后入口
        login_visible = self.find_text('Log In')
        creations_visible = self.find_text('My Creations')
        ok = login_visible and not creations_visible
        return ok, f'Log In可见={login_visible} My Creations可见={creations_visible}'

    def check_login_modal_default(self):
        """P-6-2 点 Log In 显示登录表单"""
        ok_open = self.open_login_modal()
        # 应该看到 email/password 输入框，且不是注册形态
        try:
            email = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"], input[name="email"]')
            pwd = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
            has_form = any(e.is_displayed() for e in email) and any(e.is_displayed() for e in pwd)
            return ok_open and has_form, f'打开={ok_open} email框={len(email)} pwd框={len(pwd)}'
        except Exception as e:
            return False, str(e)[:80]

    def check_email_login(self, username, password):
        """P-6-3 邮箱登录成功"""
        self.logout()
        try:
            self.click_text('Log In')
            time.sleep(1.5)
            email = self.find_one(Login.EMAIL_LOCATORS, timeout=5)
            email.clear()
            email.send_keys(username)
            pwd = self.find_one(Login.PWD_LOCATORS, timeout=5)
            pwd.clear()
            pwd.send_keys(password)
            btn = self.find_one(Login.BTN_LOCATORS, timeout=3, clickable=True)
            btn.click()
            time.sleep(6)
            # 校验：Log In 消失 + 看到登录后入口
            login_gone = not self.find_text('Log In')
            creations_visible = self.find_text('My Creations') or self.find_text('Upgrade')
            ok = login_gone and creations_visible
            return ok, f'Log In 消失={login_gone} 登录后入口可见={creations_visible}'
        except Exception as e:
            return False, str(e)[:120]

    def check_password_validation(self):
        """P-6-6 密码合规校验：输入不合规密码应有提示"""
        self.logout()
        try:
            self.click_text('Log In')
            time.sleep(1.2)
            # 切换到注册（如果有）
            self.click_text('Sign Up') or self.click_text('Register') or self.click_text('注册')
            time.sleep(1)
            email = self.find_one(Login.EMAIL_LOCATORS, timeout=3)
            email.clear()
            email.send_keys('temp_check@example.com')
            pwd = self.find_one(Login.PWD_LOCATORS, timeout=3)
            pwd.clear()
            pwd.send_keys('123')  # 短数字
            # 触发 blur / 提交
            try:
                btn = self.find_one(Login.BTN_LOCATORS, timeout=2)
                btn.click()
            except Exception:
                pwd.send_keys('\t')
            time.sleep(1)
            # 找错误提示
            body = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            keywords = ['8', 'short', 'invalid', '至少', '密码', 'character', 'weak']
            has_hint = any(k in body for k in keywords)
            return has_hint, f'命中提示关键词: {[k for k in keywords if k in body]}'
        except Exception as e:
            return False, str(e)[:120]

    def check_18plus_disabled(self):
        """P-6-9 取消 18+ 复选框，按钮应禁用"""
        self.logout()
        try:
            self.click_text('Log In')
            time.sleep(1.2)
            # 找 18+ 相关 checkbox
            checks = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
            target = None
            for c in checks:
                try:
                    label_text = ''
                    parent = c.find_element(By.XPATH, './..')
                    label_text = parent.text.lower()
                    if '18' in label_text or 'age' in label_text:
                        target = c
                        break
                except Exception:
                    continue
            if not target:
                return False, '未找到 18+ checkbox'
            # 取消勾选
            if target.is_selected():
                self.driver.execute_script("arguments[0].click();", target)
                time.sleep(0.5)
            # 检查登录按钮是否禁用
            btns = self.driver.find_elements(By.CSS_SELECTOR, 'button')
            disabled_count = 0
            for b in btns:
                txt = (b.text or '').lower()
                if any(k in txt for k in ['log in', 'login', 'sign in', 'google', 'sign up']):
                    if b.get_attribute('disabled') or b.get_attribute('aria-disabled') == 'true':
                        disabled_count += 1
            return disabled_count >= 1, f'禁用按钮数={disabled_count}'
        except Exception as e:
            return False, str(e)[:120]

    def check_terms_links_in_modal(self):
        """P-6-10 登录表单底部 Terms/Privacy 链接"""
        self.logout()
        try:
            self.click_text('Log In')
            time.sleep(1.2)
            anchors = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="terms"], a[href*="privacy"]')
            visible = [a for a in anchors if a.is_displayed()]
            return len(visible) >= 1, f'法律链接数={len(visible)}'
        except Exception as e:
            return False, str(e)[:120]

    # ---- P-7-* 产品首页 /app ----

    def check_app_loaded(self):
        self.goto('/app')
        ok = '/app' in self.driver.current_url
        return ok, f'url={self.driver.current_url}'

    def check_app_features(self):
        """4 个核心入口可见"""
        self.goto('/app')
        seen = [n for n in ['Image to Video', 'Text to Video', 'Video Extend', 'AI Effects'] if self.find_text(n)]
        return len(seen) >= 3, f'入口={seen}'

    def check_hot_templates(self):
        self.goto('/app')
        ok = self.find_text('Hot Templates') or self.find_text('Templates')
        return ok, '检测 Hot Templates' if ok else '未找到 Hot Templates'

    def check_upgrade_visible(self):
        self.goto('/app')
        ok = self.find_text('Upgrade')
        return ok, '检测 Upgrade' if ok else '未找到 Upgrade'

    # ---- P-8-* Header 顶栏 ----

    def check_header_logo_to_marketing(self):
        self.goto('/app')
        time.sleep(1)
        try:
            # logo 通常带 href="/" 或 visiva 域名
            logos = self.driver.find_elements(By.CSS_SELECTOR, 'header a[href="/"], header img, nav a[href="/"]')
            for l in logos:
                if l.is_displayed():
                    try:
                        l.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", l)
                    time.sleep(2)
                    cur = self.driver.current_url
                    ok = (cur.endswith('/') or '/app' not in cur)
                    return ok, f'url={cur}'
            return False, '未找到 logo 元素'
        except Exception as e:
            return False, str(e)[:80]

    def check_header_gift_icon(self):
        """P-8-2 礼物图标打开奖励中心"""
        self.goto('/app')
        time.sleep(1)
        try:
            # 找含 gift / reward 的按钮
            btns = self.driver.find_elements(By.CSS_SELECTOR,
                'button[aria-label*="gift" i], button[aria-label*="reward" i], header button svg, [class*="gift"]')
            target = None
            for b in btns:
                if b.is_displayed() and b.rect['y'] < 100:
                    target = b; break
            if not target:
                return False, '未找到 gift 按钮'
            try:
                target.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", target)
            time.sleep(1.5)
            # 奖励中心标识
            ok = self.find_text('Daily') or self.find_text('Refer') or self.find_text('Rewards')
            return ok, '奖励中心 slideover 出现' if ok else '点击后未见奖励内容'
        except Exception as e:
            return False, str(e)[:80]

    def check_header_credits(self):
        """P-8-5 积分显示"""
        self.goto('/app')
        time.sleep(1.5)
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, 'button')
            for b in btns:
                if not b.is_displayed():
                    continue
                t = (b.text or '').strip()
                if any(k in t for k in ['Lite', 'Pro', 'Premium', 'Free', 'Max']):
                    import re
                    m = re.search(r'(\d{2,})', t)
                    if m:
                        return True, f'积分按钮文本: {t[:60]}'
            return False, '未找到积分显示'
        except Exception as e:
            return False, str(e)[:80]

    def check_header_upgrade_modal(self):
        """P-8-6 Upgrade 按钮弹升级弹窗"""
        self.goto('/app')
        time.sleep(1)
        ok_click = self.click_text('Upgrade')
        time.sleep(2)
        # 升级弹窗包含套餐
        ok = any(self.find_text(t) for t in ['Lite', 'Pro', 'Max'])
        return ok_click and ok, f'点击成功={ok_click} 弹窗套餐可见={ok}'

    def check_header_avatar_menu(self):
        """P-8-8 点击用户头像弹 UserMenu"""
        self.goto('/app')
        time.sleep(1)
        try:
            # 头像通常是 button img / avatar 类
            avatars = self.driver.find_elements(By.CSS_SELECTOR,
                'header [class*="avatar"], header img[alt*="user" i], header button img, [class*="user-menu-trigger"]')
            target = None
            for a in avatars:
                if a.is_displayed() and a.rect['y'] < 100:
                    target = a; break
            if not target:
                return False, '未找到头像'
            try:
                target.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", target)
            time.sleep(1.5)
            ok = self.find_text('Log Out') or self.find_text('Logout') or self.find_text('Profile') or self.find_text('Settings')
            return ok, 'UserMenu 项目可见' if ok else '点击后未见 UserMenu'
        except Exception as e:
            return False, str(e)[:80]

    # ---- P-9-* 侧边栏 ----

    def check_sidebar_nav(self, label, expected_path):
        """通用侧边栏导航点击"""
        self.goto('/app')
        time.sleep(1)
        ok_click = self.click_text(label)
        time.sleep(2.5)
        cur = self.driver.current_url
        ok = expected_path in cur
        return ok, f'点击 {label} → {cur}'

    def check_sidebar_home(self):
        # 先去别的页面再点 Home
        self.goto('/app/image-to-video')
        time.sleep(1.5)
        ok_click = self.click_text('Home')
        time.sleep(2)
        cur = self.driver.current_url
        ok = cur.rstrip('/').endswith('/app')
        return ok, f'url={cur}'

    def check_sidebar_face_swap_hidden(self):
        """P-9-12 Face Swap 入口隐藏"""
        self.goto('/app')
        time.sleep(1.5)
        hidden = not self.find_text('Face Swap')
        return hidden, 'Face Swap 入口未显示' if hidden else 'Face Swap 入口仍可见'

    # ---- P-10-* UserMenu ----

    def open_user_menu(self):
        self.goto('/app')
        time.sleep(1)
        try:
            avatars = self.driver.find_elements(By.CSS_SELECTOR,
                'header [class*="avatar"], header img[alt*="user" i], header button img')
            for a in avatars:
                if a.is_displayed() and a.rect['y'] < 100:
                    try:
                        a.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", a)
                    time.sleep(1)
                    return True
        except Exception:
            pass
        return False

    def check_usermenu_logout(self):
        """退出登录"""
        opened = self.open_user_menu()
        ok_click = self.click_text('Log Out') or self.click_text('Logout') or self.click_text('Sign Out')
        time.sleep(3)
        login_visible = self.find_text('Log In')
        return opened and ok_click and login_visible, f'打开菜单={opened} 点退出={ok_click} Log In 出现={login_visible}'

    def check_usermenu_profile(self):
        opened = self.open_user_menu()
        ok_click = self.click_text('Profile') or self.click_text('Settings')
        time.sleep(2)
        cur = self.driver.current_url
        ok = '/profile' in cur or '/settings' in cur or '/account' in cur
        return opened and ok_click and ok, f'打开={opened} 点击={ok_click} url={cur}'
