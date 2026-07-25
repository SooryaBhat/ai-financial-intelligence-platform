"""Verify patches were applied correctly."""
import json
from pathlib import Path

nb_dir = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks')

checks = {
    '02_data_preprocessing.ipynb': [
        ('total_amount (not gross_amount)', lambda s: 'total_amount' in s and 'gross_amount' not in s and 'StandardScaler' in s),
    ],
    '05_inventory_prediction.ipynb': [
        ('name_wh rename', lambda s: 'rename' in s and 'name_wh' in s),
    ],
    '07_expense_prediction.ipynb': [
        ('include_groups=False', lambda s: 'include_groups=False' in s),
    ],
    '08_business_health_score.ipynb': [
        ('paid_amount sum fix', lambda s: "('paid_amount', 'sum')" in s),
        ('no lambda invoices', lambda s: "lambda x: x[invoices.loc" not in s),
    ],
    '09_anomaly_detection.ipynb': [
        ('rolling(28) not 28D', lambda s: 'rolling(28,' in s and "'28D'" not in s),
    ],
    '10_model_comparison.ipynb': [
        ('f-string fix', lambda s: "'Task':<30}" not in s),
    ],
}

all_ok = True
for nb_name, check_list in checks.items():
    nb = json.load(open(nb_dir / nb_name, encoding='utf-8'))
    full_src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code')
    
    for desc, fn in check_list:
        ok = fn(full_src)
        status = "OK" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  [{status}] {nb_name}: {desc}")

# Also check universal: no pickle in any notebook
for nb_file in nb_dir.glob('*.ipynb'):
    nb = json.load(open(nb_file, encoding='utf-8'))
    full_src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code')
    if 'import pickle' in full_src:
        print(f"  [FAIL] {nb_file.name}: still has 'import pickle'")
        all_ok = False

if all_ok:
    print("\nAll patch checks PASSED.")
else:
    print("\nSome checks FAILED - review needed.")
