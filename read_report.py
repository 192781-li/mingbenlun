import json
report = json.load(open(r'C:\Users\lison\Desktop\mingbenlun_fresh\mingben-workbench\references\old_refs_migration_report.json', encoding='utf-8'))
refs = report['refs']
print('=== 定理 top 30 ===')
theorems = sorted(refs.get('定理', {}).items(), key=lambda x: -x[1]['count'])[:30]
for k, v in theorems:
    print(f'  定理{k}: {v["count"]}次, 文件: {v["files"][:3]}')
print()
print('=== 公理 ===')
for k, v in sorted(refs.get('公理', {}).items(), key=lambda x: -x[1]['count']):
    print(f'  公理{k}: {v["count"]}次')
