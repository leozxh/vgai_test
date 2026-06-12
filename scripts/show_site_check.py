import json
d = json.load(open(r'D:\chrome\download\site_check_report.json', encoding='utf-8'))
p = sum(1 for r in d if r['pass'])
f = len(d) - p
print(f'总 {len(d)} | PASS {p} | FAIL {f}')
for r in d:
    s = 'PASS' if r['pass'] else 'FAIL'
    print(f'  {r["id"]:6} | {r["module"]:14} | {r["point"]:25} | {s} | {r["detail"][:90]}')
