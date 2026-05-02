# V95.2 NameError Fix

Problem:
Render failed with:
NameError: name 'List' is not defined

Fix:
main.py now imports:
from typing import Optional, Dict, Any, List

Also keeps:
- runtime.txt = 3.12.8
- updated requirements compatible with Python 3.12/3.14

Upload/replace these backend files:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt

Then:
Render -> executive-engine-os -> Manual Deploy -> Clear build cache & deploy

Expected:
https://executive-engine-os.onrender.com/health
shows version V95.2
