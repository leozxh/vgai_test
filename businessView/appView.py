import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import time
from urllib.parse import urlsplit
from selenium.webdriver.support.ui import WebDriverWait
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
            current = self.driver.current_url
            parsed = urlsplit(current)
            origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "https://visiva.ai"
            self.driver.get(origin + '/app')
            WebDriverWait(self.driver, 20).until(
                lambda d: '/app' in (d.current_url or '').lower()
                and d.execute_script('return document.readyState') in ('interactive', 'complete')
            )
            # 首页内容和导航均由异步数据/响应式布局渲染，不能用某一个入口
            # 作为整个 App 的加载标志。URL、品牌标题和 body 可见即可判定 shell 已就绪。
            WebDriverWait(self.driver, 15).until(
                lambda d: 'visiva' in (d.title or '').lower()
                and bool(d.execute_script(
                    "return document.body && document.body.innerText.trim().length > 0"
                ))
            )
            return True
        except Exception as e:
            logging.error(f'访问 App 页面失败: {str(e)}')
            return False

    def is_main_heading_visible(self):
        try:
            # /app 页面是 SPA，无 h1；通过 document.title 确认品牌标题可见
            title = self.driver.title or ''
            if 'visiva' in title.lower():
                return True
            # 兜底：找 DOM 中任何含 Visiva 的可见标题元素
            self.find_one_fast(AppPage.MAIN_HEADING_LOCATORS, timeout=3)
            return True
        except Exception:
            return False

    def is_hot_models_visible(self):
        try:
            self.find_one_fast(AppPage.HOT_SECTION_LOCATORS, timeout=10)
            self.find_one_fast(AppPage.MODELS_SECTION_LOCATORS, timeout=10)
            return True
        except Exception as e:
            logging.error(f'Hot/Models 区域验证失败: {str(e)}')
            return False

    def is_primary_navigation_visible(self):
        try:
            required_navigation = ('home', 'ai_effects', 'create', 'creations')
            for nav_name in required_navigation:
                locators = AppPage.PRIMARY_NAV_LOCATORS[nav_name]
                self.find_one_fast(locators, timeout=8)
                logging.info(f'新版主导航已显示: {nav_name}')

            # Apps/AI Tools 由后端展示面配置控制，可能在无可用工具时隐藏，
            # 因此只记录当前状态，不作为首页健康检查的硬性条件。
            try:
                self.find_one_fast(AppPage.PRIMARY_NAV_LOCATORS['apps'], timeout=3)
                logging.info('可选主导航已显示: apps')
            except Exception:
                logging.info('可选主导航未显示: apps（当前展示面允许隐藏）')
            return True
        except Exception as e:
            logging.error(f'新版主导航验证失败: {str(e)}')
            return False

    def are_company_policies_visible(self):
        try:
            for policy_name, locators in AppPage.COMPANY_POLICY_LOCATORS.items():
                self.find_one_fast(locators, timeout=8)
                logging.info(f'公司政策入口已显示: {policy_name}')
            return True
        except Exception as e:
            logging.error(f'公司政策入口验证失败: {str(e)}')
            return False

    # 保留旧方法名，避免其他调用方在迁移期间报 AttributeError。
    def is_hot_templates_visible(self):
        return self.is_hot_models_visible()

    def is_upgrade_visible(self):
        return self.is_primary_navigation_visible()

    def is_terms_visible(self):
        return self.are_company_policies_visible()

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
            time.sleep(0.2)
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
            WebDriverWait(self.driver, 10).until(
                lambda d: any(kw.lower() in d.current_url.lower() for kw in expected_keywords)
            )
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
