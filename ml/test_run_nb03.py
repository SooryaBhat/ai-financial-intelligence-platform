"""
test_run_nb03.py
================
Run 03_revenue_forecasting.ipynb non-interactively and report execution status and cell outputs.
"""
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\03_revenue_forecasting.ipynb')
nb_dir  = nb_path.parent

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

try:
    ep.preprocess(nb, {'metadata': {'path': str(nb_dir)}})
    print("Execution SUCCESSFUL!")
    with open(nb_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
except Exception as e:
    print(f"Execution FAILED: {e}")
    raise e
