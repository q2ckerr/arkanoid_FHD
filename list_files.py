import json
data = json.load(open(r'C:\Users\user\.qoder\cache\projects\5L_arkanoid-16bad010\agent-tools\2dd14735\0054fe19.txt', encoding='utf-8'))
# List ALL python files
for item in data.get('tree', []):
    path = item.get('path', '')
    if path.endswith('.py'):
        print(path)
