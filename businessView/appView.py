import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import time
from common.caps import DriverManager
from common.elementlibrary import AppPage


class AppView(AppPage):
    """App 主页面业务逻辑"""

    def __init__(self, driver):
        super().__init__(driver)

    def go_to_app(self):
        """访问 App 主页面"""
        try:
            logging.info('访问 /app 页面...')
            self.driver.get(self.driver.current_url.split('/app')[0] + '/app')
            time.sleep(5)
            return True
        except Exception as e:
            logging.error(f'访问 App 页面失败: {str(e)}')
            return False

    def is_main_heading_visible(self):
        try:
            self.find_one_fast(AppPage.MAIN_HEADING_LOCATORS, timeout=5)
            return True
        except Exception:
            return False

    def is_hot_templates_visible(self):
        try:
            self.find_one_fast(AppPage.HOT_TEMPLATES_LOCATORS, timeout=5)
            return True
        except Exception:
            return False

    def is_upgrade_visible(self):
        try:
            self.find_one_fast(AppPage.UPGRADE_LOCATORS, timeout=5)
            return True
        except Exception:
            return False

    def is_terms_visible(self):
        try:
            self.find_one_fast(AppPage.TERMS_LOCATORS, timeout=5)
            return True
        except Exception:
            return False

    def are_features_visible(self):
        try:
            self.find_one_fast(AppPage.IMAGE_TO_VIDEO_LOCATORS, timeout=10)
            self.find_one_fast(AppPage.TEXT_TO_VIDEO_LOCATORS, timeout=10)
            self.find_one_fast(AppPage.VIDEO_EXTEND_LOCATORS, timeout=10)
            self.find_one_fast(AppPage.AI_EFFECTS_LOCATORS, timeout=10)
            return True
        except Exception:
            return False

    def safe_click_element(self, element, element_name):
        """安全点击元素，处理被遮挡的情况"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            try:
                element.click()
                logging.info(f'成功点击{element_name}')
                return True
            except Exception:
                logging.info(f'{element_name}普通点击失败，尝试JavaScript点击')
                self.driver.execute_script("arguments[0].click();", element)
                logging.info(f'成功使用JavaScript点击{element_name}')
                return True
        except Exception as e:
            logging.error(f'{element_name}点击失败: {str(e)}')
            return False

    def click_feature(self, locators, feature_name, expected_keywords):
        """通用的功能点击和验证"""
        try:
            logging.info(f'开始点击 {feature_name}...')
            element = self.find_one_fast(locators, timeout=15)
            self.safe_click_element(element, feature_name)
            time.sleep(2)
            current_url = self.driver.current_url.lower()
            logging.info(f'当前页面URL: {current_url}')
            for kw in expected_keywords:
                if kw.lower() in current_url:
                    logging.info(f'{feature_name} 页面跳转验证成功')
                    return True
            logging.warning(f'{feature_name} 页面跳转验证失败')
            return False
        except Exception as e:
            logging.error(f'{feature_name} 操作失败: {str(e)}')
            return False

    def nav_image_to_video(self):
        return self.click_feature(AppPage.IMAGE_TO_VIDEO_LOCATORS, 'Image to Video', ['image-to-video'])

    def nav_text_to_video(self):
        return self.click_feature(AppPage.TEXT_TO_VIDEO_LOCATORS, 'Text to Video', ['text-to-video'])

    def nav_video_extend(self):
        return self.click_feature(AppPage.VIDEO_EXTEND_LOCATORS, 'Video Extend', ['video-extend'])

    def nav_ai_effects(self):
        return self.click_feature(AppPage.AI_EFFECTS_LOCATORS, 'AI Effects', ['video-effects', 'ai-effects'])

    def nav_terms(self):
        return self.click_feature(AppPage.TERMS_LOCATORS, 'Terms', ['terms'])


if __name__ == '__main__':
    driver_manager = DriverManager()
    driver = driver_manager.prod_caps()
    try:
        app_view = AppView(driver)
        logging.info('App 页面功能测试')
        app_view.go_to_app()
    finally:
        driver.quit()
