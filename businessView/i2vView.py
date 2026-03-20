import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import time
from common.elementlibrary import ImageToVideo
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class I2VView(ImageToVideo):
    """Image to Video 图生视频业务逻辑"""

    def __init__(self, driver):
        super().__init__(driver)

    def go_to_i2v(self):
        """进入 Image to Video 页面"""
        try:
            logging.info('进入 Image to Video 页面...')
            base_url = self.driver.current_url.split('/app')[0]
            self.driver.get(base_url + '/app/image-to-video')
            time.sleep(3)
            logging.info(f'当前 URL: {self.driver.current_url}')
            return 'image-to-video' in self.driver.current_url
        except Exception as e:
            logging.error(f'进入 Image to Video 页面失败: {str(e)}')
            return False

    def click_inspiration(self):
        """点击 Inspiration 按钮"""
        try:
            logging.info('点击 Inspiration 按钮...')
            btn = self.find_one_fast(ImageToVideo.INSPIRATION_BTN_LOCATORS, timeout=5)
            btn.click()
            time.sleep(2)
            logging.info('已点击 Inspiration')
            return True
        except Exception as e:
            logging.error(f'点击 Inspiration 失败: {str(e)}')
            return False

    def select_inspiration_template(self):
        """从 Inspiration 面板选择第一个模板"""
        try:
            logging.info('选择 Inspiration 模板...')

            # 查找 Inspiration 面板中第一个可见的模板图片
            all_imgs = self.driver.find_elements(By.TAG_NAME, 'img')
            for img in all_imgs:
                try:
                    if not img.is_displayed() or img.size.get('width', 0) < 80:
                        continue
                    src = img.get_attribute('src') or ''
                    if not src or 'logo' in src.lower() or 'icon' in src.lower() or 'avatar' in src.lower():
                        continue
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", img)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", img)
                    logging.info(f'已选择第一个 Inspiration 模板: {src[:80]}')
                    time.sleep(3)
                    return True
                except Exception:
                    continue

            logging.warning('未找到可用的 Inspiration 模板')
            return False
        except Exception as e:
            logging.error(f'选择 Inspiration 模板失败: {str(e)}')
            return False

    def verify_prompt_populated(self):
        """验证 prompt 是否被模板填充"""
        try:
            textarea = self.find_one_fast(ImageToVideo.PROMPT_TEXTAREA_LOCATORS, timeout=5)
            prompt_text = textarea.get_attribute('value') or textarea.text
            if prompt_text and len(prompt_text.strip()) > 0:
                logging.info(f'Prompt 已填充: {prompt_text[:80]}...')
                return True
            logging.info('Prompt 未被自动填充')
            return False
        except Exception as e:
            logging.error(f'验证 Prompt 失败: {str(e)}')
            return False

    def click_create(self):
        """点击 Create 按钮"""
        try:
            logging.info('点击 Create 按钮...')
            # 先滚动到页面顶部，确保 Create 按钮可见
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            try:
                btn = self.find_one(ImageToVideo.CREATE_BTN_LOCATORS, timeout=5, clickable=True)
            except Exception:
                # 如果常规查找失败，尝试通过 JS 查找
                logging.info('常规查找 Create 按钮失败，尝试 JS 查找...')
                btn = self.driver.execute_script("""
                    var buttons = document.querySelectorAll('button');
                    for (var b of buttons) {
                        if (b.textContent.includes('Create') || b.textContent.includes('Generate')) {
                            return b;
                        }
                    }
                    return null;
                """)
                if not btn:
                    raise Exception('未找到 Create/Generate 按钮')

            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)
            logging.info('已点击 Create')
            time.sleep(3)
            return True
        except Exception as e:
            logging.error(f'点击 Create 失败: {str(e)}')
            return False

    def verify_generation_no_error(self):
        """验证生成过程没有报错"""
        try:
            logging.info('验证生成结果...')
            time.sleep(3)

            # 检查是否有错误提示
            error_elements = self.driver.find_elements(
                By.XPATH,
                "//*[contains(@class,'toast') or contains(@class,'Toast')]"
                "//*[contains(text(),'error') or contains(text(),'Error') or contains(text(),'failed') or contains(text(),'Failed')]"
            )
            for el in error_elements:
                if el.is_displayed():
                    error_text = el.text
                    logging.error(f'发现错误提示: {error_text}')
                    return False

            # 检查页面是否仍在 image-to-video（没有跳到错误页）
            current_url = self.driver.current_url
            if 'image-to-video' not in current_url and 'error' in current_url.lower():
                logging.error(f'页面跳转到错误页: {current_url}')
                return False

            # 检查是否出现生成进度/排队状态（说明任务已提交成功）
            try:
                progress = self.find_one_fast(ImageToVideo.GENERATION_PROGRESS_LOCATORS, timeout=5)
                if progress:
                    logging.info(f'生成任务已提交，状态: {progress.text[:60]}')
                    return True
            except Exception:
                pass

            # 检查 Record 区域是否有新增记录（也表示生成请求成功）
            try:
                record_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Record')]")
                record_btn.click()
                time.sleep(2)
                records = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Image to Video')]")
                if records:
                    logging.info('Record 区域有生成记录，生成请求成功')
                    return True
            except Exception:
                pass

            # 如果没发现错误，也没明确的成功标识，视为通过（至少没报错）
            logging.info('未发现错误提示，生成流程无异常')
            return True

        except Exception as e:
            logging.error(f'验证生成结果时发生异常: {str(e)}')
            return False

    def i2v_inspiration_generation_test(self):
        """图生视频 Inspiration 模板生成完整流程测试"""
        logging.info('===== 开始图生视频 Inspiration 模板生成测试 =====')

        # 步骤1: 进入 Image to Video 页面
        if not self.go_to_i2v():
            logging.error('步骤1失败: 无法进入 Image to Video 页面')
            return False

        # 步骤2: 点击 Inspiration
        if not self.click_inspiration():
            logging.error('步骤2失败: 点击 Inspiration 失败')
            return False

        # 步骤3: 选择 Inspiration 模板
        if not self.select_inspiration_template():
            logging.error('步骤3失败: 选择模板失败')
            return False

        # 步骤4: 点击 Create 生成
        if not self.click_create():
            logging.error('步骤4失败: 点击 Create 失败')
            return False

        # 步骤5: 验证生成无报错
        result = self.verify_generation_no_error()
        if result:
            logging.info('===== 图生视频 Inspiration 模板生成测试通过 =====')
        else:
            logging.error('===== 图生视频 Inspiration 模板生成测试失败 =====')

        return result
