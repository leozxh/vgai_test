import json
data = json.load(open(r'D:\chrome\download\credits_report.json', encoding='utf-8'))
from collections import Counter
total = len(data)
passed = sum(1 for r in data if r['match'] is True)
failed = sum(1 for r in data if r['match'] is False)
errs = sum(1 for r in data if r['error'])
print(f'总计 {total} | PASS {passed} | FAIL {failed} | ERROR {errs}')
print('--- FAIL 项 ---')
for r in data:
    if r['match'] is False:
        print(f"  {r['page']:18} {r['model']:50} {r['duration']:5}/{r['resolution']:6} 按钮={r['displayed']} 实际={r['actual']} 余额 {r['before']}->{r['after']}")
print('--- ERROR 项 ---')
for r in data:
    if r['error']:
        print(f"  {r['page']:18} {r['model']:50} {r['duration']:5}/{r['resolution']:6} err={r['error']}")
print('--- 按 page 分组 ---')
c = Counter()
for r in data:
    if r['match'] is True: c[(r['page'], 'PASS')] += 1
    elif r['match'] is False: c[(r['page'], 'FAIL')] += 1
    elif r['error']: c[(r['page'], 'ERROR')] += 1
for k, v in sorted(c.items()):
    print(f'  {k}: {v}')
