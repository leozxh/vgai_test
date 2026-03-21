import logging
import os
import sys
import json
import time
import random
import re
import unittest
import importlib.util
import urllib.request
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from unittestreport import TestRunner
from baseView.baseView import BaseView


class Common(BaseView):
    """常用功能封装类"""

    def get_current_time(self):
        return time.strftime("%Y-%m-%d %H_%M_%S")

    def read_json_data(self, json_file, account_key):
        candidate_paths = [
            os.path.abspath(json_file),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), json_file.replace('/', os.sep)),
        ]
        for candidate in candidate_paths:
            if os.path.exists(candidate):
                with open(candidate, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    return data.get(account_key, {})
        raise FileNotFoundError(f"未找到 JSON 文件: {json_file}; 尝试过: {candidate_paths}")

    def generate_random_email(self):
        return f"{random.randint(1, 99999)}@testcg.com"

    def wait_for_element_visible(self, locator, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
        except TimeoutException:
            logging.error(f"元素 {locator} 在 {timeout} 秒内不可见")
            raise TimeoutException(f"元素 {locator} 在 {timeout} 秒内不可见")

    def wait_for_element_to_be_clickable(self, locator, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return element
        except TimeoutException:
            logging.error(f"元素 {locator} 在 {timeout} 秒内不可点击")
            raise TimeoutException(f"元素 {locator} 在 {timeout} 秒内不可点击")
        except Exception as e:
            logging.error(f"等待元素可点击时发生错误: {str(e)}")
            raise

    def find_one(self, locators, timeout=5, clickable=False):
        for locator in locators:
            try:
                condition = (
                    EC.element_to_be_clickable(locator)
                    if clickable
                    else EC.visibility_of_element_located(locator)
                )
                return WebDriverWait(self.driver, timeout).until(condition)
            except Exception:
                continue
        raise TimeoutException(f"未找到元素，尝试的定位有: {locators}")

    def find_one_fast(self, locators, timeout=2, clickable=False):
        for locator in locators:
            try:
                condition = (
                    EC.element_to_be_clickable(locator)
                    if clickable
                    else EC.visibility_of_element_located(locator)
                )
                return WebDriverWait(self.driver, timeout).until(condition)
            except Exception:
                continue
        raise TimeoutException(f"未找到元素，尝试的定位有: {locators}")

    def get_toast_text(self, toast_message, timeout=10):
        try:
            toast_locator = (By.XPATH, f"//*[contains(text(), '{toast_message}')]")
            toast_element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(toast_locator)
            )
            return toast_element.text
        except Exception as e:
            logging.error(f"未能找到Toast提示: {e}")
            return None

    def capture_screenshot(self, module):
        timestamp = self.get_current_time()
        screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, f'{module}_{timestamp}.png')
        logging.info(f'正在为 {module} 模块截图')
        self.driver.get_screenshot_as_file(screenshot_path)


class ReportManager:
    """测试报告管理类"""

    def __init__(self):
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        self.PROJECT_ROOT = os.path.normpath(os.path.join(CURRENT_DIR, '..'))
        if self.PROJECT_ROOT not in sys.path:
            sys.path.insert(0, self.PROJECT_ROOT)
        self.REPORTS_DIR = os.path.join(self.PROJECT_ROOT, 'reports')

        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            log_file = os.path.join(self.PROJECT_ROOT, 'logs', 'runlog.txt')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s %(name)s[line:%(lineno)d] %(levelname)s %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)

    def load_test_case(self):
        """加载测试用例"""
        TESTCASE_FILE = os.path.join(self.PROJECT_ROOT, 'testcase', 'test_apppage.py')
        spec = importlib.util.spec_from_file_location('project_test_apppage', TESTCASE_FILE)
        module_test = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module_test)
        return module_test.AppPageTest

    def load_email_config(self):
        config_path = os.path.join(self.PROJECT_ROOT, 'data', 'email_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            return config
        except FileNotFoundError:
            self.logger.error("Configuration file 'email_config.json' not found.")
            return None
        except json.JSONDecodeError:
            self.logger.error("Failed to parse 'email_config.json'.")
            return None

    def setup_test_suite(self):
        AppPageTest = self.load_test_case()
        suite = unittest.TestSuite()
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(AppPageTest))
        return suite

    def create_test_runner(self, suite):
        os.makedirs(self.REPORTS_DIR, exist_ok=True)
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        return TestRunner(suite,
                          tester='zxh',
                          title="Visiva.AI 营销站自动化测试报告",
                          report_dir=self.REPORTS_DIR,
                          desc=f"测试执行时间: {current_time} | 包含主页面加载、功能导航、登录等操作",
                          templates=1)

    def run_tests(self, runner):
        self.logger.info("开始测试...")
        try:
            original_exit = sys.exit

            def mock_exit(code=0):
                self.logger.warning(f"检测到 sys.exit({code}) 调用，但继续执行程序")
                return

            sys.exit = mock_exit
            try:
                result = runner.run()
                runner._test_result = result
                self.logger.info("测试完成，结果已保存")
                return result
            finally:
                sys.exit = original_exit
        except Exception as e:
            self.logger.error(f"运行测试时发生错误: {str(e)}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            self.logger.info("测试运行失败，但继续执行后续步骤")
            return None

    def enhance_report_with_logs(self):
        """在HTML报告中添加运行日志内容"""
        html_report_path = os.path.join(self.REPORTS_DIR, "report.html")
        log_file_path = os.path.join(self.PROJECT_ROOT, 'logs', 'runlog.txt')

        if not os.path.exists(html_report_path) or not os.path.exists(log_file_path):
            self.logger.warning("HTML报告或日志文件不存在，无法添加日志")
            return

        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()

            with open(html_report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            escaped_log_content = (log_content
                                   .replace('&', '&amp;')
                                   .replace('<', '&lt;')
                                   .replace('>', '&gt;')
                                   .replace('"', '&quot;')
                                   .replace("'", '&#x27;'))

            log_section = f"""<!-- 运行日志区域 -->
<div class="test_info" style="top: 1400px;">
    <p class="text-left text-success">
        运行日志
        <button type="button" id="toggleLogBtn" class="btn btn-sm btn-outline-success ml-2">展开</button>
    </p>
    <div class="table_data" id="logSection" style="display: none;">
        <table class="table">
            <thead class="bg-success text-light">
                <tr>
                    <th scope="col" style="width: 100%;padding: 0">测试运行日志</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="small" style="word-wrap:break-word; word-break:break-all; text-align: left;">
                        <pre style="max-height: 400px; overflow-y: auto; font-size: 12px; line-height: 16px; color: #007bff; text-align: left;">{escaped_log_content}</pre>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    <div style="height: 100px"></div>
</div>

<script>
document.getElementById('toggleLogBtn').addEventListener('click', function() {{
    var logSection = document.getElementById('logSection');
    var toggleBtn = document.getElementById('toggleLogBtn');
    if (logSection.style.display === 'none') {{
        logSection.style.display = 'block';
        toggleBtn.textContent = '收起';
        toggleBtn.classList.remove('btn-outline-success');
        toggleBtn.classList.add('btn-success');
    }} else {{
        logSection.style.display = 'none';
        toggleBtn.textContent = '展开';
        toggleBtn.classList.remove('btn-success');
        toggleBtn.classList.add('btn-outline-success');
    }}
}});
</script>"""

            if '</body>' in html_content:
                enhanced_html = html_content.replace('</body>', log_section + '</body>')
            else:
                enhanced_html = html_content + log_section

            with open(html_report_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_html)

            self.logger.info("成功将运行日志添加到HTML报告中")
        except Exception as e:
            self.logger.error(f"添加日志到HTML报告失败: {str(e)}")

    def send_test_email_only(self, runner, email_config):
        if not email_config:
            self.logger.error("Failed to load email configuration.")
            return
        try:
            self.logger.info("开始发送测试报告邮件...")
            runner.send_email(
                host=email_config["host"],
                port=email_config["port"],
                user=email_config["user"],
                password=email_config["password"],
                to_addrs=email_config["to_addrs"]
            )
            self.logger.info("测试报告邮件发送成功")
        except Exception as e:
            self.logger.error(f"发送邮件失败: {str(e)}")

    def analyze_test_results_from_html_report(self):
        """从HTML报告分析测试结果"""
        try:
            report_file = os.path.join(self.PROJECT_ROOT, 'reports', 'report.html')
            if not os.path.exists(report_file):
                self.logger.warning("HTML报告文件不存在")
                return None

            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()

            success_match = re.search(r'<button[^>]*>成功用例</button>\s*<span[^>]*class="text-success"[^>]*>(\d+)</span>', content)
            success_count = int(success_match.group(1)) if success_match else 0

            failed_match = re.search(r'<button[^>]*>失败用例</button>\s*<span[^>]*class="text-warning"[^>]*>(\d+)</span>', content)
            failed_count = int(failed_match.group(1)) if failed_match else 0

            error_match = re.search(r'<button[^>]*>错误用例</button>\s*<span[^>]*class="text-danger"[^>]*>(\d+)</span>', content)
            error_count = int(error_match.group(1)) if error_match else 0

            skipped_match = re.search(r'<button[^>]*>跳过用例</button>\s*<span[^>]*class="text-secondary"[^>]*>(\d+)</span>', content)
            skipped_count = int(skipped_match.group(1)) if skipped_match else 0

            total_tests = success_count + failed_count + error_count + skipped_count
            executed_tests = success_count + failed_count + error_count
            pass_rate = (success_count / executed_tests * 100) if executed_tests > 0 else 100.0

            self.logger.info(f"HTML报告分析: 成功={success_count}, 失败={failed_count}, 错误={error_count}, 跳过={skipped_count}, 通过率={pass_rate:.1f}%")

            # 定义测试用例名称映射
            test_case_names = {
                1: "test_01_app_load - 主页面加载测试",
                2: "test_02_features_display - 功能入口显示测试",
                3: "test_03_hot_templates - Hot Templates测试",
                4: "test_04_upgrade_terms - Upgrade/Terms测试",
                5: "test_05_nav_image_to_video - Image to Video导航",
                6: "test_06_nav_text_to_video - Text to Video导航",
                7: "test_07_nav_video_extend - Video Extend导航",
                8: "test_08_nav_ai_effects - AI Effects导航",
                9: "test_09_nav_terms - Terms页面导航",
                10: "test_10_login - 登录功能测试",
                11: "test_11_i2v_inspiration_generate - 图生视频模板生成测试",
            }

            test_details = []
            test_result_pattern = re.compile(
                r'<td>(\d+)</td>\s*'
                r'<td[^>]*>[^<]*</td>\s*'
                r'<td>(test_\d+_\w+)</td>\s*'
                r'<td>[^<]*</td>\s*'
                r'<td>[^<]*</td>\s*'
                r'<td\s+class="text-(success|warning|danger|info)">(成功|失败|错误|跳过)</td>',
                re.DOTALL
            )
            matches = test_result_pattern.findall(content)

            if matches:
                results_dict = {}
                for match in matches:
                    test_method_name = match[1]
                    result_status = match[3]
                    num_match = re.match(r'test_(\d+)_', test_method_name)
                    test_num = int(num_match.group(1)) if num_match else 0
                    test_name = test_case_names.get(test_num, test_method_name)
                    status_emoji = {'成功': '✅', '失败': '❌', '错误': '⚠️', '跳过': '⏭️'}.get(result_status, '❓')
                    results_dict[test_num] = f"{test_name} - {status_emoji}"
                for num in sorted(results_dict.keys()):
                    test_details.append(results_dict[num])
            else:
                for i in range(1, total_tests + 1):
                    test_name = test_case_names.get(i, f"test_{i}")
                    test_details.append(f"{test_name} - ✅" if i <= success_count else f"{test_name} - ❌")

            return {
                'total_tests': total_tests,
                'passed': success_count,
                'failed': failed_count,
                'errors': error_count,
                'skipped': skipped_count,
                'pass_rate': pass_rate,
                'test_details': test_details
            }
        except Exception as e:
            self.logger.error(f"从HTML报告分析测试结果失败: {str(e)}")
            return None

    def send_wechat_notification_standalone(self):
        """独立的企业微信推送方法"""
        webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=f613f748-a99e-4520-8924-0cde051486da"

        test_results = self.analyze_test_results_from_html_report()
        if not test_results:
            test_results = {
                'total_tests': 0, 'passed': 0, 'failed': 0,
                'errors': 0, 'skipped': 0, 'pass_rate': 0,
                'test_details': ['无法解析测试结果']
            }

        current_time = datetime.now()
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

        content = f"""🧪 Visiva.AI 自动化测试报告

⏰ 执行时间: {formatted_time}
👨‍💻 测试人员: zxh

📊 测试结果统计:
✅ 成功用例: {test_results['passed']}
❌ 失败用例: {test_results['failed']}
⚠️ 错误用例: {test_results['errors']}
⏭️ 跳过用例: {test_results['skipped']}
📈 通过率: {test_results['pass_rate']:.1f}%

🔍 测试详情:"""

        for detail in test_results['test_details']:
            content += f"\n{detail}"

        content += """

📧 详细报告已发送至邮箱

---
此消息由 Visiva.AI 自动化测试系统自动发送"""

        data = {
            "msgtype": "text",
            "text": {"content": content}
        }

        try:
            self.logger.info("开始发送企业微信推送...")
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=json_data,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result_data = response.read().decode('utf-8')
                result = json.loads(result_data)
                if result.get('errcode') == 0:
                    self.logger.info("✅ 企业微信推送发送成功！")
                    return True
                else:
                    self.logger.error(f"❌ 企业微信推送失败: {result.get('errmsg', '未知错误')}")
                    return False
        except Exception as e:
            self.logger.error(f"❌ 发送企业微信推送时发生错误: {str(e)}")
            return False

    def send_test_email_and_push(self, runner, email_config):
        self.send_wechat_notification_standalone()
        self.send_test_email_only(runner, email_config)
