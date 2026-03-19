import json
import os
import time
import logging.config
from os import path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# 确保 Selenium 与本地 ChromeDriver 通信不走代理
os.environ["NO_PROXY"] = os.environ.get("NO_PROXY", "") + ",localhost,127.0.0.1"
os.environ["no_proxy"] = os.environ.get("no_proxy", "") + ",localhost,127.0.0.1"
# 优先使用本地缓存的 ChromeDriver，避免网络波动导致失败
os.environ["WDM_LOCAL"] = "1"

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False

log_file_path = path.join(path.dirname(path.abspath(__file__)), '../config/log.conf')
log_path = path.normpath(path.join(path.dirname(path.abspath(__file__)), '../logs/runlog.txt'))
log_path_for_config = log_path.replace('\\', '/')
os.makedirs(path.dirname(log_path), exist_ok=True)
logging.config.fileConfig(log_file_path, defaults={'logfile': log_path_for_config}, encoding='utf-8')
logging = logging.getLogger()


class DriverManager:
    def __init__(self):
        config_path = path.join(path.dirname(path.abspath(__file__)), '../data/env.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def _is_docker(self):
        """判断是否在 Docker 容器中运行"""
        return os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == '1'

    def _build_chrome_options(self):
        """构建 Chrome 优化选项"""
        chrome_options = webdriver.ChromeOptions()

        # Docker 容器内必须 headless
        if self._is_docker():
            chrome_options.add_argument('--headless=new')

        # 从环境变量读取代理配置
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')

        # 基础性能优化
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--window-size=1920,1080')

        # 网络和稳定性优化
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-features=BlinkGenPropertyTrees')

        # 加载速度优化
        chrome_options.add_argument('--disable-fonts')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-background-networking')

        # 网络优化
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--disable-background-downloads')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-hang-monitor')
        chrome_options.add_argument('--disable-prompt-on-repost')
        chrome_options.add_argument('--disable-sync')

        # 内存和CPU优化
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=4096')

        # 实验性功能优化
        chrome_options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
        chrome_options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')

        # 抑制错误日志输出
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-gpu-logging')
        chrome_options.add_argument('--silent')
        chrome_options.add_argument('--log-level=3')

        # 抑制特定错误信息
        chrome_options.add_argument('--disable-component-extensions-with-background-pages')
        chrome_options.add_argument('--disable-extensions-file-access-check')
        chrome_options.add_argument('--disable-extensions-http-throttling')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-domain-reliability')
        chrome_options.add_argument('--disable-features=Translate,BackForwardCache')

        return chrome_options

    def init_driver(self, env, log_message=None):
        """
        初始化Chrome浏览器驱动并打开指定URL
        :param env: 环境标识，如 'test', 'dev', 'prod'
        :param log_message: 可选的日志消息
        :return: WebDriver对象
        """
        url = self.config.get(env)
        if not url:
            raise ValueError(f"Invalid environment: {env}")

        hub_url = os.environ.get('SELENIUM_HUB_URL')
        chrome_options = self._build_chrome_options()

        if hub_url:
            # 使用远程WebDriver（Selenium Grid / Docker）
            logging.info(f"使用Selenium Grid: {hub_url}")
            driver = webdriver.Remote(
                command_executor=hub_url,
                options=chrome_options
            )
        else:
            # 使用本地WebDriver
            logging.info("使用本地Chrome驱动")
            service = None
            if HAS_WEBDRIVER_MANAGER:
                try:
                    service = Service(ChromeDriverManager().install())
                except Exception as wdm_err:
                    logging.warning(f"webdriver-manager 在线获取失败: {wdm_err}")
                    # 尝试从 webdriver-manager 缓存目录中查找可用的 chromedriver
                    import glob
                    wdm_cache = os.path.expanduser("~/.wdm/drivers/chromedriver")
                    candidates = glob.glob(os.path.join(wdm_cache, "**", "chromedriver.exe"), recursive=True)
                    if not candidates:
                        candidates = glob.glob(os.path.join(wdm_cache, "**", "chromedriver"), recursive=True)
                    if candidates:
                        cached_path = candidates[-1]  # 取最新版本
                        logging.info(f"使用缓存的 ChromeDriver: {cached_path}")
                        service = Service(cached_path)
                    else:
                        logging.warning("未找到缓存的 ChromeDriver，使用 Selenium 内置管理")
            if service is None:
                service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.implicitly_wait(2)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(10)

        if log_message:
            logging.info(log_message)

        # 添加重试机制处理页面加载超时
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logging.info(f"尝试加载页面 (第 {attempt + 1} 次)...")
                driver.get(url)
                logging.info("页面加载成功")
                break
            except Exception as e:
                logging.warning(f"页面加载失败 (第 {attempt + 1} 次): {str(e)}")
                if attempt < max_retries - 1:
                    logging.info("等待 3 秒后重试...")
                    time.sleep(3)
                else:
                    logging.error("页面加载最终失败，已达到最大重试次数")
                    raise e

        return driver

    def test_caps(self):
        return self.init_driver("test", '访问测试环境，页面加载中')

    def dev_caps(self):
        return self.init_driver("dev", '访问正式环境，页面加载中')

    def prod_caps(self):
        return self.init_driver("prod", '访问生产环境，页面加载中')


if __name__ == "__main__":
    driver_manager = DriverManager()
    driver = driver_manager.prod_caps()
