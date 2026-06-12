"""基于 Visiva 站点校验文档 214 条 case 的全量自动化测试

数据驱动：每条 case 调对应 BusinessView 方法，结果写入 HTML+JSON 报告
报告位置: D:\\chrome\\download\\site_check_report.html

运行: python testcase/test_site_check.py [模块名]
不传模块名则跑全部已实现模块。
"""
import os
import sys
import time
import json
import logging
import unittest
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.caps import DriverManager
from businessView.marketingView import MarketingView
from businessView.productNavView import ProductNavView
from businessView.generationView import GenerationView
from businessView.userCenterView import UserCenterView

OUTPUT_DIR = r'D:\chrome\download'
ARG_MODULE = sys.argv[1] if len(sys.argv) > 1 else None


class SiteCheckTest(unittest.TestCase):
    """全量站点校验"""

    results = []

    @classmethod
    def setUpClass(cls):
        cls.driver_manager = DriverManager()
        cls.driver = cls.driver_manager.test_caps()
        cls.mv = MarketingView(cls.driver, base_url='https://visiva.top')
        cls.pv = ProductNavView(cls.driver, base_url='https://visiva.top')
        cls.gv = GenerationView(cls.driver)
        cls.uv = UserCenterView(cls.driver, base_url='https://visiva.top')
        # 读账号
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'account.json'), encoding='utf-8') as f:
                cls.account = json.load(f).get('account1', {})
        except Exception:
            cls.account = {}

    @classmethod
    def tearDownClass(cls):
        cls._save_report(cls)
        if cls.driver:
            cls.driver.quit()

    def _run_cases(self, module_name, cases):
        """统一执行一组 case 并记录结果。cases: [(id, point, callable)]"""
        logging.info(f'\n{"=" * 60}\n{module_name}  ({len(cases)} cases)\n{"=" * 60}')
        for cid, point, fn in cases:
            try:
                ok, detail = fn()
            except Exception as e:
                ok, detail = False, f'EXC: {str(e)[:120]}'
            status = 'PASS' if ok else 'FAIL'
            logging.info(f'  [{status}] {cid} {point}: {detail}')
            self.results.append({
                'id': cid, 'module': module_name, 'point': point,
                'pass': ok, 'detail': detail,
                'ts': time.strftime('%H:%M:%S')
            })

    # ---- 营销站首页 M-1-* ----

    def test_01_marketing_home(self):
        if ARG_MODULE and ARG_MODULE != 'marketing_home':
            self.skipTest('未选中此模块')
        cases = [
            ('M-1-1', 'TDK 检查', self.mv.check_tdk),
            ('M-1-2', 'Logo 跳回首页', self.mv.check_logo_back_home),
            ('M-1-6', '导航 Pricing 跳转', self.mv.check_nav_pricing),
            ('M-1-7', 'Get Started 跳转 /app', self.mv.check_nav_get_started),
            ('M-1-8', '语言切换 /zh-TW', self.mv.check_lang_switch),
            ('M-1-9', 'Hero CTA 跳转', self.mv.check_nav_get_started),
            ('M-1-10', '视频展示区', self.mv.check_video_section),
            ('M-1-11', 'AI Tools 区域', self.mv.check_ai_tools_section),
            ('M-1-12', 'FAQ 展开/折叠', self.mv.check_faq_expand),
            ('M-1-13', '轮播区', self.mv.check_carousel),
            ('M-1-14', 'WhatsApp 浮动按钮', self.mv.check_whatsapp_btn),
            ('M-1-18', 'Cookie Banner', self.mv.check_cookie_banner),
            ('M-1-19', '移动端汉堡菜单', self.mv.check_mobile_menu),
            ('M-1-20', '无 console 异常', self.mv.check_no_console_error),
        ]
        self._run_cases('营销站首页', cases)

    # ---- 营销站定价页 M-2-* ----

    def test_02_marketing_pricing(self):
        if ARG_MODULE and ARG_MODULE != 'marketing_pricing':
            self.skipTest('未选中此模块')
        cases = [
            ('M-2-1', 'TDK', self.mv.check_pricing_tdk),
            ('M-2-2', '套餐展示', self.mv.check_pricing_tiers),
            ('M-2-3', '月/年切换', self.mv.check_pricing_monthly_yearly),
            ('M-2-5', '未登录 Buy Now', self.mv.check_pricing_buy_not_login),
        ]
        self._run_cases('营销站定价页', cases)

    # ---- 营销站法律页 ----

    def test_03_marketing_legal(self):
        if ARG_MODULE and ARG_MODULE != 'marketing_legal':
            self.skipTest('未选中此模块')
        cases = [
            ('M-3-1', 'Terms 可访问', lambda: self.mv.check_legal_page('/terms', 'Terms')),
            ('M-4-1', 'Refund 可访问', lambda: self.mv.check_legal_page('/refund-policy', 'Refund')),
            ('M-6-1', 'Cookie 可访问', lambda: self.mv.check_legal_page('/cookie-policy', 'Cookie')),
            ('M-7-1', 'Disclaimer 可访问', lambda: self.mv.check_legal_page('/disclaimer', 'Disclaimer')),
            ('M-8-1', 'License 可访问', lambda: self.mv.check_legal_page('/license-agreement', 'License')),
            ('M-9-1', 'About 可访问', lambda: self.mv.check_legal_page('/about')),
            ('M-10-1', 'Contact 可访问', lambda: self.mv.check_legal_page('/contact-us')),
            ('M-11-1', 'FAQ 可访问', lambda: self.mv.check_legal_page('/faq')),
            ('M-12-1', 'Spicy 可访问', lambda: self.mv.check_legal_page('/spicy-ai-generator')),
        ]
        self._run_cases('营销站法律/辅助页', cases)

    # ---- P-6-* 登录/注册 ----

    def test_06_login_register(self):
        if ARG_MODULE and ARG_MODULE != 'login':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        cases = [
            ('P-6-1', '未登录访问 /app', self.pv.check_unlogin_app),
            ('P-6-2', '登录弹窗默认状态', self.pv.check_login_modal_default),
            ('P-6-3', '邮箱登录', lambda: self.pv.check_email_login(u, p)),
            ('P-6-6', '密码合规校验', self.pv.check_password_validation),
            ('P-6-9', '18+ 复选取消按钮禁用', self.pv.check_18plus_disabled),
            ('P-6-10', 'Terms/Privacy 链接', self.pv.check_terms_links_in_modal),
        ]
        self._run_cases('登录/注册', cases)

    # ---- P-7-* 产品首页 ----

    def test_07_product_home(self):
        if ARG_MODULE and ARG_MODULE != 'product_home':
            self.skipTest('未选中此模块')
        # 先确保已登录
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-7-1', '/app 加载', self.pv.check_app_loaded),
            ('P-7-2', '4 个入口可见', self.pv.check_app_features),
            ('P-7-3', 'Hot Templates', self.pv.check_hot_templates),
            ('P-7-4', 'Upgrade 入口', self.pv.check_upgrade_visible),
        ]
        self._run_cases('产品首页', cases)

    # ---- P-8-* Header 顶栏 ----

    def test_08_header(self):
        if ARG_MODULE and ARG_MODULE != 'header':
            self.skipTest('未选中此模块')
        cases = [
            ('P-8-1', 'Logo 回营销站', self.pv.check_header_logo_to_marketing),
            ('P-8-2', '礼物图标→奖励中心', self.pv.check_header_gift_icon),
            ('P-8-5', '积分显示', self.pv.check_header_credits),
            ('P-8-6', 'Upgrade 弹升级弹窗', self.pv.check_header_upgrade_modal),
            ('P-8-8', '头像弹 UserMenu', self.pv.check_header_avatar_menu),
        ]
        self._run_cases('Header 顶栏', cases)

    # ---- P-9-* 侧边栏 ----

    def test_09_sidebar(self):
        if ARG_MODULE and ARG_MODULE != 'sidebar':
            self.skipTest('未选中此模块')
        cases = [
            ('P-9-1', 'Home', self.pv.check_sidebar_home),
            ('P-9-2', 'AI Effects', lambda: self.pv.check_sidebar_nav('AI Effects', 'video-effects')),
            ('P-9-3', 'Image to Video', lambda: self.pv.check_sidebar_nav('Image to Video', 'image-to-video')),
            ('P-9-4', 'Text to Video', lambda: self.pv.check_sidebar_nav('Text to Video', 'text-to-video')),
            ('P-9-6', 'Video Extend', lambda: self.pv.check_sidebar_nav('Video Extend', 'video-extend')),
            ('P-9-7', 'Image to Image', lambda: self.pv.check_sidebar_nav('Image to Image', 'image-to-image')),
            ('P-9-8', 'Text to Image', lambda: self.pv.check_sidebar_nav('Text to Image', 'text-to-image')),
            ('P-9-9', 'My Creations', lambda: self.pv.check_sidebar_nav('My Creations', 'creations')),
            ('P-9-12', 'Face Swap 入口隐藏', self.pv.check_sidebar_face_swap_hidden),
        ]
        self._run_cases('侧边栏', cases)

    # ---- P-10-* UserMenu ----

    def test_10_usermenu(self):
        if ARG_MODULE and ARG_MODULE != 'usermenu':
            self.skipTest('未选中此模块')
        cases = [
            ('P-10-1', 'UserMenu Profile 入口', self.pv.check_usermenu_profile),
            ('P-10-9', '退出登录', self.pv.check_usermenu_logout),
        ]
        self._run_cases('UserMenu', cases)

    # ---- P-11-* Image to Video ----

    def test_11_i2v(self):
        if ARG_MODULE and ARG_MODULE != 'i2v':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-11-0', '页面加载', lambda: self.gv.check_page_loaded('i2v')),
            ('P-11-1', '模型列表 ≥2', lambda: self.gv.check_model_list_count('i2v', 2)),
            ('P-11-2', '模型切换参数变化', lambda: self.gv.check_model_switch_param_change('i2v')),
            ('P-11-3', '图片上传', lambda: self.gv.check_upload_image('i2v')),
            ('P-11-5', 'Prompt 输入', lambda: self.gv.check_prompt_input('i2v')),
            ('P-11-6', 'Intimate R4.0 时长', lambda: self.gv.check_duration_options('i2v', 'Intimate', ['5s', '10s'])),
            ('P-11-7', 'Pro T3.0 时长', lambda: self.gv.check_duration_options('i2v', 'Pro', ['5s', '8s', '10s'])),
            ('P-11-9', 'Intimate R4.0 分辨率', lambda: self.gv.check_resolution_options('i2v', 'Intimate', ['480P', '720P', '1080P'])),
            ('P-11-16', 'Create 按钮显示积分', lambda: self.gv.check_button_credits_displayed('i2v')),
        ]
        self._run_cases('Image to Video', cases)

    # ---- P-12-* Text to Video ----

    def test_12_t2v(self):
        if ARG_MODULE and ARG_MODULE != 't2v':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-12-0', '页面加载', lambda: self.gv.check_page_loaded('t2v')),
            ('P-12-1', '模型列表 ≥2', lambda: self.gv.check_model_list_count('t2v', 2)),
            ('P-12-2', '模型切换参数变化', lambda: self.gv.check_model_switch_param_change('t2v')),
            ('P-12-3', 'Prompt 输入', lambda: self.gv.check_prompt_input('t2v')),
            ('P-12-4', 'Create 按钮显示积分', lambda: self.gv.check_button_credits_displayed('t2v')),
        ]
        self._run_cases('Text to Video', cases)

    # ---- P-14-* Video Extend ----

    def test_14_video_extend(self):
        if ARG_MODULE and ARG_MODULE != 've':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-14-0', '页面加载', lambda: self.gv.check_page_loaded('ve')),
            ('P-14-1', '视频上传', lambda: self.gv.check_upload_video('ve')),
            ('P-14-2', 'Prompt 输入', lambda: self.gv.check_prompt_input('ve')),
            ('P-14-3', 'Create 按钮显示积分', lambda: self.gv.check_button_credits_displayed('ve')),
        ]
        self._run_cases('Video Extend', cases)

    # ---- P-15-* Image to Image ----

    def test_15_i2i(self):
        if ARG_MODULE and ARG_MODULE != 'i2i':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-15-0', '页面加载', lambda: self.gv.check_page_loaded('i2i')),
            ('P-15-1', '图片上传', lambda: self.gv.check_upload_image('i2i')),
            ('P-15-2', 'Prompt 输入', lambda: self.gv.check_prompt_input('i2i')),
            ('P-15-3', 'Create 按钮显示积分', lambda: self.gv.check_button_credits_displayed('i2i')),
        ]
        self._run_cases('Image to Image', cases)

    # ---- P-16-* Text to Image ----

    def test_16_t2i(self):
        if ARG_MODULE and ARG_MODULE != 't2i':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-16-0', '页面加载', lambda: self.gv.check_page_loaded('t2i')),
            ('P-16-1', 'Prompt 输入', lambda: self.gv.check_prompt_input('t2i')),
            ('P-16-2', 'Create 按钮显示积分', lambda: self.gv.check_button_credits_displayed('t2i')),
        ]
        self._run_cases('Text to Image', cases)

    # ---- P-18-* AI Effects ----

    def test_18_ai_effects(self):
        if ARG_MODULE and ARG_MODULE != 'effects':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-18-0', '页面加载', lambda: self.gv.check_page_loaded('effects')),
        ]
        self._run_cases('AI Effects', cases)

    # ---- P-19-* 奖励中心 ----

    def test_19_rewards(self):
        if ARG_MODULE and ARG_MODULE != 'rewards':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-19-1', '奖励中心打开', self.uv.check_rewards_open),
            ('P-19-4', '邀请链接', self.uv.check_rewards_referral_link),
            ('P-19-6', '邀请统计', self.uv.check_rewards_stats),
        ]
        self._run_cases('奖励中心', cases)

    # ---- P-21-* Profile ----

    def test_21_profile(self):
        if ARG_MODULE and ARG_MODULE != 'profile':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-21-1', 'Profile 页面加载', self.uv.check_profile_loaded),
            ('P-21-2', '显示邮箱', self.uv.check_profile_email_shown),
            ('P-21-3', 'Username 输入', self.uv.check_profile_username),
            ('P-21-4', '密码修改入口', self.uv.check_profile_password_change),
            ('P-21-5', '订阅信息', self.uv.check_profile_subscription_info),
            ('P-21-6', '积分显示', self.uv.check_profile_credits_shown),
        ]
        self._run_cases('Profile', cases)

    # ---- P-22-* My Creations ----

    def test_22_creations(self):
        if ARG_MODULE and ARG_MODULE != 'creations':
            self.skipTest('未选中此模块')
        u = self.account.get('username', '')
        p = self.account.get('password', '')
        try:
            self.pv.check_email_login(u, p)
        except Exception:
            pass
        cases = [
            ('P-22-1', 'Video Tab', self.uv.check_creations_video_tab),
            ('P-22-2', 'Image Tab', self.uv.check_creations_image_tab),
            ('P-22-3', '无限滚动', self.uv.check_creations_infinite_scroll),
            ('P-22-4-5', '作品预览', self.uv.check_creations_preview),
        ]
        self._run_cases('My Creations', cases)

    # ---- P-23-* 支付流程 ----

    def test_23_payment(self):
        if ARG_MODULE and ARG_MODULE != 'payment':
            self.skipTest('未选中此模块')
        cases = [
            ('P-23-1', '升级弹窗', self.uv.check_upgrade_modal),
            ('P-23-3', 'Buy Now 新标签页', self.uv.check_pricing_buy_now_redirect),
        ]
        self._run_cases('支付流程', cases)

    # ---- 报告输出 ----

    def _save_report(self):
        results = self.results
        if not results:
            return

        total = len(results)
        passed = sum(1 for r in results if r['pass'])
        failed = total - passed
        rate = passed / total * 100 if total else 0
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        rows = ''
        for i, r in enumerate(results, 1):
            status = ('<span style="color:green;font-weight:bold">PASS</span>'
                      if r['pass']
                      else '<span style="color:red;font-weight:bold">FAIL</span>')
            rows += f"""<tr>
                <td>{i}</td><td>{r['id']}</td><td>{r['module']}</td>
                <td>{r['point']}</td><td style="text-align:center">{status}</td>
                <td>{r['detail']}</td><td>{r['ts']}</td>
            </tr>\n"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Visiva 站点校验自动化报告</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 20px; background: #f5f5f5; }}
h1 {{ color: #333; }}
.summary {{ background: #fff; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px;
            display: flex; gap: 30px; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.summary .num {{ font-size: 28px; font-weight: bold; }}
.summary .label {{ font-size: 13px; color: #666; }}
.pass {{ color: green; }} .fail {{ color: red; }}
table {{ border-collapse: collapse; width: 100%; background: #fff;
         box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
th {{ background: #2d2d2d; color: #fff; padding: 10px 12px; text-align: left; font-size: 13px; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 13px; }}
tr:hover {{ background: #f9f9f9; }}
.footer {{ margin-top: 15px; color: #999; font-size: 12px; }}
</style></head><body>
<h1>Visiva 站点校验自动化报告</h1>
<div class="summary">
    <div><div class="num">{total}</div><div class="label">总计</div></div>
    <div><div class="num pass">{passed}</div><div class="label">通过</div></div>
    <div><div class="num fail">{failed}</div><div class="label">失败</div></div>
    <div><div class="num" style="color:#1a73e8">{rate:.1f}%</div><div class="label">通过率</div></div>
</div>
<table>
<thead><tr>
    <th>#</th><th>编号</th><th>模块</th><th>校验点</th>
    <th>结果</th><th>详情</th><th>时间</th>
</tr></thead>
<tbody>
{rows}
</tbody></table>
<div class="footer">执行时间: {now} | 工具: Selenium + Python | 数据源: Visiva 站点校验文档</div>
</body></html>"""

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        out_path = os.path.join(OUTPUT_DIR, 'site_check_report.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        logging.info(f'\n报告: {out_path}')
        with open(os.path.join(OUTPUT_DIR, 'site_check_report.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logging.info(f'\n{"=" * 60}\n总计 {total} | PASS {passed} | FAIL {failed} | 通过率 {rate:.1f}%\n{"=" * 60}')


if __name__ == '__main__':
    # 忽略命令行参数避免被 unittest 解析
    unittest.main(argv=[sys.argv[0]], verbosity=2)
