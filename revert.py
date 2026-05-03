import glob

files = glob.glob('backend/services/*.py') + glob.glob('backend/routes/*.py')

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    original = content
    content = content.replace('tpool.execute', 'eventlet.spawn')
    content = content.replace('from eventlet import tpool\n', '')
    
    if original != content:
        print(f"Reverted {f}")
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
