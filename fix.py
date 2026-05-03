import glob
import os

files = glob.glob('backend/services/*.py') + glob.glob('backend/routes/*.py')

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    if 'eventlet.spawn' in content:
        print(f"Fixing {f}")
        if 'import eventlet' in content and 'from eventlet import tpool' not in content:
            content = content.replace('import eventlet', 'import eventlet\nfrom eventlet import tpool')
            
        content = content.replace('eventlet.spawn', 'tpool.execute')
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
