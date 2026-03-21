import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from businessView.siginView import SiginView
from businessView.appView import AppView
from businessView.i2vView import I2VView
import unittest
import logging
from common.caps import DriverManager


class AppPageTest(unittest.TestCase):
    """Visiva.AI App 页面功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.driver_manager = DriverManager()
        cls.driver = cls.driver_manager.prod_caps()
        cls.app_view = AppView(cls.driver)
        cls.sigin_view = SiginView(cls.driver)
        cls.i2v_view = I2VView(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        logging.info('Executing test case')

    def tearDown(self):
        logging.info('Test case execution completed')

    def test_01_app_load(self):
        """主页面加载测试"""
        logging.info('开始主页面加载测试')
        self.app_view.go_to_app()
        self.assertIn("visiva", self.driver.current_url.lower())
        self.assertTrue(self.app_view.is_main_heading_visible(), "应显示 Visiva.AI 主标题")
        logging.info('主页面加载测试完成')

    def test_02_features_display(self):
        """功能入口显示测试"""
        logging.info('开始功能入口显示测试')
        self.app_view.go_to_app()
        self.assertTrue(self.app_view.are_features_visible(),
                        "应显示 Image to Video、Text to Video、Video Extend、AI Effects 四个入口")
        logging.info('功能入口显示测试完成')

    def test_03_hot_templates_display(self):
        """Hot Templates 区域测试"""
        logging.info('开始 Hot Templates 区域测试')
        self.app_view.go_to_app()
        self.assertTrue(self.app_view.is_hot_templates_visible(), "应显示 Hot Templates 区域")
        logging.info('Hot Templates 区域测试完成')

    def test_04_upgrade_terms_display(self):
        """Upgrade 和 Terms 链接测试"""
        logging.info('开始 Upgrade/Terms 链接测试')
        self.app_view.go_to_app()
        self.assertTrue(self.app_view.is_upgrade_visible(), "应显示 Upgrade")
        self.assertTrue(self.app_view.is_terms_visible(), "应显示 Terms 链接")
        logging.info('Upgrade/Terms 链接测试完成')

    def test_05_nav_image_to_video(self):
        """Image to Video 导航测试"""
        logging.info('开始 Image to Video 导航测试')
        self.app_view.go_to_app()
        result = self.app_view.nav_image_to_video()
        self.assertTrue(result, "Image to Video 页面跳转失败")
        logging.info('Image to Video 导航测试完成')

    def test_06_nav_text_to_video(self):
        """Text to Video 导航测试"""
        logging.info('开始 Text to Video 导航测试')
        self.app_view.go_to_app()
        result = self.app_view.nav_text_to_video()
        self.assertTrue(result, "Text to Video 页面跳转失败")
        logging.info('Text to Video 导航测试完成')

    def test_07_nav_video_extend(self):
        """Video Extend 导航测试"""
        logging.info('开始 Video Extend 导航测试')
        self.app_view.go_to_app()
        result = self.app_view.nav_video_extend()
        self.assertTrue(result, "Video Extend 页面跳转失败")
        logging.info('Video Extend 导航测试完成')

    def test_08_nav_ai_effects(self):
        """AI Effects 导航测试"""
        logging.info('开始 AI Effects 导航测试')
        self.app_view.go_to_app()
        result = self.app_view.nav_ai_effects()
        self.assertTrue(result, "AI Effects 页面跳转失败")
        logging.info('AI Effects 导航测试完成')

    def test_09_nav_terms(self):
        """Terms 页面导航测试"""
        logging.info('开始 Terms 页面导航测试')
        self.app_view.go_to_app()
        result = self.app_view.nav_terms()
        self.assertTrue(result, "Terms 页面跳转失败")
        logging.info('Terms 页面导航测试完成')

    def test_10_login(self):
        """登录功能测试"""
        logging.info('开始登录功能测试')
        self.app_view.go_to_app()
        data = self.sigin_view.read_json_data('data/account.json', 'account1')
        result = self.sigin_view.login_action(data['username'], data['password'])
        self.assertTrue(result, "登录失败")
        logging.info('登录功能测试完成')

    def test_11_i2v_inspiration_generate(self):
        """图生视频 Inspiration 模板生成测试"""
        logging.info('开始图生视频 Inspiration 模板生成测试')
        result = self.i2v_view.i2v_inspiration_generation_test()
        self.assertTrue(result, "图生视频 Inspiration 模板生成测试失败")
        logging.info('图生视频 Inspiration 模板生成测试完成')


if __name__ == '__main__':
    unittest.main()
