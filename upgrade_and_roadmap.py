#!/usr/bin/env python3
# upgrade_and_roadmap.py bootloader — last run completed at 2025-08-08T16:34:31Z UTC
import sys, urllib.request
RAW = "https://raw.githubusercontent.com/g0udurix/LRN/main/upgrade_and_roadmap.py"
try:
    data = urllib.request.urlopen(RAW, timeout=30).read()
    open(__file__, "wb").write(data)
    print("[bootloader] refreshed upgrade_and_roadmap.py from", RAW)
    print("[bootloader] run it again to execute the latest version.")
except Exception as e:
    print("[bootloader] failed to refresh:", e)
    sys.exit(1)
