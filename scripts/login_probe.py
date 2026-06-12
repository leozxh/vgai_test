"""快速诊断登录：截图记录每一步"""
import os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.caps import DriverManager
from selenium.webdriver.common.by import By

USER = sys.argv[1] if len(sys.argv) > 1 else 'yhy20010203@gmail.com'
PWD = sys.argv[2] if len(sys.argv) > 2 else 'vg123546'

dm = DriverManager()
driver = dm.test_caps()
OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots', 'login_probe')
os.makedirs(OUT, exist_ok=True)

try:
    time.sleep(2)
    driver.save_screenshot(os.path.join(OUT, '01_initial.png'))
    print('初始 URL:', driver.current_url)

    # 找 Log In 按钮
    btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'Log In') or contains(text(), 'Login')]")
    print(f'Log In 类按钮数: {len(btns)}')
    for i, b in enumerate(btns[:5]):
        try:
            print(f'  {i}: tag={b.tag_name} text={(b.text or "")[:40]} displayed={b.is_displayed()}')
        except Exception:
            pass

    # 点击第一个可见的
    for b in btns:
        if b.is_displayed():
            try:
                b.click()
            except Exception:
                driver.execute_script("arguments[0].click();", b)
            print('已点击 Log In')
            break
    time.sleep(2.5)
    driver.save_screenshot(os.path.join(OUT, '02_after_click_login.png'))

    # 找所有 input
    inputs = driver.find_elements(By.CSS_SELECTOR, 'input')
    print(f'页面所有 input: {len(inputs)}')
    for i, inp in enumerate(inputs[:10]):
        try:
            print(f'  {i}: type={inp.get_attribute("type")} name={inp.get_attribute("name")} placeholder={inp.get_attribute("placeholder")} displayed={inp.is_displayed()}')
        except Exception:
            pass

    # 看是否有 dialog/modal
    modals = driver.find_elements(By.CSS_SELECTOR, '[role="dialog"], [class*="modal" i], [class*="dialog" i]')
    print(f'modal/dialog 数: {len(modals)}')
    for m in modals[:3]:
        print(f'  visible={m.is_displayed()} class={(m.get_attribute("class") or "")[:80]}')

    # 尝试输入并提交
    email_input = None
    pwd_input = None
    for inp in inputs:
        t = (inp.get_attribute('type') or '').lower()
        if t == 'password':
            pwd_input = inp
        elif t in ('email', 'text'):
            if email_input is None and inp.is_displayed():
                email_input = inp
    if email_input and pwd_input:
        email_input.send_keys(USER)
        pwd_input.send_keys(PWD)
        time.sleep(0.5)
        driver.save_screenshot(os.path.join(OUT, '03_filled.png'))
        # 提交
        sub_btns = driver.find_elements(By.CSS_SELECTOR, 'button[type="submit"], button')
        for b in sub_btns:
            txt = (b.text or '').strip().lower()
            if txt in ('log in', 'login', 'sign in', 'submit', '登录'):
                try:
                    b.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", b)
                print(f'已点击提交按钮: {txt}')
                break
        time.sleep(5)
        driver.save_screenshot(os.path.join(OUT, '04_after_submit.png'))
        print('提交后 URL:', driver.current_url)
        body = driver.find_element(By.TAG_NAME, 'body').text
        print('页面 body 前 300 字符:', body[:300].replace('\n', ' | '))
        # 错误提示
        err_kws = ['incorrect', 'invalid', 'wrong', 'not found', '不正确', 'error', 'failed', 'does not exist']
        for k in err_kws:
            if k.lower() in body.lower():
                print(f'  发现错误关键词: {k}')
    else:
        print(f'未找到登录表单 email={email_input} pwd={pwd_input}')
finally:
    driver.quit()
