import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import time
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
            time.sleep(1.5)

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

            # 断言登录成功
            self.find_one(Login.LOGIN_SUCCESS_LOCATORS, timeout=8)
            logging.info('登录成功，页面加载完成')
            time.sleep(3)
            return True

        except Exception as e:
            logging.error(f'登录失败，错误信息: {e}')
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
