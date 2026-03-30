import traceback
import sys
try:
    import ui
    print("UI module loaded successfully.")
    sys.exit(0)
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
