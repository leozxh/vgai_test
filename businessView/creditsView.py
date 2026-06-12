import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import time
import re
import json
from urllib.parse import urlsplit
from common.common_fun import Common, By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class CreditsView(Common):
    """积分扣减验证业务逻辑 - 基于实际页面结构"""

    # 各模型页面路径
    MODEL_PAGES = {
        'Image to Video': '/app/image-to-video',
        'Text to Video': '/app/text-to-video',
        'Video Extend': '/app/video-extend',
        'AI Effects': '/app/video-effects',
    }

    def __init__(self, driver):
        super().__init__(driver)

    def _get_origin(self):
        parsed = urlsplit(self.driver.current_url)
        return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "https://visiva.ai"

    def go_to_model_page(self, model_name):
        """导航到指定模型页面"""
        path = self.MODEL_PAGES.get(model_name)
        if not path:
            logging.error(f'未知模型: {model_name}')
            return False
        try:
            url = self._get_origin() + path
            logging.info(f'导航到 {model_name}: {url}')
            self.driver.get(url)
            time.sleep(3)
            WebDriverWait(self.driver, 15).until(
                lambda d: path.split('/')[-1] in d.current_url
            )
            logging.info(f'已进入 {model_name}: {self.driver.current_url}')
            return True
        except Exception as e:
            logging.error(f'导航到 {model_name} 失败: {e}')
            return False

    def get_credit_balance(self):
        """
        从右上角读取积分余额。
        页面显示格式: "918534 Lite" 或 "918534|Lite" 按钮
        """
        js = """
        // 查找包含 Lite/Pro/Premium 等套餐文本的按钮，从中提取数字
        var btns = document.querySelectorAll('button');
        for (var b of btns) {
            var text = b.textContent.trim();
            if (/\\b(Lite|Pro|Premium|Free|Basic|Standard)\\b/i.test(text)) {
                var nums = text.match(/(\\d{2,})/);
                if (nums) return parseInt(nums[1]);
            }
        }
        // 备选: 查找 header/nav 区域中独立的大数字
        var header = document.querySelector('header, nav, [class*="header"], [class*="nav"]');
        if (header) {
            var spans = header.querySelectorAll('span, div, button');
            for (var s of spans) {
                var t = s.textContent.trim();
                if (/^\\d{3,}$/.test(t)) return parseInt(t);
            }
        }
        return null;
        """
        try:
            result = self.driver.execute_script(js)
            if result:
                logging.info(f'积分余额: {result}')
            else:
                logging.warning('未读取到积分余额')
            return result
        except Exception as e:
            logging.error(f'读取积分余额失败: {e}')
            return None

    def get_create_button_cost(self):
        """
        从 Create 按钮读取积分消耗数。
        按钮文本格式: "Create ⚡ 420" 或 "Create 420"
        """
        js = """
        var btns = document.querySelectorAll('button');
        for (var b of btns) {
            var text = b.textContent.trim();
            if (/create/i.test(text) && !/creation/i.test(text)) {
                var nums = text.match(/(\\d+)/);
                if (nums) return parseInt(nums[1]);
            }
        }
        return null;
        """
        try:
            result = self.driver.execute_script(js)
            if result:
                logging.info(f'Create 按钮积分消耗: {result}')
            else:
                logging.warning('未读取到 Create 按钮积分消耗')
            return result
        except Exception as e:
            logging.error(f'读取 Create 积分消耗失败: {e}')
            return None

    def get_current_model_name(self):
        """读取当前选中的模型名称（模型下拉框显示的文本）"""
        js = """
        // 模型选择器是 w-full 的按钮，包含模型名如 "Visiva Intimate R4.0"
        var btns = document.querySelectorAll('button');
        for (var b of btns) {
            var cls = b.className || '';
            var text = b.textContent.trim();
            if (cls.includes('justify-between') && /visiva|kling|wan|runway|pika|luma|sora/i.test(text)) {
                // 只取模型名，去掉描述部分
                var lines = text.split('\\n');
                return lines[0].trim();
            }
        }
        return null;
        """
        try:
            return self.driver.execute_script(js)
        except Exception:
            return None

    def get_model_dropdown_options(self):
        """
        点击模型下拉框，获取所有可选模型。
        返回 [{name, index}]
        """
        # 先点击模型下拉框
        js_click = """
        var btns = document.querySelectorAll('button');
        for (var b of btns) {
            var cls = b.className || '';
            var text = b.textContent.trim();
            if (cls.includes('justify-between') && /visiva|kling|wan|runway|pika|luma|sora/i.test(text)) {
                b.click();
                return true;
            }
        }
        return false;
        """
        try:
            clicked = self.driver.execute_script(js_click)
            if not clicked:
                logging.info('未找到模型下拉框')
                return []
            time.sleep(1)

            # 读取下拉选项
            js_options = """
            var results = [];
            // 查找下拉菜单中的选项 (通常是 popover/dropdown 中的 div/button)
            var popups = document.querySelectorAll('[class*="popover"], [class*="dropdown"], [class*="menu"], [role="listbox"], [role="menu"]');
            for (var popup of popups) {
                if (popup.offsetParent === null) continue;  // 不可见
                var items = popup.querySelectorAll('button, [role="option"], [class*="item"], [class*="option"]');
                for (var i = 0; i < items.length; i++) {
                    var text = items[i].textContent.trim().split('\\n')[0].trim();
                    if (text && text.length > 2 && text.length < 60) {
                        results.push({name: text, index: i});
                    }
                }
                if (results.length > 0) return JSON.stringify(results);
            }
            // 备选: 查找弹出层内所有可点击元素
            var overlays = document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="panel"]');
            for (var ov of overlays) {
                if (ov.offsetParent === null) continue;
                var items = ov.querySelectorAll('button, div[class*="cursor-pointer"]');
                for (var i = 0; i < items.length; i++) {
                    var text = items[i].textContent.trim().split('\\n')[0].trim();
                    if (text && /visiva|kling|wan|runway|pika|luma|sora/i.test(text)) {
                        results.push({name: text, index: i});
                    }
                }
            }
            return JSON.stringify(results);
            """
            result = self.driver.execute_script(js_options)
            options = json.loads(result) if isinstance(result, str) else (result or [])

            # 关闭下拉框 (点击空白处)
            self.driver.execute_script("document.body.click();")
            time.sleep(0.5)

            if options:
                logging.info(f'模型选项: {[o["name"] for o in options]}')
            else:
                logging.info('未发现模型下拉选项')
            return options
        except Exception as e:
            logging.error(f'获取模型下拉选项失败: {e}')
            return []

    def select_model(self, model_name):
        """选择指定模型"""
        js = f"""
        // 先点击下拉框
        var btns = document.querySelectorAll('button');
        var dropdown;
        for (var b of btns) {{
            var cls = b.className || '';
            if (cls.includes('justify-between') && /visiva|kling|wan|runway|pika|luma|sora/i.test(b.textContent)) {{
                dropdown = b;
                break;
            }}
        }}
        if (!dropdown) return false;
        dropdown.click();
        await new Promise(r => setTimeout(r, 800));

        // 在弹出层中查找目标模型
        var target = '{model_name}'.toLowerCase();
        var allClickable = document.querySelectorAll('button, [role="option"], [class*="item"], div[class*="cursor-pointer"]');
        for (var el of allClickable) {{
            if (el.offsetParent === null) continue;
            var text = el.textContent.trim().toLowerCase();
            if (text.includes(target)) {{
                el.click();
                return true;
            }}
        }}
        return false;
        """
        # 用同步方式
        js_sync = f"""
        var btns = document.querySelectorAll('button');
        for (var b of btns) {{
            var cls = b.className || '';
            if (cls.includes('justify-between') && /visiva|kling|wan|runway|pika|luma|sora/i.test(b.textContent)) {{
                b.click();
                return true;
            }}
        }}
        return false;
        """
        try:
            self.driver.execute_script(js_sync)
            time.sleep(1)

            js_select = f"""
            var target = '{model_name}'.toLowerCase();
            var allClickable = document.querySelectorAll('button, [role="option"], div[class*="cursor-pointer"]');
            for (var el of allClickable) {{
                if (el.offsetParent === null) continue;
                var text = el.textContent.trim().toLowerCase();
                if (text.includes(target)) {{
                    el.click();
                    return el.textContent.trim().split('\\n')[0].trim();
                }}
            }}
            return null;
            """
            result = self.driver.execute_script(js_select)
            if result:
                logging.info(f'已选择模型: {result}')
                time.sleep(1)
                return True
            logging.warning(f'未找到模型: {model_name}')
            self.driver.execute_script("document.body.click();")
            return False
        except Exception as e:
            logging.error(f'选择模型失败: {e}')
            return False

    def get_format_labels(self):
        """
        获取页面上的格式 label 选项。
        返回 {group_name: [{text, element_index}]}
        格式 label 使用 <label> 标签，class 含 rounded-[15px]
        """
        js = """
        var labels = document.querySelectorAll('label');
        var results = [];
        for (var i = 0; i < labels.length; i++) {
            var lb = labels[i];
            var cls = lb.className || '';
            if (!cls.includes('rounded')) continue;
            var text = lb.textContent.trim();
            if (!text || text.length > 30) continue;
            // 判断类型
            var group = 'unknown';
            if (/^\\d+s$/i.test(text)) group = 'duration';
            else if (/^\\d+P$/i.test(text) || /^\\d+K$/i.test(text)) group = 'resolution';
            else if (/^\\d+:\\d+$/.test(text) || /portrait|landscape|square/i.test(text)) group = 'ratio';
            // 判断是否被选中 (通常选中的有不同背景色)
            var computed = window.getComputedStyle(lb);
            var bg = computed.backgroundColor;
            var isSelected = (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent' && !bg.includes('0, 0, 0'));
            results.push({text: text, index: i, group: group, selected: isSelected});
        }
        return JSON.stringify(results);
        """
        try:
            result = self.driver.execute_script(js)
            labels = json.loads(result) if isinstance(result, str) else (result or [])
            # 按组分类
            groups = {}
            for lb in labels:
                g = lb['group']
                if g not in groups:
                    groups[g] = []
                groups[g].append(lb)
            if groups:
                for g, items in groups.items():
                    logging.info(f'  格式组 [{g}]: {[it["text"] + ("*" if it["selected"] else "") for it in items]}')
            return groups
        except Exception as e:
            logging.error(f'获取格式 label 失败: {e}')
            return {}

    def click_format_label(self, label_index):
        """点击指定 index 的格式 label"""
        js = f"""
        var labels = document.querySelectorAll('label');
        var count = 0;
        for (var i = 0; i < labels.length; i++) {{
            var cls = labels[i].className || '';
            if (!cls.includes('rounded')) continue;
            if (i === {label_index}) {{
                labels[i].click();
                return labels[i].textContent.trim();
            }}
        }}
        return null;
        """
        try:
            result = self.driver.execute_script(js)
            if result:
                time.sleep(0.8)
            return result
        except Exception as e:
            logging.error(f'点击格式 label 失败: {e}')
            return None

    def get_ai_effects_templates(self):
        """
        获取 AI Effects 页面的模板列表及其积分价格。
        返回 [{name, credits}]
        """
        js = """
        var results = [];
        // AI Effects 页面的模板卡片，通常有图片 + 名称 + 积分数
        var cards = document.querySelectorAll('[class*="card"], [class*="template"], [class*="grid"] > div, [class*="grid"] > a');
        for (var card of cards) {
            if (card.offsetParent === null) continue;
            var text = card.textContent.trim();
            // 提取积分数 (卡片中的独立数字)
            var nums = text.match(/\\d+/g);
            var name = '';
            // 获取卡片标题
            var titleEl = card.querySelector('p, span, h3, h4, [class*="title"], [class*="name"]');
            if (titleEl) name = titleEl.textContent.trim();
            if (!name) {
                var lines = text.split('\\n').map(function(l){ return l.trim(); }).filter(function(l){ return l; });
                name = lines[0] || '';
            }
            if (name && nums && nums.length > 0) {
                // 最后一个数字通常是积分
                var credits = parseInt(nums[nums.length - 1]);
                if (credits > 0 && credits < 100000 && name.length < 60) {
                    results.push({name: name, credits: credits});
                }
            }
        }
        return JSON.stringify(results);
        """
        try:
            result = self.driver.execute_script(js)
            templates = json.loads(result) if isinstance(result, str) else (result or [])
            if templates:
                logging.info(f'AI Effects 模板数: {len(templates)}')
            return templates
        except Exception as e:
            logging.error(f'获取 AI Effects 模板失败: {e}')
            return []

    def take_screenshot(self, name):
        """截图"""
        try:
            screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)
            safe_name = re.sub(r'[\\/:*?"<>|]', '_', name)
            path = os.path.join(screenshots_dir, f'{safe_name}_{int(time.time())}.png')
            self.driver.get_screenshot_as_file(path)
            logging.info(f'截图: {path}')
            return path
        except Exception as e:
            logging.error(f'截图失败: {e}')
            return None
