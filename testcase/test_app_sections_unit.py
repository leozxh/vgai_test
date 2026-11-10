"""App 首页内容区的浏览器回归测试。"""

import unittest
from urllib.parse import quote

from selenium import webdriver

from businessView.appView import AppView


class FastAppView(AppView):
    """保留真实定位逻辑，只缩短静态测试页的等待时间。"""

    def find_one_fast(self, locators, timeout=2, clickable=False):
        return super().find_one_fast(locators, timeout=0.2, clickable=clickable)


class AppSectionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        self.view = FastAppView(self.driver)

    def show_page(self, content):
        self.driver.get('data:text/html;charset=utf-8,' + quote(content))

    def test_visible_creation_card_and_models_pass_without_hot_heading(self):
        self.show_page('''
            <div>
              <h2>Popular AI Creation Tools</h2>
              <div class="home-hot-list">
                <a class="home-hot-card"><h3>Creation template</h3></a>
              </div>
            </div>
            <h2>Models</h2>
        ''')
        self.assertTrue(self.view.is_hot_models_visible())

    def test_heading_without_creation_card_fails(self):
        self.show_page('<h2>Popular AI Creation Tools</h2><h2>Models</h2>')
        self.assertFalse(self.view.is_hot_models_visible())

    def test_creation_card_without_models_fails(self):
        self.show_page('''
            <h2>Popular AI Creation Tools</h2>
            <div class="home-hot-list">
              <a class="home-hot-card"><h3>Creation template</h3></a>
            </div>
        ''')
        self.assertFalse(self.view.is_hot_models_visible())
