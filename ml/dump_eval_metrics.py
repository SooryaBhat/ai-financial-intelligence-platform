import json
import os
import glob

reports = glob.glob('ml/reports/*_eval.json')
print(f"Found {len(reports)} eval reports:\n")
for r in reports:
    print(f"=== {r} ===")
    with open(r) as f:
        data = json.load(f)
    print(f"Pipeline: {data.get('pipeline')}")
    print(f"Selected model: {data.get('selected_model')}")
    sel = data.get('selected_model')
    candidates = data.get('candidates', {})
    if sel in candidates:
        print(f"Winner metrics: {candidates[sel]}")
    elif 'metrics' in data:
        print(f"Top-level metrics: {data['metrics']}")
    
    if 'approach_c_holdout_company3_metrics' in data:
        print(f"Holdout Co3: {data['approach_c_holdout_company3_metrics']}")
    print()
