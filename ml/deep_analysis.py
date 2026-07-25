"""
Deep analysis of all notebooks for potential runtime errors.
"""
import json
from pathlib import Path

nb_dir = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks')

issues = []

for nb_file in sorted(nb_dir.glob('*.ipynb')):
    nb = json.load(open(nb_file, encoding='utf-8'))
    
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] != 'code':
            continue
        src = ''.join(cell['source'])
        
        # Check for 'dir()' usage (NB03 uses 'if sarima_fit in dir()')  
        if "'sarima_fit' in dir()" in src:
            issues.append(f"{nb_file.name} Cell {i}: uses 'in dir()' for variable check - may not work with nbconvert")
        
        # Check for display() calls  
        if 'display(' in src:
            issues.append(f"{nb_file.name} Cell {i}: uses display() - OK in Jupyter but need IPython")
        
        # Check for axis=1 in variance calculation with numpy  
        if "np.where(d['variance'] > 0, 'tomato', 'steelblue')" in src:
            issues.append(f"{nb_file.name} Cell {i}: np.where with pandas Series - check alignment")
        
        # Check for 'if sarima_fit in dir():'
        if "if 'sarima_fit' in dir():" in src:
            issues.append(f"{nb_file.name} Cell {i}: 'if sarima_fit in dir():' - should be 'if sarima_fit is not None'")
        
        # Check for 'weighted_score_total' referenced before potential failure
        if 'weighted_score_total' in src and 'TASK_WEIGHTS' not in src:
            issues.append(f"{nb_file.name} Cell {i}: weighted_score_total used but may not be defined if NB10 runs standalone")

print("Potential Issues Found:")
for issue in issues:
    print(f"  - {issue}")

if not issues:
    print("  No additional issues found.")
