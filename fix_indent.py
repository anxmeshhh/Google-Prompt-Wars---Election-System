import glob
import re

files = glob.glob('backend/services/*.py') + glob.glob('backend/routes/*.py')

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    # Replace unindented from eventlet import tpool with matching indentation
    new_content = re.sub(r'([ \t]*)import eventlet\nfrom eventlet import tpool', r'\1import eventlet\n\1from eventlet import tpool', content)
    
    if new_content != content:
        print(f"Fixing indentation in {f}")
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
