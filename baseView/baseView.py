import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseView(object):
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)

    def find(self, *loc):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(loc)
            )
            self.logger.info(f"Element found: {loc}")
            return element
        except Exception as e:
            self.logger.error(f"Element not found: {loc}, error: {e}")
            raise

    def finds(self, *loc):
        try:
            elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(loc)
            )
            self.logger.info(f"Elements found: {loc}")
            return elements
        except Exception as e:
            self.logger.error(f"Elements not found: {loc}, error: {e}")
            raise

    def get_window_size(self):
        size = self.driver.get_window_size()
        self.logger.info(f"Window size: {size}")
        return size
