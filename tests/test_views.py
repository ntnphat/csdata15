"""Chay thu tung trang bang Streamlit AppTest de bat loi runtime."""
import sys
from streamlit.testing.v1 import AppTest

VIEWS = ["overview", "data_quality", "analysis", "rankings", "forecast", "ai_analyst", "report", "admin"]
GUEST = {"id": "guest", "email": "guest@local", "full_name": "Guest", "is_guest": True}

failed = 0
for name in VIEWS:
    at = AppTest.from_file(f"views/{name}.py", default_timeout=180)
    at.session_state["auth_user"] = dict(GUEST)
    at.run()
    if at.exception:
        failed += 1
        print(f"[FAIL] {name}")
        for e in at.exception:
            print("   ", str(e.value)[:400].replace("\n", " | "))
    else:
        print(f"[ OK ] {name}  (markdown={len(at.markdown)}, errors={len(at.error)}, warnings={len(at.warning)})")
        for e in at.error:
            print("    error box:", e.value[:200])

print("\nFAILED:", failed, "/", len(VIEWS))
sys.exit(1 if failed else 0)
