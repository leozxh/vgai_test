"""读取 214 条 case，评估每条的可自动化程度并输出分类报告"""
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

rows = json.load(open(r'D:\vgai_test\data\site_check.json', encoding='utf-8'))
header, rows = rows[0], rows[1:]


def classify(case):
    """根据步骤+预期判断可自动化程度
    A = 完全可自动化（点击、断言文本/URL）
    B = 部分可自动化（涉及第三方跳转/弹窗外部应用，只能验到跳转那一步）
    C = 难自动化（hover 显示气泡、视觉细节、邮件回执等）
    D = 不可自动化（人工感官：动画流畅、视觉布局、Google OAuth 真实授权）
    """
    no, site, module, point, steps, expected = case[0], case[1], case[2], case[3], case[4], case[5]
    text = f'{point} {steps} {expected}'.lower()

    # D: 不可自动化
    if 'google' in text and ('oauth' in text or '授权' in text or '登录' in expected.lower()):
        return 'D', 'Google OAuth 第三方授权'
    if '支付完成' in text or '支付成功回调' in point or 'checkout' in text and '完成' in text:
        return 'D', '真实支付/订阅完成'
    if 'whatsapp web' in text or 'wa.me' in text:
        if '跳转' in expected:
            return 'B', '跳转到外部 WhatsApp'

    # C: 难自动化
    if 'hover' in text or 'hover' in expected.lower():
        return 'C', 'Hover 交互/Tooltip'
    if '动画' in text or '布局正常' in text or '无报错' in text or '视觉' in text:
        return 'C', '视觉/动画判断'
    if '邮件' in expected or '发送' in expected and 'email' in text:
        return 'C', '邮件回执'
    if '复制' in expected and '剪贴板' in text or 'copy link' in text.lower():
        return 'C', '剪贴板'

    # B: 部分可自动化（外部跳转或新标签页）
    if '新标签页' in expected or '新窗口' in expected:
        return 'B', '新标签页打开'
    if '跳转到' in expected and ('checkout' in expected.lower() or 'visiva.ai' in expected.lower() or 'web.whatsapp' in expected.lower()):
        return 'B', '跳转外部域'

    # A: 完全可自动化
    return 'A', '常规 UI 操作'


buckets = {'A': [], 'B': [], 'C': [], 'D': []}
for r in rows:
    if not r[0]:
        continue
    grade, reason = classify(r)
    buckets[grade].append((r[0], r[1], r[2], r[3], reason))

total = sum(len(v) for v in buckets.values())
print(f'总数: {total}')
for g in ['A', 'B', 'C', 'D']:
    print(f'  {g}级: {len(buckets[g])}  ({len(buckets[g])*100/total:.0f}%)')

# 按模块汇总
from collections import defaultdict
mod_grades = defaultdict(lambda: defaultdict(int))
for g in 'ABCD':
    for no, site, mod, point, reason in buckets[g]:
        mod_grades[(site, mod)][g] += 1

print('\n=== 按模块分布 ===')
for (site, mod), grades in mod_grades.items():
    summary = ' '.join(f'{g}:{grades.get(g, 0)}' for g in 'ABCD')
    total_mod = sum(grades.values())
    print(f'  {site:6} | {mod:25} 总 {total_mod:3}  {summary}')

# 输出 C/D 等级的所有 case（人工记录）
with open(r'D:\vgai_test\data\manual_only_cases.txt', 'w', encoding='utf-8') as f:
    for g in ['C', 'D']:
        f.write(f'\n=== {g} 级（{len(buckets[g])} 条）===\n')
        for no, site, mod, point, reason in buckets[g]:
            f.write(f'  [{no}] {site} / {mod} / {point}  ← {reason}\n')

# 输出 A/B 等级到 JSON，给后续脚本用
auto_list = []
for g in ['A', 'B']:
    for no, site, mod, point, reason in buckets[g]:
        # 找回完整原行
        for r in rows:
            if r[0] == no:
                auto_list.append({
                    'id': r[0], 'site': r[1], 'module': r[2], 'point': r[3],
                    'steps': r[4], 'expected': r[5], 'grade': g, 'reason': reason
                })
                break
with open(r'D:\vgai_test\data\auto_cases.json', 'w', encoding='utf-8') as f:
    json.dump(auto_list, f, ensure_ascii=False, indent=2)
print(f'\n已输出可自动化(A+B) {len(auto_list)} 条 → data/auto_cases.json')
print(f'人工 case → data/manual_only_cases.txt')
