"""
sync_runner_nb03.py
===================
Ensure fix_and_run_notebooks.py has the exact updated patch_nb03.
"""
import re
from pathlib import Path

runner_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\fix_and_run_notebooks.py')

code = runner_path.read_text(encoding='utf-8')

old_func = """def patch_nb03(src: str) -> str:
    \"\"\"NB03: Revenue Forecasting fixes.\"\"\"
    src = src.replace("if 'sarima_fit' in dir():", "if 'sarima_fit' in vars():")
    return src"""

new_func = """def patch_nb03(src: str) -> str:
    \"\"\"NB03: Revenue Forecasting fixes.\"\"\"
    src = src.replace("if 'sarima_fit' in dir():", "if 'sarima_fit' in globals() or 'sarima_fit' in locals():")
    src = src.replace("if 'sarima_fit' in vars():", "if 'sarima_fit' in globals() or 'sarima_fit' in locals():")
    return src"""

if old_func in code:
    code = code.replace(old_func, new_func)
    runner_path.write_text(code, encoding='utf-8')
    print("Runner updated.")
else:
    print("Runner already up to date.")
