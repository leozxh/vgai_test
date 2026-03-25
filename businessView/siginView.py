import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import time
from selenium.webdriver.support.ui import WebDriverWait
from common.caps import DriverManager
from common.elementlibrary import Login


class SiginView(Login):
    def __init__(self, driver):
        super().__init__(driver)

    def login_action(self, username, password):
        try:
            # 点击 Log In 按钮
            logging.info('开始查找 Log In 按钮...')
            login_btn = self.find_one_fast(Login.LOGIN_LOCATORS, timeout=5)
            login_btn.click()
            logging.info('已点击 Log In 按钮')
            self.find_one(Login.EMAIL_LOCATORS, timeout=8)

            # 输入邮箱
            logging.info('开始查找邮箱输入框...')
            email_el = self.find_one_fast(Login.EMAIL_LOCATORS, timeout=5)
            email_el.send_keys(username)
            logging.info('用户邮箱是:%s' % username)

            # 输入密码
            logging.info('开始查找密码输入框...')
            pwd_el = self.find_one_fast(Login.PWD_LOCATORS, timeout=5)
            pwd_el.send_keys(password)
            logging.info('输入密码成功')

            # 点击登录提交按钮
            btn_el = self.find_one_fast(Login.BTN_LOCATORS, timeout=3, clickable=True)
            btn_el.click()

            # 断言登录成功（避免使用恒存在元素导致假通过）
            if not self._is_login_success():
                logging.error('未检测到明确的登录成功标识')
                return False

            logging.info('登录成功，页面加载完成')
            WebDriverWait(self.driver, 5).until(
                lambda d: ('/app' in d.current_url) or ('visiva.ai' in d.current_url)
            )
            return True

        except Exception as e:
            logging.error(f'登录失败，错误信息: {e}')
            return False

    def _is_login_success(self, timeout=10):
        """判断登录是否成功"""
        # 1) 优先看登录按钮是否消失
        start = time.time()
        while time.time() - start < timeout:
            try:
                self.find_one_fast(Login.LOGIN_LOCATORS, timeout=1)
                # 还能找到 Log In，继续等
                time.sleep(0.5)
            except Exception:
                logging.info('Log In 按钮已消失，判定为登录成功')
                return True

        # 2) 再看成功标识
        try:
            self.find_one(Login.LOGIN_SUCCESS_LOCATORS, timeout=3)
            return True
        except Exception:
            return False


if __name__ == '__main__':
    driver_manager = DriverManager()
    driver = driver_manager.prod_caps()
    try:
        login_view = SiginView(driver)
        logging.info('登录功能验证')
        data = login_view.read_json_data('data/account.json', 'account1')
        login_view.login_action(data['username'], data['password'])
    finally:
        driver.quit()
