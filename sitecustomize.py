# Ensure project root is on sys.path so 'lrn' package is importable in tests without installation
import os, sys
root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)