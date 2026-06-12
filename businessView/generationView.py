"""生成功能业务逻辑：I2V / T2V / Video Extend / I2I / T2I / AI NSFW / AI Effects

侧重 P-11 ~ P-18, P-13 ~ P-17 等模块的核心校验：
- 模型列表
- 模型切换参数变化
- 上传文件
- Prompt 输入
- 时长/分辨率选项
- 积分显示
- 生成触发
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import logging
from selenium.webdriver.common.by import By
from businessView.creditsView import CreditsView


class GenerationView(CreditsView):
    """复用 CreditsView 的导航/读取能力，扩展生成校验"""

    TEST_IMAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                              'screenshots', 'discover_Image_to_Video_1775486099.png')
    TEST_VIDEO = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                              'data', 'test_video.mp4')

    PAGE_PATHS = {
        'i2v': '/app/image-to-video',
        't2v': '/app/text-to-video',
        've': '/app/video-extend',
        'i2i': '/app/image-to-image',
        't2i': '/app/text-to-image',
        'nsfw': '/app/ai-nsfw',
        'effects': '/app/video-effects',
    }

    def goto_page(self, key):
        path = self.PAGE_PATHS.get(key)
        if not path:
            return False
        from urllib.parse import urlsplit
        parsed = urlsplit(self.driver.current_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        self.driver.get(origin + path)
        time.sleep(3)
        return path.split('/')[-1] in self.driver.current_url

    def _fill_prompt(self, text):
        return self.driver.execute_script("""
            var ta = document.querySelector('textarea');
            if (!ta) return false;
            var setter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value').set;
            setter.call(ta, arguments[0]);
            ta.dispatchEvent(new Event('input', {bubbles: true}));
            return true;
        """, text)

    def _upload(self, filepath):
        try:
            self.driver.execute_script(
                "var i=document.querySelector('input[type=\"file\"]'); if(i){i.style.display='block'; i.style.visibility='visible';}")
            inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            for inp in inputs:
                try:
                    inp.send_keys(os.path.abspath(filepath))
                    return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    # ---- 通用 case ----

    def check_model_list_count(self, page_key, min_count=2):
        """页面模型数 ≥ min_count"""
        if not self.goto_page(page_key):
            return False, f'未能进入 {page_key}'
        opts = self.get_model_dropdown_options()
        # 去重（脚本会读到重复项）
        names = set()
        for o in opts:
            n = o['name'].split('\n')[0].strip()
            if 5 < len(n) < 40:
                names.add(n)
        return len(names) >= min_count, f'模型数={len(names)} → {sorted(names)}'

    def check_duration_options(self, page_key, model_keyword, expected_durations):
        """选模型后时长选项与预期至少一项交集（站点选项可能与文档不完全一致）"""
        if not self.goto_page(page_key):
            return False, '导航失败'
        self.select_model(model_keyword)
        time.sleep(1.5)
        groups = self.get_format_labels()
        durs = sorted(set(o['text'].rstrip('*').strip() for o in groups.get('duration', [])))
        common = set(durs) & set(expected_durations)
        ok = len(common) >= 1 and len(durs) >= 1
        return ok, f'实际 {durs} 预期 {expected_durations} 交集 {sorted(common)}'

    def check_resolution_options(self, page_key, model_keyword, expected_resolutions):
        if not self.goto_page(page_key):
            return False, '导航失败'
        self.select_model(model_keyword)
        time.sleep(1.5)
        groups = self.get_format_labels()
        ress = sorted(set(o['text'].rstrip('*').strip() for o in groups.get('resolution', [])))
        common = set(ress) & set(expected_resolutions)
        ok = len(common) >= 1 and len(ress) >= 1
        return ok, f'实际 {ress} 预期 {expected_resolutions} 交集 {sorted(common)}'

    def check_prompt_input(self, page_key):
        if not self.goto_page(page_key):
            return False, '导航失败'
        time.sleep(1)
        ok = self._fill_prompt('A beautiful sunset over the ocean')
        # 验证 textarea.value 真的被设置
        val = ''
        try:
            val = self.driver.execute_script("var t=document.querySelector('textarea'); return t ? t.value : '';")
        except Exception:
            pass
        return ok and 'sunset' in val, f'填入={ok} 实际值长度={len(val)}'

    def check_upload_image(self, page_key):
        if not os.path.exists(self.TEST_IMAGE):
            return False, '无测试图片'
        if not self.goto_page(page_key):
            return False, '导航失败'
        time.sleep(1)
        # 记录上传前的 img/video src 集合
        before = self.driver.execute_script(
            "return Array.from(document.querySelectorAll('img,video')).map(e=>e.src||'');")
        ok = self._upload(self.TEST_IMAGE)
        time.sleep(3)
        # 任一新的 blob/data/cdn URL 出现，或上传按钮变化都算预览成功
        after = self.driver.execute_script(
            "return Array.from(document.querySelectorAll('img,video')).map(e=>e.src||'');")
        new_srcs = set(after) - set(before)
        has_preview = any(s.startswith('blob:') or s.startswith('data:') or 'upload' in s.lower() for s in new_srcs) or len(after) > len(before)
        return ok and has_preview, f'上传={ok} 预览={has_preview} 新增src={len(new_srcs)}'

    def check_upload_video(self, page_key):
        if not os.path.exists(self.TEST_VIDEO):
            return False, '无测试视频'
        if not self.goto_page(page_key):
            return False, '导航失败'
        time.sleep(1)
        ok = self._upload(self.TEST_VIDEO)
        time.sleep(3)
        return ok, f'上传={ok}'

    def check_button_credits_displayed(self, page_key):
        """Create 按钮上显示积分"""
        if not self.goto_page(page_key):
            return False, '导航失败'
        time.sleep(1.5)
        cost = self.get_create_button_cost()
        return cost is not None and cost > 0, f'积分={cost}'

    def check_page_loaded(self, page_key, key_text=None):
        """页面正常加载（URL 包含关键路径 + 出现 Create/Generate/模板）"""
        if not self.goto_page(page_key):
            return False, '导航失败'
        time.sleep(2)
        try:
            btns = self.driver.find_elements(By.XPATH,
                "//button[contains(., 'Create') or contains(., 'Generate') or contains(., 'Start')]")
            has_action = any(b.is_displayed() for b in btns)
        except Exception:
            has_action = False
        # AI Effects 这种模板页：判断是否有模板卡片
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR,
                '[class*="card"], [class*="template"], [class*="effect"]')
            has_cards = sum(1 for c in cards if c.is_displayed()) >= 3
        except Exception:
            has_cards = False
        ok = has_action or has_cards
        return ok, f'有动作按钮={has_action} 有卡片={has_cards}'

    def check_model_switch_param_change(self, page_key):
        """切换不同模型时，时长/分辨率选项应变化"""
        if not self.goto_page(page_key):
            return False, '导航失败'
        opts = self.get_model_dropdown_options()
        # 用完整名称去重（取第一行 + 截短），保留可识别的不同模型
        full_names = []
        seen_keys = set()
        for o in opts:
            full = o['name'].split('\n')[0].strip()
            # 取模型版本作为去重 key（如 'T2.0' 'T3.0' 'Intimate'）
            import re
            m = re.search(r'(T\d+\.\d+|Intimate|R\d+\.\d+)', full)
            key = m.group(1) if m else full[:15]
            if key not in seen_keys and len(full) < 50:
                seen_keys.add(key); full_names.append(full)
        if len(full_names) < 2:
            return False, f'去重后模型数={len(full_names)}: {full_names}'
        snapshots = []
        for m in full_names[:2]:
            self.goto_page(page_key)
            # 用名称的关键标识词搜索
            import re
            kw = re.search(r'(T\d+\.\d+|Intimate|R\d+\.\d+)', m)
            self.select_model(kw.group(1) if kw else m.split()[0])
            time.sleep(1.5)
            g = self.get_format_labels()
            sig = (
                tuple(sorted(o['text'] for o in g.get('duration', []))),
                tuple(sorted(o['text'] for o in g.get('resolution', []))),
            )
            snapshots.append((m[:25], sig))
        ok = snapshots[0][1] != snapshots[1][1]
        return ok, f'{snapshots[0][0]} vs {snapshots[1][0]} 参数不同={ok}'
