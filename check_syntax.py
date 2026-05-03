import glob
import py_compile

files = glob.glob('backend/routes/*.py') + glob.glob('backend/services/*.py')
for f in files:
    try:
        py_compile.compile(f, doraise=True)
    except Exception as e:
        print(f"ERROR IN {f}:\n{e}")
